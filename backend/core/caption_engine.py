"""
Caption Engine — Gerador de Variações de Legendas por Perfil
=============================================================

Gera N captions sintaticamente únicas a partir de uma base, mantendo
hashtags idênticas. Usado pelo uniquifier flow para evitar detecção
de conteúdo duplicado via NLP do TikTok.

Usa o Oracle (Groq/Llama 3.3) para gerar variações, com fallback
mecânico (sinônimos + reordenação) caso o LLM falhe.
"""

import json
import logging
import random
import re
from typing import Dict, List, Optional

logger = logging.getLogger("CaptionEngine")


# ── Fallback mecânico: dicionário de sinônimos PT-BR coloquial ──────────

SYNONYM_MAP = {
    "kkkk": ["rsrs", "kkkkk", "KKKK", "kkkkkk"],
    "kkkkk": ["kkkk", "rsrsrs", "KKKKK"],
    "KKKK": ["kkkk", "kkkkk", "RSRS"],
    "mano": ["cara", "vei", "bro", "parça"],
    "cara": ["mano", "vei", "bixo"],
    "bixo": ["cara", "mano", "vei", "doido"],
    "vei": ["mano", "cara", "bixo"],
    "simplesmente": ["literalmente", "basicamente", "na moral"],
    "literalmente": ["simplesmente", "basicamente"],
    "demais": ["pra caramba", "d+", "absurdo"],
    "absurdo": ["insano", "surreal", "demais"],
    "insano": ["absurdo", "surreal", "doido"],
    "muito": ["mt", "demais", "absurdamente"],
    "ninguém": ["NINGUÉM", "nenhuma alma", "zero pessoas"],
    "todo mundo": ["TODO MUNDO", "a galera toda", "geral"],
    "perdeu": ["PERDEU", "jogou fora", "deixou escapar"],
    "morreu": ["capotou", "foi de base", "tombou"],
    "inacreditável": ["surreal", "impossível", "de outro mundo"],
}

EMOJI_POOL = ["💀", "😭", "🔥", "😂", "⚡", "🤯", "😳", "💯"]


def _mechanical_variation(base_caption: str, variant_index: int) -> str:
    """
    Aplica transformações mecânicas para gerar variação sem LLM.
    Cada variant_index produz uma transformação diferente.
    """
    rng = random.Random(hash(f"{base_caption}:{variant_index}"))
    result = base_caption

    strategy = variant_index % 4

    if strategy == 0:
        # Estratégia: substituir gírias por sinônimos
        words = result.split()
        new_words = []
        for word in words:
            clean = word.strip(".,!?()[]")
            if clean.lower() in SYNONYM_MAP:
                synonyms = SYNONYM_MAP[clean.lower()]
                replacement = rng.choice(synonyms)
                new_words.append(word.replace(clean, replacement))
            else:
                new_words.append(word)
        result = " ".join(new_words)

    elif strategy == 1:
        # Estratégia: inverter clausulas (split por vírgula/travessão)
        separators = [" — ", " - ", ", "]
        for sep in separators:
            if sep in result:
                parts = result.split(sep, 1)
                if len(parts) == 2:
                    result = parts[1].strip().capitalize() + sep + parts[0].strip().lower()
                break

    elif strategy == 2:
        # Estratégia: alterar capitalização enfática + adicionar/remover emoji
        # Capitalizar palavra mais longa
        words = result.split()
        if words:
            longest_idx = max(range(len(words)), key=lambda i: len(words[i]))
            words[longest_idx] = words[longest_idx].upper()
            result = " ".join(words)
        # Trocar emoji se existir
        for emoji in EMOJI_POOL:
            if emoji in result:
                replacement = rng.choice([e for e in EMOJI_POOL if e != emoji])
                result = result.replace(emoji, replacement, 1)
                break

    elif strategy == 3:
        # Estratégia: reformular como pergunta ou exclamação
        if not result.endswith("?"):
            # Adicionar pergunta retórica ao início
            prefixes = [
                "vocês viram isso?? ",
                "alguém explica isso: ",
                "como que pode? ",
                "eu não acredito: ",
            ]
            result = rng.choice(prefixes) + result[0].lower() + result[1:]
        else:
            # Já é pergunta, transformar em exclamação
            result = result.rstrip("?") + "!!!"

    return result


