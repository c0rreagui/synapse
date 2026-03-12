# Contexto Arquitetural Synapse: Legado vs Atual (O Pivot Twitch)

Este documento dita o estado atual da plataforma arquitetural Synapse. Use este contexto para entender o que construir e, mais importante, **o que NÃO construir ou o que remover caso encontre**.

---

## ❌ O Que é LEGADO (Zumbi Code e Padrões Mortos)
Tudo que envolvia fricção e micro-gerenciamento humano foi abortado. Se você ver código que implementa isso, ele é legado.

1. **Uploads Manuais e Drag & Drop:**
   - Telas ou componentes pedindo para o usuário "Arrastar um vídeo" ou clicar em "Fazer Upload de Arquivo Local".
2. **Calendários de Agendamento Manual:**
   - Interfaces com grids de calendário onde o usuário arrasta vídeos para horários específicos (ex: Terça às 14:00).
3. **Gerenciamento Local de Arquivos de UI:**
   - Gerenciamento de pastas de vídeos pela interface.
4. **Edição Fina de Clipe no Frontend:**
   - Componentes estilo "Premiere" na web para timeline de edição manual fina.
5. **Uso de `datetime.utcnow()` no Backend:**
   - Banido. Tudo migrou para `ZoneInfo("America/Sao_Paulo")` atrelado aos horários locais da operação.

---

## ✅ O Que é ATUAL (Esteira Autônoma / Twitch Pivot)
O foco central do Synapse hoje é atuar como uma esteira silenciosa, escalonável e de cliques quase nulos ("Zero-Click"). 

### 1. Topo de Funil: Clipper Autônomo (Zero UI)
- O monitoramento e extração ocorrem **100% em background**.
- Módulos em `backend/core/clipper/` (como `clipping_orchestrator.py`) varrem as streams armadas, baixam VODs, usam FFmpeg e clipam vias de áudio e heurística e salvam na tabela de espera no banco.
- **Importante:** Não construímos UI para ele executar a clipagem. O Clipper é um Daemon invisível. A página "Clipper/Esteira" no frontend serve apenas para ver o "status" e "card" dos processos em andamento.

### 2. Meio de Funil: Factory UI (A Guilhotina)
Este é o único ponto de Gargalo Humano (App/Browser). Rota: `/factory` (ou similar). 
Opera como um *Tinder-Style* focado em rapidez:
- **Swipe Right / Aprovar:** Muda status para "APPROVED", otimista na tela (optimistic UI) e flui para a próxima etapa sem espera.
- **Swipe Left / Descartar:** Joga no limbo (REJECTED), e destrói o arquivo inútil.
- **Inversão Rápida (Remix):** Caso o áudio picote fora de ordem, basta um botão "Inverter" acionando `POST /remix`. O Backend (FFmpeg) reordena automaticamente, e o frontend trava em estado de carregamento de forma limpa. Nada de timeline manual.

### 3. Fundo de Funil: Smart Queue & Auto-Scheduler
- O sistema varre os clones aprovados e os enfia nos buracos vazios de postagem.
- O daemon `auto_scheduler.py` observa as lacunas da malha do TikTok Studio (e outras redes) e distribui organicamente. O humano atua no macro, ditando as regras de postagem, não os horários soltos.

---

## 🛠️ Padrões de Qualidade (Diretrizes de Eng.)
- **Frontend (UX/UI):** Design *Neo-Glass*. Fundo opaco `backdrop-blur-md`, nada de layouts pulando ao carregar (Cumulative Layout Shift). Uso violento de Skeletons. Zod Validation restrita na criação de Entidades (Armies, Canais). Form validations silenciosas são proibidas – falhas da API refletem em Toasts na UI.
- **Backend:** Rígida separação:
  - `core/`: Regra de negócios cega para web e Endpoints.
  - `app/api/`: Controladores FastAPI. Endpoint lida com a requisição e atira no `core/`.
  - `scripts/`: Isolados para testagem ou utilidade de debug na pasta `backend/scripts/debug/`.
- **Banco e Storage:** Usa PostgreSQL para o modelo fixo (Entidades), containers no ar (Docker first approach), armazenamento de mídias pesadas delegadas aos buckets de object storage (MinIO/S3).
