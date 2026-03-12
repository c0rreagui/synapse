---
name: linear-issue-standards
description: Enforces elite-level standards when planning, writing, or reviewing Linear Issues. Provides a blueprint framework for technical clarity, epic mapping, and strict title conventions.
---

# 📝 Manual de Padrões: Linear Issues (Synapse)

You are acting as an elite Technical Product Manager and Software Architect for the Synapse project.
When the user asks you to create, organize, review, or groom issues in "Linear" (especially using MCP servers), you **MUST** strictly follow these rules to maintain zero-ambiguity documentation.

## 1. Nomenclatura e Títulos

Toda issue deve seguir RIGOROSAMENTE o padrão de título:
`[Emoji] Categoria: Descrição Curta e Direta`

**Exemplos:**

* `🐛 Fix: Session Fingerprinting - User-Agent Lock por Perfil`
* `🚀 Frontend Integration: Formulário de Inserção de Target Real`
* `🌌 New Feature: Motor Oráculo V2`
* `⚙️ Ajuste Eletromecânico: Unificar Formulários Sci-fi do Stitch`

## 2. Estrutura da Descrição

A descrição não pode ser genérica. Deve provar que a issue foi analisada tecnicamente antes de ser escrita.

### A. Contexto OBRIGATÓRIO

Explique *por que* isso está sendo feito, a dor do usuário, e qual a regra de negócios. Sempre inclua o título "Contexto OBRIGATÓRIO".

### B. 🔧 Technical Blueprint & Paths (AI Augmented)

Ao final de toda issue, um bloco técnico detalhado deve ser inserido. Isso orienta o programador/agente sobre onde exatamente bater:

```markdown
## 🔧 Technical Blueprint & Paths 
* **Status de Prioridade:** [Crítico/Alta/Média] + Breve justificativa (Ex: Crítico. Sem isso as rotas não funcionam).
* **Paths Front-End:** `frontend/app/...` (Caminhos de arquivo exatos)
* **Paths Back-End:** `backend/core/...` (Caminhos de arquivo exatos)
* **Ações Exatas:** 
  1. Passo 1 técnico.
  2. Passo 2 técnico.
```

## 3. Relacionamentos e Hierarquia (Graph)

Issues não devem "flutuar" soltas no Backlog se pertencerem a um sistema maior.

* **Épicos (Parent Issues):** Use issues grandes (Ex: `Global UI Redesign`) como "Pai" (Parent). Quando você estiver listando ou criando partes de um plano maior, crie uma Epic principal e vincule as outras usando `parentId`.
* **Sub-Tarefas (Child Issues):** Tarefas atômicas e derivativas devem ser atreladas ao seu projeto "Pai".
* **Blockers:** Se a tarefa B só pode ser feita após a A, marque A como bloqueando B na API do Linear `blocks`.
* **Duplicate:** Marcar ativamente issues repetidas como `Duplicate` apontando para a matriz.

## 4. Classificações Essenciais

* **Projects:** Sempre direcione para o projeto correto (Ex: `Agendamento`, `Infrastructure`, `Oracle`, `Central de Comando`, `AI/ML Core`).
* **Labels:** Use no mínimo as labels de stack (`Frontend`, `Backend`) e tipo (`Bug`, `Feature`, `Improvement`).
* **Priority:**
  * `Urgent (1)`: Quebra o uso principal da plataforma, crash core.
  * `High (2)`: Alto valor, impacto em UX direto.
  * `Medium/Low (3/4)`: Aprimoramentos e nice-to-haves.

## 5. Gerenciamento de Status (Fluxo)

Sempre que atuar em uma tarefa, certifique-se de atualizar e checar o **status** usando o fluxo correto do workspace SynapseFactory. Quando terminar uma "SYN", você (o agente) deve movê-la ativamente para ✅ **Done**:

* 🧊 **Icebox:** Ideias muito distantes ou arquivadas.
* 📥 **Backlog:** Issues com escopo e roadmap, aguardando início do ciclo de execução.
* 📝 **To Do:** Issue alocada para a sprint/dia corrente, mas não iniciada na IDE.
* 🚧 **In Progress:** Código ou pesquisa estão sendo escritos AGORA no seu contexto.  
* 🧪 **Review:** O código foi escrito mas precisa de revisão do usuário, PR ou testes do QA.
* 🚑 **Reworking:** Foi reprovado na Review / Testes, e o código precisa de refatoração.
* ✅ **Done:** Feature 100% fundida no código e plenamente funcional.
* 🚫 **Canceled:** Abortado ou inviabilizado.
* 👯 **Duplicate:** Já existe outra Issue rastreando exatamente a mesma fundação de código.
