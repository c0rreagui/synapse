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

## 3. Linear - Padrao de Issues

### Antes de Codificar

Se nao existe um SYN para o que voce vai fazer, CRIE UM antes de comecar.

### Padrao de Titulo

```text
[Emoji] Categoria: Descricao Clara
```

Exemplos:

- `Feature: TikTok Studio Native Scheduler`
- `Fix: Session Expired apos renovacao de LocalStorage`
- `Chore: Limpeza de scripts debug no backend`

### Campos Obrigatorios em Todo SYN

| Campo | Obrigatorio |
| --- | --- |
| Titulo (padrao acima) | Sim |
| Projeto linkado | Sim |
| Labels | Sim (minimo 1) |
| Prioridade | Sim |
| Status | Sim |
| Descricao com contexto | Sim |

### Projetos Disponiveis

| Projeto | Quando usar |
| --- | --- |
| Infrastructure | Docker, DB, sessoes, CI/CD, estabilidade |
| Agendamento | Scheduler, Auto-Scheduler, Studio Scanner |
| Central de Comando | Home, Upload, Profiles |
| Oracle | AI analysis, SEO, Deep Analytics |
| AI/ML Core | Smart Logic, Batch Manager, algoritmos |
| Design UI/UX | Visual components, Storybook, animacoes |

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

## 5. Fluxo de Testes

### Hierarquia de Ambientes

1. Container Docker (`synapse-backend`) = producao
2. Nunca assumir que ambiente local == Docker

### Antes de Marcar Qualquer Tarefa como Concluida

- [ ] Testou no container Docker (nao apenas localmente)
- [ ] Checou os logs do container (`docker logs synapse-backend --tail 50`)
- [ ] Verificou `GET /health` continua saudavel
- [ ] Notificou o usuario com resultado do teste

---

## 6. Comunicacao com o Usuario

- Usar `notify_user` para aprovacoes de mudancas de arquitetura
- Nunca implementar features grandes sem aprovacao do plano primeiro
- Documentar sempre em `implementation_plan.md` antes de executar
- Atualizar o Linear com o resultado apos concluir

---

## Assinatura

Este contrato e valido para todos os agentes (Antigravity, Gemini, Claude, GPT, etc.)
que trabalhem no Synapse. O descumprimento pode comprometer a estabilidade do sistema
e os dados do usuario.

"We do not fear the complexity. We become the master of it."

- Manifesto Synapse
