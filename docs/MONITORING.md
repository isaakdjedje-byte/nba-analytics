# 📊 MONITORING - NBA Analytics Platform

**Version :** 1.0  
**Date :** 8 Février 2026  
**Statut :** ✅ Production Ready

---

## 🎯 Vue d'Ensemble

Système de monitoring complet pour le pipeline NBA Analytics, implémentant les stories **NBA-26** (Tests), **NBA-27** (Data Quality) et **NBA-28** (Monitoring).

**Philosophie :** Centraliser les patterns dispersés plutôt que de dupliquer.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Logging    │  │   Metrics    │  │   Alerts     │     │
│  │              │  │              │  │              │     │
│  │ get_logger() │  │ PipelineMetrics│  │ AlertManager │     │
│  │              │  │              │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └────────┬────────┴────────┬────────┘              │
│                  │                 │                       │
│         ┌────────▼─────────────────▼────────┐              │
│         │     DataQualityReporter           │              │
│         │  (Validation Bronze/Silver/Gold)  │              │
│         └─────────────────┬─────────────────┘              │
│                           │                                │
│                  ┌────────▼────────┐                       │
│                  │   logs/         │                       │
│                  │   ├── metrics/  │                       │
│                  │   ├── quality/  │                       │
│                  │   └── alerts.log│                       │
│                  └─────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Modules

### 1. monitoring.py

**Localisation :** `src/utils/monitoring.py`

**Fonctionnalités :**
- Logger standardisé
- Collecte de métriques (timings, volumes, erreurs)
- Validation qualité données

**Classes principales :**

#### `get_logger(name: str)`
Logger centralisé qui remplace les 5+ configurations dispersées.

```python
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("Pipeline démarré")
logger.error("Erreur détectée")
```

#### `PipelineMetrics`
Collecte les métriques d'exécution.

```python
from src.utils import PipelineMetrics

metrics = PipelineMetrics("nba25_pipeline")

# Enregistrer timing
metrics.record_timing("feature_engineering", 2.5)

# Enregistrer volume
metrics.record_volume("predictions", 150)

# Enregistrer erreur
metrics.record_error("APIError", "Timeout NBA API")

# Finaliser et sauvegarder
metrics.finalize("success")
metrics.save_report()  # Sauvegarde dans logs/metrics/
```

**Rapport généré :**
```json
{
  "pipeline": "nba25_pipeline",
  "start_time": "2026-02-08T20:00:00",
  "timings": {
    "feature_engineering": {
      "duration_seconds": 2.5,
      "timestamp": "2026-02-08T20:00:02"
    }
  },
  "volumes": {
    "predictions": {
      "record_count": 150,
      "timestamp": "2026-02-08T20:00:05"
    }
  },
  "errors": [],
  "status": "success",
  "end_time": "2026-02-08T20:00:10",
  "total_duration_seconds": 10.0
}
```

#### `DataQualityReporter`
Valide la qualité des données à travers les couches.

```python
from src.utils import DataQualityReporter

reporter = DataQualityReporter()

# Validation complète
results = reporter.run_full_check(
    bronze_data=bronze_players,
    silver_data=silver_players,
    gold_data=ml_features
)

# Sauvegarder rapport
reporter.save_report()  # Sauvegarde dans logs/quality/
```

**Rapport généré :**
```json
{
  "bronze": {
    "record_count": 5103,
    "unique_ids": 5103,
    "duplicates": 0,
    "completion_rate": 0.67,
    "status": "pass"
  },
  "silver": {
    "record_count": 4857,
    "validation_level": "contemporary",
    "null_rate": 0.05,
    "status": "pass"
  },
  "gold": {
    "record_count": 8871,
    "feature_count": 35,
    "nan_rate": 0.001,
    "ml_ready": true,
    "status": "pass"
  },
  "summary": {
    "timestamp": "2026-02-08T20:00:00",
    "overall_status": "pass"
  }
}
```

---

### 2. alerts.py

**Localisation :** `src/utils/alerts.py`

