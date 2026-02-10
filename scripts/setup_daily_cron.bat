@echo off
REM Configuration du cron quotidien Windows pour NBA Analytics
REM À exécuter en administrateur

echo ========================================
echo NBA Analytics - Configuration Cron Quotidien
echo ========================================
echo.
echo Cette configuration va :
echo 1. Creer une tache planifiee Windows
echo 2. Execution quotidienne a 9h00
echo 3. Mise a jour automatique 2025-26
echo.
echo Email d'alerte : isaakdjedje@gmail.com
echo.
echo Appuyez sur une touche pour continuer...
pause > nul

REM Creer la tache
echo.
echo [1/3] Creation de la tache planifiee...
schtasks /create ^
    /tn "NBA_Analytics_Daily_Update" ^
    /tr "C:\Python314\python.exe C:\Users\isaac\nba-analytics\scripts\daily_update_2025-26.py" ^
    /sc daily ^
    /st 09:00 ^
    /ru "%USERNAME%" ^
    /np ^
    /f

if %errorlevel% neq 0 (
    echo.
    echo ERREUR : Impossible de creer la tache
    echo Verifiez que vous etes en mode administrateur
    pause
    exit /b 1
)

echo.
echo [2/3] Verification de la tache...
schtasks /query /tn "NBA_Analytics_Daily_Update" /fo LIST

echo.
echo [3/3] Test de la tache...
echo La tache sera executee pour la premiere fois demain a 9h00
echo Pour tester maintenant, appuyez sur O
echo.
set /p test="Voulez-vous tester maintenant ? (O/N) : "

if /i "%test%"=="O" (
    echo.
    echo Execution du test...
    schtasks /run /tn "NBA_Analytics_Daily_Update"
    echo.
    echo Test lance ! Verifiez les logs dans : logs/daily_updates.log
)

echo.
echo ========================================
echo CONFIGURATION TERMINEE
echo ========================================
echo.
echo Resume :
echo - Tache : NBA_Analytics_Daily_Update
echo - Execution : Tous les jours a 9h00
echo - Commande : scripts/daily_update_2025-26.py
echo - Logs : logs/daily_updates.log
echo.
echo Commandes utiles :
echo - Modifier : taskschd.msc
echo - Supprimer : schtasks /delete /tn "NBA_Analytics_Daily_Update" /f
echo - Desactiver : schtasks /change /tn "NBA_Analytics_Daily_Update" /disable
echo.
pause
