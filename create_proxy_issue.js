const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const teamId = 'a9ce7f3a-0415-4424-907d-6d7eb6101de1';

const proxyIssue = {
    title: '🛰️ Feature: Sistema de Proxies por Perfil (Prevent Shadowban)',
    description: '## Contexto\n\nCada perfil automatizado terá seu bot específico rodando com `Playwright`. Para evitar Shadowban e rastros compartilhados, cada perfil deverá obrigatoriamente realizar requisições usando um Proxy específico daquele perfil, e não o IP root do servidor original.\n\n## Requisitos\n\n1. O banco de dados (SQLite) precisa armazenar os dados de host/porta/user/senha do Proxy atrelados diretamente a cada `Profile`.\n2. O `browser.py` ou gerenciador de contextos do Playwright deve carregar o proxy via `--proxy-server` e autenticar via `proxy.username` e `proxy.password` de forma isolada por perfil.\n3. Implementação não será feita nesta task, mas a infraestrutura base e documentação devem prever isso no futuro.'
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

async function createProxyIssue() {
    console.log('Creating =>', proxyIssue.title);
    const res = await fetch('https://api.linear.app/graphql', {
        method: 'POST',
        headers: {
            'Authorization': linearKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: mutationQuery,
            variables: { title: proxyIssue.title, teamId: teamId, description: proxyIssue.description }
        })
    });
    const d = await res.json();
    if (d.errors) console.error(JSON.stringify(d.errors));
}

createProxyIssue().then(() => console.log('Proxy issue created.')).catch(console.error);
