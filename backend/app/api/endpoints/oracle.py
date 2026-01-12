from fastapi import APIRouter, HTTPException
from core.oracle import oracle_client

router = APIRouter()

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
    """
    from core.oracle.collector import oracle_collector
    from core.oracle.analyst import oracle_analyst

    # 1. Collect Data
    raw_data = await oracle_collector.collect_tiktok_profile(username)
    if "error" in raw_data:
        raise HTTPException(status_code=500, detail=f"Collector Failed: {raw_data['error']}")
    
    # 1.5 Sentiment Pulse: Extract Comments from Latest Video
    try:
        if raw_data.get("videos") and len(raw_data["videos"]) > 0:
            latest_video_link = raw_data["videos"][0].get("link")
            if latest_video_link:
                comments = await oracle_collector.extract_comments(latest_video_link)
                raw_data["comments"] = comments
                # Add count to performance metrics placeholder if needed
    except Exception as e:
        print(f"⚠️ Sentiment Pulse Warning: Could not extract comments: {e}")

    # 2. Analyze Data
    analysis = await oracle_analyst.analyze_profile(raw_data)
    if "error" in analysis:
        raise HTTPException(status_code=500, detail=f"Analyst Failed: {analysis['error']}")

    # 3. Automation: Save 'best_times' for Scheduler
    try:
        from core import session_manager
        # Attempt to find profile_id by username
        # This is a heuristic since we receive 'username' from UI
        sessions = session_manager.list_available_sessions()
        profile_id = None
        target_user = username.lower().replace('@', '')
        
        for s in sessions:
            if s.get("username", "").lower() == target_user:
                profile_id = s.get("id")
                break
        
        # If not found by username, maybe the username IS the profile_id? 
        # (Legacy support if frontend sends ID)
        if not profile_id and session_manager.session_exists(username):
            profile_id = username

        if profile_id and "analysis" in analysis and "best_times" in analysis["analysis"]:
            session_manager.update_profile_metadata(profile_id, {
                "oracle_best_times": analysis["analysis"]["best_times"],
                "oracle_last_run": analysis.get("timestamp", "now") # timestamp not in output yet but useful
            })
    except Exception as e:
        print(f"Failed to auto-save oracle insights: {e}")

    return analysis

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
