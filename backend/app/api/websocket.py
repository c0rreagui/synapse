"""
WebSocket endpoint para atualizações em tempo real
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json

router = APIRouter()

# Lista de conexões ativas
active_connections: List[WebSocket] = []


async def broadcast(event_type: str, data: dict):
    """Envia mensagem para todos os clientes conectados"""
    message = json.dumps({"type": event_type, "data": data})
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception:
            disconnected.append(connection)
    
    # Remove conexões mortas
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


@router.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para atualizações em tempo real"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Envia confirmação de conexão
        await websocket.send_text(json.dumps({
            "type": "connected",
            "data": {"message": "WebSocket conectado com sucesso"}
        }))
        
        # Mantém conexão aberta
        while True:
            try:
                # Aguarda mensagens do cliente (heartbeat, etc)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                
                # Responde ping com pong
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except asyncio.TimeoutError:
                # Envia ping para manter conexão viva
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


# Funções helper para outros módulos enviarem updates
async def notify_pipeline_update(status: dict):
    """Notifica mudança no status do pipeline"""
    await broadcast("pipeline_update", status)


async def notify_new_log(log_entry: dict):
    """Notifica novo log"""
    await broadcast("log_entry", log_entry)


async def notify_profile_change(profile: dict):
    """Notifica mudança em perfil"""
    await broadcast("profile_change", profile)
