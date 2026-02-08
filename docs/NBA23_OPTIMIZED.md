# NBA-23 OPTIMIZED: Player Archetypes Clustering

**Date:** 08 Fevrier 2026  
**Status:** ✅ OPTIMIZED ET TERMINE  
**Version:** 2.0

---

## 📊 RESULTATS DE L'OPTIMISATION

### Comparaison: Avant vs Apres

| Metric | Original (v1) | Optimized (v2) | Amelioration |
|--------|---------------|----------------|--------------|
| Joueurs | 4805 | 4805 | = |
| Features | 28 | 39 (+11) | +39% |
| Features selectionnees | 28 | 20 | -29% (bruit reduit) |
| Clusters | 6 | 6 | = |
| Silhouette Score | 0.118 | 0.152 | +29% |
| Calinski-Harabasz | 420 | 673 | +60% |
| Davies-Bouldin | 3.134 | 2.502 | -20% (meilleur) |

### Features Ajoutees (NBA-23 Advanced)

```python
# Pourcentages avances (avec approximation donnees equipe)
- ast_pct: Assist Percentage
- stl_pct: Steal Percentage
- blk_pct: Block Percentage
- tov_pct: Turnover Percentage
- trb_pct: Total Rebound Percentage

# Estimations avancees
- vorp: Value Over Replacement Player
- ws_per_48: Win Shares Per 48 Minutes

# Ratios de tirs
- ftr: Free Throw Rate
- 3par: 3-Point Attempt Rate

# Contexte
- years_active: Annees dans la ligue
- starter_ratio: Ratio matchs starter
```

### Processus d'Optimisation

```
1. Feature Engineering: 39 features
   ↓
2. Feature Selection:
   - Variance Threshold (30 features)
   - Correlation Filter (29 features)
   - SelectKBest (20 features)
   ↓
3. Clustering k=6-12:
   - K-Means
   - Gaussian Mixture (GMM) ← MEILLEUR
   ↓
4. Resultat: Silhouette 0.152
```

### Archétypes Identifiés (v2)

| Cluster | Archétype | Joueurs | % |
|---------|-----------|---------|---|
| 0 | Role Player | 1932 | 40.2% |
| 1 | Role Player | 195 | 4.1% |
| 2 | Role Player | 326 | 6.8% |
| 3 | Role Player | 651 | 13.5% |
| 4 | **Specialiste Defensif** | 142 | 3.0% |
| 5 | Role Player | 1559 | 32.4% |

**Nouveau:** Detection de "Specialiste Defensif" (cluster 4)

---

## 🚀 INTEGRATION NBA-22

### Features d'Equipe Creees

```python
# Diversite
- n_archetypes: Nombre d'archetypes differents
- archetype_entropy: Entropie de Shannon

# Presence binaire
- has_volume_scorer: 1 si equipe a un scoreur volume
- has_energy_big: 1 si equipe a un energy big
- has_role_player: 1 si equipe a des role players

# Distribution
- role_player_pct: % de role players
- volume_scorer_pct: % de volume scorers
- energy_big_pct: % de energy bigs

# Qualite
- avg_per: PER moyen de l'equipe
- max_per: Meilleur PER
- std_per: Variance des PER
```

### Utilisation

```python
from src.ml.archetype.nba22_integration import ArchetypeTeamFeatures

# Cree features d'equipe
integrator = ArchetypeTeamFeatures()
team_features = integrator.create_team_features()

# Integre dans NBA-22
# (voir feature_engineering_v4.py)
```

---

## 📁 FICHIERS CREES

```
data/gold/player_archetypes/
├── player_archetypes.parquet          # v1 (original)
├── player_archetypes_v2.parquet       # v2 (optimized) ← NOUVEAU
├── clustering_model.joblib            # v1
└── clustering_model_v2.joblib         # v2 ← NOUVEAU

reports/
├── nba23_report.json                  # v1
└── nba23_optimized_report.json        # v2 ← NOUVEAU

src/ml/archetype/
├── feature_engineering.py             # Modifie (+11 features)
├── auto_clustering.py                 # Modifie (+feature selection)
├── archetype_profiler.py              # Modifie
└── nba22_integration.py               # Nouveau ←

nba23_optimize.py                      # Script optimization ←
```

---

## 🎯 COMMANDES

```bash
# Executer l'optimisation
python nba23_optimize.py

# Voir resultats
cat reports/nba23_optimized_report.json

# Tester integration NBA-22
python src/ml/archetype/nba22_integration.py
```

---

## 📈 PROCHAINES ETAPES

1. **NBA-22 V4**: Integrer features d'archetypes dans les predictions de matchs
2. **Validation**: Tester si accuracy amelioree (objectif: 76.76% → 77.5%)
3. **NBA-24**: Detection progression joueurs

---

**Status:** ✅ NBA-23 OPTIMIZED - PRET POUR INTEGRATION NBA-22
