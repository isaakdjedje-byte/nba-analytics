# 🎰 Guide du Betting System NBA

**Dernière mise à jour :** 9 Février 2026  
**Version :** 1.0.0  
**Statut :** ✅ Production Ready

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation et Configuration](#installation-et-configuration)
3. [Démarrage Rapide](#démarrage-rapide)
4. [Profils de Risque](#profils-de-risque)
5. [Stratégies de Mise](#stratégies-de-mise)
6. [Paper Trading](#paper-trading)
7. [API et Intégrations](#api-et-intégrations)
8. [Dashboard](#dashboard)
9. [Planification Automatique](#planification-automatique)
10. [FAQ et Dépannage](#faq-et-dépannage)

---

## Vue d'ensemble

Le **Betting System NBA** est un système de paris sportifs professionnel intégré à la plateforme NBA Analytics. Il combine :

- 🎯 **Prédictions ML** à 83.03% d'accuracy
- 💰 **Gestion de bankroll** avec 3 profils de risque
- 📊 **5 stratégies de mise** optimisées
- 🔍 **Détection de value bets** automatique
- 📧 **Alertes email** en temps réel
- 📈 **Dashboard interactif** avec visualisations

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BETTING SYSTEM                       │
├─────────────────────────────────────────────────────────┤
│  BettingSystem (hérite ROITracker)                      │
│  ├── Bankroll (3 profils: Conservative/Moderate/Aggressive)│
│  ├── 5 Stratégies de mise (Flat, Kelly, Confidence, Value, Martingale)│
│  ├── OddsClient (The Odds API)                          │
│  └── AlertManager (email notifications)                 │
├─────────────────────────────────────────────────────────┤
│  WeeklyBettingReport                                    │
│  ├── Export JSON/CSV/HTML                               │
│  └── Envoi email automatique                            │
├─────────────────────────────────────────────────────────┤
│  BettingScheduler                                       │
│  ├── 9h: Mise à jour matinale (value bets)              │
│  ├── 18h: Mise à jour soir (résultats)                  │
│  └── Lundi: Rapport hebdomadaire                        │
└─────────────────────────────────────────────────────────┘
```

---

## Installation et Configuration

### Prérequis

- Python 3.11+
- Le projet NBA Analytics installé
- Jupyter (pour le dashboard)

### Configuration

1. **Créer le fichier `.env`** :

```bash
# API The Odds API (optionnel - mode simulation disponible)
ODDS_API_KEY=votre_cle_api_ici

# Email pour notifications
ALERT_EMAIL=isaakdjedje@gmail.com

# Configuration par défaut
INITIAL_BANKROLL=100
RISK_PROFILE=moderate
```

2. **Obtenir une clé API The Odds API** (gratuit) :
   - Aller sur https://the-odds-api.com
   - Créer un compte gratuit
   - Copier la clé API dans le fichier `.env`
   - 500 requêtes/mois gratuites

---

## Démarrage Rapide

### 1. Initialiser le système

```python
from src.betting import BettingSystem

# Initialise avec 100€ et profil modéré
betting = BettingSystem(
    initial_bankroll=100.0,
    risk_profile='moderate',
    email='isaakdjedje@gmail.com'
)

print(f"Bankroll: {betting.bankroll.current_amount}€")
print(f"Profil: {betting.bankroll.risk_profile}")
print(f"Mise min-max: {betting.bankroll.get_stake_range()}")
```

### 2. Trouver les value bets

```python
# Cherche les paris avec edge > 5%
for prediction, edge, odds in betting.find_value_bets(min_edge=0.05):
    stake = betting.calculate_stake(prediction, strategy='kelly', bookmaker_odds=odds)
    
    print(f"🎯 {prediction['home_team']} vs {prediction['away_team']}")
    print(f"   Prédiction: {prediction['prediction']}")
    print(f"   Confiance: {prediction.get('confidence', 0):.0%}")
    print(f"   Edge: {edge:.1%}")
    print(f"   Cote: {odds:.2f}")
    print(f"   💰 Mise recommandée: {stake:.2f}€")
```

### 3. Simuler un pari

```python
# Enregistre un pari pour paper trading
betting.bankroll.record_bet(
    stake=2.0,
    result='win',  # ou 'loss'
    odds=1.85
)

# Vérifie le résultat
summary = betting.bankroll.get_summary()
print(f"Balance: {summary['current']:.2f}€")
print(f"P&L: {summary['profit_loss']:+.2f}€")
print(f"ROI: {summary['roi_pct']:+.1f}%")
```

### 4. Générer un rapport

```python
from src.reporting.weekly_betting_report import WeeklyBettingReport

report_gen = WeeklyBettingReport(betting)
files = report_gen.generate_and_save()

print(f"Rapport généré:")
print(f"  JSON: {files['json']}")
print(f"  CSV: {files['csv']}")
print(f"  HTML: {files['html']}")
```

---

## Profils de Risque

### 🛡️ Conservateur

```python
betting = BettingSystem(initial_bankroll=100.0, risk_profile='conservative')
```

| Paramètre | Valeur |
|-----------|--------|
| Mise base | 1% (1€) |
| Mise max | 2% (2€) |
| Stop-loss | -10€ |
| Objectif ROI | +5% mensuel |
| Confiance min | 70% |

**Recommandé pour :** Débutants, capital faible, aversion au risque

### ⚖️ Modéré (Recommandé)

```python
betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
```

| Paramètre | Valeur |
|-----------|--------|
| Mise base | 2% (2€) |
| Mise max | 4% (4€) |
| Stop-loss | -20€ |
| Objectif ROI | +10% mensuel |
| Confiance min | 65% |

**Recommandé pour :** Utilisateurs expérimentés, équilibre risque/rendement

### 🚀 Agressif

```python
betting = BettingSystem(initial_bankroll=100.0, risk_profile='aggressive')
```

| Paramètre | Valeur |
|-----------|--------|
| Mise base | 5% (5€) |
| Mise max | 10% (10€) |
| Stop-loss | -30€ |
| Objectif ROI | +20% mensuel |
| Confiance min | 60% |

**Recommandé pour :** Traders expérimentés, haute tolérance au risque

---

## Stratégies de Mise

### 1. Flat Betting

Mise fixe en pourcentage de la bankroll.

```python
stake = betting.calculate_stake(prediction, strategy='flat')
# Toujours 1%, 2% ou 5% selon le profil
```

**Avantages :** Simple, stable, prévisible  
**Inconvénients :** N'optimise pas les opportunités

### 2. Kelly Criterion (Recommandé)

Mise optimale calculée mathématiquement.

```python
stake = betting.calculate_stake(
    prediction, 
    strategy='kelly',
    bookmaker_odds=1.85
)
```

**Formule :** `f* = (bp - q) / b`  
**Avantages :** Optimale à long terme, maximise la croissance  
**Inconvénients :** Volatilité, peut recommander des mises agressives

### 3. Confidence-Weighted

Mise proportionnelle à la confiance du modèle ML.

```python
stake = betting.calculate_stake(prediction, strategy='confidence')
```

**Avantages :** Alignée avec la qualité des prédictions  
**Inconvénients :** Dépend de la calibration du modèle

### 4. Value Betting

Mise uniquement si edge significatif (> 5%).

```python
stake = betting.calculate_stake(
    prediction,
    strategy='value',
    bookmaker_odds=1.85
)
# Retourne 0 si edge < 5%
```

**Avantages :** Discipline, positive EV garantie  
**Inconvénients :** Moins d'opportunités

### 5. Martingale (⚠️ Risqué)

Augmente la mise après une perte.

```python
stake = betting.calculate_stake(prediction, strategy='martingale')
```

**⚠️ Attention :** Très risqué, peut vider la bankroll rapidement  
**Recommandé uniquement pour :** Tests, très petites mises

---

## Paper Trading

Le **paper trading** permet de tester le système sans risquer d'argent réel.

### Workflow Recommandé

#### 1. Initialisation

```bash
# Crée l'état initial
python -c "
from src.betting import BettingSystem
import json
from pathlib import Path

betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
betting.save_betting_state('predictions/paper_trading_state.json')
print('✅ Paper trading initialisé')
"
```

#### 2. Quotidien - Matin (9h)

```python
# Charge le système
betting = BettingSystem(initial_bankroll=100.0, risk_profile='moderate')
betting.load_betting_state('predictions/paper_trading_state.json')

# Cherche les opportunités
value_bets = list(betting.find_value_bets(min_edge=0.05))

# Enregistre tes paris dans un fichier
import json
from datetime import datetime

bets = []
for pred, edge, odds in value_bets[:3]:  # Top 3
    bets.append({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'match': f"{pred['home_team']} vs {pred['away_team']}",
        'prediction': pred['prediction'],
        'edge': edge,
        'odds': odds,
        'stake': betting.calculate_stake(pred, 'kelly', odds),
        'status': 'PENDING'
    })

with open('predictions/today_bets.json', 'w') as f:
    json.dump(bets, f, indent=2)
```

#### 3. Quotidien - Soir (18h)

```python
# Mets à jour les résultats
with open('predictions/today_bets.json') as f:
    bets = json.load(f)

for bet in bets:
    # Vérifie le résultat réel
    result = input(f"{bet['match']} - Résultat (win/loss)? ")
    
    if result == 'win':
        betting.bankroll.record_bet(bet['stake'], 'win', bet['odds'])
        bet['profit'] = bet['stake'] * (bet['odds'] - 1)
    else:
        betting.bankroll.record_bet(bet['stake'], 'loss')
        bet['profit'] = -bet['stake']
    
    bet['status'] = 'COMPLETED'

# Sauvegarde
betting.save_betting_state('predictions/paper_trading_state.json')

# Affiche le résumé
summary = betting.bankroll.get_summary()
print(f"\n📊 Aujourd'hui:")
print(f"   Balance: {summary['current']:.2f}€")
print(f"   ROI: {summary['roi_pct']:+.1f}%")
```

#### 4. Hebdomadaire - Lundi

```python
from src.reporting.weekly_betting_report import WeeklyBettingReport

report_gen = WeeklyBettingReport(betting)
files = report_gen.generate_and_save()

# Optionnel : envoie par email
report_gen.send_email_report()
```

### Durée Recommandée

| Phase | Durée | Objectif |
|-------|-------|----------|
| Test initial | 1 semaine | Vérifier le fonctionnement |
| Validation | 2-4 semaines | Atteindre ROI > 5% |
| Long terme | 3+ mois | Valider la robustesse |

### Métriques à Suivre

- **Win rate** : % de paris gagnants (objectif > 55%)
- **ROI** : Retour sur investissement (objectif > 10% mensuel)
- **Max drawdown** : Perte maximale (doit être < stop-loss)
- **Sharpe ratio** : Rendement ajusté au risque

---

## API et Intégrations

### The Odds API

**Site :** https://the-odds-api.com

**Plan Gratuit :**
- 500 requêtes/mois
- NBA temps réel
- Moneylines, spreads, totals
- 20+ bookmakers

**Configuration :**

```python
from src.betting import OddsClient

# Avec clé API
client = OddsClient(api_key='votre_cle')

# Sans clé API (mode simulation)
client = OddsClient()  # Utilise des cotes simulées réalistes

# Récupère les cotes
odds = client.get_odds('Boston Celtics', 'Lakers')
print(f"Cote: {odds}")

# Stats d'utilisation
print(client.get_usage_stats())
```

### Alertes Email

Configuration dans `.env` :

```bash
ALERT_EMAIL=isaakdjedje@gmail.com
```

Types d'alertes :
- ✅ Value bets > 10% edge
- ⚠️ Stop-loss atteint
- 📊 Rapport hebdomadaire
- ❌ Erreurs système

---

## Dashboard

### Lancement

```bash
jupyter notebook notebooks/02_betting_dashboard.ipynb
```

### Fonctionnalités

1. **Configuration interactive**
   - Sélection profil de risque
   - Configuration bankroll
   - Choix stratégie

2. **Vue d'ensemble**
   - Évolution bankroll (graphique temps réel)
   - Pari gagnants/perdants
   - Métriques clés

3. **Value Bets**
   - Tableau filtrable
   - Edge et cotes
   - Mises recommandées

4. **Analyses**
   - Comparaison stratégies
   - Performance par seuil de confiance
   - Classement bookmakers

5. **Rapports**
   - Génération depuis le dashboard
   - Envoi email

---

## Planification Automatique

### Installation

**Linux/Mac (Cron) :**

```bash
# Édite le crontab
crontab -e

# Ajoute ces lignes
# Mise à jour matinale (9h)
0 9 * * * cd /chemin/vers/nba-analytics && python scripts/schedule_betting_updates.py --type=morning

# Mise à jour soir (18h)
0 18 * * * cd /chemin/vers/nba-analytics && python scripts/schedule_betting_updates.py --type=evening

# Rapport hebdomadaire (lundi 9h)
0 9 * * 1 cd /chemin/vers/nba-analytics && python scripts/schedule_betting_updates.py --type=weekly
```

**Windows (Planificateur de tâches) :**

```batch
# Crée un fichier setup_betting_schedule.bat
schtasks /create /tn "NBA_Betting_Morning" /tr "python C:\path\to\nba-analytics\scripts\schedule_betting_updates.py --type=morning" /sc daily /st 09:00

schtasks /create /tn "NBA_Betting_Evening" /tr "python C:\path\to\nba-analytics\scripts\schedule_betting_updates.py --type=evening" /sc daily /st 18:00

schtasks /create /tn "NBA_Betting_Weekly" /tr "python C:\path\to\nba-analytics\scripts\schedule_betting_updates.py --type=weekly" /sc weekly /d MON /st 09:00
```

### Exécution Manuelle

```bash
# Mise à jour matinale
python scripts/schedule_betting_updates.py --type=morning

# Mise à jour soir
python scripts/schedule_betting_updates.py --type=evening

# Rapport hebdomadaire
python scripts/schedule_betting_updates.py --type=weekly

# Tout exécuter
python scripts/schedule_betting_updates.py --type=all
```

---

## FAQ et Dépannage

### Q: Le système fonctionne-t-il sans clé API ?

**R :** Oui ! En mode simulation, les cotes sont générées de manière réaliste basée sur :
- Avantage domicile (5%)
- Force des équipes
- Variance aléatoire

### Q: Combien de paris par jour ?

**R :** Dépend des opportunités. Typiquement :
- 0-3 value bets par jour
- Seulement si edge > 5%
- Qualité > Quantité

### Q: Quand passer en mode réel ?

**R :** Recommandations :
- Minimum 50 paris en paper trading
- Win rate > 55%
- ROI > 5% sur 1 mois
- Max drawdown < 20%
- Comprendre parfaitement le système

### Q: Le Kelly Criterion est-il trop agressif ?

**R :** Le système utilise un **Kelly fractionnel** (1/4 Kelly) pour réduire la volatilité :
- Kelly plein : trop volatile
- 1/4 Kelly : optimal pour la plupart
- Jamais plus que le max du profil

### Q: Que faire si le stop-loss est atteint ?

**R :** 
1. Arrêter immédiatement les paris
2. Analyser les causes
3. Vérifier les modèles ML
4. Attendre 1 semaine avant de reprendre
5. Réduire les mises de moitié

### Q: Les cotes changent-elles ?

**R :** Oui ! Le système :
- Met en cache les cotes 2 heures
- Rafraîchit automatiquement
- Compare avec les prédictions ML
- Alerte si drift important

### Q: Comment contribuer ?

**R :** Le système est extensible :
- Ajouter des stratégies dans `betting_system.py`
- Intégrer d'autres bookmakers
- Créer de nouvelles visualisations
- Améliorer les algorithmes

---

## Ressources

### Documentation

- [INDEX.md](INDEX.md) - Index de navigation
- [JIRA_BACKLOG.md](JIRA_BACKLOG.md) - Tickets et planning
- [memoir.md](memoir.md) - Journal du projet

### Code Source

- `src/betting/betting_system.py` - Classe principale
- `src/betting/odds_client.py` - Client API
- `src/reporting/weekly_betting_report.py` - Rapports
- `scripts/schedule_betting_updates.py` - Planification

### Notebooks

- `notebooks/02_betting_dashboard.ipynb` - Dashboard interactif

---

## Support

**Email :** isaakdjedje@gmail.com

**Problèmes ?**
1. Vérifier les logs dans `logs/betting_scheduler.log`
2. Consulter la [FAQ](#faq-et-dépannage)
3. Ouvrir une issue sur GitHub

---

**Bonne chance avec vos paris ! 🍀**

*Disclaimer : Ce système est fourni à des fins éducatives. Les paris sportifs comportent des risques. Ne pariez jamais plus que vous ne pouvez perdre.*
