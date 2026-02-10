@echo off
chcp 65001 >nul
echo ==========================================
echo   NBA ANALYTICS DASHBOARD - Démarrage
echo ==========================================
echo.

echo [1/3] Démarrage du Backend API...
start "Backend API" cmd /k "cd /d C:\Users\isaac\nba-analytics && python -m nba.api.main"
echo Backend démarré sur http://localhost:8000
echo.

timeout /t 3 /nobreak >nul

echo [2/3] Démarrage du Frontend...
start "Frontend React" cmd /k "cd /d C:\Users\isaac\nba-analytics\frontend && npm run dev -- --host"
echo Frontend démarré sur http://localhost:5173
echo.

timeout /t 5 /nobreak >nul

echo [3/3] Vérification des services...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Backend API en ligne
) else (
    echo [⚠] Backend API démarrage en cours...
)

echo.
echo ==========================================
echo   SERVICES ACTIFS :
echo   - Backend : http://localhost:8000
echo   - Frontend : http://localhost:5173
echo.
echo   Pages disponibles :
echo   - Dashboard : http://localhost:5173/
echo   - Predictions Week : http://localhost:5173/predictions
echo   - Paper Trading : http://localhost:5173/betting
echo   - Pipeline ML : http://localhost:5173/ml-pipeline
echo ==========================================
echo.
pause
