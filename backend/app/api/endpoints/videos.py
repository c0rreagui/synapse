"""
Videos endpoint - Lista vídeos processados, agendados e concluídos
"""
import os
import json
from datetime import datetime
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DONE_DIR = os.path.join(BASE_DIR, "done")
ERRORS_DIR = os.path.join(BASE_DIR, "errors")

@router.get("/completed")
async def get_completed_videos() -> List[Dict[str, Any]]:
    """Lista vídeos que foram processados com sucesso"""
    videos = []
    
    if not os.path.exists(DONE_DIR):
        return []
    
    for filename in os.listdir(DONE_DIR):
        if filename.endswith(".mp4"):
            video_path = os.path.join(DONE_DIR, filename)
            json_path = video_path + ".json"
            
            # Dados básicos
            video_info = {
                "id": filename.replace(".mp4", ""),
                "filename": filename,
                "status": "completed",
                "size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2),
                "processed_at": datetime.fromtimestamp(os.path.getmtime(video_path)).isoformat()
            }
            
            # Adiciona metadados se existirem
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        video_info["caption"] = metadata.get("caption", "")
                        video_info["profile"] = metadata.get("profile_id", "")
                        video_info["schedule_time"] = metadata.get("schedule_time")
                        if video_info["schedule_time"]:
                            video_info["status"] = "scheduled"
                except:
                    pass
            
            videos.append(video_info)
    
    # Ordena por data (mais recente primeiro)
    videos.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
    return videos[:50]  # Limita a 50 mais recentes


@router.get("/failed")
async def get_failed_videos() -> List[Dict[str, Any]]:
    """Lista vídeos que falharam no processamento"""
    videos = []
    
    if not os.path.exists(ERRORS_DIR):
        return []
    
    for filename in os.listdir(ERRORS_DIR):
        if filename.endswith(".mp4"):
            video_path = os.path.join(ERRORS_DIR, filename)
            error_path = video_path + ".error.txt"
            
            video_info = {
                "id": filename.replace(".mp4", ""),
                "filename": filename,
                "status": "failed",
                "size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2),
                "failed_at": datetime.fromtimestamp(os.path.getmtime(video_path)).isoformat()
            }
            
            # Adiciona mensagem de erro se existir
            if os.path.exists(error_path):
                try:
                    with open(error_path, 'r', encoding='utf-8') as f:
                        video_info["error_message"] = f.read()[:500]  # Limita a 500 chars
                except:
                    pass
            
            videos.append(video_info)
    
    videos.sort(key=lambda x: x.get("failed_at", ""), reverse=True)
    return videos[:20]


@router.get("/stats")
async def get_video_stats() -> Dict[str, Any]:
    """Retorna estatísticas dos vídeos"""
    completed = len([f for f in os.listdir(DONE_DIR) if f.endswith(".mp4")]) if os.path.exists(DONE_DIR) else 0
    failed = len([f for f in os.listdir(ERRORS_DIR) if f.endswith(".mp4")]) if os.path.exists(ERRORS_DIR) else 0
    
    # Conta agendados
    scheduled = 0
    if os.path.exists(DONE_DIR):
        for filename in os.listdir(DONE_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(DONE_DIR, filename), 'r') as f:
                        data = json.load(f)
                        if data.get("schedule_time"):
                            scheduled += 1
                except:
                    pass
    
    return {
        "total_completed": completed,
        "total_failed": failed,
        "total_scheduled": scheduled,
        "success_rate": round(completed / max(completed + failed, 1) * 100, 1)
    }
