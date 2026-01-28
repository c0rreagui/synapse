$backendPath = "c:\APPS - ANTIGRAVITY\Synapse\backend"
$frontendPath = "c:\APPS - ANTIGRAVITY\Synapse\frontend"

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host '🚀 Starting Backend...'; python -m uvicorn app.main:app --reload --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '🎨 Starting Frontend...'; npm run dev"

# Start Factory Watcher
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host '🏭 Starting Factory Watcher...'; python core/factory_watcher.py"

Write-Host "✅ All servers launched in separate windows."
