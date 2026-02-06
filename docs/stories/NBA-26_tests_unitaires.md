---
Story: NBA-26
Epic: Data Quality & Monitoring (NBA-9)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-26: Tests unitaires des transformations

## 📋 Description

Créer une suite de tests complète pour les fonctions de traitement avec couverture > 80%.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-17** : Nettoyage
- ✅ **NBA-18** : Métriques
- ✅ **NBA-19** : Agrégations

## ✅ Critères d'acceptation

### 1. Tests PySpark créés dans tests/

**Structure:**
```
tests/
├── __init__.py
├── conftest.py                 # Fixtures PySpark
├── test_cleaning.py            # NBA-17
├── test_metrics.py             # NBA-18
├── test_aggregations.py        # NBA-19
├── test_transformations.py     # Utilitaires
└── test_end_to_end.py          # Pipeline complet
```

**Exemple test_cleaning.py:**
```python
import pytest
from pyspark.sql import SparkSession
from src.processing.clean_data import remove_duplicates, handle_nulls

@pytest.fixture(scope="session")
def spark():
    """Fixture Spark Session"""
    return SparkSession.builder \
        .appName("Test") \
        .master("local[2]") \
        .getOrCreate()

class TestDataCleaning:
    
    def test_remove_duplicates(self, spark):
        """Test suppression doublons"""
        data = [(1, "A"), (1, "A"), (2, "B")]
        df = spark.createDataFrame(data, ["id", "name"])
        
        result = remove_duplicates(df, ["id"])
        assert result.count() == 2
    
    def test_handle_nulls(self, spark):
        """Test gestion nulls"""
        data = [(1, None), (2, "B"), (None, "C")]
        df = spark.createDataFrame(data, ["id", "name"])
        
        result = handle_nulls(df, critical_cols=["id"])
        assert result.filter(col("id").isNull()).count() == 0
```

---

### 2. Couverture de test > 80%

```bash
# Générer rapport couverture
pytest --cov=src --cov-report=html --cov-report=term

# Vérifier > 80%
Name                          Stmts   Miss  Cover
-----------------------------------------------
src/__init__.py                   0      0   100%
src/processing/clean_data.py     45      5    89%
src/utils/nba_formulas.py        38      3    92%
-----------------------------------------------
TOTAL                           200     25    88%
```

---

### 3. Tests pour toutes les fonctions

- ✅ `clean_data.py` : remove_duplicates, handle_nulls, remove_outliers
- ✅ `nba_formulas.py` : calculate_per, calculate_ts_pct, calculate_usg_pct
- ✅ `team_aggregates.py` : create_team_aggregates, calculate_season_averages

---

### 4. CI exécutant les tests automatiquement

**.github/workflows/tests.yml:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

### 5. Tous les tests passants

```bash
$ pytest tests/ -v

============================= test session starts =============================
platform linux -- Python 3.11.0
collected 25 items

tests/test_cleaning.py::TestDataCleaning::test_remove_duplicates PASSED [  4%]
tests/test_cleaning.py::TestDataCleaning::test_handle_nulls PASSED      [  8%]
tests/test_metrics.py::TestMetrics::test_per_calculation PASSED         [ 12%]
tests/test_metrics.py::TestMetrics::test_ts_calculation PASSED          [ 16%]
...
======================== 25 passed in 12.34s ================================
```

## 📦 Livrables

- ✅ `tests/` - Suite complète de tests
- ✅ `.github/workflows/tests.yml` - CI GitHub Actions
- ✅ `pytest.ini` - Configuration pytest
- ✅ Couverture > 80%

## 🎯 Definition of Done

- [ ] Tests pour toutes les fonctions critiques
- [ ] Couverture > 80%
- [ ] CI GitHub Actions configurée
- [ ] Tous les tests passants
- [ ] Rapport couverture généré
