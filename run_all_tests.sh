#!/bin/bash
# Script de test complet NBA-29
# Usage: ./run_all_tests.sh [--docker] [--e2e]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
RUN_DOCKER=false
RUN_E2E=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --docker)
      RUN_DOCKER=true
      shift
      ;;
    --e2e)
      RUN_E2E=true
      shift
      ;;
    *)
      echo "Usage: $0 [--docker] [--e2e]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧪 NBA-29 Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Phase 1: Préparation
echo -e "${YELLOW}📦 Phase 1: Préparation...${NC}"
echo ""

echo "Vérification des dépendances..."

# Détection du bon Python (celui qui a pytest)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python non trouvé${NC}"
    exit 1
fi

# Utilise le même Python pour pip
PIP_CMD="$PYTHON_CMD -m pip"

echo "Python: $($PYTHON_CMD --version)"
echo "Pip: $($PIP_CMD --version)"

# Fonction pour vérifier et installer les dépendances
check_and_install() {
    local package=$1
    local import_name=${2:-$package}
    
    $PYTHON_CMD -c "import $import_name" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  $package non trouvé. Installation...${NC}"
        $PIP_CMD install -q $package
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $package installé${NC}"
        else
            echo -e "${RED}❌ Échec installation $package${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ $package déjà installé${NC}"
    fi
}

echo ""
echo "Vérification et installation des dépendances..."

# Liste des dépendances requises
declare -a packages=(
    "pydantic-settings"
    "typer"
    "fastapi"
    "uvicorn"
    "rich"
    "pandas"
    "pyarrow"
    "pytest"
    "httpx"
)

# Vérification et installation
for pkg in "${packages[@]}"; do
    check_and_install "$pkg" || {
        echo -e "${RED}❌ Impossible d'installer les dépendances${NC}"
        exit 1
    }
done

echo ""
echo "Installation des dépendances de test supplémentaires..."
$PIP_CMD install -q pytest-asyncio || {
    echo -e "${RED}❌ Échec installation dépendances${NC}"
    exit 1
}

echo -e "${GREEN}✅ Préparation terminée${NC}"
echo ""

# Phase 2: Tests Unitaires
echo -e "${YELLOW}📝 Phase 2: Tests Unitaires...${NC}"
echo ""

echo "Test Configuration..."
pytest tests/unit/test_config.py -v --tb=short || {
    echo -e "${RED}❌ Tests config échoués${NC}"
    exit 1
}

echo ""
echo "Test Reporting..."
pytest tests/unit/test_reporting.py -v --tb=short || {
    echo -e "${RED}❌ Tests reporting échoués${NC}"
    exit 1
}

echo ""
echo "Test Exporters Avancés..."
pytest tests/unit/test_exporters_advanced.py -v --tb=short || {
    echo -e "${RED}❌ Tests exporters avancés échoués${NC}"
    exit 1
}

echo -e "${GREEN}✅ Tests Unitaires terminés${NC}"
echo ""

# Phase 3: Tests Intégration
echo -e "${YELLOW}🔗 Phase 3: Tests Intégration...${NC}"
echo ""

echo "Test API..."
pytest tests/integration/test_api.py -v --tb=short || {
    echo -e "${RED}❌ Tests API échoués${NC}"
    exit 1
}

echo ""
echo "Test CLI..."
pytest tests/integration/test_cli.py -v --tb=short || {
    echo -e "${RED}❌ Tests CLI échoués${NC}"
    exit 1
}

echo ""
echo "Test Catalog avec données réelles..."
pytest tests/integration/test_catalog_real.py -v --tb=short || {
    echo -e "${RED}❌ Tests catalog réel échoués${NC}"
    exit 1
}

echo -e "${GREEN}✅ Tests Intégration terminés${NC}"
echo ""

# Phase 4: Tests Docker (optionnel)
if [ "$RUN_DOCKER" = true ]; then
    echo -e "${YELLOW}🐳 Phase 4: Tests Docker...${NC}"
    echo ""
    
    # Vérifie Docker
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ docker-compose non installé${NC}"
        exit 1
    fi
    
    echo "Démarrage stack Docker..."
    docker-compose up -d postgres redis api || {
        echo -e "${RED}❌ Échec démarrage Docker${NC}"
        exit 1
    }
    
    echo "Attente des services (20s)..."
    sleep 20
    
    echo ""
    echo "Test Docker infrastructure..."
    pytest tests/e2e/test_docker.py -v --tb=short || {
        echo -e "${RED}❌ Tests Docker échoués${NC}"
        docker-compose down
        exit 1
    }
    
    echo "Arrêt stack Docker..."
    docker-compose down
    
    echo -e "${GREEN}✅ Tests Docker terminés${NC}"
    echo ""
fi

# Phase 5: Tests E2E (optionnel)
if [ "$RUN_E2E" = true ]; then
    echo -e "${YELLOW}🎯 Phase 5: Tests E2E...${NC}"
    echo ""
    
    echo "Test Pipeline E2E..."
    pytest tests/e2e/test_pipeline.py -v --tb=short || {
        echo -e "${RED}❌ Tests E2E échoués${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✅ Tests E2E terminés${NC}"
    echo ""
fi

# Phase 6: Démonstration
echo -e "${YELLOW}🎬 Phase 6: Démonstration...${NC}"
echo ""

if [ -f "demo_nba29.py" ]; then
    echo "Exécution script démonstration..."
    python demo_nba29.py || {
        echo -e "${YELLOW}⚠️  Démonstration a rencontré des erreurs (non critique)${NC}"
    }
else
    echo -e "${YELLOW}⚠️  Script démo non trouvé${NC}"
fi

echo ""

# Résumé
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ TOUS LES TESTS ONT RÉUSSI!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Résumé:"
echo "  ✅ Tests Unitaires: 8 + 9 + 6 = 23 tests"
echo "  ✅ Tests Intégration: 10 + 8 + 6 = 24 tests"

if [ "$RUN_DOCKER" = true ]; then
    echo "  ✅ Tests Docker: 6 tests"
fi

if [ "$RUN_E2E" = true ]; then
    echo "  ✅ Tests E2E: 5 tests"
fi

echo ""
echo "Commandes utiles:"
echo "  ./run_all_tests.sh              # Tests de base"
echo "  ./run_all_tests.sh --docker     # + Tests Docker"
echo "  ./run_all_tests.sh --docker --e2e  # Complet"
echo ""
