const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const teamId = 'a9ce7f3a-0415-4424-907d-6d7eb6101de1';

const newIssues = [
    {
        title: '🚀 Frontend Integration: Formulário de Inserção de Target Real',
        description: 'A página Clipper clássica conversava direto com a API (`POST /api/v1/clipper/targets`), enquanto a interface nova ainda não faz o envio dinâmico do formulário no botão INICIAR. A interface precisa capturar a URL da Twitch inserida pelo usuário e mandar para o backend.'
    },
    {
        title: '🚀 Frontend Integration: Visualização Dinâmica da Lista de Alvos',
        description: 'A nova grade ALVOS DE RECONHECIMENTO ORBITAL possui mock data (Kai Cenat, Pokimane, etc). Precisa ser substituída pelo State real vindo do backend (GET `/api/v1/clipper/targets`), renderizando componentes baseados nesses dados dinamicamente.'
    },
    {
        title: '🚀 Frontend Integration: Mecânica de Auto Refresh Nativa',
        description: 'Restabelecer hooks (`useSWR` ou polling com `useEffect`) para buscar atualizações dos jobs em background, mostrando progresso no painel da Fábrica e status na lista Clipper.'
    },
    {
        title: '🌌 New Feature: Central de Comando (Dashboard Analytics)',
        description: 'O Dashboard Principal necessita de APIs para preencher os mostradores: Velocidade Orbital, KPIs de Clipes e Retenção, e tráfego em tempo real do pipeline. Desenvolver os endpoints backend para alimentar isso.'
    },
    {
        title: '🌌 New Feature: Tela da Fábrica de Vídeos Kanban',
        description: 'A fábrica antes era lista genérica. O projeto Stitch trouxe o modelo Kanban (Fila, Edição, Áudio, Concluído). O backend precisará fornecer os status detalhados e o frontend fará os agrupamentos via columns.'
    },
    {
        title: '🌌 New Feature: Scheduler PDD API (Calendário 3D)',
        description: 'A Grade Temporal necessita desenvolvimento de uma API cron em um modelo de Publicações. O frontend agora tem calendário para mostrar onde e quando vídeos serão postados.'
    },
    {
        title: '🌌 New Feature: Monitor de Telemetria Interativo (WebSockets)',
        description: 'O front-end ganhou terminal CLI. O backend FastApi precisará expor um recurso real `WebSocket` (WebSocket Endpoint) que assine eventos emitidos pelo worker/arq e flusheie logs no formato serializado.'
    },
    {
        title: '🌌 New Feature: Motor Oráculo V2',
        description: 'O input pede ideias de descoberta e tags profundas. Desenvolver um workflow integrando com Large Language Models na parte do python para devolver JSON para essa interface responder.'
    },
    {
        title: '🌌 New Feature: Cofre de Configurações Dinâmicas',
        description: 'API Keys de LLM e hardware limits rodam no `.env`. Construir CRUD para gerir essas configs via DB (settings table), persistidas, permitindo a rotação através da página de Configuração de Sistema.'
    }
];

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

async function createIssues() {
    for (const issue of newIssues) {
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
}

createIssues().then(() => console.log('All issues created.')).catch(console.error);
