# SYNAPSE - CONTRATO DE AGENTE
>
> Versao: 1.0 | Criado: 2026-02-18
> Assinado: Antigravity & c0rreagui

Este documento e a Lei para qualquer agente (IA ou humano) que trabalhe no Synapse.
Todo agente DEVE ler este contrato ao iniciar uma sessao.

---

## 1. Antes de Comecar (Checklist Obrigatorio)

- [ ] Leia `manifesto.md` para entender o espirito do projeto
- [ ] Confirme que o Docker esta rodando (`docker ps | grep synapse`)
- [ ] Verifique `GET http://localhost:8000/health` - deve retornar `{"status":"healthy"}`
- [ ] Identifique SE existe uma issue SYN aberta para o que voce vai fazer

---

## 2. Regras de Codigo

### 2.1 Boundary de Modulos (CRITICO)

```text
core/     -> Logica de negocio pura
             - NUNCA importa de app/
             - Modificacoes aqui afetam toda a plataforma

app/api/  -> Endpoints HTTP
             - Pode importar de core/
             - Nao contem logica de negocio diretamente

scripts/  -> Ferramentas avulsas
             - NUNCA importadas por core/ ou app/
             - Scripts de debug vao em scripts/debug/
```

### 2.2 Onde Colocar Scripts Novos

| Tipo | Onde |
| --- | --- |
| Debugar banco de dados | `backend/scripts/debug/` |
| Investigar bug especifico | `backend/scripts/debug/` |
| Teste de feature nova | `backend/tests/` |
| Script de manutencao | `backend/scripts/maintenance/` |
| NUNCA | Na raiz do `backend/` |

### 2.3 Timezone (CRITICO)

```python
# CORRETO
from zoneinfo import ZoneInfo
sp_tz = ZoneInfo("America/Sao_Paulo")
now = datetime.now(sp_tz)

# ERRADO - NUNCA FAZER
now = datetime.utcnow()
now = datetime.now()  # sem timezone
```

---

## 3. Linear - A Memória Coletiva Inteligente (SISTEMA PRINCIPAL)

> **"O Linear não é apenas um tracker - é a fonte da verdade absoluta, a memória de longo prazo e a documentação principal do Synapse."**

**NUNCA NEGLIGENCIE O LINEAR.** Se não está no Linear, com a riqueza de detalhes e qualidade esperadas, então não foi feito. TODA a documentação atualizada do projeto (diagramas, decisões arquiteturais, métricas e checklists) deve residir primariamente lá.

### Antes de Codificar e Durante o Processo

Se nao existe um SYN para o que voce vai fazer, CRIE UM antes de comecar. Ao finalizar uma branch/tarefa, ATUALIZE a issue com o máximo de detalhes possível, espelhando os relatórios de `walkthrough` e `implementation_plan` na própria Issue do Linear.

### Padrao de Titulo

```text
[Emoji] Categoria: Descricao Clara
```

Exemplos:

- `🚀 Feature: Inteface Ultra-Premium UX/UI - Parte 1`
- `🐛 Bug: Session Expired apos renovacao de LocalStorage`
- `🔧 Chore: Refatoracao de scripts debug no backend`

### O Padrão de Qualidade do Linear (Score > 90)

Toda Issue concluída no Linear DEVE almejar o nível de "Excellent" (Quality Score ≥ 90). Para isso, as issues devem obrigatoriamente conter:

- **Diagramas de Arquitetura:** Utilize blocos Markdown com `mermaid` para desenhar fluxos sempre que o código passar de 50 linhas ou introduzir nova lógica.
- **Tabelas Explicativas:** Tabelas mostrando Decisões Arquiteturais, Rotas Novas (Method, Endpoint, Schemas) e Comparativos Before/After.
- **Screenshots / Carousel:** Inserir a sintaxe `carousel` no markdown evidenciando as mudanças visuais que foram validadas e testadas (Antes, Depois, Vídeo Demo).
- **Riqueza de Markdown:** Use labels de cores (🚨 Critical, 🚀 Feature, 🎨 UI/UX) e as propriedades adequadas (Project, Priority, Status).

### Campos Obrigatorios em Todo SYN

| Campo | Obrigatorio |
| --- | --- |
| Titulo (padrao acima) | Sim |
| Projeto linkado | Sim |
| Labels | Sim (minimo 1) |
| Prioridade | Sim |
| Status | Sim |
| Descricao com contexto Rico | Sim |

