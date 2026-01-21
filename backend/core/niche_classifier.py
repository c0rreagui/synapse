"""
🏷️ Niche Classifier - Classificador de Nicho usando Groq/LLM
Classifica sons virais em nichos específicos usando IA
"""
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

# Nichos suportados
NICHOS = [
    "tech",       # Tecnologia, programação, IA
    "fitness",    # Academia, exercícios, saúde
    "meme",       # Humor, comédia, trends engraçados
    "dance",      # Danças, challenges coreografados
    "lifestyle",  # Dia a dia, rotina, vlogs
    "beauty",     # Maquiagem, skincare, moda
    "food",       # Culinária, receitas, restaurantes
    "gaming",     # Jogos, streams, gameplay
    "education",  # Educativo, tutoriais, curiosidades
    "business",   # Negócios, empreendedorismo, finanças
    "motivation", # Motivacional, autoajuda
    "music",      # Músicas originais, covers
    "general"     # Conteúdo geral/indefinido
]


@dataclass
class NicheClassification:
    """Resultado da classificação de nicho"""
    sound_id: str
    title: str
    author: str
    primary_niche: str
    confidence: float
    secondary_niches: List[str]
    reasoning: str = ""


class NicheClassifier:
    """
    Classificador de nicho usando LLM (Groq via oracle_client).
    Analisa título, artista e contexto para determinar nicho.
    """
    
    def __init__(self):
        self._oracle = None
        self._cache: Dict[str, NicheClassification] = {}
    
    def _get_oracle(self):
        """Lazy load do oracle client"""
        if self._oracle is None:
            try:
                from core.oracle.client import oracle_client
                self._oracle = oracle_client
                logger.info(f"🧠 Classificador usando provider: {oracle_client.provider}")
            except ImportError:
                logger.warning("⚠️ Oracle client não disponível, usando classificação por regras")
                self._oracle = None
        return self._oracle
    
    def classify(self, sound: Dict) -> NicheClassification:
        """
        Classifica um som em um nicho.
        
        Args:
            sound: Dict com title, author, e opcionalmente sample_captions
            
        Returns:
            NicheClassification com nicho primário e secundários
        """
        title = sound.get("title", "")
        author = sound.get("author", "")
        sound_id = sound.get("id", "")
        
        # Verificar cache
        cache_key = f"{title}_{author}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Tentar classificação via LLM
        oracle = self._get_oracle()
        if oracle:
            try:
                classification = self._classify_with_llm(sound_id, title, author, sound)
                self._cache[cache_key] = classification
                return classification
            except Exception as e:
                logger.warning(f"Erro na classificação LLM: {e}")
        
        # Fallback: classificação por regras
        classification = self._classify_with_rules(sound_id, title, author)
        self._cache[cache_key] = classification
        return classification
    
    def _classify_with_llm(
        self, 
        sound_id: str, 
        title: str, 
        author: str,
        sound: Dict
    ) -> NicheClassification:
        """Classificação usando LLM (Groq)"""
        oracle = self._get_oracle()
        
        sample_captions = sound.get("sample_captions", [])
        captions_text = ", ".join(sample_captions[:5]) if sample_captions else "não disponível"
        
        prompt = f"""Classifique esta música/som do TikTok em um nicho de conteúdo.

INFORMAÇÕES DO SOM:
- Título: {title}
- Artista: {author}
- Exemplos de legendas de vídeos usando este som: {captions_text}

NICHOS DISPONÍVEIS:
{', '.join(NICHOS)}

Responda APENAS em JSON válido no formato:
{{
    "primary_niche": "nome_do_nicho",
    "confidence": 0.8,
    "secondary_niches": ["nicho2", "nicho3"],
    "reasoning": "explicação curta"
}}

JSON:"""

        try:
            response = oracle.generate_content(prompt)
            response_text = response.text.strip()
            
            # Limpar resposta (remover markdown se houver)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text)
            
            primary = data.get("primary_niche", "general")
            if primary not in NICHOS:
                primary = "general"
            
            secondary = [n for n in data.get("secondary_niches", []) if n in NICHOS]
            
            return NicheClassification(
                sound_id=sound_id,
                title=title,
                author=author,
                primary_niche=primary,
                confidence=min(1.0, max(0.0, data.get("confidence", 0.5))),
                secondary_niches=secondary[:3],
                reasoning=data.get("reasoning", "")
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Erro ao parsear JSON do LLM: {e}")
            raise
    
    def _classify_with_rules(
        self, 
        sound_id: str, 
        title: str, 
        author: str
    ) -> NicheClassification:
        """Classificação baseada em regras (fallback)"""
        title_lower = title.lower()
        author_lower = author.lower()
        combined = f"{title_lower} {author_lower}"
        
        # Regras simples baseadas em palavras-chave
        rules = {
            "tech": ["tech", "code", "ai", "robot", "future", "cyber", "digital"],
            "fitness": ["workout", "gym", "fit", "strong", "training", "exercise"],
            "meme": ["meme", "funny", "lol", "oh no", "dramatic", "bruh"],
            "dance": ["dance", "challenge", "choreo", "move", "beat"],
            "beauty": ["makeup", "beauty", "glow", "skin", "hair", "fashion"],
            "food": ["food", "cook", "recipe", "eat", "taste", "chef"],
            "gaming": ["game", "gamer", "play", "level", "boss", "stream"],
            "motivation": ["motivation", "success", "hustle", "grind", "dream"],
            "music": ["original sound", "cover", "remix", "beat", "melody"],
        }
        
        for niche, keywords in rules.items():
            for keyword in keywords:
                if keyword in combined:
                    return NicheClassification(
                        sound_id=sound_id,
                        title=title,
                        author=author,
                        primary_niche=niche,
                        confidence=0.6,
                        secondary_niches=[],
                        reasoning=f"Keyword match: '{keyword}'"
                    )
        
        # Default: general
        return NicheClassification(
            sound_id=sound_id,
            title=title,
            author=author,
            primary_niche="general",
            confidence=0.4,
            secondary_niches=[],
            reasoning="No specific keywords found"
        )
    
    def classify_batch(self, sounds: List[Dict]) -> List[NicheClassification]:
        """Classifica múltiplos sons"""
        results = []
        for sound in sounds:
            try:
                classification = self.classify(sound)
                results.append(classification)
            except Exception as e:
                logger.warning(f"Erro ao classificar {sound.get('title', 'unknown')}: {e}")
                # Adicionar classificação default
                results.append(NicheClassification(
                    sound_id=sound.get("id", ""),
                    title=sound.get("title", ""),
                    author=sound.get("author", ""),
                    primary_niche="general",
                    confidence=0.0,
                    secondary_niches=[],
                    reasoning="Classification failed"
                ))
        return results
    
    def get_available_niches(self) -> List[str]:
        """Retorna lista de nichos disponíveis"""
        return NICHOS.copy()


# Singleton
niche_classifier = NicheClassifier()
