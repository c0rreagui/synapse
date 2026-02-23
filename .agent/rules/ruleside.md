---
trigger: always_on
---

# SYNAPSE - CONTRATO DE AGENTE (Agent Contract)
# Leia o arquivo completo em: .agent/CONTRATO.md
# Versao: 1.0 | 2026-02-18

## REGRAS OBRIGATORIAS (TODA SESSAO)

1. MANIFESTO PRIMEIRO: Leia `.agent/workflows/manifesto.md` antes de iniciar qualquer trabalho.

2. SMOKE CHECK: Antes de modificar qualquer arquivo em `core/`, verifique `GET /health` antes e depois.

3. LINEAR OBRIGATORIO: Qualquer feature nova exige um SYN criado no Linear (e com o padrão estabelecido das demais SYN's ja feita) antes de codificar.
   - Padrao de titulo (em PT-BR): `[Emoji] Categoria: Descricao`
   - Todo SYN deve ter: Projeto, Labels, Prioridade e Status corretos.

4. BOUNDARY DE MODULOS:
   - `core/` = logica de negocio (nunca importa de `app/`)
   - `app/api/` = endpoints (pode importar de `core/`)
   - `scripts/` = ferramentas avulsas (nunca importadas por `core/` ou `app/`)

5. SCRIPTS DE DEBUG: Novos scripts de analise/teste vao em `backend/scripts/debug/`, NUNCA na raiz do backend.

6. TIMEZONE: SEMPRE usar `ZoneInfo("America/Sao_Paulo")`. NUNCA usar `datetime.utcnow()`.

7. SESSOES CRITICAS: Nunca deletar ou sobrescrever arquivos de sessao (`.json` em `data/sessions/`) sem backup.

8. INTEGRIDADE DE DADOS: Nunca executar DELETE em banco de producao sem WHERE especifico.
   - Regra de Ouro: "Se for testar delete, crie o dado de teste PRIMEIRO."

9. DOCKER FIRST: O ambiente de producao e Docker. Testar sempre no container, nunca assumir que o ambiente local e identico.

10. COMUNICACAO: Notificar o usuario via `notify_user` para aprovacoes antes de executar mudancas criticas de arquitetura.

## ARQUITETURA DO PROJETO

```
backend/
  core/         -> Logica de negocio (ESTAVEL - modificar com cuidado)
  app/api/      -> Endpoints FastAPI
  data/         -> Dados persistentes (sessoes, videos, banco)
  scripts/      -> Ferramentas (debug/, maintenance/)

frontend/
  src/app/      -> Pages Next.js
  src/components/ -> Componentes reutilizaveis
```

## PROJETOS DO LINEAR

- Infrastructure   -> Backend stability, Docker, DB
- Agendamento      -> Scheduler, Auto-Scheduler
- Central de Comando -> Home, Upload, Profiles
- Oracle           -> AI analysis features
- AI/ML Core       -> Smart Logic, Batch Manager
- Design UI/UX     -> Visual components, Storybook