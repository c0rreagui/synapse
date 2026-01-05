@echo off
echo ===========================================
echo    🚀 STARTING SYNAPSE AUTO-CONTENT EMPIRE
echo ===========================================

cd /d "%~dp0"

echo [1/3] Launching Backend API (Port 8000)...
start "Synapse Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"

echo [2/3] Launching Frontend (Port 3000)...
start "Synapse Frontend" cmd /k "cd frontend && npm run dev"

echo [3/3] Launching Factory Watcher...
start "Synapse Watcher" cmd /k "cd backend && python core/factory_watcher.py"

echo.
echo ✅ All systems launching in separate windows!
echo ⏳ Please wait 10-15 seconds for servers to initialize.
echo.
echo 👉 Frontend: http://localhost:3000
echo 👉 Backend:  http://localhost:8000/docs
echo.
pause
