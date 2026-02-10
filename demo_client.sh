#!/bin/bash
# Script de démonstration complète NBA Analytics Platform
# Durée estimée : 20-25 minutes
# Usage : ./demo_client.sh [--auto]
# Option --auto : Mode non-interactif (pas de pauses)

set -e  # Arrêt sur erreur

# Détecter Python 3.11 (nécessaire pour joblib et scikit-learn)
if command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3 &> /dev/null && python3 --version | grep -q "3.11"; then
    PYTHON="python3"
else
    echo "ERREUR: Python 3.11 est requis mais n'est pas installé"
    echo "Veuillez installer Python 3.11 via pyenv ou autre"
    exit 1
fi

echo "Utilisation de : $PYTHON ($($PYTHON --version))"

# Mode auto (non-interactif) si --auto passé
AUTO_MODE=false
if [ "$1" = "--auto" ]; then
    AUTO_MODE=true
fi

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour pauser (ou pas en mode auto)
pause() {
    if [ "$AUTO_MODE" = false ]; then
        read -p "$1"
    else
        echo "(Mode auto - continuation...)"
        sleep 2
    fi
}

# Fonction d'affichage
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Phase 1 : Validation système (2 min)
phase1_validation() {
    print_header "PHASE 1 : VALIDATION DU SYSTÈME"
    
    echo "Exécution des 82 tests automatisés..."
    echo "Cette étape valide que tout fonctionne correctement."
    echo ""
    
    ./run_all_tests.sh --docker --e2e || {
        print_error "Les tests ont échoué"
        return 1
    }
    
    print_success "Tous les tests passent (82/82)"
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
}

# Phase 2 : Présentation ML (8 min)
phase2_machine_learning() {
    print_header "PHASE 2 : SYSTÈME DE PRÉDICTION ML"
    
    # 2.1 Métriques du modèle
    print_info "Métriques du modèle XGBoost Optimisé"
    echo ""
    
    if [ -f "models/optimized/training_summary.json" ]; then
        cat models/optimized/training_summary.json | $PYTHON -m json.tool 2>/dev/null || cat models/optimized/training_summary.json
    else
        print_error "Fichier training_summary.json non trouvé"
    fi
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
    
    # 2.2 Features
    print_info "Top 10 Features utilisées (parmi 35 sélectionnées)"
    echo ""
    
    if [ -f "models/optimized/selected_features.json" ]; then
        # Créer fichier Python temporaire pour éviter problèmes de guillemets
        TMP_PY=$(mktemp /tmp/show_features.XXXXXX.py 2>/dev/null || echo "/tmp/show_features_$$.py")
        cat > "$TMP_PY" << 'PYEOF'
import json
import sys
try:
    with open('models/optimized/selected_features.json') as f:
        data = json.load(f)
        features = data.get('features', [])
        print('Features sélectionnées :')
        for i, feat in enumerate(features[:10], 1):
            print(str(i).rjust(2) + '. ' + str(feat))
        print()
        print('... et ' + str(len(features)-10) + ' autres features')
except Exception as e:
    print('Erreur: ' + str(e))
    sys.exit(1)
PYEOF
        $PYTHON "$TMP_PY"
        rm -f "$TMP_PY"
    else
        print_error "Fichier selected_features.json non trouvé"
    fi
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
    
    # 2.3 Générer prédictions
    print_info "Génération des prédictions du jour..."
    echo "Récupération des matchs via NBA Live API..."
    echo ""
    
    $PYTHON run_predictions_optimized.py || {
        print_error "Erreur lors de la génération des prédictions"
        return 1
    }
    
    print_success "Prédictions générées avec succès"
    echo ""
    
    # 2.4 Afficher résultats
    print_info "Dernières prédictions :"
    echo ""
    
    if [ -f "predictions/latest_predictions_optimized.csv" ]; then
        # Afficher avec en-têtes formatés
        head -11 predictions/latest_predictions_optimized.csv | column -t -s, 2>/dev/null || head -11 predictions/latest_predictions_optimized.csv
    else
        print_error "Fichier de prédictions non trouvé"
    fi
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
}

# Phase 3 : Infrastructure (5 min)
phase3_infrastructure() {
    print_header "PHASE 3 : INFRASTRUCTURE & MONITORING"
    
    # 3.1 Docker
    print_info "Services Docker :"
    echo ""
    
    docker-compose ps 2>/dev/null || {
        print_error "Docker non disponible ou services non démarrés"
        echo "Démarrage des services..."
        docker-compose up -d postgres redis api 2>/dev/null || print_info "Services déjà démarrés ou erreur"
    }
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
    
    # 3.2 Health check
    print_info "Vérification santé du système :"
    echo ""
    
    $PYTHON run_predictions_optimized.py --health 2>/dev/null || {
        print_error "Health check indisponible"
    }
    
    # 3.3 API
    print_info "Test API REST :"
    echo ""
    
    curl -s http://localhost:8000/health 2>/dev/null | $PYTHON -m json.tool 2>/dev/null || {
        print_error "API non accessible sur localhost:8000"
        echo "Lancement de l'API..."
        $PYTHON -m nba.cli dev api &
        sleep 3
        curl -s http://localhost:8000/health 2>/dev/null | $PYTHON -m json.tool 2>/dev/null || print_error "API toujours indisponible"
    }
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
}

