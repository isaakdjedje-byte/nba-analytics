---
Story: NBA-30
Epic: Reporting & Visualization (NBA-10)
Points: 3
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-30: Rapport hebdomadaire automatique

## 📋 Description

Générer un rapport automatique des top joueurs de la semaine avec calcul des meilleurs performers et export CSV daté.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-18** : Métriques avancées
- ✅ **NBA-24** : Détection progression

## ✅ Critères d'acceptation

### 1. Script weekly_report.py créé

```python
#!/usr/bin/env python3
"""Génération rapport hebdomadaire automatique"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc, row_number
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import json

class WeeklyReportGenerator:
    """Générateur de rapport hebdomadaire"""
    
    def __init__(self):
        self.spark = SparkSession.builder.getOrCreate()
        self.report_date = datetime.now()
    
    def get_top_scorers(self, n=10):
        """Top 10 meilleurs scorers de la semaine"""
        
        df = spark.read.format("delta").load("data/silver/players_advanced/")
        
        # Filtrer semaine courante
        week_ago = self.report_date - timedelta(days=7)
        df_week = df.filter(col("last_game_date") >= week_ago)
        
        # Top scorers
        top_scorers = (df_week
            .select("id", "full_name", "team", "pts", "per")
            .orderBy(desc("pts"))
            .limit(n)
        )
        
        return top_scorers
    
    def get_most_efficient(self, n=10):
        """Top 10 joueurs les plus efficaces (PER)"""
        
        df = spark.read.format("delta").load("data/silver/players_advanced/")
        
        most_efficient = (df
            .select("id", "full_name", "team", "per", "ts_pct")
            .orderBy(desc("per"))
            .limit(n)
        )
        
        return most_efficient
    
    def get_rising_stars(self, n=10):
        """Top 10 joueurs en progression"""
        
        # Utiliser NBA-24
        from src.ml.detect_progression import get_top_rising_stars
        return get_top_rising_stars(n)
    
    def generate_report(self):
        """Générer rapport complet"""
        
        report = {
            "report_date": self.report_date.isoformat(),
            "week_of": (self.report_date - timedelta(days=7)).strftime("%Y-%m-%d"),
            "top_scorers": [row.asDict() for row in self.get_top_scorers(10).collect()],
            "most_efficient": [row.asDict() for row in self.get_most_efficient(10).collect()],
            "rising_stars": [row.asDict() for row in self.get_rising_stars(10).collect()]
        }
        
        return report
    
    def save_report(self, report):
        """Sauvegarder rapport"""
        
        # JSON
        json_path = f"reports/weekly_report_{self.report_date.strftime('%Y%m%d')}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # CSV pour top scorers
        csv_path = f"reports/top_scorers_{self.report_date.strftime('%Y%m%d')}.csv"
        self.get_top_scorers(10).toPandas().to_csv(csv_path, index=False)
        
        print(f"✅ Rapport sauvegardé: {json_path}")
        return json_path, csv_path

# Point d'entrée
def main():
    generator = WeeklyReportGenerator()
    report = generator.generate_report()
    generator.save_report(report)
    
    print("✅ Rapport hebdomadaire généré!")

if __name__ == "__main__":
    main()
```

---

### 2. Top 10 joueurs calculé correctement

**Critères de sélection:**
- **Top Scorers**: Moyenne points sur la semaine
- **Most Efficient**: PER (Player Efficiency Rating)
- **Rising Stars**: Progression vs moyenne carrière

---

### 3. Export CSV daté dans reports/

Format: `reports/weekly_report_YYYYMMDD.csv`

---

### 4. Planification configurée (cron/scheduler)

**Crontab:**
```bash
# Tous les lundis à 9h
0 9 * * 1 cd /path/to/nba-analytics && python src/reporting/weekly_report.py
```

**Ou avec Python schedule:**
```python
import schedule
import time

def job():
    main()

# Tous les lundis à 9h
schedule.every().monday.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

### 5. Email de notification optionnel

```python
def send_report_email(report_path):
    """Envoyer rapport par email"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    
    msg = MIMEMultipart()
    msg['From'] = 'nba-analytics@example.com'
    msg['To'] = 'manager@example.com'
    msg['Subject'] = f'NBA Weekly Report - {datetime.now().strftime("%Y-%m-%d")}'
    
    # Attacher fichier
    with open(report_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {os.path.basename(report_path)}"
    )
    msg.attach(part)
    
    # Envoyer
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    server.send_message(msg)
    server.quit()
```

## 📦 Livrables

- ✅ `src/reporting/weekly_report.py`
- ✅ `reports/weekly_report_YYYYMMDD.json`
- ✅ `reports/top_scorers_YYYYMMDD.csv`
- ✅ Crontab configuré

## 🎯 Definition of Done

- [ ] Script weekly_report.py créé
- [ ] Top 10 scorers calculés
- [ ] Top 10 efficaces calculés
- [ ] Rapport exporté CSV daté
- [ ] Planification configurée (cron)
- [ ] Email de notification (optionnel)
