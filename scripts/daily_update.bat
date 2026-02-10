@echo off
REM Script Windows pour mise à jour quotidienne NBA Analytics
REM À configurer dans le Planificateur de tâches Windows (Task Scheduler)
REM Exécution quotidienne à 9h00

cd /d "C:\Users\isaac\nba-analytics"

echo ========================================
echo NBA Analytics - Mise a jour quotidienne
echo Date: %date% %time%
echo ========================================

python src\ml\pipeline\full_season_pipeline.py --daily-update

if %errorlevel% neq 0 (
    echo ERREUR lors de la mise a jour
    exit /b 1
)

echo ========================================
echo Mise a jour terminee
echo ========================================