**Fonctionnalités :**
- Système d'alertes avec logs dédiés
- Alertes spécifiques (drift, qualité, pipeline, performance)

**Classes principales :**

#### `AlertManager`
Gestionnaire d'alertes centralisé.

```python
from src.utils import AlertManager

alerts = AlertManager()
alerts.send_alert("Message", "warning", "mon_module")
```

#### Fonctions helper

```python
from src.utils import (
    alert_on_drift,
    alert_on_quality_failure,
    alert_on_pipeline_failure,
    alert_on_performance_degradation,
    send_alert
)

# Alerte sur drift détecté
alert_on_drift("weighted_form_diff", drift_score=0.08, threshold=0.05)

# Alerte sur échec validation
alert_on_quality_failure("silver_players", ["Taux nulls: 15%"])

# Alerte sur échec pipeline
alert_on_pipeline_failure("nba22_training", "Out of memory", "model_training")

# Alerte sur dégradation performance
alert_on_performance_degradation("accuracy", 0.72, 0.76, 5.0)

# Alerte générique
send_alert("Message personnalisé", "info", "mon_module")
```

**Format logs/alerts.log :**
```
2026-02-08 20:00:00 - WARNING - ⚠️  [drift_monitoring] Drift détecté sur 'weighted_form_diff': score=0.0800 < seuil=0.05
2026-02-08 20:00:01 - ERROR - ❌ [data_quality] Validation qualité échouée pour 'silver_players': Taux nulls: 15%
2026-02-08 20:00:02 - ERROR - ❌ [nba22_training] Pipeline 'nba22_training' échoué à l'étape 'model_training': Out of memory
```

---

## 🔧 Intégration dans les Pipelines

### Enhanced Pipeline (NBA-25)

Le pipeline ML automatisé utilise le monitoring pour tracker les performances.

```python
# Dans enhanced_pipeline.py
from src.utils import PipelineMetrics, alert_on_pipeline_failure, log_pipeline_start, log_pipeline_end

class EnhancedPredictionPipeline:
    def run_auto_pipeline(self, ...):
        log_pipeline_start("NBA-25: PIPELINE ML AUTOMATISÉ")
        metrics = PipelineMetrics("nba25_auto_pipeline")
        
        try:
            # Phase 1: Health check
            phase_start = time.time()
            health = self.check_system_health()
            metrics.record_timing("health_check", time.time() - phase_start)
            
            # Phase 2: Predictions
            phase_start = time.time()
            predictions = self.run_daily_predictions()
            metrics.record_timing("predictions", time.time() - phase_start)
            metrics.record_volume("predictions", len(predictions))
            
            # Finalisation
            metrics.finalize("success")
            metrics.save_report()
            log_pipeline_end("NBA-25: PIPELINE ML AUTOMATISÉ", "success")
            
        except Exception as e:
            metrics.record_error("PipelineError", str(e))
            metrics.finalize("failure")
            metrics.save_report()
            alert_on_pipeline_failure("nba25_auto_pipeline", str(e), "pipeline_execution")
            log_pipeline_end("NBA-25: PIPELINE ML AUTOMATISÉ", "failure")
```

### Drift Monitoring (NBA-22)

Le monitoring de drift déclenche automatiquement des alertes.

```python
# Dans drift_monitoring.py
from src.utils import alert_on_drift, alert_on_performance_degradation

class DataDriftMonitor:
    def detect_feature_drift(self, ...):
        # ... détection drift ...
        
        if result['drift_detected']:
            for feat in drifted_features:
                alert_on_drift(feat['feature'], feat['p_value'], self.alert_threshold)
    
    def check_performance_degradation(self, ...):
        # ... check performance ...
        
        if result['degradation_detected']:
            alert_on_performance_degradation(
                "accuracy", current_acc, global_acc, 10.0
            )
```

---

## 📊 Dashboard Monitoring

### Voir les métriques

