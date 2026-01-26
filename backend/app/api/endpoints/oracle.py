from fastapi import APIRouter, HTTPException
from core.oracle import oracle_client
from core.oracle import oracle  # Unified Oracle

router = APIRouter()

# ========== UNIFIED ORACLE ENDPOINTS ==========

@router.get("/status")
async def oracle_status():
    """Get Oracle status with all faculties."""
    return oracle.ping()

@router.post("/full-scan/{username}")
async def full_scan(username: str):
    """
    Complete profile analysis using all Oracle faculties.
    (Sense + Mind)
    """
    result = await oracle.full_scan(username)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # 🧠 AUTO-LEARN: Save 'best_times' for Scheduler
    try:
        from core import session_manager
        # Attempt to find profile_id by username
        sessions = session_manager.list_available_sessions()
        profile_id = None
        target_user = username.lower().replace('@', '')
        
        for s in sessions:
            if s.get("username", "").lower() == target_user:
                profile_id = s.get("id")
                break
        
        # Heuristic fallback
        if not profile_id and session_manager.session_exists(username):
            profile_id = username

        # Extract best times from strategic_analysis (Mind Faculty output)
        if profile_id and "strategic_analysis" in result:
            strategy = result["strategic_analysis"]
            if "best_times" in strategy:
                from fastapi.concurrency import run_in_threadpool
                await run_in_threadpool(session_manager.update_profile_metadata, profile_id, {
                    "oracle_best_times": strategy["best_times"],
                    "oracle_last_run": "now" 
                })
                print(f"✅ Oracle Insight: Saved {len(strategy['best_times'])} optimal times for {profile_id}")

        # 📸 AUTO-LEARN: Save 'latest_videos' & 'stats' for Deep Analytics
        if profile_id and "raw_data" in result:
             raw = result["raw_data"]
             updates = {}
             
             # Save Stats (Followers, Likes, etc)
             if "followers" in raw:
                 updates["stats"] = {
                     "followerCount": raw.get("followers"),
                     "heartCount": raw.get("likes"),
                     "followingCount": raw.get("following"),
                     "videoCount": len(raw.get("videos", []))
                 }

             # Save Videos (Top 10 for Analytics)
             if "videos" in raw and raw["videos"]:
                 # Map scraper video format to Metadata format if needed, or save raw
                 # Scraper: {views, link, index}
                 # Aggregator expects: {stats: {playCount, diggCount}, createTime}
                 # We need to enrich or map. Scraper currently only gets views.
                 # Let's save what we have, Aggregator handles missing keys gracefully-ish
                 enrich_videos = []
                 for v in raw["videos"]:
                     # Convert "1.2M" to integer for Aggregator
                     views_str = v.get("views", "0").upper()
                     multiplier = 1
                     if "K" in views_str:
                         multiplier = 1000
                         views_str = views_str.replace("K", "")
                     elif "M" in views_str:
                         multiplier = 1000000
                         views_str = views_str.replace("M", "")
                     
                     try:
                         view_count = int(float(views_str) * multiplier)
                     except:
                         view_count = 0

                     enrich_videos.append({
                         "stats": {
                             "playCount": view_count,
                             "diggCount": 0, # Scraper simple didn't get this
                             "commentCount": 0
                         },
                         "createTime": 0, # We don't have date yet from simple scraper
                         "link": v.get("link")
                     })

                 updates["latest_videos"] = enrich_videos

             if updates:
                 from fastapi.concurrency import run_in_threadpool
                 await run_in_threadpool(session_manager.update_profile_metadata, profile_id, updates)
                 print(f"✅ Oracle Insight: Persisted stats & {len(updates.get('latest_videos', []))} videos for {profile_id}")

    except Exception as e:
        print(f"⚠️ Failed to auto-save oracle insights: {e}")

    return result

@router.post("/spy/{target_username}")
async def spy_competitor_unified(target_username: str):
    """
    Deep competitive analysis using unified Oracle.
    """
    result = await oracle.spy_competitor(target_username)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# ========== LEGACY ENDPOINTS (for backward compatibility) ==========


