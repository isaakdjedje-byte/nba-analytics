# Système de Backtest Hybride - NBA Analytics

**Date** : 09/02/2026  
**Version** : 1.0  
**Status** : Production Ready

---

## 🎯 Vue d'Ensemble

Système de backtest avancé permettant de valider les performances du modèle de prédiction NBA sur des saisons passées avec comparaison aux résultats réels.

### Philosophie

**"Valider avant de prédire"** - Tester le modèle sur des données historiques réelles pour :
- Mesurer la fiabilité des prédictions
- Identifier les périodes et équipes les plus prévisibles
- Optimiser la stratégie de pari (focus High Confidence ≥70%)
- Détecter la dérive des performances

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCES DE DONNÉES                                         │
├─────────────────────────────────────────────────────────────┤
│  2024-25 (Complète)          2025-26 (Via API)              │
│  ├── features_v3.parquet     ├── NBA API (LeagueGameFinder) │
│  │   (1,309 matchs)          │   (783 matchs)               │
│  └── Données complètes       └── Temps réel                 │
└────────────────────┬─────────────────────┬──────────────────┘
                     │                     │
┌────────────────────▼─────────────────────▼──────────────────┐
│  PIPELINE DE BACKTEST                                       │
├─────────────────────────────────────────────────────────────┤
│  1. Chargement modèle (XGBoost V3)                          │
│  2. Prédictions avec calibration                            │
│  3. Comparaison avec résultats réels                        │
│  4. Calcul métriques (Accuracy, Precision, Recall, F1, AUC) │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  SORTIES                                                    │
├─────────────────────────────────────────────────────────────┤
│  • Rapport HTML (5 graphiques SVG)                          │
│  • Données JSON (brutes)                                    │
│  • CSV détaillés (match par match)                          │
│  • Logs d'exécution                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Résultats

### Saison 2024-25 (Référence)

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Accuracy** | **77.77%** | ✅ Excellent |
| **Precision** | 78.73% | ✅ Bon |
| **Recall** | 81.26% | ✅ Très bon |
| **F1-Score** | 79.97% | ✅ Très bon |
| **AUC** | 0.8533 | ✅ Excellent |
| **Matchs analysés** | 1,309 | ✅ Complet |

**Performance par niveau de confiance :**
- High (≥70%) : **~85% accuracy** ⭐
- Medium (60-70%) : ~65% accuracy
- Low (<60%) : ~50% accuracy

### Saison 2025-26 (En cours via API)

| Métrique | Valeur | Note |
|----------|--------|------|
| **Accuracy** | **54.79%** | ⚠️ Bas (features approximatives) |
| **Méthode** | LeagueGameFinder | ✅ API NBA officielle |
| **Matchs** | 783 | ✅ Récupérés automatiquement |
| **Inscription** | Non requise | ✅ Gratuit |

**Explication de la différence :**
- Features V3 indisponibles pour 2025-26
- Utilisation de features proxy (moyennes 2024-25)
- Changements de roster/dynamique entre saisons
- Données partielles (saison en cours)

---

## 🛠️ Composants Techniques

### 1. Récupération API (`external_api_nba.py`)

**Méthodes tentées (ordre) :**

1. **LeagueGameFinder** (dates)
   - Endpoint : `stats.nba.com/stats/leaguegamefinder`
   - Plage : 21/10/2025 → 08/02/2026
   - Résultat : 783 matchs avec scores
   - **Méthode retenue** ✅

2. **Scoreboard** (matchs récents)
   - Endpoint : `nba_api.live.nba.endpoints.scoreboard`
   - Matchs du jour uniquement
   - Fallback si méthode 1 échoue

3. **BoxScore individuel**
   - Par game_id
   - Lent mais précis
   - Dernier recours

4. **Fallback local**
   - Calendrier sans résultats
   - Permet les prédictions futures

**Avantages :**
- ✅ Pas d'inscription requise
- ✅ API officielle NBA (fiable)
- ✅ Système de backup robuste
- ✅ Gestion des rate limits

### 2. Pipeline de Backtest (`backtest_hybrid_master.py`)

**Architecture :**
```python
class HybridBacktester:
    def run_phase_complete():
        # 1. Backtest 2024-25 (features complètes)
        results_2024_25 = backtest_2024_25()
        
        # 2. Backtest 2025-26 (via API)
        results_2025_26 = backtest_2025_26_api()
        
        # 3. Prédictions futures
        predictions_future = predict_upcoming()
        
        # 4. Sauvegarde
        save_all_results()
```

**Temps d'exécution :**
- 2024-25 : ~2 minutes (1,309 matchs)
- 2025-26 : ~3 minutes (783 matchs + API)
- Total : ~5-7 minutes

### 3. Génération de Rapports (`generate_combined_report.py`)

**Graphiques générés :**

1. **01_accuracy_2024-25_trend.svg**
   - Évolution de l'accuracy cumulée
   - Ligne de référence à 50%
   - Ligne finale (77.77%)

2. **02_metrics_comparison.svg**
   - Comparaison barres 2024-25 vs 2025-26
   - Accuracy, Precision, Recall, F1

3. **03_confidence_distribution.svg**
   - Histogramme des confiances
   - Répartition High/Medium/Low

4. **04_monthly_performance.svg**
   - Performance par mois (2024-25)
   - Nombre de matchs par mois

5. **05_season_comparison.svg**
   - Comparaison visuelle globale
   - Matchs + Accuracy côte à côte

**Rapport HTML :**
- Thème sombre (CSS personnalisé)
- Navigation sidebar
- Sections interactives
- Téléchargements intégrés
- Responsive design

### 4. Mise à Jour Quotidienne (`daily_update_2025-26.py`)

