<#
.SYNOPSIS
    Synapse Deploy Script - Transfers project files to production VPS.

.DESCRIPTION
    Uses SCP to copy essential project files from Windows host to
    the production VPS at /opt/synapse. Excludes all dev artifacts,
    media, database volumes, node_modules, and caches.

.NOTES
    Prerequisites:
    - OpenSSH client installed (built into Windows 10/11)
    - SSH key configured for root@46.225.62.76 (or you will be prompted for password)

.USAGE
    .\deploy.ps1
    .\deploy.ps1 -DryRun    # Preview what will be synced
#>

param(
    [switch]$DryRun
)

# =============================================
# CONFIG
# =============================================
$VPS_HOST = "46.225.62.76"
$VPS_USER = "root"
$VPS_PATH = "/opt/synapse"
$LOCAL_PATH = "d:\APPS - ANTIGRAVITY\Synapse"

# =============================================
# EXCLUDE PATTERNS (for robocopy staging)
# =============================================
$EXCLUDE_DIRS = @(
    ".git"
    ".venv"
    ".next"
    ".pytest_cache"
    ".vscode"
    ".idea"
    "node_modules"
    "__pycache__"
    "ms-playwright"
    "MONITOR"
    "auto-content-empire"
    "tools"
    # Data volumes (NEVER transfer)
    "postgres"
    "redis"
    "minio"
    # Media processing dirs
    "inputs"
    "processing"
    "done"
    "errors"
    "media"
    # Test artifacts
    "test_videos"
    "screenshots"
    "test-results"
    "playwright-report"
    "storybook-static"
)

$EXCLUDE_FILES = @(
    "*.mp4"
    "*.mov"
    "*.avi"
    "*.mkv"
    "*.webm"
    "*.wav"
    "*.mp3"
    "*.log"
    "*.png"
    "*.jpg"
    "*.jpeg"
    "*.db"
    "*.sqlite"
    "*.sqlite3"
    "*.bat"
    "*.pyc"
    "*.pyo"
    ".env"
    ".env.local"
    "synapse.db*"
    "debug_*.py"
    "check_*.py"
    "inspect_*.py"
    "verify_*.py"
    "browser_test_log.txt"
    "header_comparison.json"
    "import_errors.txt"
    "validator_debug.log"
    "debug_upload_page.html"
    "TRELLO*.json"
    "sonar-project.properties"
    "pyrightconfig.json"
    "heal_*.png"
    "test_screenshot.jpg"
    "debug_session_test.png"
)

# =============================================
# FUNCTIONS
# =============================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n>>> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "    OK: $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "    WARN: $Message" -ForegroundColor Yellow
}

# =============================================
# MAIN
# =============================================

Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  SYNAPSE DEPLOY v1.0 - Production Transfer" -ForegroundColor Magenta
Write-Host "  Target: ${VPS_USER}@${VPS_HOST}:${VPS_PATH}" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# Step 1: Create staging directory with filtered files
$STAGING = "$env:TEMP\synapse_deploy_staging"
Write-Step "Preparando staging em $STAGING"

if (Test-Path $STAGING) {
    Remove-Item -Recurse -Force $STAGING
}

$robocopyExcludeDirs = $EXCLUDE_DIRS | ForEach-Object { "/XD", $_ }
$robocopyExcludeFiles = $EXCLUDE_FILES | ForEach-Object { "/XF", $_ }

if ($DryRun) {
    Write-Warn "DRY RUN: Simulando copia para staging..."
    $robocopyArgs = @($LOCAL_PATH, $STAGING, "/E", "/L") + $robocopyExcludeDirs + $robocopyExcludeFiles
} else {
    $robocopyArgs = @($LOCAL_PATH, $STAGING, "/E", "/NFL", "/NDL", "/NJH", "/NJS") + $robocopyExcludeDirs + $robocopyExcludeFiles
}

& robocopy @robocopyArgs | Out-Null
Write-Ok "Staging preparado"

if ($DryRun) {
    Write-Warn "DRY RUN concluido. Nenhum arquivo transferido."
    exit 0
}

# Step 2: Create remote directory
Write-Step "Criando diretorio remoto ${VPS_PATH}"
ssh "${VPS_USER}@${VPS_HOST}" "mkdir -p ${VPS_PATH}"
Write-Ok "Diretorio remoto criado"

# Step 3: Transfer files via SCP
Write-Step "Transferindo arquivos via SCP..."
Write-Host "    Isso pode levar alguns minutos dependendo da conexao..." -ForegroundColor DarkGray
scp -r "${STAGING}\*" "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/"

if ($LASTEXITCODE -eq 0) {
    Write-Ok "Transferencia concluida com sucesso!"
} else {
    Write-Host "    ERRO: Transferencia falhou (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

# Step 4: Transfer .env.production as .env
Write-Step "Transferindo .env.production como .env"
scp "${LOCAL_PATH}\.env.production" "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/.env"
Write-Ok ".env transferido"

# Step 5: Cleanup staging
Write-Step "Limpando staging"
Remove-Item -Recurse -Force $STAGING
Write-Ok "Staging removido"

# Step 6: Set permissions on VPS
Write-Step "Ajustando permissoes no servidor"
ssh "${VPS_USER}@${VPS_HOST}" "chmod -R 755 ${VPS_PATH} && chown -R root:root ${VPS_PATH}"
Write-Ok "Permissoes ajustadas"

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  DEPLOY CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos (executar via SSH na VPS):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. ssh root@${VPS_HOST}" -ForegroundColor White
Write-Host "  2. cd ${VPS_PATH}" -ForegroundColor White
Write-Host "  3. nano .env  # Ajustar senhas reais" -ForegroundColor White
Write-Host "  4. docker compose -f docker-compose.production.yml up -d --build" -ForegroundColor White
Write-Host "  5. docker exec -i synapse-db psql -U synapse -d synapse_db < backend/scripts/migrations/add_antidetect_columns.sql" -ForegroundColor White
Write-Host ""
