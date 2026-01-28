@echo off
echo ===========================================
echo    🎨 STARTING SYNAPSE DESIGN SYSTEM
echo ===========================================

cd /d "%~dp0"

echo [1/1] Launching Storybook Container (Port 6006)...
echo.
echo NOTE: This runs in a separate Docker namespace 'synapse-design-system'.
echo You can manage it independently in Docker Desktop.
echo.

docker-compose -f docker-compose.storybook.yml -p synapse-design-system up -d

echo.
echo ✅ Storybook container started!
echo ⏳ Access at: http://localhost:6006
echo.
pause
