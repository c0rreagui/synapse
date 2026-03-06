from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from core.models import Proxy, Profile
import httpx

router = APIRouter()

class ProxyCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    fingerprint_ua: Optional[str] = None
    geolocation_latitude: Optional[str] = None
    geolocation_longitude: Optional[str] = None
    active: bool = True

class ProxyResponse(ProxyCreate):
    id: int
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[ProxyResponse])
def get_proxies(db: Session = Depends(get_db)):
    return db.query(Proxy).all()

@router.post("", response_model=ProxyResponse)
def create_proxy(proxy: ProxyCreate, db: Session = Depends(get_db)):
    # [SYN-110] Upsert: if proxy with same server exists, update it
    existing = db.query(Proxy).filter(Proxy.server == proxy.server).first()
    if existing:
        for key, value in proxy.model_dump().items():
            if value is not None:  # Only update non-None fields
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    db_proxy = Proxy(**proxy.model_dump())
    db.add(db_proxy)
    db.commit()
    db.refresh(db_proxy)
    return db_proxy

@router.put("/{proxy_id}", response_model=ProxyResponse)
def update_proxy(proxy_id: int, proxy: ProxyCreate, db: Session = Depends(get_db)):
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
        
    for key, value in proxy.model_dump().items():
        setattr(db_proxy, key, value)
        
    db.commit()
    db.refresh(db_proxy)
    return db_proxy

@router.delete("/{proxy_id}")
def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
        
    # Free profiles that are bound to this proxy to prevent FK constraints
    profiles = db.query(Profile).filter(Profile.proxy_id == proxy_id).all()
    for p in profiles:
        p.proxy_id = None
        
    db.delete(db_proxy)
    db.commit()
    return {"status": "success"}

class ProxyValidateRequest(BaseModel):
    server: str
    username: Optional[str] = None
    password: Optional[str] = None

@router.post("/validate")
async def validate_proxy(proxy: ProxyValidateRequest):
    server = proxy.server
    if proxy.username and proxy.password:
        protocol = "http://"
        if server.startswith("http://"):
            server = server[7:]
        elif server.startswith("https://"):
            protocol = "https://"
            server = server[8:]
        proxy_url = f"{protocol}{proxy.username}:{proxy.password}@{server}"
    else:
        proxy_url = server if server.startswith("http") else f"http://{server}"

    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
            resp = await client.get("http://ip-api.com/json/")
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "status": "success",
                    "ip": data.get("query"),
                    "city": data.get("city"),
                    "region": data.get("regionName"),
                    "country": data.get("countryCode"),
                    "message": f"Proxy OK: {data.get('city')}, {data.get('regionName')}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Falha na geolocalização: {data.get('message', 'Erro desconhecido')}"
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Proxy falhou: Connection Timeout ou Erro de Autenticação."
        }

@router.post("/{proxy_id}/test")
async def test_proxy(proxy_id: int, db: Session = Depends(get_db)):
    db_proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not db_proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    server = db_proxy.server
    if db_proxy.username and db_proxy.password:
        protocol = "http://"
        if server.startswith("http://"):
            server = server[7:]
        elif server.startswith("https://"):
            protocol = "https://"
            server = server[8:]
        proxy_url = f"{protocol}{db_proxy.username}:{db_proxy.password}@{server}"
    else:
        proxy_url = server

    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
            resp = await client.get("http://ip-api.com/json/")
            data = resp.json()
            if data.get("status") == "success":
                country = data.get("country", "")
                city = data.get("city", "")
                isp = data.get("isp", "")
                proxy_ip = data.get("query", "unknown")
                location = f"{city}, {country}" if city and country else (country or "Unknown Location")
                
                return {
                    "status": "success",
                    "proxy_ip": proxy_ip,
                    "location": location,
                    "isp": isp,
                    "message": f"IP: {proxy_ip} | Loc: {location} | ISP: {isp}"
                }
            else:
                return {
                    "status": "success",
                    "proxy_ip": "Unknown",
                    "message": "Connected successfully, but IP details are unavailable."
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Proxy failed: {str(e)}"
        }
