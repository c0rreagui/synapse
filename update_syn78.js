const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const issueId = '218bc7ab-1a1f-4140-87f3-ccf6202563a5'; // SYN-78 (was Kanban)

const mutationQuery = `
  mutation IssueUpdate($id: String!, $title: String!, $description: String!) {
    issueUpdate(id: $id, input: {
      title: $title,
      description: $description
    }) {
      success
    }
  }
`;

const newTitle = '🌌 New Feature: Fila de Publicação Inteligente (Smart Queue)';
const newDescription = `## Contexto Modificado
Anteriormente pensado como um Kanban de aprovação manual, o fluxo agora será **100% automatizado**.
Como a automação gera múltiplos clipes por dia, nós não podemos flodar o TikTok (limite seguro de ~2 postagens/dia).

## Requisitos do Fluxo
1. **Ingestão Automática:** Quando o \`editor.py\` terminar de renderizar o \`final_stitched.mp4\`, ele NÃO aguardará aprovação humana.
2. **Fila Circular / Time-slots:** O vídeo entrará numa "Fila de Publicação" (Publish Queue).
3. **Distribuição:** A UI da Fábrica de Vídeos mostrará essa Fila. O sistema (Scheduler/Oráculo) irá distribuir os vídeos prontos nos horários vagos do banco de dados, respeitando o limite de 2 posts por dia por perfil.
4. A tela no Frontend deverá exibir a Fila (Próximos a serem postados, e os já postados), dando visibilidade total ao usuário sem exigir que ele clique em "Aprovar".`;

async function updateIssue() {
    console.log('Updating SYN-78 to Smart Queue...');
    const res = await fetch('https://api.linear.app/graphql', {
        method: 'POST',
        headers: {
            'Authorization': linearKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: mutationQuery,
            variables: { id: issueId, title: newTitle, description: newDescription }
        })
    });
    const d = await res.json();
    if (d.errors) console.error(JSON.stringify(d.errors));
}

updateIssue().then(() => console.log('Issue updated.')).catch(console.error);
