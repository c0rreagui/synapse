const fs = require('fs');

const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

const issuesStr = fs.readFileSync('C:/Users/guico/.gemini/antigravity/brain/d7c48aa6-72db-4178-b93e-485c55d69282/linear_issues.json', 'utf8').replace(/^\uFEFF/, '');
const issuesData = JSON.parse(issuesStr);
const nodes = issuesData.data.issues.nodes;

const mutationQuery = `
  mutation ArchiveIssue($id: String!) {
    issueArchive(id: $id) {
      success
    }
  }
`;

async function archiveIssues() {
    for (const issue of nodes) {
        // Keep general issues
        if (issue.title.includes('Smoke Test') || issue.title.includes('Limpeza de Scripts') || issue.title.includes('Grafana')) {
            console.log('Keeping:', issue.title);
            continue;
        }

        console.log('Archiving:', issue.title);

        await fetch('https://api.linear.app/graphql', {
            method: 'POST',
            headers: {
                'Authorization': linearKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: mutationQuery,
                variables: { id: issue.id }
            })
        });
    }
}

archiveIssues().then(() => console.log('Done archiving.')).catch(console.error);
