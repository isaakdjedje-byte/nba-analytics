---
Story: NBA-27
Epic: Data Quality & Monitoring (NBA-9)
Points: 3
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-27: Data Quality Checks automatisés

## 📋 Description

Implémenter des contrôles qualité automatiques sur les données avec validation des schémas, détection d'anomalies et validation des ranges.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-26** : Tests unitaires

## ✅ Critères d'acceptation

### 1. Script data_quality.py créé

```python
#!/usr/bin/env python3
"""Data Quality Checks"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, isnan
import json
from datetime import datetime

class DataQualityChecker:
    """Classe de vérification qualité données"""
    
    def __init__(self):
        self.spark = SparkSession.builder.getOrCreate()
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def check_schema(self, df, required_columns):
        """Vérifier présence colonnes obligatoires"""
        missing = [c for c in required_columns if c not in df.columns]
        status = len(missing) == 0
        
        self.checks.append({
            "name": "Schema Validation",
            "status": "PASS" if status else "FAIL",
            "details": f"Missing: {missing}" if missing else "All columns present"
        })
        
        return status
    
    def check_nulls(self, df, threshold=0.05):
        """Vérifier taux de nulls"""
        total = df.count()
        
        for col_name in df.columns:
            null_count = df.filter(col(col_name).isNull()).count()
            null_rate = null_count / total
            
            if null_rate > threshold:
                self.checks.append({
                    "name": f"Null Check - {col_name}",
                    "status": "FAIL",
                    "details": f"{null_rate:.1%} nulls (threshold: {threshold:.1%})"
                })
                return False
        
        self.checks.append({
            "name": "Null Check",
            "status": "PASS",
            "details": f"All columns < {threshold:.1%} nulls"
        })
        return True
    
    def check_ranges(self, df, column_rules):
        """Vérifier valeurs dans ranges valides"""
        for col_name, (min_val, max_val) in column_rules.items():
            if col_name in df.columns:
                outliers = df.filter(
                    (col(col_name) < min_val) | (col(col_name) > max_val)
                ).count()
                
                if outliers > 0:
                    self.checks.append({
                        "name": f"Range Check - {col_name}",
                        "status": "FAIL",
                        "details": f"{outliers} values outside [{min_val}, {max_val}]"
                    })
                    return False
        
        self.checks.append({
            "name": "Range Check",
            "status": "PASS",
            "details": "All values in valid ranges"
        })
        return True
    
    def generate_report(self, output_path="reports/data_quality.json"):
        """Générer rapport qualité"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.checks),
            "passed": sum(1 for c in self.checks if c["status"] == "PASS"),
            "failed": sum(1 for c in self.checks if c["status"] == "FAIL"),
            "checks": self.checks
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return report

# Utilisation
def main():
    checker = DataQualityChecker()
    
    # Lire données
    df = spark.read.format("delta").load("data/silver/players_advanced/")
    
    # Vérifications
    checker.check_schema(df, ["id", "full_name", "pts", "per"])
    checker.check_nulls(df, threshold=0.05)
    checker.check_ranges(df, {
        "per": (0, 40),
        "ts_pct": (0, 1),
        "pts": (0, 50)
    })
    
    # Rapport
    report = checker.generate_report()
    
    if report["failed"] > 0:
        print(f"❌ {report['failed']} checks failed")
        exit(1)
    else:
        print(f"✅ All {report['total_checks']} checks passed")

if __name__ == "__main__":
    main()
```

---

### 2. Vérification schéma

Vérifier colonnes obligatoires présentes:
- `id`, `full_name`, `team`, `season`
- `pts`, `reb`, `ast`, `per`, `ts_pct`

---

### 3. Détection nulls/anomalies

- Taux nulls < 5% par colonne
- Détection doublons (IDs uniques)
- Anomalies statistiques (z-score > 3)

---

### 4. Validation des ranges

```python
VALIDATION_RULES = {
    "per": (0, 40),           # PER entre 0 et 40
    "ts_pct": (0, 1),         # TS% entre 0 et 100%
    "pts": (0, 50),           # Points par match
    "reb": (0, 25),           # Rebonds
    "ast": (0, 15),           # Passes
    "minutes": (0, 48),       # Minutes
    "height": (160, 240),     # Taille cm
    "weight": (60, 160)       # Poids kg
}
```

---

### 5. Rapport qualité généré

**Exemple rapport:**
```json
{
  "timestamp": "2024-02-06T15:30:00",
  "total_checks": 5,
  "passed": 5,
  "failed": 0,
  "checks": [
    {
      "name": "Schema Validation",
      "status": "PASS",
      "details": "All columns present"
    },
    {
      "name": "Null Check",
      "status": "PASS",
      "details": "All columns < 5.0% nulls"
    },
    {
      "name": "Range Check - per",
      "status": "PASS",
      "details": "All values in valid ranges"
    }
  ]
}
```

## 📦 Livrables

- ✅ `src/quality/data_quality.py`
- ✅ `src/quality/validation_rules.yaml`
- ✅ `reports/data_quality.json` (généré après chaque run)

## 🎯 Definition of Done

- [ ] Script data_quality.py fonctionnel
- [ ] Vérification schéma automatique
- [ ] Détection nulls et anomalies
- [ ] Validation ranges métriques
- [ ] Rapport JSON généré après chaque exécution
- [ ] Intégré dans pipeline (exécutable après NBA-18)
