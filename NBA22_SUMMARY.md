# NBA-22: Résultats de l'Entraînement ML

**Date :** 08 Février 2026  
**Statut :** ✅ TERMINÉ  
**Objectif :** Accuracy > 60% pour prédiction des matchs NBA

---

## 🎯 Résumé des Résultats

| Modèle | Accuracy | Precision | Recall | F1-Score | AUC |
|--------|----------|-----------|---------|----------|-----|
| **Random Forest** | **76.1%** | 75.5% | 83.1% | 79.1% | 83.9% |
| Gradient Boosting | 75.6% | 75.8% | 81.3% | 78.4% | 83.2% |

**🏆 Meilleur modèle : Random Forest (76.1% accuracy)**  
✅ Objectif atteint : > 60% accuracy

---

## 📊 Caractéristiques du Dataset

- **Matchs totaux :** 8,871
- **Features utilisées :** 24 (sans data leakage)
- **Train :** 6,250 matchs (saisons 2018-2023)
- **Test :** 2,621 matchs (saisons 2023-2025)
- **Home win rate :** 54.6% (test set)
- **Baseline (home advantage) :** ~54% → **Gain : +22%**

---

## 🔝 Top 5 Features Importantes

1. **win_pct_diff** - Différence de win rate entre équipes
2. **home_win_pct** - Win rate cumulé équipe home
3. **away_win_pct** - Win rate cumulé équipe away
4. **h2h_home_win_rate** - Historique face-à-face
5. **home_avg_pts_last_5** - Points moyens (5 derniers matchs)

---

## 🗂️ Structure des Fichiers

```
models/experiments/nba22_20260208_111840/
├── model_rf.joblib          # Modèle Random Forest (5MB)
├── model_gbt.joblib         # Modèle Gradient Boosting (0.4MB)
└── metrics.json             # Métriques comparatives
```

---

## 🚀 Utilisation

### Entraîner les modèles
```bash
python src/ml/nba22_train.py
```

### Utiliser l'orchestrateur
```bash
# Entraînement
python -m src.ml.nba22_orchestrator train

# Comparer les expérimentations
python -m src.ml.nba22_orchestrator compare

# Déployer en production
python -m src.ml.nba22_orchestrator deploy \
  --model models/experiments/nba22_20260208_111840/model_rf.joblib \
  --version v1.0.0
```

### Analyse dans Jupyter
```bash
jupyter notebook notebooks/04_nba22_results.ipynb
```

---

## ⚠️ Points Importants

### Data Leakage Évité
Les features suivantes ont été **exclues** car calculées sur le match en cours :
- Scores (home_score, away_score)
- Stats match (home_reb, home_ast, etc.)
- Métriques avancées (home_ts_pct, home_game_score)

### Validation Temporelle
- Split temporel strict : train avant test chronologiquement
- Dernière date train : 2023-06-12
- Première date test : 2023-10-24
- ✅ Pas de fuite de données temporelle

---

## 📈 Prochaines Étapes

- [ ] **NBA-22-2** : Régression pour prédire le score exact
- [ ] **NBA-22-3** : Clustering des profils de joueurs
- [ ] **NBA-23** : Détection des joueurs en progression
- [ ] **NBA-25** : Pipeline ML automatisé

---

## 📝 Métriques Détaillées

```json
{
  "best_model": {
    "name": "rf",
    "accuracy": 0.761,
    "algorithm": "rf"
  },
  "models": {
    "rf": {
      "accuracy": 0.761,
      "precision": 0.755,
      "recall": 0.831,
      "f1": 0.791,
      "auc": 0.839
    },
    "gbt": {
      "accuracy": 0.756,
      "precision": 0.758,
      "recall": 0.813,
      "f1": 0.784,
      "auc": 0.832
    }
  }
}
```

---

**NBA-22 TERMINÉ AVEC SUCCÈS** 🎉
