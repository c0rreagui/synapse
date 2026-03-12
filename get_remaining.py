import urllib.request
import json
import os

url = 'https://api.linear.app/graphql'
headers = {
    'Authorization': os.environ.get('LINEAR_API_KEY'),
    'Content-Type': 'application/json'
}

query = '''
query {
    issues(filter: { state: { name: { in: ["Backlog", "Icebox", "Canceled", "Done", "In Progress", "Todo"] } } }) {
        nodes {
            id
            identifier
            title
            project { id name }
        }
    }
}
'''
req = urllib.request.Request(url, data=json.dumps({'query': query}).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        nodes = data['data']['issues']['nodes']
        issues_to_update = []
        for n in nodes:
            # Check if project is Legado
            project = n.get('project')
            if not project or project.get('name') != 'LEGADO':
                issues_to_update.append(n)
        for iss in issues_to_update:
            print(f"{iss['id']} - {iss['identifier']}")
except Exception as e:
    print('Error:', e)