```bash
# Lister tous les rapports de métriques
ls -lt logs/metrics/

# Voir le dernier rapport
cat logs/metrics/$(ls -t logs/metrics/ | head -1)

# Suivre en temps réel
tail -f logs/metrics/*.json
```

### Voir les alertes

```bash
# Voir toutes les alertes
cat logs/alerts.log

# Voir les alertes récentes
tail -n 50 logs/alerts.log

# Suivre en temps réel
tail -f logs/alerts.log

# Filtrer par sévérité
grep "ERROR" logs/alerts.log
grep "WARNING" logs/alerts.log
```

### Voir les rapports qualité

```bash
# Lister les rapports qualité
ls -lt logs/quality/

# Voir le dernier rapport
cat logs/quality/$(ls -t logs/quality/ | head -1)
```

---

## ⚙️ Configuration

### monitoring.yaml

**Localisation :** `configs/monitoring.yaml`

**Sections principales :**

```yaml
monitoring:
  logging:
    level: INFO
    format: json
    rotation: daily
    retention_days: 30
    
  metrics:
    enabled: true
    collect_timing: true
    collect_volume: true
    thresholds:
      max_pipeline_duration_seconds: 3600
      max_error_rate: 0.05
      
  quality:
    enabled: true
    thresholds:
      bronze:
        min_completion_rate: 0.30
      silver:
        max_null_rate: 0.20
      gold:
        max_nan_rate: 0.01
        
  alerts:
    enabled: true
    channels:
      log:
        enabled: true
        file: logs/alerts.log
      console:
        enabled: true
        min_severity: error
```

---

## 🧪 Tests

### Tests ML Pipeline

**Fichier :** `tests/test_ml_pipeline_critical.py`

```bash
# Exécuter tous les tests
pytest tests/test_ml_pipeline_critical.py -v

# Exécuter une classe de tests spécifique
pytest tests/test_ml_pipeline_critical.py::TestOptimizedTrainer -v

# Exécuter un test spécifique
pytest tests/test_ml_pipeline_critical.py::TestOptimizedTrainer::test_trainer_initialization -v
```

**Couverture :**
- Entraînement optimisé
- Détection de drift
- Calibration des probabilités
- Sélection de features
- Pipeline quotidien
- Flux end-to-end

---

## 📈 Métriques Clés

### Performance Pipeline

| Métrique | Seuil d'alerte | Description |
|----------|----------------|-------------|
| Pipeline duration | > 1h | Temps total d'exécution |
| Phase timing | Variable | Temps par étape |
| Error rate | > 5% | Taux d'erreurs |

### Qualité Données

| Couche | Complétion | Nulls | Statut |
|--------|------------|-------|--------|
| Bronze | > 30% | < 70% | ✓ |
| Silver | > 80% | < 20% | ✓ |
| Gold | > 95% | < 1% | ✓ |

### Performance ML

| Métrique | Baseline | Seuil alerte |
|----------|----------|--------------|
| Accuracy | 76.76% | -5% |
| AUC | 84.93% | -3% |
| Brier Score | 0.15 | +10% |

---

## 🚨 Alertes Importantes

### Drift Détecté
**Cause :** Distribution des features change significativement  
**Action :** Réentraîner le modèle avec nouvelles données

### Performance Dégradée
**Cause :** Accuracy baisse de > 5% vs baseline  
**Action :** Vérifier data quality, réentraîner si nécessaire

### Pipeline Failure
**Cause :** Exception non gérée dans le pipeline  
**Action :** Vérifier logs, corriger erreur, relancer

### Quality Check Failed
**Cause :** Données ne respectent pas les seuils qualité  
**Action :** Vérifier source données, corriger anomalies

---

## 🔗 Ressources

- **Code source :** `src/utils/monitoring.py`, `src/utils/alerts.py`
- **Tests :** `tests/test_ml_pipeline_critical.py`
- **Configuration :** `configs/monitoring.yaml`
- **Documentation API :** `src/utils/__init__.py`

---

**Dernière mise à jour :** 8 Février 2026  
**Version :** 1.0  
**Auteur :** Agent/Data Engineer
