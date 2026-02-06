@echo off
chcp 65001 >nul
REM Script professionnel pour lancer les tests NBA Analytics dans Docker
REM Usage: scripts\run_tests.bat [options pytest]
REM Exemple: scripts\run_tests.bat -v -k test_merge

echo 🧪 NBA Analytics - Lancement des tests
echo ======================================
echo.

REM Vérifier que Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur: Docker n'est pas installé
    exit /b 1
)

REM Vérifier que Docker Compose est disponible
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur: Docker Compose n'est pas installé
    exit /b 1
)

REM Vérifier si les conteneurs sont en cours d'exécution
docker-compose ps | findstr "Up" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Les conteneurs ne sont pas démarrés. Démarrage...
    docker-compose up -d spark-nba
    echo ⏳ Attente de l'initialisation de Spark (10s)...
    timeout /t 10 /nobreak >nul
)

echo ✅ Environnement Docker prêt
echo.

REM Exécuter les tests dans Docker
echo 🚀 Exécution des tests...
docker-compose exec -T spark-nba pytest tests/ %*

set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
if %TEST_EXIT_CODE% == 0 (
    echo ✅ Tous les tests ont passé avec succès !
) else (
    echo ❌ Certains tests ont échoué
)

exit /b %TEST_EXIT_CODE%
