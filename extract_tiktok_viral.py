import os
import time
import json
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\tiktok_fyp_database.json"
PROFILE_PATH = r"d:\APPS - ANTIGRAVITY\Synapse\.playwright_profile"

def parse_count(text):
    if not text:
        return 0
    text = text.upper()
    multiplier = 1
    if 'K' in text:
        multiplier = 1000
        text = text.replace('K', '')
    elif 'M' in text:
        multiplier = 1000000
        text = text.replace('M', '')
    
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0

def calculate_sigma(shares, saves):
    if saves == 0:
        return 0
    return round((shares / saves) * 100, 2)

def determine_category(sigma):
    if sigma >= 200:
        return "Hyper-Viral (Extremely High Social Currency)"
    elif sigma >= 100:
        return "Viral (High Social Currency)"
    elif sigma >= 50:
        return "Trending (Good Shareability)"
    else:
        return "Standard (Low Shareability)"

def get_db():
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            try:
                db_data = json.load(f)
                if isinstance(db_data, list):
                     return db_data
                return []
            except Exception:
                return []
    return []

def save_db(db):
    try:
        if os.path.exists(DATABASE_PATH):
            with open(DATABASE_PATH + '.bak', 'w', encoding='utf-8') as f:
             json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        pass

    with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def check_if_ad(page):
    try:
        is_ad = page.evaluate('''(function() {
            let elements = document.querySelectorAll('span, p, div');
            for(let el of elements){
                if(el.innerText && (el.innerText.includes('Patrocinado') || el.innerText.includes('Sponsored'))){
                    return true;
                }
            }
            return false;
        })()''')
        return is_ad
    except Exception:
        return False

def extract_current_video_data(page):
    try:
        data = page.evaluate('''(function() {
            let authorEl = document.querySelector('h3[data-e2e="video-author-uniqueid"], a[data-e2e="video-author-uniqueid"]');
            
            let likeEl = document.querySelector('strong[data-e2e="like-count"]');
            let commEl = document.querySelector('strong[data-e2e="comment-count"]');
            let shareEl = document.querySelector('strong[data-e2e="share-count"]');
            // 'saves' generally doesn't have a reliable data-e2e sometimes, so try 'undefined-count' or find the bookmark icon
            let saveEl = document.querySelector('strong[data-e2e="undefined-count"], strong[data-e2e="bookmark-count"]');
            
            let captionEl = document.querySelector('div[data-e2e="video-desc"]');
            
            let res = {
                author: authorEl ? authorEl.innerText : "Unknown",
                caption: captionEl ? captionEl.innerText : "",
                likes: likeEl ? likeEl.innerText : "0",
                comments: commEl ? commEl.innerText : "0",
                shares: shareEl ? shareEl.innerText : "0",
                saves: saveEl ? saveEl.innerText : "0",
            };
            
            // Best effort fallback if the exact tags above failed
            if(res.likes === "0" && res.comments === "0"){
                let strongs = document.querySelectorAll('button strong');
                if(strongs.length >= 3){
                    res.likes = strongs[0].innerText || "0";
                    res.comments = strongs[1].innerText || "0";
                    res.saves = strongs[2].innerText || "0";
                    res.shares = strongs[3] ? strongs[3].innerText : "0";
                }
            }
            return res;
        })()''')
        
        return {
            "author": data["author"].strip(),
            "caption": data["caption"].strip(),
            "metrics": {
                "likes": parse_count(data["likes"]),
                "comments": parse_count(data["comments"]),
                "saves": parse_count(data["saves"]),
                "shares": parse_count(data["shares"])
            }
        }
    except Exception as e:
        logging.error(f"Error extracting data: {e}")
        return None

def main():
    db = get_db()
    
    videos_collected = sum(len(batch.get("videos", [])) for batch in db)
    target_videos = 500
    
    if videos_collected >= target_videos:
        logging.info("Already reached 500 videos!")
        return
        
    logging.info(f"Loaded database. Currently have {videos_collected} videos.")
    logging.info(f"Target is {target_videos}. Missing {target_videos - videos_collected}.")

    seen_authors = set()
    for batch in db:
        for v in batch.get("videos", []):
            author = v.get("author")
            if author:
                 seen_authors.add(author)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 720}
        )
        page = context.pages[0] if context.pages else context.new_page()
        stealth_sync(page)

        logging.info("Acessando TikTok FYP...")
        page.goto("https://www.tiktok.com/foryou", timeout=60000)
        
        logging.info("Aguardando 60s para carregar a pagina inicial, contornar verificacoes anti-bot e permitir login manual (se necessario)...")
        page.wait_for_timeout(60000)
        
        consecutive_errors = 0
        current_batch_videos = []
        
        while videos_collected < target_videos:
            try:
                logging.info("Assistindo video para simular watch time (8 segundos)...")
                page.wait_for_timeout(8000)
                
                if check_if_ad(page):
                    logging.info("[-] Patrocinado detectado. Pulando...")
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(1500)
                    consecutive_errors = 0
                    continue
                    
                data = extract_current_video_data(page)
                author = data["author"] if data else "Unknown"
                
                if author == "Unknown" or not author:
                    consecutive_errors += 1
                    logging.warning(f"[-] Nao foi possivel ler os dados corretamente (Erro domina? Captcha?). Pulando... ({consecutive_errors}/5)")
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(2000)
                    
                    if consecutive_errors > 5:
                        logging.error("Multiplos erros consecutivos, possivel captcha. Pausando script por 30s...")
                        page.wait_for_timeout(30000)
                        consecutive_errors = 0
                    continue
                else:
                    consecutive_errors = 0
                
                if author in seen_authors:
                    logging.info(f"[-] Autor repetido ({author}). Pulando...")
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(1500)
                    continue
                
                shares = data["metrics"].get("shares", 0)
                saves = data["metrics"].get("saves", 0)
                likes = data["metrics"].get("likes", 0)
                comments = data["metrics"].get("comments", 0)
                sigma = calculate_sigma(shares, saves)
                cat = determine_category(sigma)
                
                videos_collected += 1
                
                video_record = {
                    "author": author,
                    "caption": data["caption"][:200],
                    "likes": likes,
                    "comments": comments,
                    "saves": saves,
                    "shares": shares,
                    "sigma_ratio_calculated": sigma,
                    "category": cat
                }
                
                current_batch_videos.append(video_record)
                seen_authors.add(author)
                
                logging.info(f"[+] Video {videos_collected}/500 coletado! (Autor: {author} | Sigma: {sigma}%)")
                
                # Save batch explicitly after 10 videos (or if it hits 500)
                if len(current_batch_videos) >= 10 or videos_collected >= target_videos:
                     new_batch = {
                         "batch_timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         "videos": current_batch_videos
                     }
                     db.append(new_batch)
                     save_db(db)
                     logging.info(f"==> Novo Micro-Batch salvo com sucesso! (Total extraido: {videos_collected}/500)")
                     current_batch_videos = []
                
                # Ir pro proximo video
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(1500)
                
            except Exception as e:
                 logging.error(f"Erro inesperado no laco principal: {e}")
                 page.wait_for_timeout(5000)
                 page.keyboard.press("ArrowDown")
                 
        save_db(db) # Final save is redundant since the array handles up to the exact count, but good measure.
        logging.info("SUCESSO! Meta de 500 videos atingida perfeitamente pela automacao stealth.")
        context.close()

if __name__ == "__main__":
    main()
