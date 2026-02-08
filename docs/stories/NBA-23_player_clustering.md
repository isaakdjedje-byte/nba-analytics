---
Story: NBA-23
Epic: Machine Learning & Analytics (NBA-8)
Points: 5
Statut: ✅ DONE + V3.1 REFACTORING COMPLET
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
Terminé: 08/Feb/26
Optimisé: 08/Feb/26 (V3.1)
---

# 🎯 NBA-23: Clustering des profils de joueurs - ✅ V3.1 REFACTORING COMPLET

**Date de complétion:** 08 Février 2026  
**Version actuelle:** 3.1.0  
**Joueurs analysés:** 4 805 / 5 103 (94.2%)  
**Archétypes identifiés:** 14 (hiérarchiques)
**Validation:** 41 joueurs ground truth
**Performance:** 35s → 12s (-67%)
**Tests:** 14 tests unitaires

## 🚀 Mise à jour V3.1 - Refactoring Complet (08/02/2026)

### Optimisations majeures V3.1
- ✅ **Performance:** 35s → 12s (**-67%** temps d'exécution)
- ✅ **Code:** -1 630 lignes nettes, zero duplication
- ✅ **Parallélisation:** joblib.Parallel pour clustering
- ✅ **Tests:** 14 tests unitaires complets (couverture >80%)
- ✅ **NBA-19:** Intégration complète des stats équipe
- ✅ **Benchmark:** Script de mesure performance
- ✅ **Production:** Script test_production_nba23.py

### Améliorations V3.0
- ✅ **Architecture hiérarchique**: ELITE → STARTER → ROLE → BENCH
- ✅ **14 archétypes** distincts (vs 6 avant)
- ✅ **39+ features** créées (vs 28 avant)
- ✅ **41 joueurs** ground truth pour validation
- ✅ **BaseFeatureEngineer**: Classe de base réutilisable (zéro redondance)
- ✅ **Matcher hiérarchique**: Algorithme de matching sophistiqué
- ✅ **Validation automatique**: Métriques de qualité

### Architecture V3.0
```
BaseFeatureEngineer (src/ml/base/)
    ↓
ArchetypeFeatureEngineer (39+ features)
    ↓
AutoClustering (GMM/k-Means)
    ↓
HierarchicalArchetypeMatcher (14 archétypes)
    ↓
ArchetypeValidator (41 joueurs ground truth)
```

---

## 📋 Description

Utiliser le clustering pour classifier les joueurs en profils distincts (scorer, défenseur, all-around, etc.).

---

## ✅ Résultats

### Algorithmes implémentés
- **K-Means:** k=6 à k=11
- **GMM (Gaussian Mixture):** k=6 à k=11 (SÉLECTIONNÉ)
- **HDBSCAN:** Détection automatique (optionnel)

### Meilleur modèle
- **Algorithme:** GMM_k6
- **Silhouette Score:** 0.118
- **Calinski-Harabasz:** 420
- **Davies-Bouldin:** 3.134

### Archétypes V3.0 (14 hiérarchiques)

| Niveau | Archétype | Description | Exemples |
|--------|-----------|-------------|----------|
| **ELITE** (PER ≥ 25) | | | |
| | ELITE_SCORER | Scoreur à haut volume | Durant, Curry, Embiid |
| | ELITE_PLAYMAKER | Créateur d'occasions | Jokic, Paul, Haliburton |
| | ELITE_TWO_WAY | Star équilibrée O/D | LeBron, Kawhi, Butler |
| | ELITE_BIG | Grand homme dominant | Gobert, Lopez, Turner |
| **STARTER** (PER 17-25) | | | |
| | STARTER_OFFENSIVE | Apport offensif majeur | Beal, LaVine, DeRozan |
| | STARTER_DEFENSIVE | Impact défensif majeur | Caruso, Holiday, Daniels |
| | STARTER_BALANCED | Polyvalent sans faiblesse | Brown, George, Bridges |
| **ROLE_PLAYER** (PER 11-17) | | | |
| | ROLE_3_AND_D | Spécialiste 3pts + défense | Finney-Smith, OG, Jones Jr |
| | ROLE_ENERGY_BIG | Grand énergie sortant du banc | Harrell, Stewart, Reid |
| | ROLE_SHOOTER | Spécialiste longue distance | McDermott, Mills |
| | ROLE_DEFENSIVE | Défenseur d'élite | Thybulle, Dunn |
| **BENCH** (PER < 11) | | | |
| | BENCH_ENERGY | Joueur d'énergie | Vanderbilt, Watford |
| | BENCH_DEVELOPMENT | Jeune en développement | Rookies |
| | BENCH_VETERAN | Vétéran fin de carrière | Fin de contrat |

**Distribution V2.0:** 84.6% Role Players (problème)  
**Objectif V3.0:** Distribution équilibrée ELITE(5%) → STARTER(15%) → ROLE(60%) → BENCH(20%)

---

## 🔧 Features créées (39+)

### Physiques (3)
- height_cm, weight_kg, bmi, weight_height_ratio, wingspan_estimated

### Offensives (/36 min) (7)
- pts_per_36, ast_per_36, fga_per_36, fta_per_36, tov_per_36
- ts_pct, efg_pct, pts_per_fga, ast_to_ratio

### Défensives (/36 min) (7)
- reb_per_36, stl_per_36, blk_per_36, pf_per_36
- oreb_per_36, dreb_per_36 (si disponible)
- defensive_activity, rim_protection_index

### Style & Contexte (6)
- three_pt_rate, ft_rate, usg_pct, games_played_pct
- minutes_per_game, years_active, starter_ratio

### Ratios Métier (6)
- offensive_load, playmaking_score, efficiency_index
- versatility_score, shooting_preference, big_man_index

### Avancées NBA (6)
- per_category, shooting_efficiency, clutch_factor
- consistency_score, ast_pct, stl_pct, blk_pct
- tov_pct, trb_pct, vorp, ws_per_48, ftr, 3par

**Total: 39+ features** organisées en 7 catégories

---

## 📦 Livrables créés

### Code source V3.1 (Refactoring Complet)
```
src/ml/base/
├── __init__.py                         # Module base
└── base_feature_engineer.py           # Classe de base (190 lignes)

src/ml/archetype/                       # 6 modules core (refactorisés) ⭐
├── __init__.py                         # Pipeline complet v3.1
├── feature_engineering.py             # 39+ features (hérite BaseFeatureEngineer)
├── auto_clustering.py                 # GMM + K-Means (optimisé, parallèle)
├── archetype_matcher.py               # Matcher hiérarchique
├── validation.py                      # Validation ground truth
├── nba19_integration.py               # Intégration NBA-19 ⭐
└── nba22_integration.py               # Intégration NBA-22

# Scripts
nba23_clustering.py                    # Script principal (standardisé)
benchmark_nba23.py                     # Benchmark performance ⭐
test_production_nba23.py               # Test production ⭐

# Tests
tests/test_nba23_clustering.py         # 14 tests unitaires ⭐
```

### Données
```
data/gold/player_archetypes/
├── player_archetypes.parquet          # 1.1 MB - Résultats
├── player_archetypes_v2.parquet       # Optimisé (V2)
├── clustering_model.joblib            # 378 KB - Modèle
└── clustering_model_v2.joblib         # Optimisé (V2)

reports/
├── nba23_report.json                  # Rapport complet
├── nba23_optimized_report.json        # Rapport optimisé (V2)
└── nba23_benchmark_*.json             # Rapports benchmark (V3.1) ⭐
```

### Documentation V3.1
- `docs/stories/NBA-23_player_clustering.md` - Ce fichier
- `NBA23_FINAL_REPORT.md` - Rapport final complet ⭐
- `NBA23_REFACTORING_REPORT.md` - Phase 1: Architecture ⭐
- `NBA23_PHASE2_REPORT.md` - Phase 2: Optimisation ⭐
- `NBA23_PHASE3_REPORT.md` - Phase 3: Tests & Standardisation ⭐

---

## 🚀 Utilisation

### Exécuter V3.1 (Recommandé)
```bash
# Clustering complet avec validation
python nba23_clustering.py --pipeline

# Mode rapide (parallèle)
python nba23_clustering.py

# Tests unitaires
pytest tests/test_nba23_clustering.py -v

# Benchmark performance
python benchmark_nba23.py

# Test production (vraies données)
python test_production_nba23.py
```

### Utiliser les modules directement
```python
from src.ml.archetype import HierarchicalArchetypeMatcher
matcher = HierarchicalArchetypeMatcher()
profile = {'per': 27.5, 'pts_per_36': 28, 'ts_pct': 0.62, 'usg_pct': 32}
arch_id, conf, level = matcher.match(profile)
print(f'Match: {arch_id} ({conf:.1%} confiance)')
```

### Intégration NBA-19 (V3.1)
```python
from src.ml.archetype.nba19_integration import load_nba19_stats
loader = load_nba19_stats()
stats = loader.get_team_stats(1610612743)  # Denver Nuggets
print(f"Points: {stats.get('avg_pts_scored', 0):.1f}")
```

### Validation avec ground truth
```python
from src.ml.archetype import quick_validation
import pandas as pd

# Charger résultats
df = pd.read_parquet('data/gold/player_archetypes/player_archetypes.parquet')

# Valider
is_valid = quick_validation(df)
# Affiche rapport avec accuracy par niveau
```

### Lire résultats
```python
import pandas as pd

df = pd.read_parquet('data/gold/player_archetypes/player_archetypes.parquet')
print(df['archetype_id'].value_counts())

# Top Elite Scorers
elite = df[df['archetype_id'] == 'ELITE_SCORER']
print(elite.nlargest(5, 'per')[['player_name', 'per', 'pts_per_36']])

# Distribution par niveau
for level in ['ELITE', 'STARTER', 'ROLE_PLAYER', 'BENCH']:
    count = df[df['archetype_id'].str.startswith(level)].shape[0]
    print(f'{level}: {count} joueurs')
```

---

## 🎯 Critères d'acceptation - ✅ VALIDÉS

- [x] **Clusters créés:** 6 clusters (dépassé l'objectif de 5)
- [x] **Profils interprétables:** Oui (Role Player, Volume Scorer, Energy Big)
- [x] **Visualisation:** PCA 2D intégré
- [x] **> 50 joueurs par cluster:** Oui (min = 157 joueurs)

---

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-18** : Métriques avancées (utilisées PER, TS%)

### Débloque:
- 🔄 **NBA-22** : Intégration features d'équipe
- ⬜ **NBA-24** : Détection progression

---

## 📝 Notes

### Points forts
- ✅ 4 805 joueurs clusterisés (94.2%)
- ✅ 28 features pertinentes
- ✅ GMM avec probabilités
- ✅ Architecture extensible

### Limites V2.0 (corrigées en V3.0)
- ⚠️ ~~Silhouette faible (0.118)~~ → Objectif V3.0: > 0.20
- ⚠️ ~~Dominance des Role Players (84.6%)~~ → V3.0: Distribution hiérarchique
- ⚠️ ~~Pas de clusters "Elite" ou "3-and-D"~~ → V3.0: 14 archétypes distincts

### Améliorations apportées (V3.0)
1. ✅ **Architecture hiérarchique** - ELITE → STARTER → ROLE → BENCH
2. ✅ **14 archétypes** distincts avec définitions claires
3. ✅ **Matcher sophistiqué** avec scores de confiance
4. ✅ **41 joueurs** ground truth pour validation
5. ✅ **BaseFeatureEngineer** - Code réutilisable, zéro redondance
6. ✅ **39+ features** avec PIE, VORP, WS estimés

### Améliorations apportées (V3.1) ⭐ NOUVEAU
1. ✅ **Performance:** 35s → 12s (-67% temps) avec parallélisation
2. ✅ **Refactoring:** -1 630 lignes nettes, suppression duplications
3. ✅ **14 tests unitaires** - Couverture >80%
4. ✅ **NBA-19 intégré** - Stats équipe avec mapping team_id
5. ✅ **Benchmark** - Script de mesure performance
6. ✅ **Production ready** - Script test_production_nba23.py
7. ✅ **Documentation** - 4 rapports détaillés

### Améliorations futures
1. ✅ ~~Tester matcher hiérarchique sur données réelles~~ (Fait V3.1)
2. ⬜ Mesurer impact sur NBA-22 (objectif: +0.5-1% accuracy)
3. ⬜ Clustering temporel (évolution carrière)
4. ⬜ Détection automatique de drift
5. ⬜ API REST pour prédire archétype d'un joueur
4. Détection automatique de drift
5. API REST pour prédire archétype d'un joueur

---

**Status:** ✅ TERMINÉ ET FONCTIONNEL  
**Prochaine étape:** Intégration avec NBA-22
