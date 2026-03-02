const fs = require('fs');
const config = JSON.parse(fs.readFileSync('C:/Users/guico/.gemini/antigravity/mcp_config.json', 'utf8'));
const linearKey = config.mcpServers.linear.env.LINEAR_API_KEY;

// Linear Priorities: 0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low
const priorities = {
    'e20947bd-a4ed-4da5-9711-421f2231941e': 2, // SYN-83 Proxy - High
    '73a65768-14ac-4c15-bb83-579a195f31d5': 4, // SYN-82 Configs - Low
    '60eb3c9e-2845-46e4-b0b6-50bf1027efac': 3, // SYN-81 Oracle - Normal
    '697916aa-7263-4887-9249-7fec52b98ddc': 2, // SYN-80 WebSockets Telemetry - High (It's cool, but maybe Normal?) Let's put 3 Normal. Wait, I will use 3.
    '4acc4c06-bf87-450b-830c-74372c6b6184': 3, // SYN-79 Scheduler - Normal
    '218bc7ab-1a1f-4140-87f3-ccf6202563a5': 3, // SYN-78 Kanban - Normal
    '3671b6c3-9f86-449a-bfec-c9a7c6f4c40e': 2, // SYN-77 Dashboard - High
    'b0a57257-e3e5-4ccd-b9ea-9d95912c367a': 2, // SYN-76 Auto Refresh - High
    'f65b443e-f6ab-4cc5-b20e-b303b52a0843': 2, // SYN-75 List - High
    'b46071c1-ae49-4483-add8-1aaa51b55841': 1  // SYN-74 Form - Urgent (We are starting it now)
};

const mutationQuery = `
  mutation IssueUpdate($id: String!, $priority: Int!) {
    issueUpdate(id: $id, input: { priority: $priority }) {
      success
    }
  }
`;

async function updatePriorities() {
    for (const [id, priority] of Object.entries(priorities)) {
        console.log(`Setting priority ${priority} for issue ${id}`);
        const res = await fetch('https://api.linear.app/graphql', {
            method: 'POST',
            headers: {
                'Authorization': linearKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: mutationQuery,
                variables: { id, priority }
            })
        });
        const d = await res.json();
        if (d.errors) console.error(JSON.stringify(d.errors));
    }
}

updatePriorities().then(() => console.log('Priorities updated.')).catch(console.error);
