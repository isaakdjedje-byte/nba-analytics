---
Story: NBA-28
Epic: Data Quality & Monitoring (NBA-9)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-28: Monitoring et alerting

## 📋 Description

Mettre en place le monitoring du pipeline avec logging structuré, alertes en cas d'erreurs et dashboard des métriques.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-26** : Tests
- ✅ **NBA-27** : Data Quality

## ✅ Critères d'acceptation

### 1. Logging structuré avec timestamps

```python
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

class StructuredLogger:
    """Logger avec format JSON structuré"""
    
    def __init__(self, name="nba_pipeline"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Handler fichier JSON
        logHandler = logging.FileHandler("logs/pipeline.json")
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        self.logger.addHandler(logHandler)
        
        # Handler console
        consoleHandler = logging.StreamHandler()
        self.logger.addHandler(consoleHandler)
    
    def log_event(self, event_type, data):
        """Log événement structuré"""
        self.logger.info("Pipeline Event", extra={
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        })
    
    def log_error(self, error, context):
        """Log erreur avec contexte"""
        self.logger.error("Pipeline Error", extra={
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "context": context
        })

# Utilisation
logger = StructuredLogger()
logger.log_event("INGESTION_START", {"season": "2023-24"})
logger.log_event("INGESTION_END", {"records": 1230, "duration": 45.2})
```

---

### 2. Alertes si erreurs détectées

```python
import smtplib
from email.mime.text import MIMEText
import os

class AlertManager:
    """Gestion des alertes"""
    
    def __init__(self):
        self.email_enabled = os.getenv("ALERT_EMAIL_ENABLED", "false") == "true"
        self.slack_enabled = os.getenv("ALERT_SLACK_ENABLED", "false") == "true"
    
    def send_alert(self, level, message, details):
        """Envoyer alerte selon niveau"""
        
        if level == "CRITICAL":
            self._send_email_alert(message, details)
            self._send_slack_alert(message, details)
        elif level == "WARNING":
            self._send_slack_alert(message, details)
        
        # Toujours logger
        print(f"🚨 ALERT [{level}]: {message}")
    
    def _send_email_alert(self, message, details):
        """Envoyer email d'alerte"""
        if not self.email_enabled:
            return
        
        msg = MIMEText(f"{message}\n\nDetails: {json.dumps(details, indent=2)}")
        msg['Subject'] = f'[NBA-Analytics] ALERT: {message}'
        msg['From'] = 'alerts@nba-analytics.com'
        msg['To'] = 'admin@example.com'
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)
    
    def _send_slack_alert(self, message, details):
        """Envoyer message Slack"""
        if not self.slack_enabled:
            return
        
        import requests
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        payload = {
            "text": f"🚨 *NBA Pipeline Alert*\n{message}\n```{json.dumps(details, indent=2)}```"
        }
        
        requests.post(webhook_url, json=payload)

# Utilisation
alerts = AlertManager()
alerts.send_alert("CRITICAL", "Pipeline failed", {"error": "Out of memory", "stage": "NBA-18"})
```

---

### 3. Dashboard métriques

**Métriques à suivre:**
- Temps de traitement par étape
- Nombre de records traités
- Taux d'erreur
- Utilisation ressources (CPU, RAM)

```python
class MetricsCollector:
    """Collecter métriques pipeline"""
    
    def __init__(self):
        self.metrics = []
    
    def record_metric(self, stage, metric_name, value, unit=""):
        """Enregistrer métrique"""
        self.metrics.append({
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "metric": metric_name,
            "value": value,
            "unit": unit
        })
    
    def save_metrics(self):
        """Sauvegarder métriques"""
        with open("logs/metrics.json", "w") as f:
            json.dump(self.metrics, f, indent=2)

# Utilisation
metrics = MetricsCollector()
metrics.record_metric("NBA-17", "processing_time", 120.5, "seconds")
metrics.record_metric("NBA-17", "records_processed", 5103, "records")
metrics.save_metrics()
```

---

### 4. Gestion des erreurs avec retry logic

```python
import time
from functools import wraps

def retry_on_error(max_retries=3, delay=2):
    """Décorateur retry avec backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    
                    wait_time = delay * (2 ** retries)  # Exponentiel
                    print(f"⚠️ Retry {retries}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
            
            return None
        return wrapper
    return decorator

# Utilisation
@retry_on_error(max_retries=3, delay=2)
def fetch_api_data(endpoint):
    """Fetcher données API avec retry"""
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json()
```

## 📦 Livrables

- ✅ `src/monitoring/logger.py` - Logging structuré
- ✅ `src/monitoring/alerts.py` - Gestion alertes
- ✅ `src/monitoring/metrics.py` - Collecte métriques
- ✅ `src/utils/retry.py` - Retry decorator
- ✅ `logs/pipeline.json` - Logs structurés
- ✅ `logs/metrics.json` - Métriques

## 🎯 Definition of Done

- [ ] Logging JSON structuré implémenté
- [ ] Alertes email/Slack configurables
- [ ] Dashboard métriques (temps, records, erreurs)
- [ ] Retry logic sur appels API
- [ ] Monitoring temps réel ou batch
