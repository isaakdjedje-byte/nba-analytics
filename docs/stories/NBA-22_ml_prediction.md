---
Story: NBA-22
Epic: Machine Learning & Analytics (NBA-8)
Points: 8
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-22: Modèle de prédiction des résultats de matchs

## 📋 Description

Créer un modèle ML Spark pour prédire le vainqueur des matchs avec précision > 60%.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-21** : Features ML

## ✅ Critères d'acceptation

### 1. Modèle Random Forest entraîné

```python
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import VectorAssembler

def train_model():
    # Lire features
    df = spark.read.format("delta").load("data/gold/ml_features/")
    
    # Assembler features
    feature_cols = ["home_avg_pts", "away_avg_pts", "home_win_rate", "h2h_home_win_rate"]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    df_vec = assembler.transform(df)
    
    # Split
    train, test = df_vec.randomSplit([0.8, 0.2], seed=42)
    
    # Modèle
    rf = RandomForestClassifier(
        labelCol="target",
        featuresCol="features",
        numTrees=100,
        seed=42
    )
    
    model = rf.fit(train)
    return model, test
```

### 2. Précision > 60%

```python
def evaluate_model(model, test_data):
    predictions = model.transform(test_data)
    
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator
    evaluator = MulticlassClassificationEvaluator(labelCol="target")
    
    accuracy = evaluator.evaluate(predictions, {evaluator.metricName: "accuracy"})
    
    assert accuracy > 0.60, f"Accuracy: {accuracy:.3f}"
    print(f"✅ Accuracy: {accuracy:.3f}")
    
    return accuracy
```

### 3. Modèle sauvegardé

```python
model.save("models/random_forest_v1")
```

### 4. Évaluation avec métriques

- Accuracy, Precision, Recall, F1-score

## 📦 Livrables

- ✅ `src/ml/train_model.py`
- ✅ `src/ml/predict.py`
- ✅ `models/random_forest_v1/`
- ✅ `models/metrics.json`

## 🎯 Definition of Done

- [ ] Modèle Random Forest entraîné
- [ ] Accuracy > 60% sur test
- [ ] Métriques complètes (accuracy, precision, recall, f1)
- [ ] Modèle sauvegardé
