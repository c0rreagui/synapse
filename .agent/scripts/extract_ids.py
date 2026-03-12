import json

# path to output.txt
file_path = "C:/Users/guico/.gemini/antigravity/brain/8547d533-4011-4860-b3bc-3d095d35a8d1/.system_generated/steps/101/output.txt"

legado_project_id = "4a57eaa1-3444-4f4b-9f21-3d03fcc84f63"
legado_state_id = "c7db039a-9eb3-4fdb-8ac4-68aee594bbf6"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

issues = data.get("issues", [])
ids_to_update = []

for idx, issue in enumerate(issues):
    # check state and project
    state = issue.get("status") or (issue.get("state", {}).get("name", "") if isinstance(issue.get("state"), dict) else "")
    project_id = issue.get("projectId") or (issue.get("project", {}).get("id", "") if isinstance(issue.get("project"), dict) else "")
    state_id = issue.get("stateId") # The MCP output might not give stateId directly, let me check status name.
    
    # Wait, the structure from MCP list_issues is:
    # { "id": "uuid", "identifier": "SYN-130", ... "status": "✅ Done", 
    #   "project": "...", "projectId": "...", "state": ... }
    # Legado status is "Legado"
    if issue.get("status") == "Legado" and issue.get("projectId") == legado_project_id:
        continue
    
    ids_to_update.append(issue["id"])

print("IDs to update:")
for id in ids_to_update:
    print(id)

print(f"Total: {len(ids_to_update)}")
