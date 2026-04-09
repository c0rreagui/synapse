---
name: tiktok-auditor-viral
description: Análise reversa do algoritmo do TikTok FYP (Sondagens e Métricas). Versão pragmática e iterativa (Micro-Batching) desenhada para os limites de timeout do Antigravity.
---

# ** Manual de Padrões: TikTok Auditor Viral (Pragmatic Edition)**

Você está atuando como o núcleo analítico de nível Staff (Antigravity), um Agente Autônomo de Inteligência de Dados operando através do `browser_subagent`.

Sua missão é dissecar a matemática da atenção humana da FYP do TikTok. Devido à pesada virtualização do DOM (React/Next.js) do TikTok e aos limites estritos de timeout das sessões de browser automatizado (que lançam erro `Execution context was destroyed`), **ESTA SKILL DEVE SER EXECUTADA EM MICRO-BATCHES ITERATIVOS**. A meta final de amostragem pode ser 500 vídeos, mas a execução será fatalmente dividida em blocos seguros de 10 a 15 vídeos por sessão do subagente.

## **1. Arquitetura de Evasão Básica (Anti-Bot Stealth)**

A plataforma descarrega contexto e bloqueia scroll autônomo. Opere com pragmatismo cirúrgico:

📌 **Regra 1**: Modais de "Sign Up" e Captchas destroem a interação do Playwright. Instrua sempre o subagente a usar injeção CDP ou avaliar código no console para ocultar overlays: `div[class*="login-modal"], div[id*="captcha"], div[class*="download-app"] { display: none !important; opacity: 0 !important; pointer-events: none !important; }`. Nunca use `click()` em botões de fechar (X), pois ativam a heurística de trajetória rasteada.

📌 **Regra 2**: A rolagem (scroll) deve ser pontual. O TikTok carrega de 2 em 2 blocos pesadamente; rolar a página em excesso trava a Thread principal da aba.

## **2. Lógica de Extração Híbrida (Densidade de Imagem + Metrics)**

Para garantir uma análise fotográfica e sintática absoluta nas janelas de estabilidade:

- **Filtro Rigoroso (Anti-Anúncio e Anti-Repetição):** Identifique proativamente anúncios nativos (tags "Sponsored", "Patrocinado", ou botões CTA externos gigantescos). Adicionalmente, armazene a assinatura/URL do TikTok para detetar repetições orgânicas. **Se for anúncio ou vídeo já coletado no ciclo, PULE imediatamente via scroll** sem focar processamento.
- **Métricas e Tema:** Colete `@Username`, `Caption`, e as massas numéricas (`Likes, Comments, Saves, Shares`).
- **O Rácio Sigma (Partilhas vs. Guardados):** Calcule `(Shares / Saves) * 100`. Altos ratios indicam Moeda Social; baixos indicam Guardados Pessoais.
- **Inspeção Visual Profunda:** Não faça suposições baseadas apenas num único snapshot (primeira visualização). Capture **no mínimo 10 screenshots em momentos diferentes ao longo do frame inteiro do vídeo**. Isto gera o mapa de calor visual necessário para OCR profundo dos ganchos, trocas de câmeras e legendas ocultas.

## **3. Orquestração de Micro-Batches e Armazenamento (Regras Fatais)**

É absolutamente **PROIBIDO** instruir o `browser_subagent` a rolar agressivamente por 50 ou mais vídeos contíguos na mesma sessão. O TikTok esvaziará a DOM virtual.

📌 **Micro-Batching (10 a 15 Vídeos):** Cada invocação ao subagente é uma "Missão Curta" e objetiva.

📌 **Transbordo Seguro (Commit Automático):** O Agente Principal (Antigravity/Gemini) deve receber a saída consolidada do subagente (um JSON minimalista descrevendo os <=15 vídeos) e imediatamente fazer *commit/append* dessa saída para uma base de dados JSON temporária em disco, na área de trabalho ou diretório de logs do usuário (ex: `tiktok_fyp_database.json`). Não confie na janela de contexto prolongada.

**Formato de Retorno Esperado do Subagente por Micro-Batch a ser apensado ao JSON Central:**
```json
{
  "batch_timestamp": "2026-...",
  "videos": [
    {
      "author": "@exemplo",
      "caption": "texto da legenda visível na DOM...",
      "likes": 12000,
      "comments": 400,
      "saves": 1200,
      "shares": 3000,
      "sigma_ratio_calculated": 250,
      "category": "Social Currency High Sigma"
    }
  ]
}
```

## **4. O Ciclo de Execução do Antigravity**

Sempre que acionado para o roteiro "TikTok Auditor Viral" ou pedirem para compilar amostras:

1. Inicie (se não houver) o ficheiro `tiktok_fyp_database.json`.
2. Despache o `browser_subagent` com a instrução de ocultar as *Sign-up Walls* e rolar suavemente **apenas 10 a 15 posts**, gerando e devolvendo o JSON formatado supracitado.
3. Receba o resultado na sua thread e grave fisicamente o JSON atualizado.
4. Aborte a sessão do browser para libertar recursos.
5. Repita o ciclo em loop autônomo silenciosamente (ou perguntando ao utilizador "Fase 1 completa. Deseja adicionar o próximo batch ao banco?").
6. Ao final da operação agregada, consolide a totalidade de videos em um grande Blueprint de texto (Artefato Analítico Final) sem estressar a navegação.

## **5. Restrições Absolutas (O Que NUNCA Fazer)**

\***NUNCA** invente valores para as métricas se não os visualizar claramente. Insira valores nulos ou descarte o nodo se o TikTok ofuscar a métrica M/K daquele post. A matemática Sigma baseia-se em integridade não-alucinada.

\***JAMAIS** confie no tempo de vida longo de um agente headless. Adote a estratégia corporativa robusta: sessões assíncronas curtas com checkpoint (saving) agressivo para disco.

\***NÃO** crie viés em nicho de vídeo nem julgue qualidades. O conteúdo mais banal, se tem 5.000 Shares vs 500 Saves (Sigma Ratio 1000), carrega o segredo arquitetural do algoritmo e vale mais focado do que edições cinematográficas ignoradas. Siga a matemática da multidão.

---
// Fim do Documento