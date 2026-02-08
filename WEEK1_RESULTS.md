# WEEK 1 - RÉSULTATS PARTIELS

**Date** : 08 Février 2026  
**Durée** : ~15 minutes (surprisingly fast!)  
**Status** : ✅ Phase 1 terminée

---

## 🎯 Résultats des Optimisations

### Random Forest (50 trials, 3 min)
```json
{
  "accuracy": 76.19%,
  "auc": 84.33%,
  "best_params": {
    "n_estimators": 828,
    "max_depth": 13,
    "min_samples_split": 4,
    "min_samples_leaf": 10,
    "max_features": "sqrt",
    "bootstrap": true
  }
}
```
**vs Baseline** : 76.19% vs 76.10% (+0.09%)

### XGBoost (100 trials, 2 min 50s) 🏆
```json
{
  "accuracy": 76.76%,
  "auc": 84.99%,
  "best_params": {
    "n_estimators": 567,
    "max_depth": 4,
    "learning_rate": 0.010,
    "subsample": 0.736,
    "colsample_bytree": 0.991,
    "min_child_weight": 7,
    "gamma": 0.237,
    "reg_alpha": 4.6e-07,
    "reg_lambda": 4.6e-07
  }
}
```
**vs Baseline** : 76.76% vs 76.10% (+0.66%)
**vs RF** : 76.76% vs 76.19% (+0.57%)

---

## 📊 Progression

| Étape | Baseline | Après Optuna | Gain |
|-------|----------|--------------|------|
| Random Forest | 76.10% | 76.19% | +0.09% |
| XGBoost | - | 76.76% | Nouveau meilleur ! |

**Meilleur modèle actuel** : XGBoost (76.76%)

---

## ✨ Nouvelles Features (10 créées)

1. `momentum_diff` - Différence de forme
2. `offensive_efficiency_diff` - Différence offensive
3. `rebounding_diff` - Différence de rebonds
4. `fatigue_combo` - Combinaison fatigue
5. `rest_advantage_squared` - Avantage repos (non-linéaire)
6. `win_pct_momentum_interaction` - Interaction niveau/forme
7. `home_h2h_advantage` - Avantage H2H à domicile
8. `win_pct_diff_squared` - Diff niveau au carré
9. `h2h_pressure` - Intensité rivalité
10. `h2h_margin_weighted` - Marge H2H pondérée

**Dataset** : 8871 matchs × 65 features (was 55)

---

## 🚀 Prochaines Étapes (Suite Semaine 1)

### 1. Stacking (Aujourd'hui)
Combiner RF + XGB + NN → Objectif 77.5-78%

### 2. Calibration (Demain)
Calibrer les probabilités pour les paris

### 3. Test sur nouvelles features (Demain)
Ré-entraîner avec les 65 features (vs 24 actuelles)

---

## 📁 Fichiers Créés

```
results/week1/
├── rf_best_params.json       ✅
├── xgb_best_params.json      ✅
├── rf_optimization.db        ✅
├── xgb_optimization.db       ✅
├── new_features_v2.json      ✅
├── rf_log.txt                ✅
├── xgb_log.txt               ✅
└── orchestrator_log.txt      ✅

models/week1/
├── rf_optimized.pkl          ✅
└── xgb_optimized.pkl         ✅

data/gold/ml_features/
└── features_enhanced_v2.parquet  ✅ (65 features)
```

---

## 💡 Observations

1. **Vitesse** : Les calculs ont été beaucoup plus rapides que prévu (3 min vs 4-6h)
   - Dataset petit (8k samples)
   - CPU puissant (i7, 12 threads)
   - Optuna très efficace

2. **XGBoost gagnant** : Meilleur que RF de +0.57%
   - Plus régulier (learning_rate faible = 0.01)
   - Régularisation L1/L2 activée

3. **Gains modestes** : +0.66% sur XGBoost
   - Les hyperparamètres n'étaient pas très loin de l'optimal
   - Le vrai gain viendra du stacking + nouvelles features

---

## 🎯 Objectif Semaine 1 (Restant)

**Actuel** : 76.76% (XGBoost)  
**Objectif** : 79-80%  
**Gap** : +2.24% à +3.24%

**Plan pour combler le gap** :
1. ✅ Optimisation (fait)
2. ⏳ Stacking (en cours)
3. ⏳ Nouvelles features (à tester)
4. ⏳ Calibration

---

**Suite** : Je crée maintenant le stacking avec les modèles optimisés !
