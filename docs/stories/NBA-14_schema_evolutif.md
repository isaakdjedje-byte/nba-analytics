---
Story: NBA-14
Epic: Data Ingestion & Collection (NBA-6)
Points: 5
Statut: In Progress
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-14: Gestion des schémas évolutifs

## 📋 Description

Gérer les changements de schéma dans les données NBA avec Delta Lake. Implémenter un système de versioning des schémas qui permet d'évoluer sans casser les traitements existants.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-12** : Pipeline Spark batch (Delta Lake déjà en place)
- ✅ **NBA-13** : Streaming (gestion temps réel)

### Bloque:
- ⬜ **NBA-17** : Nettoyage (nécessite schéma stable)
- ⬜ **NBA-18** : Métriques avancées (dépend du schéma final)
- ⬜ **NBA-20** : Transformation matchs (structure des données)

### Parallèle avec:
- ⬜ **NBA-15** : Récupération données (doit respecter schéma)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ NBA-12  │────→│ NBA-14  │────→│ NBA-17  │
│ (Delta) │     │(Schémas)│     │(Clean)  │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ├────→ NBA-18 (Métriques)
                     │
                     ├────→ NBA-20 (Transform)
                     │
                     └────→ NBA-15 (parallel)
```

## 📥📤 Entrées/Sorties

### Données en entrée:
- **`data/processed/games_enriched/`** : Delta Lake existant (NBA-12)
- **Structure actuelle** : 20+ colonnes (PTS, REB, AST, PER, TS%, etc.)

### Données en sortie:
- **`data/processed/games_enriched/`** : Même chemin avec MergeSchema
- **`data/processed/schema_versions/`** : Historique des versions
- **`docs/schema_evolution.log`** : Log des changements

### Format:
- **Format**: Delta Lake 3.0
- **Partitionnement**: `season`, `game_year` (conservé)
- **Versioning**: Time travel Delta Lake + métadonnées custom

## 🛠️ Stack Technique

- **PySpark 3.5** : Lectures/écritures Delta
- **Delta Lake 3.0** : MergeSchema, time travel
- **Python 3.11** : Script de gestion
- **PyYAML** : Configuration schémas

### Bibliothèques:
```python
from delta import DeltaTable, configure_spark_with_delta_pip
from pyspark.sql.functions import lit, current_timestamp
import yaml
import json
```

## ✅ Critères d'acceptation détaillés

### 1. MergeSchema activé sur les écritures Delta

**Test détaillé:**
```python
# DONNÉES TEST
df_old = spark.createDataFrame([
    ("2024-01-01", "LAL", 120, None),      # Sans nouvelle colonne
    ("2024-01-02", "GSW", 115, None)
], ["date", "team", "points", "new_metric"])

# ÉCRITURE AVEC MERGESCHEMA
df_old.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("data/processed/games_enriched/")

# VÉRIFICATION
schema = spark.read.format("delta").load("data/processed/games_enriched/").schema
assert "new_metric" in [f.name for f in schema.fields]
print("✅ MergeSchema fonctionne!")
```

**Résultat attendu:**
- Schéma évolutif sans erreur
- Colonnes manquantes = null
- Anciennes données conservées

---

### 2. Versioning des schémas fonctionnel

**Test détaillé:**
```python
# TEST TIME TRAVEL
from delta import DeltaTable

dt = DeltaTable.forPath(spark, "data/processed/games_enriched/")
history = dt.history()

# Vérifier qu'on a au moins 2 versions
assert len(history) >= 2, "Besoin d'historique pour test"

# Lire version N-1
df_v1 = spark.read \
    .format("delta") \
    .option("versionAsOf", 0) \
    .load("data/processed/games_enriched/")

# Lire version N (actuelle)
df_v2 = spark.read \
    .format("delta") \
    .load("data/processed/games_enriched/")

# Vérifier différences
old_cols = set(df_v1.columns)
new_cols = set(df_v2.columns)
added_cols = new_cols - old_cols

print(f"✅ Colonnes ajoutées: {added_cols}")
print(f"✅ Time travel fonctionne: {len(history)} versions")
```

**Résultat attendu:**
- Lecture version historique possible
- Différence colonnes identifiable
- Métadonnées de changement présentes

---

### 3. Test de changement de schéma réussi

**Scénario de test complet:**

**Étape 1: Schéma initial (V1)**
```python
# Créer données V1
df_v1 = spark.createDataFrame([
    (1, "LAL", 120.0, 45),
    (2, "GSW", 115.0, 42)
], ["game_id", "team", "points", "rebounds"])

df_v1.write.format("delta").mode("overwrite") \
    .save("data/processed/test_schema/")
