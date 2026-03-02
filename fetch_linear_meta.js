const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const teamId = 'a9ce7f3a-0415-4424-907d-6d7eb6101de1';

async function queryLinear(query) {
    const res = await fetch('https://api.linear.app/graphql', {
        method: 'POST',
        headers: {
            'Authorization': linearKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    return res.json();
}

async function start() {
    const data = await queryLinear(`
    query {
      projects {
        nodes {
          id
          name
        }
      }
      issueLabels {
        nodes {
          id
          name
        }
      }
      issues(filter: { team: { id: { eq: "${teamId}" } } }) {
        nodes {
          id
          title
          identifier
        }
      }
    }
  `);

    fs.writeFileSync('D:/APPS - ANTIGRAVITY/Synapse/linear_meta.json', JSON.stringify(data, null, 2));
    console.log('Saved to linear_meta.json');
}

start().catch(console.error);
