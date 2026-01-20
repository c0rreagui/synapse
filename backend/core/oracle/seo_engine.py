import requests
from PIL import Image
from io import BytesIO
from core.oracle.client import oracle_client
import json

class SEOEngine:
    def __init__(self):
        self.client = oracle_client

    def audit_profile(self, metadata: dict) -> dict:
        """
        Multimodal audit of a profile.
        1. Text Analysis (Bio, Username)
        2. Vision Analysis (Avatar)
        """
        score = 0
        details = []
        
        # 1. Text Analysis
        bio = metadata.get("bio", "") or metadata.get("bio_description", "") or metadata.get("signature", "")
        if not bio:
            details.append({"type": "warning", "msg": "Biografia vazia. Oportunidade perdida."})
        elif len(bio) < 10:
            details.append({"type": "warning", "msg": "Bio muito curta."})
            score += 10
        else:
            score += 30
            details.append({"type": "success", "msg": "Tamanho da bio OK."})

        # 2. Vision Analysis (Avatar)
        avatar_url = metadata.get("avatar_url") or metadata.get("avatar_larger")
        vision_score = 0
        vision_feedback = "Sem avatar para analisar."

        if avatar_url:
            try:
                # Download Image (Mimic Browser to avoid 403)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.tiktok.com/'
                }
                response = requests.get(avatar_url, headers=headers, timeout=10, verify=False)
                
                # If download fails (403/404), throw to trigger fallback
                if response.status_code != 200:
                    raise Exception(f"Download HTTP {response.status_code}")

                img = Image.open(BytesIO(response.content))
                
                # Convert to RGB/JPEG for compatibility
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Oracle Prompt
                prompt = [
                    "Voce e um especialista em Branding de Redes Sociais. Analise esta foto de perfil.",
                    img,
                    """
                    Responda SOMENTE um JSON neste formato:
                    {
                        "score": 0-100,
                        "impression": "string curta descrevendo a vibe",
                        "pros": ["ponto forte 1", "ponto forte 2"],
                        "cons": ["ponto fraco 1"],
                        "verdict": "Profissional" | "Amador" | "Confuso"
                    }
                    """
                ]
                
                try:
                    ai_res = self.client.generate_content(prompt)
                    # Extract JSON
                    txt = ai_res.text
                    if "```json" in txt:
                        txt = txt.split("```json")[1].split("```")[0]
                    elif "```" in txt:
                            txt = txt.split("```")[1].split("```")[0]
                            
                    vision_data = json.loads(txt)
                    vision_score = vision_data.get("score", 50)
                    vision_feedback = vision_data.get("impression", "Analise concluida")
                    
                    details.append({
                        "type": "vision", 
                        "data": vision_data
                    })
                    score += (vision_score * 0.5) # Weight Vision 50%
                    
                except Exception as e:
                    raise e # Trigger outer fallback

            except Exception as e:
                print(f"Vision Analysis unavailable: {e}")
                # FALLBACK: Text-Only Analysis
                try:
                    fallback_prompt = f"""
                    Sou um especialista de Branding. Não consigo ver o avatar (Erro Download), mas analise este perfil pelo nome e bio:
                    Username: {metadata.get('username')}
                    Bio: {bio}
                    
                    Responda JSON:
                    {{
                        "score": 50,
                        "impression": "Análise baseada apenas em Texto (Avatar indisponível). Bio sugere...",
                        "pros": ["Texto descritivo"],
                        "cons": ["Avatar não carregou"],
                        "verdict": "Incompleto"
                    }}
                    """
                    fb_res = self.client.generate_content(fallback_prompt)
                    fb_txt = fb_res.text.replace("```json", "").replace("```", "").strip()
                    vision_data = json.loads(fb_txt)
                    vision_score = vision_data.get("score", 50) # Update local var
                    
                    details.append({
                        "type": "warning",
                        "msg": f"Análise Visual indisponível. Relatório gerado via Texto (Fallback).",
                    })
                    details.append({
                        "type": "vision",
                        "data": vision_data
                    })
                    score += (vision_score * 0.5) # Weight Vision 50%
                except:
                    details.append({"type": "error", "msg": "Falha total na Análise de Branding."})
                    score += 50
        else:
            score += 0 

        # 3. Content Visual Analysis (Latest Video Cover)
        recent_videos = metadata.get("recent_videos", [])
        if recent_videos and len(recent_videos) > 0:
            latest_video = recent_videos[0]
            cover_url = latest_video.get("cover") or latest_video.get("dynamic_cover")
            
            if cover_url:
                try:
                    # Download Cover
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://www.tiktok.com/'
                    }
                    response = requests.get(cover_url, headers=headers, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        cover_img = Image.open(BytesIO(response.content))
                        if cover_img.mode in ("RGBA", "P"):
                            cover_img = cover_img.convert("RGB")
                            
                        # Vision Prompt
                        prompt = [
                            "Analise esta capa (thumbnail) do video mais recente deste perfil.",
                            cover_img,
                            """
                            Responda SOMENTE JSON:
                            {
                                "score": 0-100,
                                "hook_strength": "Fraco" | "Medio" | "Forte",
                                "visual_appeal": "comentario sobre cores/texto",
                                "improvement_tip": "dica para melhorar a capa"
                            }
                            """
                        ]
                        
                        ai_res = self.client.generate_content(prompt)
                        txt = ai_res.text.replace("```json", "").replace("```", "").strip()
                        cover_data = json.loads(txt)
                        
                        details.append({
                            "type": "video_vision",
                            "data": cover_data,
                            "msg": "Análise Visual da Última Capa"
                        })
                        score += (cover_data.get("score", 50) * 0.2) # Bonus points
                        
                except Exception as e:
                    print(f"Content Vision Failed: {e}")
                    details.append({"type": "warning", "msg": f"Erro na análise visual do conteúdo: {str(e)}"})

        # 4. Full Page Vibe Analysis (New)
        screenshot_path = metadata.get("screenshot_path")
        if screenshot_path:
            try:
                import os
                if os.path.exists(screenshot_path):
                    vibe_data = self.analyze_full_page_vibe(screenshot_path)
                    
                    details.append({
                        "type": "full_page_vibe",
                        "data": vibe_data,
                        "msg": "Análise Visual Completa (Vibe Check)"
                    })
                    score += (vibe_data.get("score", 50) * 0.3) # Weight 30%
            except Exception as e:
                 print(f"Full Page Vision Failed: {e}")
                 details.append({"type": "warning", "msg": f"Erro no Vibe Check: {e}"})

        # Finalize
        total_score = min(100, int(score))
        return {
            "total_score": total_score,
            "vision_score": vision_score,
            "details": details,
            "profile_overiew": {
                "username": metadata.get("unique_id") or metadata.get("username"),
                "bio": bio
            }
        }
    
    def analyze_full_page_vibe(self, screenshot_path: str) -> dict:
        """
        Analyzes the full page screenshot for branding cohesion.
        Called by Oracle before/during audit.
        """
        try:
            img = Image.open(screenshot_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            prompt = [
                "Analise este screenshot da página inteira do perfil TikTok.",
                img,
                """
                Responda SOMENTE JSON:
                {
                    "score": 0-100,
                    "layout_quality": "Clean" | "Crowded" | "Professional",
                    "branding_consistency": "comentario sobre a consistencia visual (cores, thumbnails)",
                    "vibe_check": "Qual a 'energia' do perfil? (Ex: Caótico, Minimalista, Corporate, Gamer)",
                    "improvement_action": "O que mudar no layout/identidade visual?"
                }
                """
            ]
            
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)
        except Exception as e:
             return {"error": str(e)}

    def competitor_spy(self, target_username: str) -> dict:
        """
        Spy on a competitor.
        MOCK DATA for scraping, REAL AI for analysis.
        """
        
        # MOCKED Scraped Data (Simulating what a scraper would return)
        # MOCKED Scraped Data (Smart Demo)
        if any(x in target_username.lower() for x in ["game", "zoka", "play", "cortes"]):
             mock_scraped_data = {
                "username": target_username,
                "followers": 554000,
                "bio": "Gamer lifestyle 🎮 | Lives todos os dias | Cola na grade!",
                "recent_posts": [
                    {"desc": "O susto que eu tomei nesse jogo kkkk", "views": 45000},
                    {"desc": "Melhor jogada da semana #clips", "views": 120000},
                    {"desc": "Live ON! Corre pra assistir", "views": 32000}
                ],
                "top_hashtags": ["#gaming", "#streamer", "#clips", "#viral"]
            }
        else:
             mock_scraped_data = {
                "username": target_username,
                "followers": 15400,
                "bio": "Marketing Digital sem enrolação 🚀 | Te ensino a vender todo dia | 👇 Aula Gratuita",
                "recent_posts": [
                    {"desc": "3 Erros que matam seu alcance #marketing #dicas", "views": 4500},
                    {"desc": "Como fiz R$10k em 7 dias (Case real)", "views": 12000},
                    {"desc": "Pare de postar conteudo ruim!", "views": 3200}
                ],
                "top_hashtags": ["#marketingdigital", "#vendas", "#empreendedorismo"]
            }
        
        # Oracle Analysis (Turbo Mode - BRUTAL)
        prompt = f"""
        Atue como um Consultor de Growth Hacking EXTREMAMENTE CRÍTICO e DATA-DRIVEN.
        Analise este perfil concorrente sem piedade.
        
        Dados do Alvo:
        {json.dumps(mock_scraped_data, indent=2)}
        
        Sua missão é DESTRUIR a estratégia deles e encontrar brechas para eu dominar.
        NÃO dê conselhos genéricos ("melhore a bio"). Dê táticas de guerrilha.
        
        Responda em JSON compatível com o schema:
        {{
            "niche_detected": "Nicho exato (ex: Low-Ticket Info Product)",
            "weakness_exposed": "Ache o ponto fraco. (Ex: 'Eles tem views mas não vendem nada pq o CTA é fraco', 'O conteúdo é repetitivo e o público está cansado'). Seja ácido.",
            "content_hooks_to_steal": [
                "Hook específico derivado dos posts deles que funcionaram",
                "Hook 2"
            ],
            "growth_strategy_detected": "Engenharia reversa do funil deles. O que eles estão fazendo nos bastidores?",
            "better_bio_suggestion": "Reescreva a bio deles para humilhar a atual em termos de conversão."
        }}
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            
            analysis = json.loads(txt)
            return {
                "scraped_data": mock_scraped_data,
                "analysis": analysis
            }
        except Exception as e:
            return {"error": str(e), "scraped_data": mock_scraped_data}

    def auto_fix_bio(self, current_bio: str, niche: str) -> list:
        prompt = f"""
        Atue como Copywriter Senior de TikTok.
        Bio Atual: "{current_bio}"
        Nicho: "{niche}"
        
        Gere 5 opcoes de Bio altamente conversivas (max 80 caracteres, usar emojis).
        Use gatilhos mentais de Autoridade, Prova Social ou Urgência.
        
        Retorne APENAS um JSON array de strings: ["Opcao 1", ..., "Opcao 5"]
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                 txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except:
            return ["Falha ao gerar bios. Tente novamente."]

    def generate_content_metadata(self, filename: str, niche: str = "General", duration: int = 0) -> dict:
        """
        Generates Viral Caption and Hashtags based on Filename context.
        Used by Ingestion to pre-populate metadata.
        """
        # Clean filename
        clean_name = filename.replace("_", " ").replace("-", " ").replace(".mp4", "")
        
        prompt = f"""
        Atue como um Estrategista de Conteúdo Viral (TikTok/Reels).
        Analise este arquivo de vídeo que acabou de ser enviado:
        
        Nome do Arquivo: "{clean_name}"
        Nicho do Perfil: "{niche}"
        
        Tarefa:
        1. Crie uma LEGENDA (Caption) altamente engajadora (curta, com pergunta ou gancho).
        2. Selecione 15 HASHTAGS otimizadas para este nicho.
        3. Estime um "Potencial Viral" (0-100) baseado no tema sugerido pelo nome.
        
        Responda APENAS JSON:
        {{
            "suggested_caption": "string",
            "hashtags": ["#tag1", "#tag2"],
            "viral_score": 85,
            "viral_reason": "Explica por que este tema funciona"
        }}
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except Exception as e:
            print(f"Content Gen Error: {e}")
            return {
                "suggested_caption": f"{clean_name} - Confira!",
                "hashtags": ["#viral", "#fyp"],
                "viral_score": 50,
                "viral_reason": f"Erro na IA: {str(e)}"
            }

seo_engine = SEOEngine()
