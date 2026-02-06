---
Story: NBA-23
Epic: Machine Learning & Analytics (NBA-8)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-23: Clustering des profils de joueurs

## 📋 Description

Utiliser K-Means pour classifier les joueurs en 5 profils (shooter, défenseur, all-around).

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-18** : Métriques avancées

## ✅ Critères d'acceptation

### 1. 5 clusters définis

```python
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler

def cluster_players():
    df = spark.read.format("delta").load("data/silver/players_advanced/")
    
    # Features
    feature_cols = ["pts", "reb", "ast", "stl", "blk", "ts_pct"]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="raw_features")
    df_vec = assembler.transform(df)
    
    # Standardisation
    scaler = StandardScaler(inputCol="raw_features", outputCol="features")
    df_scaled = scaler.fit(df_vec).transform(df_vec)
    
    # K-Means k=5
    kmeans = KMeans(k=5, seed=42)
    model = kmeans.fit(df_scaled)
    
    predictions = model.transform(df_scaled)
    return model, predictions
```

### 2. Caractéristiques identifiées

Profils attendus:
- Scorers (haut pts)
- Big Men (haut reb, blk)
- Playmakers (haut ast)
- Role Players (moyen)
- Defenders (haut stl, blk, bas pts)

### 3. Visualisation

Graphique 2D avec PCA

### 4. Script cluster_players.py

## 📦 Livrables

- ✅ `src/ml/cluster_players.py`
- ✅ `data/gold/player_clusters/`
- ✅ `reports/cluster_profiles.json`

## 🎯 Definition of Done

- [ ] 5 clusters créés
- [ ] Profils interprétables
- [ ] Visualisation générée
- [ ] > 50 joueurs par cluster