### Projetos Disponiveis

| Projeto | Quando usar |
| --- | --- |
| Infrastructure | Docker, DB, sessoes, CI/CD, estabilidade |
| Agendamento | Scheduler, Auto-Scheduler, Studio Scanner |
| Central de Comando | Home, Upload, Profiles |
| Oracle | AI analysis, SEO, Deep Analytics |
| AI/ML Core | Smart Logic, Batch Manager, algoritmos |
| Design UI/UX | Visual components, Storybook, animacoes, redesigns estéticos |

### Labels Disponiveis

`Backend` `Frontend` `Bug` `Feature` `Improvement` `Polimento` `AI/ML` `Testes`

---

## 4. Seguranca de Dados

### Sessoes TikTok (SAGRADO)

- Arquivos em `data/sessions/` sao irreplaceaveis
- NUNCA deletar sem backup
- NUNCA sobrescrever sem confirmar que a nova sessao funciona primeiro

### Banco de Dados

```python
# CORRETO - sempre com WHERE especifico
db.query(ScheduleItem).filter(ScheduleItem.id == specific_id).delete()

# ERRADO - NUNCA EM PRODUCAO
db.query(ScheduleItem).delete()  # sem filtro!
```

---

## 5. Fluxo de Testes e Deployment

### Hierarquia de Ambientes

1. Localhost (Dev) = Ambiente de programacao inicial
2. Container Docker (`synapse-backend`) = Producao

### Dev-First e Deploy Seguro (CRITICO)

- NUNCA realize deploy ou teste diretamente no ambiente de producao sem validar antes em desenvolvimento (localhost).
- Toda feature nova, tela nova ou refatoracao deve iniciar e ser inteiramente construida em `localhost`.
- Apenas quando a feature estiver perfeitamente estavel no ambiente local, ela podera avancar para o deploy no Docker/Producao.

### Antes de Marcar Qualquer Tarefa como Concluida

- [ ] Testou ponta-a-ponta no dev local e em seguida no container Docker.
- [ ] Checou os logs do container (`docker logs synapse-backend --tail 50`)
- [ ] Verificou `GET /health` continua saudavel
- [ ] Notificou o usuario com resultado do teste

---

## 6. Comunicacao com o Usuario

- Usar `notify_user` para aprovacoes de mudancas de arquitetura
- Nunca implementar features grandes sem aprovacao do plano primeiro
- Documentar sempre em `implementation_plan.md` antes de executar
- Atualizar o Linear com o resultado apos concluir

## 7. Gerenciamento de Janela de Contexto (Limite de Tokens)

> **CRÍTICO: O limite absoluto de contexto (Context Window Limit) da plataforma Antigravity e modelos como Claude Opus/Gemini é de 200.000 tokens. Estourar este limite acarreta em erros fatais (HTTP 400 Bad Request).**

Para evitar a sobrecarga de tokens (Context Bloat), todos os Agentes DEVEM adotar as seguintes estratégias de fragmentação progressiva:

1. **Divisão por Fases (Chunking):** Nunca tente ler 30 arquivos de uma vez ou processar logs gigantescos de uma só vez.
2. **Execução Modular:** Se uma análise for massiva, divida a varredura e entregue as resenhas/relatórios em partes (por módulo) em mensagens diferentes.
3. **Mantenha os Prompts Limpos:** Ao gerar código, não recrie o arquivo inteiro a menos que seja um arquivo novo. Use ferramentas de `replace_file_content` ou scripts isolados para alterar *apenas as linhas que importam*.
4. **Fechamento de Subsistemas:** Assim que um agente (ex: *QA Browser Subagent*) tiver coletado os dados necessários, ele deve ser finalizado e reportar um resumo otimizado ao invés de cuspir toda a árvore do DOM bruta na conversa atual.

*(Se você notar que a conversa já alcançou vasta complexidade temporal, peça ao humano para consolidar a sessão ou resuma ativamente os dados para economizar espaço de prompt.)*

---

## Assinatura

Este contrato e valido para todos os agentes (Antigravity, Gemini, Claude, GPT, etc.)
que trabalhem no Synapse. O descumprimento pode comprometer a estabilidade do sistema
e os dados do usuario.

"We do not fear the complexity. We become the master of it."

- Manifesto Synapse
