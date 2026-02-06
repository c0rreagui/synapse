import requests
from PIL import Image
from io import BytesIO
from core.oracle.client import oracle_client
import json
import os

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
                from core.network_utils import get_tiktok_headers
                headers = get_tiktok_headers()
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
                    from core.network_utils import get_tiktok_headers
                    headers = get_tiktok_headers()
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
                "icon": "[BIO]",
                "items": []
            },
            "avatar": {
                "score": vision_score,
                "label": "Visual Branding",
                "icon": "[ART]",
                "items": []
            },
            "content": {
                "score": 50,
                "label": "Capas de Vídeo",
                "icon": "[VIDEO]",
                "items": []
            },
            "vibe": {
                "score": 50,
                "label": "Vibe Check",
                "icon": "[VIBE]",
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
        
        # Emoji-safe logic for bio check
        has_contact_info = any(x in bio.lower() for x in ["@", "link", "clique", "dm", "contato", "email", "www"])
        
        if not has_contact_info:
            # Use PERSONALIZED CTAs from niche detection (if available)
            personalized_ctas = niche_data.get("personalized_ctas", [])
            if personalized_ctas:
                sections["bio"]["cta_suggestions"] = personalized_ctas
                recommendations.append(f"Adicionar CTA na bio. Sugestões para '{niche_data.get('niche', 'seu nicho')}': {', '.join(personalized_ctas[:2])}")
            else:
                # Fallback to generic CTAs
                cta_examples = [
                    "[LINK] Link na bio",
                    "[DM] DM para parcerias",
                    "[LINK] Meu curso/produto no link",
                    "[+] Siga para mais conteúdo",
                    "[VIDEO] Novo vídeo todo dia!",
                    "[CONTACT] Contato comercial"
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

    async def competitor_spy(self, target_username: str) -> dict:
        """
        ENHANCED Spy on a competitor with DEEP analysis using REAL DATA.
        """
        from core.oracle.collector import oracle_collector
        
        print(f"[SPY] Spying on {target_username}...")
        
        # 1. Real Scraping
        scraped_stats = await oracle_collector.collect_tiktok_profile(target_username)
        
        if "error" in scraped_stats:
            # Fallback only on hard error, but usually we want to know
            print(f"[WARNING] Scraping failed: {scraped_stats['error']}")
            return {"error": "Falha ao coletar dados do perfil. Verifique o user ou tente novamente.", "details": scraped_stats}

        # 2. Parse Numbers (Convert "35.3M" -> 35300000)
        def parse_stat(val):
            if isinstance(val, (int, float)): return int(val)
            if not val or val == "Unknown": return 0
            val = val.upper().replace("LIKES", "").replace("FOLLOWERS", "").replace("FOLLOWING", "").strip()
            mult = 1
            if "K" in val:
                mult = 1000
                val = val.replace("K", "")
            elif "M" in val:
                mult = 1000000
                val = val.replace("M", "")
            elif "B" in val:
                mult = 1000000000
                val = val.replace("B", "")
            try:
                return int(float(val) * mult)
            except:
                return 0

        # Enrich stats with parsed values for AI math
        scraped_stats["followers_count"] = parse_stat(scraped_stats.get("followers"))
        scraped_stats["likes_count"] = parse_stat(scraped_stats.get("likes"))
        scraped_stats["following_count"] = parse_stat(scraped_stats.get("following"))
        
        # 3. Calculate Derived Metrics
        videos = scraped_stats.get("videos", [])
        total_views = 0
        total_interactions = 0
        
        for v in videos:
            v_views = parse_stat(v.get("views"))
            total_views += v_views
            # We don't have likes/comments per video in basic scrape, assume 10% engagement for estimation if missing
            # But wait, collector structure for videos only has 'views'.
            # Let's derive ESTIMATED engagement from total likes / total videos (heuristic)
            
        video_count_est = max(1, len(videos)) # Only top 5 usually
        # To get real avg, we need total video count? We don't have it easily from HTML sometimes.
        # Let's use the valid videos we found.
        
        if video_count_est > 0:
            avg_views = total_views / video_count_est
        else:
            avg_views = 0
            
        # Engagement Rate global heuristic: (Total Likes / Total Videos) / Avg Views?
        # Better: (Likes / Followers) is a common simplistic metric if we don't have per-video engagement
        # Let's use a mock engagement rate if we lack granular data, or calculate strictly.
        if scraped_stats["followers_count"] > 0:
            # Likes per follower ratio (Popstar metric)
            engagement_rate = round((scraped_stats["likes_count"] / scraped_stats["followers_count"]) * 10, 2) # Arbitrary scale factor
        else:
            engagement_rate = 0.0

        scraped_stats["avg_views_recent"] = int(avg_views)
        scraped_stats["est_engagement_rate"] = engagement_rate
        
        # 4. ENHANCED Oracle Analysis Prompt
        prompt = f"""
        Você é um ESPECIALISTA em Análise Competitiva de TikTok.
        
        Dados REAIS do Alvo (@{target_username}):
        {json.dumps(scraped_stats, indent=2, ensure_ascii=False)}
        
        OBS: Os dados acima foram extraídos em tempo real. "videos" contém apenas os últimos posts.
        Use os números de seguidores/likes TOTAIS para julgar a autoridade.
        
        Analise CADA aspecto e retorne um relatório DETALHADO.
        
        Responda SOMENTE JSON:
        {{
            "competitor_score": 0-100 (quão perigoso/forte é este competidor),
            "threat_level": "Baixo" | "Médio" | "Alto" | "Crítico",
            "niche": "Nicho exato detectado",
            "profile_analysis": {{
                "bio_quality": 0-100,
                "bio_critique": "Critica construtiva da bio",
                "branding_strength": "Fraco" | "Médio" | "Forte",
                "audience_type": "Descrição do público dele"
            }},
            "content_strategy": {{
                "posting_frequency": "Baseado na frequencia aparente",
                "content_pillars": ["Pilar Provável 1", "Pilar 2"],
                "format_preference": "Formato aparente (Reels, Vlogs, Cortes)",
                "hook_style": "Estilo de titulos/hooks usados",
                "cta_usage": "Uso de chamadas para ação"
            }},
            "strengths": ["Ponto forte 1", "Ponto forte 2"],
            "weaknesses": ["Fraqueza 1", "Fraqueza 2"],
            "content_hooks_to_steal": ["Hook derivado 1", "Hook 2", "Hook 3"],
            "opportunity_zones": ["Oportunidade 1", "Oportunidade 2"],
            "battle_plan": {{
                "immediate_actions": ["Ação 1", "Ação 2"],
                "content_ideas": ["Ideia 1", "Ideia 2"],
                "differentiation_strategy": "Estratégia única"
            }},
            "killer_bio": "Sugestão de bio melhorada"
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
                "scraped_data": scraped_stats,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "error": f"AI Parsing failed: {str(e)}", 
                "scraped_data": scraped_stats,
                "analysis": {
                    "competitor_score": 0,
                    "weaknesses": ["Erro na IA"],
                    "threat_level": "Erro"
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

    async def generate_content_metadata(
        self, 
        filename: str, 
        niche: str = "General", 
        duration: int = 0,
        video_path: str = None,  # Path to video for Vision analysis
        use_vision: bool = True   # Toggle Vision analysis
    ) -> dict:
        """
        Generates Viral Caption and Hashtags based on Filename AND video visual context.
        Uses Vision AI to analyze actual video content when video_path is provided.
        """
        import PIL.Image
        import logging
        logger = logging.getLogger(__name__)
        
        # Clean filename
        clean_name = filename.replace("_", " ").replace("-", " ").replace(".mp4", "")
        
        # [SYN-VISION] Analyze video frames for context
        visual_context = ""
        if video_path and use_vision and os.path.exists(video_path):
            try:
                from core.oracle.faculties.vision import VisionFaculty
                vision = VisionFaculty(self.client)
                
                # Extrair 1 frame central do video
                logger.info(f"[VISION] Analisando video para contexto visual: {video_path}")
                frames = vision.extract_frames(video_path, num_frames=1)
                
                if frames and os.path.exists(frames[0]):
                    img = PIL.Image.open(frames[0])
                    # Pedir descricao curta e objetiva
                    vision_prompt = [
                        "Descreva esta cena de video em 2-3 frases CURTAS.",
                        "Foque em: QUEM esta no video, O QUE estao fazendo, ONDE estao.",
                        "Seja objetivo e descritivo, sem interpretar emocoes.",
                        "Responda em portugues.",
                        img
                    ]
                    vision_res = self.client.generate_content(vision_prompt)
                    visual_context = vision_res.text.strip()
                    logger.info(f"[VISION] Contexto visual obtido: {visual_context[:100]}...")
                    
                    # Limpar frame temporario
                    try:
                        os.remove(frames[0])
                    except:
                        pass
            except Exception as e:
                logger.warning(f"[VISION] Analise visual falhou (usando apenas filename): {e}")
        
        # [SYN-40] Fetch Real Trending Hashtags
        from core.oracle.trend_checker import trend_checker
        cached_trends = trend_checker.get_cached_trends()
        trend_tags = []
        if cached_trends and "trends" in cached_trends:
            # Filter trends that might match niche or are generic high-volume
            # Extract hashtags if title starts with #, otherwise just pass titles as context
            for t in cached_trends["trends"][:10]:
                if t["title"].startswith("#"):
                    trend_tags.append(t["title"])
        
        trend_context = f"Trending Now: {', '.join(trend_tags)}" if trend_tags else "No specific live trends, use evergreen viral tags."

        # Build visual context line if available
        visual_line = f"Descricao Visual do Video (analise de frame): {visual_context}" if visual_context else "Descricao Visual: Nao disponivel - use o nome do arquivo como referencia"

        prompt = f"""
        Atue como um Estrategista de Conteudo Viral (TikTok/Reels).
        Analise este arquivo de video que acabou de ser enviado:
        
        Nome do Arquivo: "{clean_name}"
        Nicho do Perfil: "{niche}"
        {visual_line}
        Contexto Viral: {trend_context}
        
        IMPORTANTE: Se a Descricao Visual estiver disponivel, BASEIE a legenda no conteudo REAL do video!
        
        Tarefa:
        1. Crie uma LEGENDA (Caption) altamente engajadora.
           - OBRIGATORIO: Terminar com um CTA de Crescimento (Ex: "Siga para mais", "Curte se concorda").
           - Use ganchos de curiosidade.
           - IMPORTANTE: NAO inclua hashtags na legenda! As hashtags vao em campo separado.
        2. Selecione 5-7 HASHTAGS otimizadas (MAXIMO 7):
           - 2-3 Tags de Nicho (Especificas do conteudo)
           - 2-3 Tags Virais (fyp, viral, foryou)
           - 1-2 Tags de Tendencia (se relevante do Contexto Viral)
        3. Estime um "Potencial Viral" (0-100).
        
        Responda APENAS JSON:
        {{
            "suggested_caption": "Legenda aqui SEM hashtags (incluindo emojis e CTA)",
            "hashtags": ["tag1", "tag2", "tag3"],
            "viral_score": 85,
            "viral_reason": "Explica por que este tema funciona"
        }}
        
        REGRAS IMPORTANTES:
        - A legenda NAO deve conter nenhuma hashtag (elas serao adicionadas automaticamente)
        - Os hashtags na lista NAO devem ter o simbolo # (sera adicionado automaticamente)
        - MAXIMO 7 hashtags para evitar parecer spam
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
                "suggested_caption": f"{clean_name} - Siga para mais content! 👇",
                "hashtags": ["#viral", "#fyp", f"#{niche.replace(' ', '')}"],
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
