# 🏀 NBA-13 : Spark Streaming Box Score

## 📋 Vue d'ensemble

Pipeline Spark Streaming pour consommer les statistiques NBA en temps réel (simulation depuis données historiques).

## 🎯 Architecture

```
Simulateur (Python)  ===>  Fichiers JSON  ===>  Spark Streaming  ===>  Delta Lake
     (écriture)            (dossier)           (Micro-batch)        (data/silver/)
```

## 📁 Fichiers créés

- `src/ingestion/streaming_simulator.py` - Génère des box scores en fichiers JSON
- `src/ingestion/streaming_ingestion.py` - Pipeline Spark Streaming
- `scripts/test_streaming.py` - Guide de test

## 🚀 Démarrage rapide

### Architecture améliorée (sans conflit de fichiers)

Le système utilise maintenant des **dossiers uniques** par exécution avec synchronisation automatique.

### Ordre de lancement :

**Terminal 1 : Démarrer Spark Streaming (en premier)**
```bash
docker-compose exec spark-nba python src/ingestion/streaming_ingestion.py
```

**Le stream va attendre automatiquement le simulateur...**

**Terminal 2 : Démarrer le simulateur (après)**
```bash
docker-compose exec spark-nba python src/ingestion/streaming_simulator.py
```

Le simulateur crée un dossier unique (`run_YYYYMMDD_HHMMSS`), écrit tous les fichiers, puis crée un fichier `COMPLETE` pour signaler la fin.

Spark détecte automatiquement ce dossier et commence le traitement.

## ⚙️ Configuration

**Dans `streaming_ingestion.py` :**
- `CHECKPOINT_LOCATION = "data/checkpoints/live_games"`
- `OUTPUT_PATH = "data/silver/live_games"`
- `INPUT_PATH = "data/streaming/input"`
- `BATCH_INTERVAL = "30 seconds"`
- **Timeout d'attente : 15 minutes (900s)**
- **Durée de traitement : 13 minutes (780s)**

**Dans `streaming_simulator.py` :**
- **Durée de génération : ~10.5 minutes (21 box scores × 30s)**
- **Dossier unique par exécution : `run_YYYYMMDD_HHMMSS`**

## 📊 Données générées

**Box Score toutes les 30 secondes :**
- Score cumulé
- % de réussite (FG, 3PTS, LF)
- Rebonds, passes, interceptions, contres
- Métriques dérivées (efficacité, qualité de shoot)

## ✅ Vérification

```bash
docker-compose exec spark-nba python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.format('delta').load('data/silver/live_games')
print(f'Evenements recus: {df.count()}')
df.show(10)
"
```

## 📝 Critères d'acceptation NBA-13

- [x] Spark Streaming configuré
- [x] Consommation données temps réel (simulation)
- [x] Stockage Delta Lake en mode append
- [x] CheckpointLocation configuré
- [x] Stream fonctionnel pendant 120s+

## 🔧 Dépannage

**Erreur "Connection refused" :**
→ Démarrer d'abord le simulateur (Terminal 1)

**Pas de données reçues :**
→ Vérifier que les deux processus tournent
→ Vérifier les logs du simulateur

**Port déjà utilisé :**
→ Changer `SIMULATOR_PORT` dans les deux fichiers
