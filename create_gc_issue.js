const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const teamId = 'a9ce7f3a-0415-4424-907d-6d7eb6101de1';

const issue = {
    title: '🛰️ Arquitetura: Galeria Estática FastAPI e Garbage Collector (5-Day TTL)',
    description: `## Arquitetura de Retenção de Vídeos (Asset Retention Policy)

O \`editor.py\` não deve sobrescrever um único \`final_stitched.mp4\` na raiz da pasta. Ele agora deve salvar os exports numa pasta dedicada (\`backend/data/exports/\`) com nomes em hash + job id.

### Requisitos:
1. **Mounting Estático no FastAPI:** O diretório \`data/exports/\` será exposto via URL estática, permitindo acesso nativo aos \`.mp4\` pelas tags \`<video>\` no frontend (ex: Factory / Queue previews).
2. **Garbage Collector (Cron Job Python):** Agendar uma rotina de cron (noturna) no background worker que verifica a 'idade' dos \`.mp4\`. Tudo que for mais antigo que 120 horas (5 dias) será deletado fisicamente do disco com \`os.remove()\`.
3. **Database Flag:** Os registros do DB deverão ter o flag de \`EXPIRED\` ativado assim que o Garbage Collector coletar o lixo correspondente daquele video, instruindo a UI a ocultar o player ou substituí-lo por 'VÍDEO VENCIDO'.`
};

const mutationQuery = `
  mutation IssueCreate($title: String!, $teamId: String!, $description: String!) {
    issueCreate(input: {
      title: $title,
      teamId: $teamId,
      description: $description
    }) {
      success
      issue {
        id
        title
      }
    }
  }
`;

async function createIssue() {
    console.log('Creating =>', issue.title);
    const res = await fetch('https://api.linear.app/graphql', {
        method: 'POST',
        headers: {
            'Authorization': linearKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: mutationQuery,
            variables: { title: issue.title, teamId: teamId, description: issue.description }
        })
    });
    const d = await res.json();
    if (d.errors) console.error(JSON.stringify(d.errors));
}

createIssue().then(() => console.log('GC Issue created.')).catch(console.error);
