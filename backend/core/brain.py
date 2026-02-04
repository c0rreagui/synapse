"""
BRAIN Module - O Cerebro do Conteudo
Responsavel por gerar metadados inteligentes (Legendas, Hashtags)
baseado no nome do arquivo e perfil detectado.
"""
import random
import re
import logging
import os

logger = logging.getLogger(__name__)

# Configuracoes de Nicho (Mock DB)
NICHE_CONFIG = {
    "p1": {
        "type": "cortes",
        "hashtags": ["cortes", "podcast", "humor", "viral", "fy"],
        "hooks": [
            "Voce nao vai acreditar nisso!",
            "O final e surpreendente!",
            "Melhor momento do podcast!",
            "Quem concorda?"
        ]
    },
    "p2": {
        "type": "curiosidades",
        "hashtags": ["curiosidades", "fatos", "vocesabia", "interessante", "historia"],
        "hooks": [
            "Sabia dessa?",
            "Fato curioso do dia!",
            "Isso vai explodir sua mente",
            "A verdade sobre..."
        ]
    },
    "default": {
        "type": "geral",
        "hashtags": ["fyp", "foryou", "viral", "tiktok"],
        "hooks": ["Confira isso!", "Muito bom!", "Olha so"]
    }
}

async def generate_smart_caption(filename: str, profile_prefix: str = None, video_path: str = None) -> dict:
    """
    Gera legenda e hashtags inteligentes baseadas no arquivo.
    Usa o Oracle SEO Engine (IA Real) para analise.
    Se video_path fornecido, usa Vision AI para analisar o conteudo visual.
    """
    try:
        # 1. Detectar Perfil se nao fornecido
        if not profile_prefix:
            # Aceita p1, p2, pcortes, pnews (alfanumerico apos @)
            match = re.match(r"^@?([a-zA-Z0-9]+)_", filename)
            profile_prefix = match.group(1) if match else "default"
        
        # Standardize prefix for niche lookup
        # Convert 'tiktok_profile_01' -> 'p1'
        if profile_prefix and profile_prefix.startswith('tiktok_profile_'):
            try:
                parts = profile_prefix.split('_')
                if len(parts) >= 3:
                     profile_prefix = f"p{int(parts[2])}"
            except: pass

        # Determine Niche based on profile prefix (Generic mapping for now, or fetch from DB)
        # For speed, we just map prefix -> simple niche, 
        # but seo_engine.generate_content_metadata accepts niche string.
        niche_map = {
            "p1": "Cortes e Humor",
            "p2": "Curiosidades e Fatos",
            "default": "General Viral Content"
        }
        niche = niche_map.get(profile_prefix, "General Viral Content")

        logger.info(f"[BRAIN] Solicitando ao Oracle (SEO Engine) para: {filename} (Nicho: {niche})")
        
        # 2. Call Real Oracle
        from core.oracle.seo_engine import seo_engine
        
        metadata = await seo_engine.generate_content_metadata(filename, niche=niche, video_path=video_path)
        
        caption = metadata.get("suggested_caption")
        hashtags = metadata.get("hashtags", [])
        
        logger.info(f"[BRAIN] Oracle retornou: {caption[:30]}...")
        
        return {
            "caption": caption,
            "hashtags": hashtags,
            "profile": profile_prefix,
            "derived_title": filename,
            "viral_score": metadata.get("viral_score", 0),
            "viral_reason": metadata.get("viral_reason", "")
        }
        
    except Exception as e:
        logger.error(f"[BRAIN] Erro no Brain (Fallback para Mock): {e}")
        # Fallback Mock (Legacy logic)
        # [SYN-FIX] Clean filename garbage (uptake from ingestion system names)
        base = os.path.basename(filename)
        base = os.path.splitext(base)[0]
        # Remove prefixes like p1_, ptiktok_profile_..._
        base = re.sub(r'^(p\d+|ptiktok_profile_[a-zA-Z0-9]+)_', '', base)
        # Remove UUID suffix (8 chars) if present
        base = re.sub(r'_[a-f0-9]{8}$', '', base)
        
        clean_name = base.replace("_", " ").title().strip()
        if not clean_name:
            clean_name = "Video Incrível"

        return {
            "caption": f"Confira esse vídeo! {clean_name} 👇",
            "hashtags": ["#fyp", "#viral", "#foryou"],
            "profile": profile_prefix or "default",
            "derived_title": clean_name
        }

import os # Necessário para splitext