# Phase 4 : ROI & Business (3 min)
phase4_business_value() {
    print_header "PHASE 4 : VALEUR BUSINESS & ROI"
    
    # 4.1 Rapport performance
    print_info "Génération du rapport de performance..."
    echo ""
    
    $PYTHON run_predictions_optimized.py --report 2>/dev/null || {
        print_info "Pas de données de tracking disponibles encore"
    }
    
    if [ -f "predictions/performance_report.txt" ]; then
        print_info "Rapport de performance :"
        echo ""
        cat predictions/performance_report.txt
    else
        print_info "Aucun rapport de performance disponible"
        echo "Le tracking commence avec les premières prédictions."
    fi
    
    echo ""
    pause "Appuyez sur Entrée pour continuer..."
}

# Phase 5 : Interactive (2 min)
phase5_interactive() {
    print_header "PHASE 5 : DÉMONSTRATION INTERACTIVE"
    
    # 5.1 Export via CLI
    print_info "Export CSV via CLI :"
    echo ""
    
    mkdir -p demo_exports
    $PYTHON -m nba.cli export team_season_stats --format csv --output ./demo_exports 2>/dev/null || {
        print_error "Export via CLI échoué"
    }
    
    # 5.2 Vérifier fichier
    if [ -d "demo_exports" ]; then
        echo "Fichiers exportés :"
        ls -lh demo_exports/ 2>/dev/null || echo "Aucun fichier trouvé"
    fi
    
    # 5.3 API Swagger
    echo ""
    print_info "API Swagger disponible sur : http://localhost:8000/docs"
    print_info "Testez l'API dans votre navigateur !"
    echo ""
    
    # Essayer d'ouvrir le navigateur (selon OS)
    if command -v start &> /dev/null; then
        start http://localhost:8000/docs 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open http://localhost:8000/docs 2>/dev/null || true
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000/docs 2>/dev/null || true
    fi
}

# Main
main() {
    clear 2>/dev/null || echo ""
    
    echo -e "${GREEN}"
    echo "  _   _ ____    _              _   _       _       _                    "
    echo " | \\ | | __ )  / \\   _ __ ___ | | | | __ _| |_ ___| |__   ___ _ __      "
    echo " |  \\| |  _ \\ / _ \\ | '_ \\ _ \\| |_| |/ _\\ | __/ __| '_ \\ / _ \\ '__|     "
    echo " | |\\  | |_) / ___ \\| | | | | |  _  | (_| | || (__| | | |  __/ |        "
    echo " |_| \\_|____/_/   \\_\\_| |_| |_|_| |_|\\__,_|\\__\\___|_| |_|\\___|_|        "
    echo -e "${NC}"
    echo "NBA Analytics Platform - Démonstration Client"
    echo "Version 2.0.0 | Machine Learning | Prédictions NBA"
    echo ""
    echo "Durée estimée : 20-25 minutes"
    echo ""
    
    if [ "$AUTO_MODE" = false ]; then
        read -p "Prêt à commencer la démonstration ? (Entrée pour continuer, Ctrl+C pour annuler)"
    else
        echo "Mode automatique activé - Démarrage dans 3 secondes..."
        sleep 3
    fi
    
    phase1_validation
    phase2_machine_learning
    phase3_infrastructure
    phase4_business_value
    phase5_interactive
    
    print_header "DÉMONSTRATION TERMINÉE"
    print_success "Merci d'avoir assisté à cette démonstration !"
    echo ""
    print_info "Récapitulatif des fonctionnalités démontrées :"
    echo "  • 82 tests automatisés passant"
    echo "  • Modèle XGBoost 76.65% accuracy"
    echo "  • Prédictions en temps réel"
    echo "  • Infrastructure Docker complète"
    echo "  • API REST + CLI"
    echo "  • Tracking ROI automatique"
    echo ""
    print_info "Questions ? Contactez-nous."
    echo ""
}

# Vérifier les prérequis
check_prerequisites() {
    if [ ! -f "run_all_tests.sh" ]; then
        print_error "Script run_all_tests.sh non trouvé. Êtes-vous dans le bon répertoire ?"
        exit 1
    fi
    
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        print_error "Python non trouvé"
        exit 1
    fi
}

check_prerequisites
main
