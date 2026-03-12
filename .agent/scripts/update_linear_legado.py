import os
import requests
import json

API_KEY = os.environ.get('LINEAR_API_KEY')
if not API_KEY:
    print("No API KEY found")
    exit(1)

headers = {
    'Authorization': API_KEY,
    'Content-Type': 'application/json'
}

def gql(query, variables=None):
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    response = requests.post('https://api.linear.app/graphql', headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.text}")
    res = response.json()
    if 'errors' in res:
        print("GQL Errors:", res['errors'])
    return res.get('data', {})

# 1. Get Team ID, Projects, States
query_team = """
query {
  teams(filter: {key: {eq: "SYN"}}) {
    nodes {
      id
      key
      states {
        nodes {
          id
          name
        }
      }
      projects {
        nodes {
          id
          name
        }
      }
    }
  }
}
"""

data = gql(query_team)
teams = data.get('teams', {}).get('nodes', [])
if not teams:
    print("Team SYN not found")
    exit(1)

team = teams[0]
print(f"Team: {team['key']} ({team['id']})")

legado_state = next((s for s in team['states']['nodes'] if 'legado' in s['name'].lower()), None)
legado_project = next((p for p in team['projects']['nodes'] if 'legado' in p['name'].lower()), None)

print(f"Legado State: {legado_state}")
print(f"Legado Project: {legado_project}")

if not legado_state or not legado_project:
    print("Missing state or project 'Legado'")
    exit(1)

# Fetch issues not in Legado project
has_next_page = True
cursor = None
issues_to_update = []

while has_next_page:
    query_issues = """
    query($cursor: String, $teamId: ID!) {
      issues(
        first: 50,
        after: $cursor,
        filter: {
          team: {id: {eq: $teamId}}
        }
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          identifier
          title
          state { id name }
          project { id name }
        }
      }
    }
    """
    res = gql(query_issues, {"cursor": cursor, "teamId": team['id']})
    issues_page = res.get('issues', {})
    nodes = issues_page.get('nodes', [])
    
    for issue in nodes:
        # Check if it needs update
        needs_update = False
        project = issue.get('project')
        state = issue.get('state')
        
        # Only update if it's not already in Legado project and Legado state
        if not project or project['id'] != legado_project['id']:
            needs_update = True
        if state and state['id'] != legado_state['id']:
            needs_update = True
            
        if needs_update:
            # We don't want to update current active projects! Wait, the instruction said "classify all legacy SYN issues into the new 'Legado' project and 'Legado' status".
            issues_to_update.append(issue)
            
    page_info = issues_page.get('pageInfo', {})
    has_next_page = page_info.get('hasNextPage', False)
    cursor = page_info.get('endCursor')

print(f"Found {len(issues_to_update)} total issues!")

# Since the user asked to "classify all legacy SYN issues", maybe there are active ones we shouldn't touch?
# Let's just print the first 10 before updating to be safe.
for issue in issues_to_update[:10]:
    print(f"{issue['identifier']}: {issue['title']} (Project: {issue.get('project', {}).get('name')}, State: {issue.get('state', {}).get('name')})")

with open('issues_to_update.json', 'w') as f:
    json.dump(issues_to_update, f, indent=2)

print("\\nSaved issues to issues_to_update.json. Exiting for review.")