**Fonctionnement :**
```bash
# Exécution quotidienne à 9h00
python scripts/daily_update_2025-26.py

# Actions :
# 1. Récupère nouveaux résultats (veille)
# 2. Met à jour backtest 2025-26
# 3. Recalcule métriques
# 4. Régénère rapport HTML
# 5. Vérifie alertes (< 60% accuracy)
```

**Configuration cron Windows :**
```batch
# setup_daily_cron.bat
schtasks /create /tn "NBA_Analytics_Daily_Update" ^
    /tr "python scripts/daily_update_2025-26.py" ^
    /sc daily /st 09:00
```

**Alertes email :**
- Destinataire : isaakdjedje@gmail.com
- Déclencheurs :
  - Échec de la mise à jour
  - Performance < 60% sur 7 jours
  - Erreur API

---

## 📁 Structure des Fichiers

```
scripts/
├── backtest_hybrid_master.py      # Pipeline principal
├── generate_combined_report.py    # Générateur HTML
├── daily_update_2025-26.py        # MAJ quotidienne
└── setup_daily_cron.bat           # Config Windows

src/ingestion/
└── external_api_nba.py            # Module API sans inscription

reports/
├── index.html                     # Rapport principal
├── assets/
│   └── dark-theme.css             # Style sombre
├── figures/                       # Graphiques SVG
│   ├── 01_accuracy_2024-25_trend.svg
│   ├── 02_metrics_comparison.svg
│   ├── 03_confidence_distribution.svg
│   ├── 04_monthly_performance.svg
│   └── 05_season_comparison.svg
├── 2024-25/
│   └── backtest_data.json
└── 2025-26/
    ├── backtest_partial.json
    └── predictions_future.json

predictions/
├── backtest_2024-25_detailed.csv  # 113 KB
└── backtest_2025-26_detailed.csv  # 86 KB

logs/
├── backtest_master.log
└── daily_updates.log
```

---

## 🚀 Guide d'Utilisation

### 1. Première Exécution

```bash
# Installation dépendances (si besoin)
pip install matplotlib tqdm

# Backtest complet
python scripts/backtest_hybrid_master.py --phase complete

# Générer rapport
python scripts/generate_combined_report.py

# Ouvrir rapport
start reports/index.html  # Windows
open reports/index.html   # Mac
xdg-open reports/index.html  # Linux
```

### 2. Test Rapide (100 matchs)

```bash
# Pour valider que tout fonctionne
python scripts/backtest_hybrid_master.py --phase test
```

### 3. Configuration Cron (MAJ Quotidienne)

```bash
# Windows (en administrateur)
scripts/setup_daily_cron.bat

# Ou manuellement
schtasks /create /tn "NBA_Daily" /tr "python scripts/daily_update_2025-26.py" /sc daily /st 09:00
```

---

## 📊 Interprétation des Résultats

### Métriques Clés

**Accuracy (77.77%)**
- % de prédictions correctes
- Objectif : > 70%
- 77.77% = Excellent

**Precision (78.73%)**
- % de prédictions "Home Win" correctes
- Évite les faux positifs

**Recall (81.26%)**
- % de vrais "Home Win" détectés
- Évite les faux négatifs

**F1-Score (79.97%)**
- Moyenne harmonique Precision/Recall
- Équilibre entre les deux

**AUC (0.8533)**
- Area Under ROC Curve
- > 0.8 = Excellent modèle
- < 0.5 = Aléatoire

### Utilisation Stratégique

**Stratégie recommandée :**
```
Si Confiance >= 70%:
    → PARIER (accuracy ~85%)
Si 60% <= Confiance < 70%:
    → OPTIONNEL (risque modéré)
Si Confiance < 60%:
    → SKIP (trop risqué)
```

**Insights 2024-25 :**
- Meilleurs mois : Novembre, Janvier
- Pires mois : Octobre (début saison)
- Équipes prévisibles : Celtics, Nuggets
- Équipes difficiles : Pistons, Hornets

---

## 🔧 Dépannage

### Problème : 0 matchs trouvés pour 2025-26

**Cause probable :** API temporairement indisponible

**Solution :**
```python
# Attendre 5 minutes et réessayer
# Ou utiliser méthode alternative (Scoreboard)
```

### Problème : Rate limit API

**Symptôme :** Erreur 429 (Too Many Requests)

**Solution :**
- Déjà géré : délai 1.5s entre requêtes
- Attendre 1 heure si persistant

### Problème : Features manquantes

**Pour 2025-26 :**
- Normal : pas de features V3 disponibles
- Utilise moyennes 2024-25 comme proxy
- Résultats moins fiables (attendu)

---

## 📈 Évolutions Futures

**Version 2.0 (prévue) :**
- [ ] Ajouter saison 2023-24
- [ ] Comparaison 3 saisons
- [ ] Prédictions playoffs
- [ ] Dashboard interactif (Streamlit)
- [ ] Alertes Slack (optionnel)

**Optimisations :**
- [ ] Parallélisation des appels API
- [ ] Cache local des résultats
- [ ] Compression automatique des archives

---

## 📞 Support

**Email d'alertes :** isaakdjedje@gmail.com

**Logs :**
- `logs/backtest_master.log` - Exécutions backtest
- `logs/daily_updates.log` - MAJ quotidiennes

**Documentation :**
- Ce fichier : `docs/BACKTEST_SYSTEM.md`
- Index général : `docs/INDEX.md`
- Architecture : `docs/ARCHITECTURE_V2.md`

---

**Dernière mise à jour :** 09/02/2026  
**Version :** 1.0  
**Auteur :** NBA Analytics Team
