"""
BRAIN Module - O Cerebro do Conteudo
Responsavel por gerar metadados inteligentes (Legendas, Hashtags)
baseado no nome do arquivo e perfil detectado.
"""
import random
import re
import logging

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

async def generate_smart_caption(filename: str, profile_prefix: str = None) -> dict:
    """
    Gera legenda e hashtags inteligentes baseadas no arquivo.
    Ex: @p1_gato_engracado.mp4 -> "O final e surpreendente! Gato Engracado #humor #gato"
    """
    try:
        # 1. Detectar Perfil se nao fornecido
        if not profile_prefix:
            # Aceita p1, p2, pcortes, pnews (alfanumerico apos @)
            match = re.match(r"^@?([a-zA-Z0-9]+)_", filename)
            profile_prefix = match.group(1) if match else "default"
        
        # Normaliza chave (caso venha vazia ou errada)
        profile_key = profile_prefix if profile_prefix in NICHE_CONFIG else "default"
        config = NICHE_CONFIG[profile_key]
        
        # 2. Limpar Nome do Arquivo para Titulo
        # Remove extensao e prefixo @pX_
        clean_name = re.sub(r"^@?p\d+_", "", filename) # Remove prefixo
        clean_name = os.path.splitext(clean_name)[0]   # Remove .mp4
        clean_name = clean_name.replace("_", " ").replace("-", " ") # _ para espaco
        clean_title = clean_name.title() # Title Case
        
        # 3. Escolher Gancho
        hook = random.choice(config["hooks"])
        
        # 4. Montar Legenda
        caption = f"{hook} {clean_title}"
        
        # 5. Selecionar Hashtags
        # Mistura as do nicho com algumas gerais
        niche_tags = config["hashtags"]
        general_tags = NICHE_CONFIG["default"]["hashtags"]
        
        # Seleciona 3-5 tags do nicho e 1-2 gerais
        selected_tags = random.sample(niche_tags, min(len(niche_tags), 4)) + \
                        random.sample(general_tags, 1)
        
        logger.info(f"[BRAIN] Brain gerou para {filename}: {caption}")
        
        return {
            "caption": caption,
            "hashtags": selected_tags,
            "profile": profile_key,
            "derived_title": clean_title
        }
        
    except Exception as e:
        logger.error(f"[BRAIN] Erro no Brain: {e}")
        # Fallback seguro
        return {
            "caption": f"Video novo! {filename}",
            "hashtags": ["fyp", "viral"],
            "profile": "default"
        }

import os # Necessário para splitext
