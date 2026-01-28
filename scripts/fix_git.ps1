$ErrorActionPreference = "Stop"

Write-Host "🔧 Starting Git Auto-Fix..." -ForegroundColor Cyan

# 1. Initialize if missing
if (-not (Test-Path ".git")) {
    Write-Host "📂 Initializing generic Git repository..."
    git init
}
else {
    Write-Host "📂 Git repository found."
}

# 2. Add all files
Write-Host "➕ Adding ALL files to staging (this might take a moment)..."
git add .

# 3. Commit
try {
    git commit -m "feat(migration): Ingestion to Home Migration + Scheduling Features"
    Write-Host "✅ Changes committed." -ForegroundColor Green
}
catch {
    Write-Host "ℹ️ No changes to commit or commit failed (check status)." -ForegroundColor Yellow
}

# 4. Configure Remote
$remoteUrl = "https://github.com/c0rreagui/synapse.git"
$remoteName = "synapse-git"

if (git remote | Select-String -Pattern $remoteName) {
    Write-Host "🔗 Remote '$remoteName' exists. Updating URL..."
    git remote set-url $remoteName $remoteUrl
}
else {
    Write-Host "🔗 Adding remote '$remoteName'..."
    git remote add $remoteName $remoteUrl
}

# 5. Push
Write-Host "🚀 Pushing to '$remoteName' (master)..."
try {
    git push -u $remoteName master
    Write-Host "🏆 SUCCESS: Code pushed to remote!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Push failed. You might need to 'git pull' first or check credentials." -ForegroundColor Red
    Write-Host "Error details: $_"
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
