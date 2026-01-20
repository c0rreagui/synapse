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
                session_manager.update_profile_metadata(profile_id, {
                    "oracle_best_times": strategy["best_times"],
                    "oracle_last_run": "now" 
                })
                print(f"✅ Oracle Insight: Saved {len(strategy['best_times'])} optimal times for {profile_id}")

        # 📸 AUTO-LEARN: Save 'recent_videos' for Visual Audit
        if profile_id and "raw_data" in result and "videos" in result["raw_data"]:
             videos = result["raw_data"]["videos"][:3] # Keep top 3
             if videos:
                session_manager.update_profile_metadata(profile_id, {
                    "recent_videos": videos
                })
                print(f"✅ Oracle Insight: Saved {len(videos)} recent videos for {profile_id}")

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

class ReplyRequest(BaseModel):
    comment: str
    tone: str = "Witty"
    context: str = ""

@router.post("/reply")
async def generate_reply(request: ReplyRequest):
    """
    Generates a reply to a comment using the Auto-Responder.
    """
    from core.oracle.community_manager import community_manager
    return {"reply": community_manager.generate_reply(request.comment, request.tone, request.context)}

# --- SEO & DISCOVERY (TURBO) ---
from core.oracle.seo_engine import seo_engine
from core import session_manager

@router.post("/seo/audit/{profile_id}")
async def audit_profile(profile_id: str):
    metadata = session_manager.get_profile_metadata(profile_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 📸 Visual Audit: Capture Full Page Screenshot
    username = metadata.get("username") or metadata.get("unique_id")
    if username:
        try:
            print(f"📸 Starting Visual Audit Scan for @{username}...")
            screenshot_path = await oracle.sense.capture_profile_screenshot(username)
            if screenshot_path:
                metadata["screenshot_path"] = screenshot_path
                # Persist screenshot path for future reference
                session_manager.update_profile_metadata(profile_id, {"screenshot_path": screenshot_path})
        except Exception as e:
            print(f"⚠️ Visual Audit Scan Failed: {e}")

    result = seo_engine.audit_profile(metadata)
    
    # Auto-save last audit
    session_manager.update_profile_metadata(profile_id, {"last_seo_audit": result})
    return result

class SpyRequest(BaseModel):
    competitor_handle: str

@router.post("/seo/spy")
async def spy_competitor(request: SpyRequest):
    return seo_engine.competitor_spy(request.competitor_handle)

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
