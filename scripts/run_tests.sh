#!/bin/bash
# Script professionnel pour lancer les tests NBA Analytics dans Docker
# Usage: ./scripts/run_tests.sh [options pytest]
# Exemple: ./scripts/run_tests.sh -v -k test_merge

# Désactiver la conversion de chemins MSYS (Git Bash) pour Docker
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

set -e

echo "🧪 NBA Analytics - Lancement des tests"
echo "======================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Erreur: Docker n'est pas installé${NC}"
    exit 1
fi

# Vérifier que Docker Compose est disponible
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Erreur: Docker Compose n'est pas installé${NC}"
    exit 1
fi

# Vérifier si les conteneurs sont en cours d'exécution
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Les conteneurs ne sont pas démarrés. Démarrage...${NC}"
    docker-compose up -d spark-nba
    echo -e "${YELLOW}⏳ Attente de l'initialisation de Spark (10s)...${NC}"
    sleep 10
fi

echo -e "${GREEN}✅ Environnement Docker prêt${NC}"
echo ""

# Exécuter les tests dans Docker
echo "🚀 Exécution des tests..."
docker-compose exec -T spark-nba pytest tests/ "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les tests ont passé avec succès !${NC}"
else
    echo -e "${RED}❌ Certains tests ont échoué${NC}"
fi

exit $TEST_EXIT_CODE