def _parse_variations_json(content: str, count: int) -> Optional[List[Dict]]:
    """Tenta parsear a resposta do LLM como JSON de variações."""
    # Estratégia 1: parse direto
    try:
        data = json.loads(content)
        if "variations" in data and isinstance(data["variations"], list):
            return data["variations"]
    except json.JSONDecodeError:
        pass

    # Estratégia 2: extrair de code fence
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1))
            if "variations" in data and isinstance(data["variations"], list):
                return data["variations"]
        except json.JSONDecodeError:
            pass

    # Estratégia 3: buscar objeto JSON com "variations" key (greedy braces)
    match = re.search(r'\{[^{}]*"variations"\s*:\s*\[.*\]\s*\}', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if "variations" in data and isinstance(data["variations"], list):
                return data["variations"]
        except json.JSONDecodeError:
            pass

    return None


async def generate_caption_variations(
    base_caption: str,
    hashtags: List[str],
    count: int,
    tone: str = "Viral",
) -> List[Dict[str, any]]:
    """
    Gera N variações sintaticamente únicas de uma caption base.
    Hashtags são mantidas idênticas em todas as variações.

    Returns:
        [{"caption": "variação 1...", "hashtags": ["#same", ...]}, ...]

    Se o LLM falhar, usa fallback mecânico para garantir entrega.
    """
    if count <= 1:
        return [{"caption": base_caption, "hashtags": hashtags}]

    if not base_caption or not base_caption.strip():
        return [{"caption": "", "hashtags": hashtags} for _ in range(count)]

    # ── Tentar via Oracle (Groq/Llama 3.3) ──
    try:
        from core.oracle import oracle_client

        system_prompt = f"""Você é um redator brasileiro especialista em TikTok.
Receba UMA caption base e produza EXATAMENTE {count} variações ÚNICAS.

REGRAS ABSOLUTAS:
1. Toda variação transmite a MESMA mensagem e emoção da base
2. Toda variação usa sintaxe, ordem de palavras e fraseado DIFERENTE
3. NÃO altere o significado nem adicione informação nova
4. NÃO altere hashtags — retorne EXATAMENTE como recebido
5. Cada variação DEVE passar num teste de detecção de duplicatas (NLP)
6. Use PT-BR coloquial natural (como brasileiro real escreve no TikTok)
7. Tom: {tone}

TÉCNICAS OBRIGATÓRIAS (use pelo menos 2 por variação):
- Reordenar cláusulas ("ele desistiu do boss" → "do boss, ele desistiu")
- Usar sinônimos (mano→cara, kkkk→rsrs, insano→absurdo)
- Mudar ênfase (CAPS em palavras diferentes)
- Variar pontuação (... vs !!! vs ??)
- Reformular perguntas retóricas
- Inverter ordem sujeito-verbo
- Alterar gírias mantendo naturalidade

FORMATO DE RESPOSTA (JSON estrito):
{{"variations": [{{"caption": "variação 1", "hashtags": {json.dumps(hashtags, ensure_ascii=False)}}}, ...]}}

IMPORTANTE: Retorne EXATAMENTE {count} variações. Não inclua texto fora do JSON."""

        user_prompt = f"""Caption base para variar:
"{base_caption}"

Hashtags (manter idênticas): {json.dumps(hashtags, ensure_ascii=False)}

Gere {count} variações únicas."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = oracle_client.generate_content(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.95,
            max_completion_tokens=2048,
        )

        content = result.text if hasattr(result, "text") else str(result)
        variations = _parse_variations_json(content, count)

        if variations and len(variations) >= count:
            # Limpar e validar
            clean_variations = []
            for v in variations[:count]:
                caption = v.get("caption", "").strip()
                if caption.startswith('"') and caption.endswith('"'):
                    caption = caption[1:-1]
                # Strip hashtags inline (LLM pode inserir apesar da instrução)
                caption = re.sub(r'(?<!\w)#\w+', '', caption).strip()
                clean_variations.append({
                    "caption": caption or base_caption,
                    "hashtags": hashtags,  # Sempre as mesmas
                })

            logger.info(
                f"CaptionEngine: {count} variações geradas via Oracle "
                f"(base: {len(base_caption)} chars)"
            )
            return clean_variations

        # LLM retornou menos variações que o pedido
        logger.warning(
            f"CaptionEngine: Oracle retornou {len(variations) if variations else 0}/{count} variações, "
            f"completando com fallback mecânico"
        )
        llm_variations = []
        if variations:
            for v in variations:
                caption = v.get("caption", "").strip()
                if caption.startswith('"') and caption.endswith('"'):
                    caption = caption[1:-1]
                caption = re.sub(r'(?<!\w)#\w+', '', caption).strip()
                llm_variations.append({"caption": caption or base_caption, "hashtags": hashtags})

        # Completar com fallback mecânico
        while len(llm_variations) < count:
            idx = len(llm_variations)
            mech_caption = _mechanical_variation(base_caption, idx)
            llm_variations.append({"caption": mech_caption, "hashtags": hashtags})

        return llm_variations[:count]

    except Exception as e:
        logger.warning(f"CaptionEngine: Oracle falhou ({e}), usando fallback mecânico completo")

    # ── Fallback mecânico completo ──
    variations = [{"caption": base_caption, "hashtags": hashtags}]
    for i in range(1, count):
        mech_caption = _mechanical_variation(base_caption, i)
        variations.append({"caption": mech_caption, "hashtags": hashtags})

    logger.info(f"CaptionEngine: {count} variações geradas via fallback mecânico")
    return variations
