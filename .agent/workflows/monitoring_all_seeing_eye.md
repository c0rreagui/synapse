---
description: Guia para usar o Olho Que Tudo Vê (Sistema de Monitoramento Ultra-Detalhado)
---

# 👁️ Olho Que Tudo Vê - Monitoramento

Este workflow explica como executar e analisar o sistema de monitoramento completo do TikTok Studio.

## 1. Executar Teste Monitorado

Para rodar uma sessão de upload completa com monitoramento ativado (gera screenshots, DOM, traces, logs, etc). Certifique-se de ter o arquivo de teste `@p2_teste_multiconta.mp4` em `backend/media/` ou ajuste o script `backend/test_monitored_upload.py`.

// turbo
python backend/test_monitored_upload.py

## 2. Localização dos Resultados

Os resultados são salvos automaticamente na pasta `MONITOR/runs/{run_id}`.

- **01_capturas/**: Screenshots e Vídeos.
- **02_codigo/**: HTML, DOM JSON, Scripts, CSS.
- **03_dados/**: Cookies, Storage, Globals.
- **04_debug/**: Console Logs, Network, Performance.
- **05_traces/**: Arquivo de Trace do Playwright.

O relatório resumido está em: `MONITOR/runs/{run_id}/README.md`

## 3. Visualizar Playwright Trace (Interativo)

Esta é a ferramenta mais poderosa para debug. Permite "viajar no tempo" e ver exatamente o que aconteceu.
Substitua `{run_id}` pelo ID da pasta gerada em `MONITOR/runs/`.

Exemplo de comando (ajuste o ID):

```bash
npx playwright show-trace MONITOR/runs/SEU_ID_AQUI/05_traces/SEU_ID_AQUI_trace.zip
```

## 4. Integração em Código

Para usar o monitoramento em novos scripts ou fluxos:

```python
from core.uploader_monitored import upload_video_monitored

# O uploader monitorado retorna dict com status e caminhos dos relatórios
result = await upload_video_monitored(
    session_name="nome_da_sessao",
    video_path="caminho/do/video.mp4",
    caption="Sua legenda aqui",
    schedule_time="2026-01-01T10:00", # Opcional
    post=False # True para postar/agendar de verdade
)

print(f"Trace salvo em: {result.get('trace_file')}")
print(f"Relatório em: {result.get('monitor_report')}")
```
