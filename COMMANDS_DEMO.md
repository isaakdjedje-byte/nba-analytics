# 📋 Commandes de Démonstration - NBA Analytics Platform
## Copier-coller prêt à l'emploi

---

## 🚀 DÉMARRAGE RAPIDE (30 secondes)

```bash
# Vérifier version
nba version

# Voir le catalogue
nba catalog list

# Exporter un dataset
nba export team_season_stats --format csv
```

---

## ✅ PHASE 1 : VALIDATION (2 minutes)

```bash
# Exécuter tous les tests (82 tests)
./run_all_tests.sh --docker --e2e

# Vérifier que tout passe
echo "Tests terminés avec succès !"
```

**Sortie attendue :** ✅ 82 tests passed

---

## 🧠 PHASE 2 : MACHINE LEARNING (8 minutes)

### 2.1 Métriques du Modèle
```bash
# Afficher les métriques complètes
cat models/optimized/training_summary.json | python -m json.tool

# Afficher les 10 features les plus importantes
python -c "
import json
with open('models/optimized/selected_features.json') as f:
    features = json.load(f)
    print('Top 10 features :')
    for i, f in enumerate(features[:10], 1):
        print(f'{i:2d}. {f}')
    print(f'\nTotal : {len(features)} features sélectionnées')
"
```

**Métriques clés à souligner :**
- **Accuracy : 76.65%**
- **AUC : 84.9%**
- **Features : 35** (sélectionnées parmi 85)
- **Brier Score : 0.158** (probabilités bien calibrées)

### 2.2 Générer Prédictions
```bash
# Générer prédictions du jour avec l'API NBA Live
python run_predictions_optimized.py

# Vérifier les résultats formatés
cat predictions/latest_predictions_optimized.csv | column -t -s,

# Compter les recommandations HIGH_CONFIDENCE
grep -c "HIGH_CONFIDENCE" predictions/latest_predictions_optimized.csv

# Afficher uniquement les HIGH_CONFIDENCE
grep "HIGH_CONFIDENCE" predictions/latest_predictions_optimized.csv | column -t -s,
```

### 2.3 Vérifications Système
```bash
# Vérifier santé du système
python run_predictions_optimized.py --health

# Vérifier si données ont drifté
python run_predictions_optimized.py --drift

# Voir le rapport de performance
python run_predictions_optimized.py --report
```

---

## 🐳 PHASE 3 : INFRASTRUCTURE (5 minutes)

### Docker & Services
```bash
# Vérifier l'état des services Docker
docker-compose ps

# Démarrer les services (si nécessaire)
docker-compose up -d postgres redis api

# Vérifier logs d'un service
docker-compose logs --tail=50 api
```

### API REST
```bash
# Test health endpoint
curl http://localhost:8000/health

# Lister tous les datasets via API
curl http://localhost:8000/api/v1/datasets | python -m json.tool

# Obtenir détails d'un dataset
curl http://localhost:8000/api/v1/datasets/team_season_stats | python -m json.tool

# Exporter via API
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{"dataset": "team_season_stats", "format": "csv"}'

# Scanner le catalogue via API
curl -X POST http://localhost:8000/api/v1/catalog/scan
```

### Lancer l'API en local
```bash
# Méthode 1 : Via CLI
nba dev api

# Méthode 2 : Via Python
python -m nba.api.main

# Avec rechargement auto (développement)
nba dev api --reload

# Sur port différent
nba dev api --port 8080
```

---

## 💰 PHASE 4 : ROI & BUSINESS (3 minutes)

### Tracking & Performance
```bash
# Générer rapport de performance complet
python run_predictions_optimized.py --report

# Afficher rapport
 cat predictions/performance_report.txt

# Voir l'historique complet des prédictions
cat predictions/tracking_history.csv | column -t -s,

# Nombre total de prédictions trackées
wc -l predictions/tracking_history.csv

# Dernières prédictions avec résultats
tail -10 predictions/tracking_history.csv | column -t -s,
```

### Analyse Performance
```bash
# Calculer accuracy globale
python -c "
import pandas as pd
df = pd.read_csv('predictions/tracking_history.csv')
accuracy = df['correct'].mean() * 100
print(f'Accuracy globale : {accuracy:.1f}%')
print(f'Nombre de prédictions : {len(df)}')
"

# Performance par niveau de confiance
python -c "
import pandas as pd
df = pd.read_csv('predictions/tracking_history.csv')
for conf in ['HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE']:
    subset = df[df['recommendation'] == conf]
    if len(subset) > 0:
        acc = subset['correct'].mean() * 100
        print(f'{conf}: {acc:.1f}% ({len(subset)} prédictions)')
"
```

---

## 🎬 PHASE 5 : INTERACTIVE (2 minutes)

### Export Multi-Formats
```bash
# Créer répertoire de démo
mkdir -p demo_exports

# Export CSV (Excel-friendly)
nba export team_season_stats --format csv --output demo_exports

# Export Parquet (analytics)
nba export team_season_stats --format parquet --output demo_exports

# Export JSON (API)
nba export team_season_stats --format json --output demo_exports

# Vérifier exports
ls -lh demo_exports/

# Tous les datasets d'un coup
nba export all --output demo_exports --format csv
```

