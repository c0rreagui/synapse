---
description: Guia para usar o Olho Que Tudo Vê (Sistema de Monitoramento Ultra-Detalhado)
---

# 👁️ O OLHO QUE TUDO VÊ (Sonar & Monitoramento)

Este guia explica como usar o novo sistema de monitoramento de saúde ("Sonar") e as ferramentas de debug visual.

## 1. O Sonar (Indicador de Saúde)

Localizado no topo da barra lateral esquerda, o Sonar é seu indicador de confiança imediata.

### Estados do Indicador

- **🟢 Verde (Pulsando):** O sistema está 100% online. O Scheduler está rodando e verificou itens nos últimos 90 segundos.
- **🟡 Amarelo:** O sistema está "Stalled" (atrasado). O Scheduler está rodando, mas não reporta há 1-3 minutos (possivelmente processando algo pesado).
- **🔴 Vermelho:** O sistema está OFFLINE ou TRAVADO. O Scheduler não reporta há >3 minutos. Reinicie o backend imediatamente.

## 2. Monitoramento de Uploads (Olho de Deus)

Para cada upload, o sistema gera uma pasta de evidências em `backend/MONITOR/runs/`.

### O que é salvo

- **🕵️‍♂️ Traces Completos:** Arquivos `.zip` que podem ser abertos no Playwright Trace Viewer (`npx playwright show-trace ...`) para ver exatamente o que o bot viu (cliques, redes, console).
- **📸 Screenshots:** Capturas passo-a-passo e contínuas (a cada 500ms).
- **📝 Relatório JSON:** Log estruturado de cada etapa.

## 3. Como Verificar Falhas

Se um post falhar:

1. Vá em `backend/MONITOR/runs/` e ordene por data.
2. Abra a pasta mais recente.
3. Abra o `REPORT.json` para ver o erro.
4. Se precisar ver a tela, use o comando fornecido no log para abrir o Trace Viewer.