```

**Étape 2: Schéma évolutif (V2)**
```python
# Ajouter colonnes
df_v2 = spark.createDataFrame([
    (3, "BOS", 108.0, 38, 25, 0.58),  # + assists, + ts_pct
    (4, "MIA", 112.0, 41, 22, 0.62)
], ["game_id", "team", "points", "rebounds", "assists", "ts_pct"])

df_v2.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("data/processed/test_schema/")
```

**Étape 3: Vérifications**
```python
# Lire toutes les données
df_all = spark.read.format("delta").load("data/processed/test_schema/")

# Vérifications:
assert df_all.count() == 4, "Toutes les lignes présentes"
assert "assists" in df_all.columns, "Nouvelle colonne ajoutée"
assert "ts_pct" in df_all.columns, "Nouvelle colonne ajoutée"

# Vérifier nulls pour anciennes données
v1_data = df_all.filter(col("game_id").isin([1, 2]))
assert v1_data.filter(col("assists").isNull()).count() == 2, "Anciennes données = null"

print("✅ Changement de schéma réussi!")
print(f"   - Total lignes: {df_all.count()}")
print(f"   - Total colonnes: {len(df_all.columns)}")
print(f"   - Colonnes: {df_all.columns}")
```

**Résultat attendu:**
- 4 lignes (2 V1 + 2 V2)
- 6 colonnes (4 originales + 2 nouvelles)
- V1: assists=null, ts_pct=null
- V2: valeurs renseignées

---

### 4. Documentation des évolutions de schéma

**Livrable:** `docs/schema_evolution.log`

**Format attendu:**
```yaml
schema_versions:
  - version: 1
    date: "2024-02-06T10:30:00"
    columns: ["game_id", "team", "points", "rebounds"]
    nb_records: 8600
    
  - version: 2
    date: "2024-02-06T11:15:00"
    columns: ["game_id", "team", "points", "rebounds", "assists", "ts_pct"]
    nb_records: 8602
    changes:
      added: ["assists", "ts_pct"]
      removed: []
      modified: []
    author: "NBA-14"
```

**Test:**
```python
import yaml

with open("docs/schema_evolution.log") as f:
    history = yaml.safe_load(f)

assert len(history["schema_versions"]) >= 2
assert "changes" in history["schema_versions"][-1]
print("✅ Documentation à jour!")
```

## ⚠️ Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Breaking change** | Faible | Critique | Tests sur environnement isolé avant prod |
| **Données corrompues** | Faible | Critique | Backup automatique avant migration |
| **Performance dégradée** | Moyen | Moyen | Monitoring temps requêtes, optimise si besoin |
| **Incohérence métrique** | Moyen | Élevé | Validation données après changement (NBA-27) |
| **Rollback impossible** | Faible | Élevé | Time travel Delta = rollback toujours possible |

### Plan de secours:
1. Backup automatique: `cp -r data/processed/ data/backup/$(date +%Y%m%d)/`
2. Rollback: `spark.read.format("delta").option("versionAsOf", N-1).load(...)`
3. Hotfix: Script de correction rapide

## 📦 Livrables

### Code:
- ✅ `src/utils/schema_manager.py` - Gestionnaire de schémas
- ✅ `src/utils/schema_config.yaml` - Configuration schémas
- ✅ `tests/test_schema_evolution.py` - Tests unitaires

### Documentation:
- ✅ `docs/schema_evolution.log` - Historique versions
- ✅ `docs/SCHEMA_VERSIONING.md` - Guide d'utilisation

### Données:
- ✅ `data/processed/games_enriched/` - Delta Lake avec MergeSchema activé
- ✅ `data/processed/schema_versions/` - Backup versions

## 🎯 Definition of Done

- [x] Code review effectué
- [ ] Tests passants (pytest tests/test_schema_evolution.py)
- [ ] Documentation à jour
- [ ] Pas de régression sur NBA-12/NBA-13
- [ ] Performance acceptable (< 10% dégradation)
- [ ] Mergé dans master (PR #X)

## 📝 Notes d'implémentation

### Activation MergeSchema:
```python
# Option globale
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# Option par écriture
df.write.format("delta").option("mergeSchema", "true").mode("append").save(...)
```

### Vérification version:
```python
from delta import DeltaTable
dt = DeltaTable.forPath(spark, path)
print(dt.history().select("version", "timestamp", "operation").show())
```

## 🔗 Références

- [Delta Lake Schema Evolution](https://docs.delta.io/latest/delta-update.html#automatic-schema-update)
- [Time Travel](https://docs.delta.io/latest/delta-batch.html#data-versioning)
- NBA-12: Pipeline batch existant
- NBA-13: Streaming avec Delta