### CLI - Catalogue
```bash
# Lister datasets
nba catalog list

# Scanner et mettre à jour le catalogue
nba catalog scan

# Voir détails d'un dataset
nba catalog show --dataset team_season_stats

# Export catalogue complet
nba export all --format json --output ./catalog_export
```

### Exploration Données
```bash
# Nombre de datasets gold
ls data/gold/*/*.parquet | wc -l

# Taille totale des données
du -sh data/

# Derniers fichiers modifiés
ls -lt data/gold/*/* | head -10

# Statistiques rapides
python -c "
import pandas as pd
df = pd.read_parquet('data/gold/team_season_stats/team_season_stats.parquet')
print(f'Nombre équipes : {len(df)}')
print(f'Colonnes : {len(df.columns)}')
print(f'Taille : {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB')
"
```

---

## 🎯 COMMANDES SPÉCIALES

### Mode Paper Trading
```bash
# Prédictions quotidiennes automatiques
python run_predictions_optimized.py

# Mise à jour des résultats (après les matchs)
python run_predictions_optimized.py --update

# Rapport hebdomadaire
python run_predictions_optimized.py --report

# Voir historique complet
cat predictions/tracking_history.csv
```

### Réentraînement Modèle
```bash
# Réentraîner avec nouvelles données
python src/ml/pipeline/train_optimized.py

# Vérifier nouvelles métriques
cat models/optimized/training_summary.json | python -m json.tool

# Comparer avec ancien modèle
ls -lt models/optimized/
```

### Tests Spécifiques
```bash
# Tests ML critiques
pytest tests/test_ml_pipeline_critical.py -v

# Tests E2E
pytest tests/e2e/test_pipeline.py -v

# Tests avec couverture
pytest tests/ --cov=nba --cov-report=html
```

---

## 🛠️ DÉPANNAGE

### Si les tests échouent
```bash
# Nettoyer et relancer
docker-compose down
docker-compose up -d postgres redis
./run_all_tests.sh

# Voir logs détaillés
./run_all_tests.sh --docker --e2e 2>&1 | tee test_output.log
```

### Si l'API ne répond pas
```bash
# Vérifier port utilisé
netstat -an | grep 8000  # Windows
lsof -i :8000            # Mac/Linux

# Relancer sur port différent
nba dev api --port 8001

# Vérifier processus Python
ps aux | grep python  # Mac/Linux
tasklist | findstr python  # Windows
```

### Si erreur Unicode (Windows)
```bash
# Changer page de code
chcp 65001

# Ou utiliser Windows Terminal
# Ou définir variable d'environnement
set PYTHONIOENCODING=utf-8
```

### Problèmes Docker
```bash
# Nettoyer conteneurs orphelins
docker-compose down --remove-orphans

# Reconstruire images
docker-compose up -d --build

# Vérifier espace disque
docker system df

# Nettoyer si nécessaire
docker system prune -f
```

### Reset Complet
```bash
# Supprimer données et recommencer
rm -rf data/exports/*
rm -rf predictions/*.csv
rm -rf models/optimized/*
docker-compose down
./run_all_tests.sh --docker --e2e
```

---

## 📊 STATISTIQUES RAPIDES

```bash
# Nombre total de matchs analysés
python -c "
import pandas as pd
df = pd.read_parquet('data/gold/ml_features/features_all.parquet')
print(f'Matchs analysés : {len(df):,}')
"

# Nombre de joueurs
python -c "
import pandas as pd
df = pd.read_parquet('data/gold/player_team_season/player_team_season.parquet')
print(f'Joueurs : {len(df):,}')
"

# Période couverte
python -c "
import pandas as pd
df = pd.read_parquet('data/gold/team_season_stats/team_season_stats.parquet')
print(f'Saisons : {df[\"season\"].nunique()}')
print(f'Années : {sorted(df[\"season\"].unique())}')
"

# Dernière mise à jour
stat predictions/latest_predictions_optimized.csv

# Taille du catalogue
ls -lh data/catalog.db
```

---

## 💡 ASTUCES

### Raccourcis Bash/Zsh
```bash
# Ajouter à ~/.bashrc ou ~/.zshrc
alias nba-demo='./demo_client.sh'
alias nba-test='./run_all_tests.sh --docker --e2e'
alias nba-predict='python run_predictions_optimized.py'
alias nba-report='python run_predictions_optimized.py --report'
alias nba-api='nba dev api'
```

### Script rapide
```bash
# Créer un script de démo rapide
cat > quick_demo.sh << 'EOF'
#!/bin/bash
nba version
nba catalog list | head -5
python run_predictions_optimized.py --health
python run_predictions_optimized.py 2>/dev/null || echo "Pas de matchs aujourd'hui"
EOF
chmod +x quick_demo.sh
```

### Export Automatique
```bash
# Script d'export quotidien
cat > daily_export.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
mkdir -p exports/$DATE
nba export all --format csv --output exports/$DATE
nba export all --format parquet --output exports/$DATE
echo "Exports terminés pour $DATE"
EOF
chmod +x daily_export.sh
```

---

**Dernière mise à jour :** $(date)
**Version :** 2.0.0
