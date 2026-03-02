const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const teamId = 'a9ce7f3a-0415-4424-907d-6d7eb6101de1';

const issue = {
    title: '🔀 Ideia: Botão "Switch" (Inverter Ordem) na Vitrine de Vídeos',
    description: `## Contexto
Durante o processo de junção (stitching) de dois clipes para formar um vídeo de >60s na Twitch, a Inteligência Artificial muitas vezes seleciona os clipes corretamente, mas a ordem lógica ou de retenção fica invertida no resultado final (ex: o Clípe 2 deveria ser o Clípe 1).

## Requisito (Fluxo Tinder-Style)
Na interface da Vitrine ("Reservatório de Aprovação"), além dos botões:
- 🟢 Aprovar (Mandaria para a Fila de Publicação)
- 🔴 Descartar (Mandaria pro Lixo / Deleta do HD)

Precisamos de um **TERCEIRO BOTÃO**:
- 🔀 **Inverter e Aprovar** (Switch)

### O que o Botão Switch faz?
1. Ele diz para o backend: *"Eu gostei desse vídeo, mas refaça o stitch invertendo a ordem dos clipes base (Clip 2 na frente do Clip 1)."*
2. O Backend coloca na fila de processamento (Fila interna do Render) uma task rápida com o FFMpeg.
3. Assim que o Render terminar, este vídeo recriado entra automaticamente na **Fila de Publicação** (Queue).`
};

const mutationQuery = `
  mutation IssueCreate($title: String!, $teamId: String!, $description: String!) {
    issueCreate(input: {
      title: $title,
      teamId: $teamId,
      description: $description
    }) {
      success
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

createIssue().then(() => console.log('Switch Issue created.')).catch(console.error);
