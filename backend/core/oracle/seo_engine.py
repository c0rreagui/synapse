import requests
from PIL import Image
from io import BytesIO
from core.oracle.client import oracle_client
import json

class SEOEngine:
    def __init__(self):
        self.client = oracle_client

    def audit_profile(self, metadata: dict) -> dict:
        """
        Multimodal audit of a profile.
        0. Niche Detection (NEW)
        1. Text Analysis (Bio, Username)
        2. Vision Analysis (Avatar)
        """
        score = 0
        details = []
        
        # 0. NICHE DETECTION - Analyze username, bio, and label to detect niche
        bio = metadata.get("bio", "") or metadata.get("bio_description", "") or metadata.get("signature", "")
        username = metadata.get("username") or metadata.get("unique_id") or ""
        label = metadata.get("label", "")
        
        detected_niche = self._detect_niche(username, bio, label)
        details.append({"type": "niche", "data": detected_niche})
        
        # 1. Text Analysis
        if not bio:
            details.append({"type": "warning", "msg": "Biografia vazia. Oportunidade perdida."})
        elif len(bio) < 10:
            details.append({"type": "warning", "msg": "Bio muito curta."})
            score += 10
        else:
            score += 30
            details.append({"type": "success", "msg": "Tamanho da bio OK."})

        # 2. Vision Analysis (Avatar)
        avatar_url = metadata.get("avatar_url") or metadata.get("avatar_larger")
        vision_score = 0
        vision_feedback = "Sem avatar para analisar."

        if avatar_url:
            try:
                # Download Image (Mimic Browser to avoid 403)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.tiktok.com/'
                }
                response = requests.get(avatar_url, headers=headers, timeout=10, verify=False)
                
                # If download fails (403/404), throw to trigger fallback
                if response.status_code != 200:
                    raise Exception(f"Download HTTP {response.status_code}")

                img = Image.open(BytesIO(response.content))
                
                # Convert to RGB/JPEG for compatibility
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Oracle Prompt - ENHANCED for rich analysis
                prompt = [
                    "Você é um ESPECIALISTA SENIOR em Branding de Redes Sociais com 15 anos de experiência. Analise esta foto de perfil com extrema atenção aos detalhes.",
                    img,
                    """
                    Faça uma análise PROFUNDA e retorne SOMENTE JSON neste formato:
                    {
                        "score": 0-100,
                        "impression": "descrição curta da vibe geral em 1 frase",
                        "professionalism": "Amador" | "Intermediário" | "Profissional" | "Expert",
                        "color_analysis": {
                            "dominant_colors": ["cor1", "cor2"],
                            "harmony": "Harmônico" | "Conflitante" | "Neutro",
                            "mood": "Energético" | "Calmo" | "Sério" | "Divertido" | "Misterioso"
                        },
                        "composition": {
                            "face_visible": true/false,
                            "centered": true/false,
                            "quality": "Alta" | "Média" | "Baixa",
                            "lighting": "Bom" | "Ruim" | "Perfeito"
                        },
                        "pros": ["ponto forte 1 (específico)", "ponto forte 2 (específico)", "ponto forte 3"],
                        "cons": ["ponto fraco 1 (com sugestão de melhoria)", "ponto fraco 2"],
                        "immediate_actions": [
                            {"priority": 1, "action": "ação urgente", "impact": "Alto"},
                            {"priority": 2, "action": "ação recomendada", "impact": "Médio"}
                        ],
                        "verdict": "Profissional" | "Amador" | "Confuso" | "Mediano",
                        "viral_potential": "Baixo" | "Médio" | "Alto",
                        "competitor_comparison": "Acima da média" | "Na média" | "Abaixo da média"
                    }
                    """
                ]
                
                try:
                    ai_res = self.client.generate_content(prompt)
                    # Extract JSON
                    txt = ai_res.text
                    if "```json" in txt:
                        txt = txt.split("```json")[1].split("```")[0]
                    elif "```" in txt:
                            txt = txt.split("```")[1].split("```")[0]
                            
                    vision_data = json.loads(txt)
                    vision_score = vision_data.get("score", 50)
                    vision_feedback = vision_data.get("impression", "Analise concluida")
                    
                    details.append({
                        "type": "vision", 
                        "data": vision_data
                    })
                    score += (vision_score * 0.5) # Weight Vision 50%
                    
                except Exception as e:
                    raise e # Trigger outer fallback

            except Exception as e:
                print(f"Vision Analysis unavailable: {e}")
                # FALLBACK: Text-Only Analysis
                try:
                    fallback_prompt = f"""
                    Sou um especialista de Branding. Não consigo ver o avatar (Erro Download), mas analise este perfil pelo nome e bio:
                    Username: {metadata.get('username')}
                    Bio: {bio}
                    
                    Responda JSON:
                    {{
                        "score": 50,
                        "impression": "Análise baseada apenas em Texto (Avatar indisponível). Bio sugere...",
                        "pros": ["Texto descritivo"],
                        "cons": ["Avatar não carregou"],
                        "verdict": "Incompleto"
                    }}
                    """
                    fb_res = self.client.generate_content(fallback_prompt)
                    fb_txt = fb_res.text.replace("```json", "").replace("```", "").strip()
                    vision_data = json.loads(fb_txt)
                    vision_score = vision_data.get("score", 50) # Update local var
                    
                    details.append({
                        "type": "warning",
                        "msg": f"⚠️ Avatar: Download falhou. Análise de Branding gerada via Texto.",
                    })
                    details.append({
                        "type": "vision",
                        "data": vision_data
                    })
                    score += (vision_score * 0.5) # Weight Vision 50%
                except:
                    details.append({"type": "error", "msg": "Falha total na Análise de Branding."})
                    score += 50
        else:
            score += 0 

        # 3. Content Visual Analysis (Latest Video Cover)
        recent_videos = metadata.get("recent_videos", [])
        if recent_videos and len(recent_videos) > 0:
            latest_video = recent_videos[0]
            cover_url = latest_video.get("cover") or latest_video.get("dynamic_cover")
            
            if cover_url:
                try:
                    # Download Cover
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://www.tiktok.com/'
                    }
                    response = requests.get(cover_url, headers=headers, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        cover_img = Image.open(BytesIO(response.content))
                        if cover_img.mode in ("RGBA", "P"):
                            cover_img = cover_img.convert("RGB")
                            
                        # Vision Prompt
                        prompt = [
                            "Analise esta capa (thumbnail) do video mais recente deste perfil.",
                            cover_img,
                            """
                            Responda SOMENTE JSON:
                            {
                                "score": 0-100,
                                "hook_strength": "Fraco" | "Medio" | "Forte",
                                "visual_appeal": "comentario sobre cores/texto",
                                "improvement_tip": "dica para melhorar a capa"
                            }
                            """
                        ]
                        
                        ai_res = self.client.generate_content(prompt)
                        txt = ai_res.text.replace("```json", "").replace("```", "").strip()
                        cover_data = json.loads(txt)
                        
                        details.append({
                            "type": "video_vision",
                            "data": cover_data,
                            "msg": "Análise Visual da Última Capa"
                        })
                        score += (cover_data.get("score", 50) * 0.2) # Bonus points
                        
                except Exception as e:
                    print(f"Content Vision Failed: {e}")
                    details.append({"type": "warning", "msg": f"Erro na análise visual do conteúdo: {str(e)}"})

        # 4. Full Page Vibe Analysis (New)
        screenshot_path = metadata.get("screenshot_path")
        if screenshot_path:
            try:
                import os
                if os.path.exists(screenshot_path):
                    vibe_data = self.analyze_full_page_vibe(screenshot_path)
                    
                    details.append({
                        "type": "full_page_vibe",
                        "data": vibe_data,
                        "msg": "✅ Vibe Check: Análise da Página Completa"
                    })
                    score += (vibe_data.get("score", 50) * 0.3) # Weight 30%
            except Exception as e:
                 print(f"Full Page Vision Failed: {e}")
                 details.append({"type": "warning", "msg": f"Erro no Vibe Check: {e}"})

        # Finalize - Build Structured Response
        total_score = min(100, int(score))
        
        # Organize into sections for frontend
        sections = {
            "bio": {
                "score": 70 if len(bio) > 50 else 40,
                "label": "Bio & Identidade",
                "icon": "📝",
                "items": []
            },
            "avatar": {
                "score": vision_score,
                "label": "Visual Branding",
                "icon": "🎨",
                "items": []
            },
            "content": {
                "score": 50,
                "label": "Capas de Vídeo",
                "icon": "🎬",
                "items": []
            },
            "vibe": {
                "score": 50,
                "label": "Vibe Check",
                "icon": "✨",
                "items": []
            }
        }
        
        recommendations = []
        niche_data = {}
        
        # Parse details into sections
        for item in details:
            item_type = item.get("type", "")
            
            # Handle Niche Detection Result
            if item_type == "niche":
                niche_data = item.get("data", {})
                # Add personalized recommendations from niche analysis
                for rec in niche_data.get("personalized_recommendations", []):
                    recommendations.append(rec)
                    
            elif item_type == "bio":
                sections["bio"]["items"].append({"status": "ok", "text": item.get("msg", "")})
            elif item_type == "warning" and "Avatar" in item.get("msg", ""):
                sections["avatar"]["items"].append({"status": "warning", "text": item.get("msg", "")})
            elif item_type == "warning" and "Bio" in item.get("msg", ""):
                sections["bio"]["items"].append({"status": "warning", "text": item.get("msg", "")})
            elif item_type == "vision":
                data = item.get("data", {})
                sections["avatar"]["score"] = data.get("score", 50)
                sections["avatar"]["raw_data"] = data  # Pass full AI response
                
                # Core impression
                if data.get("impression"):
                    sections["avatar"]["items"].append({"status": "info", "text": data["impression"]})
                
                # Professionalism badge
                if data.get("professionalism"):
                    sections["avatar"]["items"].append({"status": "badge", "text": f"Nível: {data['professionalism']}"})
                
                # Color Analysis
                color_data = data.get("color_analysis", {})
                if color_data.get("dominant_colors"):
                    sections["avatar"]["items"].append({"status": "info", "text": f"Cores: {', '.join(color_data['dominant_colors'])}"})
                if color_data.get("mood"):
                    sections["avatar"]["items"].append({"status": "info", "text": f"Mood: {color_data['mood']}"})
                
                # Composition
                comp = data.get("composition", {})
                if comp.get("quality"):
                    status = "ok" if comp["quality"] == "Alta" else "warning" if comp["quality"] == "Baixa" else "info"
                    sections["avatar"]["items"].append({"status": status, "text": f"Qualidade: {comp['quality']}"})
                if comp.get("lighting"):
                    sections["avatar"]["items"].append({"status": "info", "text": f"Iluminação: {comp['lighting']}"})
                
                # Pros
                for pro in data.get("pros", []):
                    sections["avatar"]["items"].append({"status": "ok", "text": pro})
                
                # Cons
                for con in data.get("cons", []):
                    sections["avatar"]["items"].append({"status": "warning", "text": con})
                
                # Immediate Actions (Priority-based recommendations)
                for action in data.get("immediate_actions", []):
                    priority = action.get("priority", 99)
                    action_text = action.get("action", "")
                    impact = action.get("impact", "")
                    if action_text:
                        recommendations.append(f"[P{priority}] {action_text} (Impacto: {impact})")
                
                # Viral Potential
                if data.get("viral_potential"):
                    sections["avatar"]["items"].append({"status": "badge", "text": f"Potencial Viral: {data['viral_potential']}"})
                
            elif item_type == "video_vision":
                data = item.get("data", {})
                sections["content"]["score"] = data.get("score", 50)
                sections["content"]["raw_data"] = data
                
                if data.get("hook_strength"):
                    status = "ok" if data["hook_strength"] == "Forte" else "warning" if data["hook_strength"] == "Fraco" else "info"
                    sections["content"]["items"].append({"status": status, "text": f"Força do Hook: {data['hook_strength']}"})
                if data.get("visual_appeal"):
                    sections["content"]["items"].append({"status": "ok", "text": data["visual_appeal"]})
                if data.get("improvement_tip"):
                    sections["content"]["items"].append({"status": "tip", "text": data["improvement_tip"]})
                    recommendations.append(data["improvement_tip"])
                    
            elif item_type == "full_page_vibe":
                data = item.get("data", {})
                sections["vibe"]["score"] = data.get("score", 50)
                sections["vibe"]["raw_data"] = data
                
                # Core Vibe
                if data.get("overall_vibe"):
                    sections["vibe"]["items"].append({"status": "badge", "text": f"Vibe: {data['overall_vibe']}"})
                if data.get("first_impression"):
                    sections["vibe"]["items"].append({"status": "info", "text": f"Primeira Impressão: {data['first_impression']}"})
                
                # Layout Analysis
                layout = data.get("layout_analysis", {})
                if layout.get("quality"):
                    status = "ok" if layout["quality"] in ["Clean", "Balanced"] else "warning"
                    sections["vibe"]["items"].append({"status": status, "text": f"Layout: {layout['quality']}"})
                if layout.get("visual_hierarchy"):
                    sections["vibe"]["items"].append({"status": "info", "text": f"Hierarquia Visual: {layout['visual_hierarchy']}"})
                
                # Thumbnail Analysis
                thumbs = data.get("thumbnail_analysis", {})
                if thumbs.get("consistency"):
                    status = "ok" if thumbs["consistency"] == "Alta" else "warning" if thumbs["consistency"] == "Baixa" else "info"
                    sections["vibe"]["items"].append({"status": status, "text": f"Thumbnails: {thumbs['consistency']} consistência"})
                if thumbs.get("hook_strength"):
                    sections["vibe"]["items"].append({"status": "info", "text": f"Hook Visual: {thumbs['hook_strength']}"})
                
                # Branding Cohesion
                brand = data.get("branding_cohesion", {})
                if brand.get("professional_level"):
                    sections["vibe"]["items"].append({"status": "badge", "text": f"Nível: {brand['professional_level']}"})
                if brand.get("style_consistency"):
                    sections["vibe"]["items"].append({"status": "info", "text": brand["style_consistency"]})
                
                # Viral Readiness
                if data.get("viral_readiness"):
                    status = "ok" if "Pronto" in data["viral_readiness"] else "warning"
                    sections["vibe"]["items"].append({"status": status, "text": f"Viral Ready: {data['viral_readiness']}"})
                
                # Pros/Cons
                for pro in data.get("pros", []):
                    sections["vibe"]["items"].append({"status": "ok", "text": pro})
                for con in data.get("cons", []):
                    sections["vibe"]["items"].append({"status": "warning", "text": con})
                
                # Immediate Actions
                for action in data.get("immediate_actions", []):
                    priority = action.get("priority", 99)
                    action_text = action.get("action", "")
                    impact = action.get("impact", "")
                    if action_text:
                        recommendations.append(f"[P{priority}] {action_text} (Impacto: {impact})")
        
        # Bio length check
        if len(bio) < 30:
            sections["bio"]["items"].append({"status": "warning", "text": "Bio muito curta"})
            recommendations.append("Expandir bio com mais informações")
        elif len(bio) > 50:
            sections["bio"]["items"].append({"status": "ok", "text": f"Tamanho da bio OK ({len(bio)} chars)"})
        
        if "📧" not in bio and "@" not in bio and "link" not in bio.lower() and "👇" not in bio and "clique" not in bio.lower():
            # Use PERSONALIZED CTAs from niche detection (if available)
            personalized_ctas = niche_data.get("personalized_ctas", [])
            if personalized_ctas:
                sections["bio"]["cta_suggestions"] = personalized_ctas
                recommendations.append(f"Adicionar CTA na bio. Sugestões para '{niche_data.get('niche', 'seu nicho')}': {', '.join(personalized_ctas[:2])}")
            else:
                # Fallback to generic CTAs
                cta_examples = [
                    "👇 Link na bio",
                    "📩 DM para parcerias",
                    "🔗 Meu curso/produto no link",
                    "✨ Siga para mais conteúdo",
                    "🎬 Novo vídeo todo dia!",
                    "💼 Contato comercial"
                ]
                sections["bio"]["cta_suggestions"] = cta_examples
                recommendations.append(f"Adicionar CTA na bio")

        return {
            "total_score": total_score,
            "vision_score": vision_score,
            "sections": sections,
            "recommendations": recommendations[:5],  # Top 5 tips
            "niche": niche_data,  # Include full niche analysis
            "details": details,  # Keep raw details for debugging
            "profile_overiew": {
                "username": metadata.get("unique_id") or metadata.get("username"),
                "bio": bio
            }
        }
    
    def analyze_full_page_vibe(self, screenshot_path: str) -> dict:
        """
        Analyzes the full page screenshot for branding cohesion.
        Called by Oracle before/during audit.
        """
        try:
            img = Image.open(screenshot_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            prompt = [
                "Você é um ESPECIALISTA em UX/UI e Branding Digital com foco em TikTok. Analise este screenshot do perfil COMPLETO.",
                img,
                """
                Faça uma análise EXTREMAMENTE DETALHADA e retorne SOMENTE JSON:
                {
                    "score": 0-100,
                    "overall_vibe": "Qual a 'energia' dominante? (Ex: Caótico, Minimalista, Corporate, Gamer, Lifestyle, Educativo)",
                    "first_impression": "O que um visitante pensa nos primeiros 3 segundos?",
                    "layout_analysis": {
                        "quality": "Clean" | "Crowded" | "Balanced" | "Caótico",
                        "visual_hierarchy": "Clara" | "Confusa" | "Inexistente",
                        "above_fold_impact": "Forte" | "Fraco" | "Médio"
                    },
                    "thumbnail_analysis": {
                        "consistency": "Alta" | "Média" | "Baixa" | "Inexistente",
                        "color_palette": ["cor1", "cor2", "cor3"],
                        "text_usage": "Sim com consistência" | "Sim mas inconsistente" | "Não usa texto",
                        "face_presence": "Sempre" | "Às vezes" | "Nunca",
                        "hook_strength": "Forte" | "Médio" | "Fraco"
                    },
                    "branding_cohesion": {
                        "score": 0-100,
                        "color_consistency": "Consistente" | "Variado" | "Caótico",
                        "style_consistency": "Forte identidade" | "Identidade parcial" | "Sem identidade clara",
                        "professional_level": "Agência" | "Creator experiente" | "Iniciante" | "Amador"
                    },
                    "engagement_signals": {
                        "content_variety": "Boa" | "Limitada" | "Excessiva",
                        "posting_frequency_feel": "Ativo" | "Esporádico" | "Abandonado",
                        "call_to_action_visible": true/false
                    },
                    "pros": ["ponto forte 1 específico", "ponto forte 2", "ponto forte 3"],
                    "cons": ["problema 1 com solução", "problema 2 com solução"],
                    "immediate_actions": [
                        {"priority": 1, "action": "ação urgente", "impact": "Alto", "effort": "Baixo"},
                        {"priority": 2, "action": "ação importante", "impact": "Alto", "effort": "Médio"},
                        {"priority": 3, "action": "nice to have", "impact": "Médio", "effort": "Baixo"}
                    ],
                    "competitor_positioning": "Como este perfil se compara com top creators do nicho?",
                    "viral_readiness": "Pronto para viralizar" | "Precisa de ajustes" | "Longe do ideal"
                }
                """
            ]
            
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)
        except Exception as e:
             return {"error": str(e)}

    def competitor_spy(self, target_username: str) -> dict:
        """
        ENHANCED Spy on a competitor with DEEP analysis.
        """
        
        # MOCKED Scraped Data (Smart Demo based on username)
        if any(x in target_username.lower() for x in ["game", "zoka", "play", "cortes"]):
             mock_scraped_data = {
                "username": target_username,
                "followers": 554000,
                "following": 320,
                "likes": 12500000,
                "videos": 450,
                "bio": "Gamer lifestyle 🎮 | Lives todos os dias | Cola na grade!",
                "recent_posts": [
                    {"desc": "O susto que eu tomei nesse jogo kkkk", "views": 45000, "likes": 3200, "comments": 120},
                    {"desc": "Melhor jogada da semana #clips", "views": 120000, "likes": 8500, "comments": 340},
                    {"desc": "Live ON! Corre pra assistir", "views": 32000, "likes": 2100, "comments": 89}
                ],
                "top_hashtags": ["#gaming", "#streamer", "#clips", "#viral"]
            }
        else:
             mock_scraped_data = {
                "username": target_username,
                "followers": 15400,
                "following": 890,
                "likes": 234000,
                "videos": 127,
                "bio": "Marketing Digital sem enrolação 🚀 | Te ensino a vender todo dia | 👇 Aula Gratuita",
                "recent_posts": [
                    {"desc": "3 Erros que matam seu alcance #marketing #dicas", "views": 4500, "likes": 320, "comments": 45},
                    {"desc": "Como fiz R$10k em 7 dias (Case real)", "views": 12000, "likes": 890, "comments": 67},
                    {"desc": "Pare de postar conteudo ruim!", "views": 3200, "likes": 210, "comments": 23}
                ],
                "top_hashtags": ["#marketingdigital", "#vendas", "#empreendedorismo"]
            }
        
        # Calculate derived metrics
        avg_views = sum(p["views"] for p in mock_scraped_data["recent_posts"]) / len(mock_scraped_data["recent_posts"])
        engagement_rate = round((sum(p["likes"] + p["comments"] for p in mock_scraped_data["recent_posts"]) / sum(p["views"] for p in mock_scraped_data["recent_posts"])) * 100, 2)
        
        mock_scraped_data["avg_views"] = int(avg_views)
        mock_scraped_data["engagement_rate"] = engagement_rate
        
        # ENHANCED Oracle Analysis Prompt
        prompt = f"""
        Você é um ESPECIALISTA em Análise Competitiva de TikTok com 10 anos de experiência.
        Faça uma análise PROFUNDA e ESTRATÉGICA deste concorrente.
        
        Dados do Alvo:
        {json.dumps(mock_scraped_data, indent=2, ensure_ascii=False)}
        
        Analise CADA aspecto e retorne um relatório DETALHADO.
        
        Responda SOMENTE JSON:
        {{
            "competitor_score": 0-100 (quão forte é este competidor),
            "threat_level": "Baixo" | "Médio" | "Alto" | "Crítico",
            "niche": "Nicho exato detectado",
            "profile_analysis": {{
                "bio_quality": 0-100,
                "bio_critique": "Análise detalhada da bio",
                "branding_strength": "Fraco" | "Médio" | "Forte",
                "audience_type": "Descrição do público-alvo"
            }},
            "content_strategy": {{
                "posting_frequency": "Diário" | "3-5x semana" | "Irregular",
                "content_pillars": ["Pilar 1", "Pilar 2", "Pilar 3"],
                "format_preference": "Formato mais usado",
                "hook_style": "Estilo de gancho usado",
                "cta_usage": "Como usam CTAs"
            }},
            "strengths": [
                "Ponto forte 1 específico",
                "Ponto forte 2 específico"
            ],
            "weaknesses": [
                "Fraqueza explorável 1 (com sugestão de como atacar)",
                "Fraqueza explorável 2 (com sugestão de como atacar)"
            ],
            "content_hooks_to_steal": [
                "Hook específico que funcionou + por que funciona",
                "Hook 2 + por que funciona",
                "Hook 3 + por que funciona"
            ],
            "opportunity_zones": [
                "Oportunidade 1: Onde você pode superá-los",
                "Oportunidade 2: Gap no mercado que eles não cobrem"
            ],
            "battle_plan": {{
                "immediate_actions": ["Ação 1 para hoje", "Ação 2 para amanhã"],
                "content_ideas": ["Ideia de conteúdo 1 baseada na análise", "Ideia 2"],
                "differentiation_strategy": "Como se posicionar diferente deles"
            }},
            "killer_bio": "Bio otimizada que seria melhor que a deles"
        }}"""
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            
            analysis = json.loads(txt)
            return {
                "scraped_data": mock_scraped_data,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "error": str(e), 
                "scraped_data": mock_scraped_data,
                "analysis": {
                    "competitor_score": 50,
                    "threat_level": "Médio",
                    "niche": "Desconhecido",
                    "weaknesses": ["Erro na análise - tente novamente"],
                    "content_hooks_to_steal": ["Não disponível"]
                }
            }

    def auto_fix_bio(self, current_bio: str, niche: str) -> list:
        prompt = f"""
        Atue como Copywriter Senior de TikTok.
        Bio Atual: "{current_bio}"
        Nicho: "{niche}"
        
        Gere 5 opcoes de Bio altamente conversivas (max 80 caracteres, usar emojis).
        Use gatilhos mentais de Autoridade, Prova Social ou Urgência.
        
        Retorne APENAS um JSON array de strings: ["Opcao 1", ..., "Opcao 5"]
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                 txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except:
            return ["Falha ao gerar bios. Tente novamente."]

    def suggest_keywords(self, niche: str) -> dict:
        """
        [SYN-27] Suggests high-potential keywords for a specific niche.
        Uses Tavily (if available) or AI reasoning.
        """
        # Tenta usar Tavily se disponível (integração futura ou via prompt se tiver acesso web)
        # Aqui usamos o poder do LLM para gerar keywords baseadas em conhecimento de tendências
        
        prompt = f"""
        Atue como um Especialista em SEO de TikTok.
        Gere uma lista de KEYWORDS e TERMOS DE PESQUISA de alto potencial para o nicho: "{niche}".
        
        Classifique em:
        1. Broad (Alto volume)
        2. Specific (Cauda longa / Baixa competição)
        3. Trending (O que está em alta agora)
        
        Responda SOMENTE JSON:
        {{
            "niche": "{niche}",
            "high_volume": ["term1", "term2", "term3", ...],
            "long_tail": ["term1", "term2", "..."],
            "trending_now": ["term1", "term2", ...],
            "content_ideas": ["Ideia de video usando keyword 1", "Ideia 2"]
        }}
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                 txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except Exception as e:
            return {"error": str(e), "niche": niche}

    def analyze_content_gaps(self, username: str, topic: str) -> dict:
        """
        [SYN-27] Identifies content gaps (what is NOT being covered but should be).
        """
        prompt = f"""
        Analise o tópico "{topic}" para o perfil "{username}".
        Identifique CONTENT GAPS (Lacunas de Conteúdo):
        - O que os competidores estão fazendo que este perfil NÃO está?
        - Perguntas que o público faz mas ninguém responde bem?
        - Sub-nichos inexplorados dentro de {topic}?
        
        Responda SOMENTE JSON:
        {{
            "topic": "{topic}",
            "missing_formats": ["Live", "Tutorial", "Vlog", ...],
            "unanswered_questions": ["Pergunta 1", "Pergunta 2"],
            "underserved_subtopics": ["Subtopico 1", "Subtopico 2"],
            "blue_ocean_strategy": "Uma estratégia para dominar uma área sem competição"
        }}
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                 txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except Exception as e:
            return {"error": str(e)}

    def generate_content_metadata(self, filename: str, niche: str = "General", duration: int = 0) -> dict:
        """
        Generates Viral Caption and Hashtags based on Filename context.
        Used by Ingestion to pre-populate metadata.
        """
        # Clean filename
        clean_name = filename.replace("_", " ").replace("-", " ").replace(".mp4", "")
        
        prompt = f"""
        Atue como um Estrategista de Conteúdo Viral (TikTok/Reels).
        Analise este arquivo de vídeo que acabou de ser enviado:
        
        Nome do Arquivo: "{clean_name}"
        Nicho do Perfil: "{niche}"
        
        Tarefa:
        1. Crie uma LEGENDA (Caption) altamente engajadora (curta, com pergunta ou gancho).
        2. Selecione 15 HASHTAGS otimizadas para este nicho.
        3. Estime um "Potencial Viral" (0-100) baseado no tema sugerido pelo nome.
        
        Responda APENAS JSON:
        {{
            "suggested_caption": "string",
            "hashtags": ["#tag1", "#tag2"],
            "viral_score": 85,
            "viral_reason": "Explica por que este tema funciona"
        }}
        """
        
        try:
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
        except Exception as e:
            print(f"Content Gen Error: {e}")
            return {
                "suggested_caption": f"{clean_name} - Confira!",
                "hashtags": ["#viral", "#fyp"],
                "viral_score": 50,
                "viral_reason": f"Erro na IA: {str(e)}"
            }

    def _detect_niche(self, username: str, bio: str, label: str) -> dict:
        """
        Uses AI to detect the profile's niche and generate personalized recommendations.
        """
        try:
            context = f"Username: {username}\nBio: {bio}\nLabel: {label}"
            
            prompt = f"""Analise este perfil TikTok e identifique o NICHO:

{context}

Responda SOMENTE JSON:
{{
    "niche": "Nome curto do nicho (ex: Cortes de Podcast, Receitas, Fitness, Humor, Games, Educação, Música, Moda, Tech, Finanças, Viagem, Pets)",
    "niche_confidence": "Alta" | "Média" | "Baixa",
    "audience": "Descrição do público-alvo ideal em 1 frase",
    "content_style": "Estilo predominante (ex: Educativo, Entretenimento, Inspiracional, Informativo, Tutorial)",
    "personalized_recommendations": [
        "Recomendação específica para este nicho 1",
        "Recomendação específica para este nicho 2",
        "Recomendação específica para este nicho 3"
    ],
    "personalized_ctas": [
        "CTA específico para o nicho",
        "Outro CTA relevante para o público",
        "CTA de conversão para este tipo de conteúdo"
    ],
    "competitor_tip": "Dica baseada em top creators deste nicho",
    "trending_format": "Formato de vídeo que está em alta neste nicho"
}}"""
            
            ai_res = self.client.generate_content(prompt)
            txt = ai_res.text
            
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            
            return json.loads(txt)
            
        except Exception as e:
            print(f"Niche Detection Error: {e}")
            return {
                "niche": "Geral",
                "niche_confidence": "Baixa",
                "audience": "Público geral",
                "content_style": "Variado",
                "personalized_recommendations": [
                    "Definir um nicho claro para atrair público fiel",
                    "Manter consistência no estilo de conteúdo",
                    "Usar hashtags relevantes para o tema"
                ],
                "personalized_ctas": [
                    "👇 Siga para mais conteúdo",
                    "💬 Comente sua opinião",
                    "🔔 Ative as notificações"
                ],
                "competitor_tip": "Analise creators do seu nicho para inspiração",
                "trending_format": "Vídeos curtos com hook forte nos primeiros 3s"
            }

seo_engine = SEOEngine()