@router.get("/ping")
async def ping_oracle():
    """Checks connection with Gemini."""
    result = oracle_client.ping()
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result

@router.post("/collect")
async def collect_data(username: str):
    """
    Triggers the Oracle Collector to scrape a TikTok profile.
    """
    from core.oracle.collector import oracle_collector
    
    result = await oracle_collector.collect_tiktok_profile(username)
    if "error" in result:
         raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/analyze")
async def analyze_profile(username: str):
    """
    Full Flow: Scrape TikTok -> Analyze with Gemini -> Return Strategy
    migrated to use Unified Oracle Sense + Mind
    """
    # Use Unified Oracle which has the Session fix
    result = await oracle.full_scan(username)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    # BACKWARD COMPATIBILITY: Map unified result to legacy format expected by frontend
    # Unified returns: { "username": ..., "raw_data": ..., "strategic_analysis": ... }
    # Legacy expected: { "profile": ..., "analysis": ..., "timestamp": ... }
    
    analysis_data = result.get("strategic_analysis", {})
    raw_data = result.get("raw_data", {})
    
    # Auto-save insights logic (preserved from legacy)
    try:
        from core import session_manager
        sessions = session_manager.list_available_sessions()
        profile_id = None
        target_user = username.lower().replace('@', '')
        
        for s in sessions:
            if s.get("username", "").lower() == target_user:
                profile_id = s.get("id")
                break
        
        if not profile_id and session_manager.session_exists(username):
            profile_id = username

        if profile_id and "best_times" in analysis_data:
            session_manager.update_profile_metadata(profile_id, {
                "oracle_best_times": analysis_data["best_times"],
                "oracle_last_run": "now"
            })
    except Exception as e:
        print(f"Failed to auto-save oracle insights: {e}")

    return {
        "profile": username,
        "analysis": analysis_data,
        "raw_data": raw_data, # Include raw data for visual audit if needed
        "timestamp": "now"
    }

@router.post("/analyze_video")
async def analyze_video_url(video_url: str):
    """
    Downloads a video, extracts frames, and performs visual analysis.
    """
    from core.oracle.visual_cortex import visual_cortex
    import os
    import aiohttp
    
    # Quick hack to download video to temp
    local_filename = f"temp_video_{os.urandom(4).hex()}.mp4"
    local_path = os.path.join("/app/processing", local_filename)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    with open(local_path, 'wb') as f:
                        f.write(await resp.read())
                else:
                    raise HTTPException(status_code=400, detail="Could not download video")
        
        # Analyze
        result = await visual_cortex.analyze_video_content(local_path)
        
        # Cleanup
        if os.path.exists(local_path):
            os.remove(local_path)
            
        return result

    except Exception as e:
        if os.path.exists(local_path):
             os.remove(local_path)
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List

class RewriteRequest(BaseModel):
    draft: str
    tone: str = "Viral"

