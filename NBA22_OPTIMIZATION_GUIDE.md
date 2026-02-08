# NBA-22 Optimizations - Guide d'utilisation

## 🚀 Nouvelles fonctionnalités (v2.0)

### 1. Feature Selection (Sélection de features)
**Objectif:** Réduire de 80 à 35 features pour améliorer les performances et réduire l'overfitting.

**Comment ça marche:**
- Utilise l'importance des features XGBoost
- Compare ANOVA F-test, Mutual Information, et RFE
- Sélectionne les 35 meilleures features

**Résultat:** Modèle plus rapide, moins d'overfitting

### 2. Calibration des Probabilités
**Objectif:** Rendre les probabilités fiables pour les paris.

**Problème:** Si le modèle prédit 80% de confiance, il ne gagne pas 80% du temps.
**Solution:** Calibration avec Isotonic Regression pour que proba=0.8 → 80% de win rate réel.

**Métrique:** Brier Score (plus petit = mieux)

### 3. Monitoring Data Drift
**Objectif:** Détecter quand les données changent et que le modèle doit être réentraîné.

**Détecte:**
- **Feature drift:** Changement dans la distribution des features
- **Concept drift:** Changement dans la relation features-target
- **Performance drift:** Baisse de l'accuracy

### 4. Système de Santé
**Objectif:** Vérifier que tous les composants fonctionnent correctement.

**Vérifie:**
- Données disponibles
- Modèles entraînés
- Prédictions récentes
- Tracking ROI fonctionnel

## 📊 Commandes

### Entraînement optimisé complet
```bash
python src/ml/pipeline/train_optimized.py
```

Cela va:
1. Charger les données
2. Sélectionner les 35 meilleures features
3. Entraîner XGBoost + Random Forest
4. Calibrer les probabilités
5. Sauvegarder les modèles optimisés

### Prédictions optimisées
```bash
python run_predictions_optimized.py
```

Utilise:
- Modèle optimisé (35 features)
- Probabilités calibrées
- API NBA Live

### Mise à jour des résultats
```bash
python run_predictions_optimized.py --update
```

Interface interactive pour entrer les résultats des matchs.

### Rapport de performance
```bash
python run_predictions_optimized.py --report
```

Génère un rapport ROI avec accuracy par niveau de confiance.

### Vérification de santé
```bash
python run_predictions_optimized.py --health
```

Vérifie que tout fonctionne correctement.

### Détection de drift
```bash
python run_predictions_optimized.py --drift
```

Analyse si les données ont changé.

### Réentraînement
```bash
python run_predictions_optimized.py --train
```

Relance l'entraînement complet.

### Lancement complet
```bash
python launch_optimization.py
```

Lance toutes les étapes d'optimisation séquentiellement.

## 📁 Fichiers créés

### Modèles optimisés
```
models/optimized/
├── model_xgb.joblib              # Modèle XGBoost optimisé
├── model_rf.joblib               # Random Forest (backup)
├── calibrator_xgb.joblib         # Calibrateur de probabilités
└── selected_features.json        # Liste des 35 features sélectionnées
```

### Résultats
```
results/feature_selection/
├── selected_features.json        # Features sélectionnées
└── selection_comparison.json     # Comparaison des méthodes
```

### Prédictions
```
predictions/
├── predictions_optimized_*.csv   # Prédictions avec calibration
├── latest_predictions_optimized.csv
├── tracking_history.csv          # Historique ROI
├── health_report.json            # Rapport de santé
└── drift_report.json             # Rapport de drift
```

## 🎯 Workflow recommandé

### Quotidien
```bash
# 1. Faire les prédictions
python run_predictions_optimized.py

# 2. Après les matchs, mettre à jour les résultats
python run_predictions_optimized.py --update

# 3. Voir le rapport
python run_predictions_optimized.py --report
```

### Hebdomadaire
```bash
# Vérifier la santé du système
python run_predictions_optimized.py --health

# Vérifier le drift
python run_predictions_optimized.py --drift

# Si problème: réentraîner
python run_predictions_optimized.py --train
```

### Mensuel
```bash
# Réentraînement complet avec nouvelles données
python src/ml/pipeline/train_optimized.py
```

## 📈 Métriques de suivi

### Performance du modèle
- **Accuracy:** Objectif > 76%
- **AUC:** Objectif > 84%
- **Brier Score:** Objectif < 0.18 (plus petit = mieux)

### ROI
- **HIGH_CONFIDENCE (>70%):** Devrait avoir > 70% de win rate
- **MEDIUM_CONFIDENCE (60-70%):** Devrait avoir > 60% de win rate
- **LOW_CONFIDENCE (55-60%):** À éviter ou petites mises

### Santé du système
- **Data drift:** p-value > 0.05 (pas de drift)
- **Performance drift:** Accuracy ne baisse pas de > 10%
- **Disponibilité:** Tous les composants fonctionnent

## ⚠️ Alertes

### Drift détecté
Si le monitoring détecte un drift:
1. Vérifier les données d'entrée
2. Réentraîner le modèle: `python run_predictions_optimized.py --train`
3. Si persiste: investiguer la source du drift

### Performance en baisse
Si l'accuracy baisse de > 10%:
1. Vérifier avec `--health`
2. Réentraîner le modèle
3. Si persiste: besoin de nouvelles features ou données

## 🔧 Dépannage

### "Modèle optimisé non trouvé"
```bash
python src/ml/pipeline/train_optimized.py
```

### "Erreur de calibration"
Vérifiez que le fichier existe:
```bash
ls models/optimized/calibrator_xgb.joblib
```

### "Données historiques insuffisantes"
Certaines équipes n'ont pas assez d'historique. C'est normal pour les nouvelles équipes.

## 📚 Architecture

```
Pipeline Optimisé:

API NBA Live
    ↓
Feature Engineering (35 features sélectionnées)
    ↓
Modèle XGBoost Optimisé
    ↓
Calibration des Probabilités
    ↓
Prédictions Calibrées
    ↓
Tracking ROI
    ↓
Monitoring Drift
```

## 🎓 Notes techniques

### Feature Selection
- **Méthode:** XGBoost Feature Importance
- **Nombre:** 35 features (réduit de 80)
- **Avantage:** Moins d'overfitting, plus rapide

### Calibration
- **Méthode:** Isotonic Regression
- **Validation:** Brier Score
- **Avantage:** Probabilités fiables pour Kelly Criterion

### Drift Detection
- **Méthode:** Kolmogorov-Smirnov test
- **Seuil:** p-value < 0.05
- **Fréquence:** Recommandé hebdomadaire

---

**Dernière mise à jour:** 2026-02-08  
**Version:** NBA-22 v2.0 Optimized
