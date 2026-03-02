const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

// Project IDs
const PROJECTS = {
    INFRA: 'c3b0a910-4cdf-41e2-9ccd-6e67dc28e052',
    CENTRAL: 'e910b71e-ebf1-434b-b824-1a5137fdc45b',
    ORACLE: '40c16ece-27d4-4dfe-a1f5-86433984f56c',
    LOGS: '8bd808cb-9779-4fec-abb3-808a7dd9bad8',
    AGENDAMENTO: '2bb4e0c9-d6c3-4dd2-b894-0e2a2cb28a6a',
    FACTORY: '42235ddd-cc6c-4807-81e1-df2f47ed75e7'
};

// Label IDs
const LABELS = {
    BACKEND: '0ac38afe-5bda-457c-b96b-b489d212b13a',
    FRONTEND: '33575177-8141-4e4c-bae1-c35ba1cb5acf',
    FEATURE: '3d7e34ba-9f18-4947-92d9-769035810562',
    AIML: 'fabd3f02-fb59-4d9b-bd34-7030659ba79c',
    QUICKWIN: '1ce8450a-db55-4560-85f7-edbacd36c850',
    IMPROVEMENT: 'b6123261-851a-417a-a0ac-9a612bc41484'
};

const mapping = {
    'e20947bd-a4ed-4da5-9711-421f2231941e': { project: PROJECTS.INFRA, labels: [LABELS.BACKEND, LABELS.FEATURE] }, // SYN-83
    '73a65768-14ac-4c15-bb83-579a195f31d5': { project: PROJECTS.CENTRAL, labels: [LABELS.BACKEND, LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-82
    '60eb3c9e-2845-46e4-b0b6-50bf1027efac': { project: PROJECTS.ORACLE, labels: [LABELS.AIML, LABELS.BACKEND, LABELS.FEATURE] }, // SYN-81
    '697916aa-7263-4887-9249-7fec52b98ddc': { project: PROJECTS.LOGS, labels: [LABELS.BACKEND, LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-80
    '4acc4c06-bf87-450b-830c-74372c6b6184': { project: PROJECTS.AGENDAMENTO, labels: [LABELS.BACKEND, LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-79
    '218bc7ab-1a1f-4140-87f3-ccf6202563a5': { project: PROJECTS.FACTORY, labels: [LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-78
    '3671b6c3-9f86-449a-bfec-c9a7c6f4c40e': { project: PROJECTS.CENTRAL, labels: [LABELS.BACKEND, LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-77
    'b0a57257-e3e5-4ccd-b9ea-9d95912c367a': { project: PROJECTS.FACTORY, labels: [LABELS.FRONTEND, LABELS.IMPROVEMENT] }, // SYN-76
    'f65b443e-f6ab-4cc5-b20e-b303b52a0843': { project: PROJECTS.CENTRAL, labels: [LABELS.FRONTEND, LABELS.FEATURE] }, // SYN-75
    'b46071c1-ae49-4483-add8-1aaa51b55841': { project: PROJECTS.CENTRAL, labels: [LABELS.FRONTEND, LABELS.QUICKWIN] } // SYN-74
};

const mutationQuery = `
  mutation IssueUpdate($id: String!, $projectId: String!, $labelIds: [String!]) {
    issueUpdate(id: $id, input: {
      projectId: $projectId,
      labelIds: $labelIds
    }) {
      success
    }
  }
`;

async function updateIssues() {
    for (const [id, update] of Object.entries(mapping)) {
        console.log(`Updating issue ${id} -> Project: ${update.project}`);
        const res = await fetch('https://api.linear.app/graphql', {
            method: 'POST',
            headers: {
                'Authorization': linearKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: mutationQuery,
                variables: { id, projectId: update.project, labelIds: update.labels }
            })
        });
        const d = await res.json();
        if (d.errors) console.error(JSON.stringify(d.errors));
    }
}

updateIssues().then(() => console.log('All issues updated.')).catch(console.error);