@router.post("/rewrite_caption")
async def rewrite_caption(request: RewriteRequest):
    """
    Rewrites a draft caption using Viral Copywriting Frameworks.
    """
    prompt = f"""
    You are a Viral Copywriting Expert on TikTok.
    Rewrite the following caption draft to make it extremely engaging, clickbaity, and viral.
    
    Draft: "{request.draft}"
    Tone: {request.tone}
    
    Apply frameworks like AIDA (Attention, Interest, Desire, Action) or "The Gap".
    Input language might be anything, but OUTPUT MUST BE PORTUGUESE (PT-BR).
    
    Output JSON format:
    {{
        "options": [
            "Variation 1 (Short & Punchy)",
            "Variation 2 (Storytelling)",
            "Variation 3 (Controversial/Question)"
        ],
        "hashtags": ["#tag1", "#tag2", "#tag3"]
    }}
    """
    
    try:
        response = oracle_client.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        return json.loads(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {e}")

class GenerateCaptionRequest(BaseModel):
    instruction: str
    tone: str = "Viral"
    include_hashtags: bool = True
    length: str = "short" # short, medium, long
    video_context: str = "" # Filename or visual description
    output_type: str = "caption" # caption, hashtags

@router.post("/generate_caption")
async def generate_caption(request: GenerateCaptionRequest):
    """
    Generates a caption OR hashtags based on instructions.
    """
    real_trends = []
    if request.include_hashtags or request.output_type == "hashtags":
        try:
            # [SYN-44] Use Tavily to get REAL-TIME viral tags
            from core.oracle.tavily_client import tavily_client
            # Use user instruction as topic if available, otherwise context, otherwise fallback
            topic = request.instruction.strip() if request.instruction else (request.video_context if request.video_context else "Viral TikTok Trends")
            # If topic looks like a filename, fallback to generic
            if topic.endswith(('.mp4', '.mov', '.avi')):
                topic = "Viral TikTok Trends" 
                
            real_trends = await tavily_client.search_hashtags(topic=topic, platform="TikTok")
        except Exception as e:
            print(f"⚠️ Tavily hashtag fetch failed: {e}")

    trends_context = f"REAL-TIME TRENDING TAGS (Use these if relevant): {', '.join(real_trends)}" if real_trends else ""

    if request.output_type == "hashtags":
        prompt = f"""
        Generate exactly 3-5 highly relevant, high-impact hashtags for a TikTok video.
        
        CONTEXT:
        - Topic: {request.video_context}
        - Tone: {request.tone}
        - {trends_context}
        
        RULES:
        1. QUANTITY: STICK TO 3 AWSOME TAGS (Max 5). QUALITY > QUANTITY.
        2. STRATEGY: 1 Broad (#FYP or #Viral) + 2-3 Specific Niche Tags.
        3. Output ONLY the hashtags separated by spaces.
        4. No other text.
        """
    else:
        length_instruction = "Concise but impactful (Start with a killer Hook, 2-3 short sentences total)." if request.length == "short" else "Story-driven (Hook -> Value -> Retention, 4-6 lines)."
        
        # Determine Primary Source
        user_intent = request.instruction.strip()
        if not user_intent:
             primary_directive = f"Create a viral caption relevant to the topic: '{request.video_context}'."
        else:
             primary_directive = f"The user wrote: '{user_intent}'. ELABORATE on this idea."

        prompt = f"""
        You are a World-Class UX Writer and Viral TikTok Copywriter.
        Your job is NOT to describe the video. Your job is to SELL the click/watch time using psychology.
        
        CONTEXT:
        - Tone: {request.tone}
        - Topic: "{request.video_context}"
        - Length: {length_instruction}
        - User Directive: "{user_intent if user_intent else '(None - Use Topic)'}"
        - {trends_context}

        🔥 PRIMARY DIRECTIVE:
        {primary_directive}
        
        🧠 UX WRITING RULES:
        1. **KILL THE ROBOT**: No "Neste vídeo", "Confira", "Estou aqui". Be direct.
        2. **THE HOOK IS GOD**: First line must be a thumb-stopper.
        3. **CONVERSATIONAL**: Lowercase aesthetic, minimal punctuation. Gen Z vibe.
        
        #️⃣ SMART HASHTAG STRATEGY (CRITICAL):
        {'If hashtags are allowed:' if request.include_hashtags else 'SKIP THIS SECTION (No Hashtags).'}
        1. **Quantity**: EXACTLY 3-5 tags.
        2. **The Mix**:
           - 1x Broad/Viral (e.g. #fyp, #viral)
           - 2x Niche (e.g. #marketingdigital, #dicas)
           - 1x Specific Context (e.g. #copywritingtips)
        3. **Integration**: Place them at the very end, separated by spaces.
        4. **Real-Time**: If specific tags were provided in Context, USE THEM if relevant.

        🎨 TONE ADJUSTMENT:
        - "Viral": High dopamine. Short. Punchy.
        - "Polêmico": Divisive.
        - "Engraçado": Self-deprecating or ironic.
        - "Profissional": Clean, direct benefit.

        OUTPUT FORMAT (PT-BR):
        [Hook / Reaction]
        
        [Context / Twist]
        
        [Hashtags]
        """
    
    try:
        response = oracle_client.generate_content(prompt)
        text = response.text.strip()
        
        # 🧹 STRICT FILTERING (Remove LLM Meta-Talk)
        import re
        # Remove common prefixes like "Here is...", "Based on...", "Given..."
        text = re.sub(r"^(Here is|Based on|Given|Sure|Okay|No problem|Anotação|Note|Obviamente|Claro).*?(\n|$)", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
        # Remove markdown bold labels like **Legenda:** or **Caption:**
        text = re.sub(r"\*\*(Legenda|Caption|Resultado|Output|Hook):\*\*\s*", "", text, flags=re.IGNORECASE)
        # Remove surrounding quotes
        text = re.sub(r"^[\"']|[\"']$", "", text)
        # Remove lines that are just "Instruction:" or similar
        text = re.sub(r"^(Instruction|Directive):.*", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()
        
        # ✂️ HASHTAG ENFORCER (Rule: Max 5)
        # 1. Identify all hashtags in the text
        tags_found = re.findall(r"#\w+", text)
        
        if len(tags_found) > 5:
            # Keep only the first 5
            allowed_tags = tags_found[:5]
            
            # Remove ALL hashtags from the text to start clean
            # Note: This regex removes #word. careful not to break text like "eu amo #brasil". 
            # But usually hashtags are at the end. 
            # Strategy: Split text into Body and Tags parts based on the first group of hashtags at the end
            
            # Simple approach: Replace the detected spam tags with empty, then append allowed
            text_no_tags = re.sub(r"#\w+(?:\s+#\w+)*$", "", text).strip() 
            # If standard regex fails to catch scattered tags, we just force append.
            # But to be safe, let's just use the text as is if regex is too complex, 
            # BUT usually the LLM puts them at the end.
            
            # Let's try aggressive cleanup of the END of the string
            lines = text.split('\n')
            new_lines = []
            captured_tags = []
            
            for line in lines:
                # If line is mostly hashtags, ignore it
                if line.strip().startswith('#') and len(re.findall(r"#\w+", line)) > 0:
                    continue
                new_lines.append(line)
            
            text = "\n".join(new_lines).strip()
            text += f"\n\n{' '.join(allowed_tags)}"
            
        return {"caption": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

class ReplyRequest(BaseModel):
    comment: str
    tone: str = "Witty"
    context: str = ""

@router.post("/reply")
@router.post("/reply")
async def generate_reply(request: ReplyRequest):
    """
    Generates a reply to a comment using the Auto-Responder.
    """
    from core.oracle.community_manager import community_manager
    from fastapi.concurrency import run_in_threadpool
    
    reply_text = await run_in_threadpool(
        community_manager.generate_reply, 
        request.comment, 
        request.tone, 
        request.context
    )
    return {"reply": reply_text}

# --- SEO & DISCOVERY (TURBO) ---
from core.oracle.seo_engine import seo_engine
from core import session_manager

@router.post("/seo/audit/{profile_id}")
@router.post("/seo/audit/{profile_id}")
async def audit_profile(profile_id: str):
    from fastapi.concurrency import run_in_threadpool
    
    # Run sync DB read in threadpool
    metadata = await run_in_threadpool(session_manager.get_profile_metadata, profile_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 📸 Visual Audit: Capture Full Page Screenshot
    username = metadata.get("username") or metadata.get("unique_id")
    if username:
        try:
            print(f"📸 Starting Visual Audit Scan for @{username}...")
            # oracle.sense is already async, keep as is
            screenshot_path = await oracle.sense.capture_profile_screenshot(username)
            if screenshot_path:
                metadata["screenshot_path"] = screenshot_path
                # Persist screenshot path (sync DB write)
                await run_in_threadpool(session_manager.update_profile_metadata, profile_id, {"screenshot_path": screenshot_path})
        except Exception as e:
            print(f"⚠️ Visual Audit Scan Failed: {e}")

    # Run blocking analysis engine
    result = await run_in_threadpool(seo_engine.audit_profile, metadata)
    
    # Auto-save last audit (sync DB write)
    await run_in_threadpool(session_manager.update_profile_metadata, profile_id, {"last_seo_audit": result})
    return result

class SpyRequest(BaseModel):
    competitor_handle: str

@router.post("/seo/spy")
async def spy_competitor(request: SpyRequest):
    return await seo_engine.competitor_spy(request.competitor_handle)

class FixBioRequest(BaseModel):
    current_bio: str
    niche: str

@router.post("/seo/fix-bio")
async def fix_bio(request: FixBioRequest):
    options = seo_engine.auto_fix_bio(request.current_bio, request.niche)
    return {"options": options}

class HashtagRequest(BaseModel):
    niche: str
    topic: str

@router.post("/seo/hashtags")
async def create_hashtags(request: HashtagRequest):
    prompt = f"""
    Gerar 3 grupos de hashtags para TikTok.
    Nicho: {request.niche}
    Topico: {request.topic}
    
    Output JSON:
    {{
        "broad": ["#tag1", ...], // Alto volume
        "niche": ["#tag2", ...], // Especificas
        "trending": ["#tag3", ...] // Oportunidades
    }}
    """
    try:
        # seo_engine instance has .client
        res = seo_engine.client.generate_content(prompt)
        text = res.text.replace("```json", "").replace("```", "").strip()
        import json
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

@router.get("/seo/keywords/{niche}")
async def get_seo_keywords(niche: str):
    """
    [SYN-27] Discover high-potential keywords for a niche.
    """
    return seo_engine.suggest_keywords(niche)

class GapRequest(BaseModel):
    username: str
    topic: str

@router.post("/seo/gaps")
async def analyze_content_gaps(request: GapRequest):
    """
    [SYN-27] Identify content gaps and opportunities.
    """
    return seo_engine.analyze_content_gaps(request.username, request.topic)

@router.get("/seo/opportunities/{username}")
async def get_opportunities(username: str):
    """
    [SYN-27] Quick opportunity check based on latest audit.
    """
    from core import session_manager
    # Tenta obter ID da sessão ou usar username direto
    metadata = session_manager.get_profile_metadata(username)
    if not metadata:
        # Tenta buscar por sessão
        sessions = session_manager.list_available_sessions()
        for s in sessions:
            if s.get("username", "").lower() == username.lower().replace("@", ""):
                 metadata = session_manager.get_profile_metadata(s.get("id"))
                 break
    
    if not metadata:
        return {"message": "Nenhuma auditoria recente encontrada para gerar oportunidades. Execute /full-scan primeiro."}
    
    # Extrair oportunidades salvas ou gerar novas
    audit = metadata.get("last_seo_audit", {})
    recs = audit.get("recommendations", [])
    niche = audit.get("niche", {})
    
    return {
        "username": username,
        "niche_detected": niche.get("niche", "Unknown"),
        "top_recommendations": recs,
        "missed_ctas": audit.get("sections", {}).get("bio", {}).get("cta_suggestions", [])
    }


# --- TREND CHECKER ENDPOINTS ---
from core.oracle.trend_checker import trend_checker

@router.get("/trends")
async def get_cached_trends():
    """Get cached trending sounds (no scraping)."""
    return trend_checker.get_cached_trends()


class TrendFetchRequest(BaseModel):
    category: str = "all"
    min_growth: float = 100


@router.post("/trends/fetch")
async def fetch_trends(request: TrendFetchRequest):
    """
    Fetch fresh trending sounds from TikTok Creative Center.
    This performs live scraping and updates the cache.
    """
    trends = await trend_checker.fetch_trending_sounds(
        category=request.category,
        min_growth=request.min_growth
    )
    return {
        "trends": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "growth_24h": t.growth_24h,
                "usage_count": t.usage_count,
                "confidence": t.confidence
            }
            for t in trends
        ],
        "count": len(trends),
        "fetched_at": trend_checker.last_updated.isoformat() if trend_checker.last_updated else None
    }


class HashtagValidateRequest(BaseModel):
    hashtag: str


@router.post("/trends/validate-hashtag")
async def validate_hashtag(request: HashtagValidateRequest):
    """Validate if a hashtag is currently trending."""
    result = await trend_checker.validate_hashtag(request.hashtag)
    return result


# --- SENTIMENT PULSE ENDPOINTS ---
from core.oracle.sentiment_pulse import sentiment_pulse


@router.post("/sentiment/profile/{username}")
async def analyze_profile_sentiment(username: str, max_comments: int = 50):
    """
    Analyze sentiment of comments on a profile's latest videos.
    Returns sentiment percentages and strategy recommendations.
    """
    result = await sentiment_pulse.analyze_profile_sentiment(username, max_comments)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


class VideoSentimentRequest(BaseModel):
    video_url: str
    max_comments: int = 50


@router.post("/sentiment/video")
async def analyze_video_sentiment(request: VideoSentimentRequest):
    """Analyze sentiment of comments on a specific video."""
    result = await sentiment_pulse.analyze_video_sentiment(
        request.video_url, 
        request.max_comments
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


class StrategyRequest(BaseModel):
    positive_pct: float
    negative_pct: float


@router.post("/sentiment/strategy")
async def get_strategy(request: StrategyRequest):
    """Get strategy recommendations based on sentiment percentages (no scraping)."""
    return sentiment_pulse.get_strategy_recommendations(
        request.positive_pct,
        request.negative_pct
    )


# --- TAVILY EXTERNAL RESEARCH (SYN-21) ---
from core.oracle.tavily_client import tavily_client, TavilySearchResponse


class ResearchRequest(BaseModel):
    query: str
    search_depth: str = "basic"  # "basic" (1 credit) or "advanced" (2 credits)
    max_results: int = 5
    topic: str = "general"  # "general" or "news"
    days: int = None  # For news, filter by recent days


@router.post("/research")
async def web_research(request: ResearchRequest):
    """
    🔍 Pesquisa web via Tavily API.
    
    Usa créditos do Tavily (1 para basic, 2 para advanced).
    Cache de 1h para economizar créditos.
    """
    result = await tavily_client.search(
        query=request.query,
        search_depth=request.search_depth,
        max_results=request.max_results,
        topic=request.topic,
        days=request.days,
        include_answer=True
    )
    
    return {
        "success": True,
        "query": result.query,
        "answer": result.answer,
        "results": [r.to_dict() for r in result.results],
        "response_time": result.response_time,
        "source": "tavily"
    }


class NicheTrendsRequest(BaseModel):
    niche: str
    platform: str = "TikTok"


@router.post("/external-trends")
async def get_external_trends(request: NicheTrendsRequest):
    """
    📈 Busca tendências externas para um nicho via Tavily.
    
    Combina dados de múltiplas fontes web em tempo real.
    """
    result = await tavily_client.search_trends(
        niche=request.niche,
        platform=request.platform
    )
    
    return {
        "success": True,
        "niche": request.niche,
        "platform": request.platform,
        "insights": result.answer,
        "sources": [r.to_dict() for r in result.results],
        "response_time": result.response_time
    }


class ExternalHashtagRequest(BaseModel):
    topic: str
    platform: str = "TikTok"


@router.post("/hashtags-external")
async def get_external_hashtags(request: ExternalHashtagRequest):
    """
    #️⃣ Busca hashtags em alta via pesquisa web (Tavily).
    
    Complementa a busca interna do TrendChecker com dados externos.
    """
    hashtags = await tavily_client.search_hashtags(
        topic=request.topic,
        platform=request.platform
    )
    
    return {
        "success": True,
        "topic": request.topic,
        "platform": request.platform,
        "hashtags": hashtags,
        "count": len(hashtags),
        "source": "tavily"
    }


class CompetitorAnalysisRequest(BaseModel):
    competitor_name: str
    platform: str = "TikTok"


@router.post("/competitor-research")
async def research_competitor(request: CompetitorAnalysisRequest):
    """
    🔎 Análise de concorrente via pesquisa web (Tavily).
    
    Busca informações públicas sobre estratégia e desempenho do concorrente.
    """
    result = await tavily_client.analyze_competitor(
        competitor_name=request.competitor_name,
        platform=request.platform
    )
    
    return {
        "success": True,
        **result
    }

