---
Story: NBA-31
Epic: Reporting & Visualization (NBA-10)
Points: 5
Statut: To Do
Priorité: Medium
Assigné: Isaak
Créé: 05/Feb/26
---

# 🎯 NBA-31: Dashboard interactif

## 📋 Description

Créer un dashboard Jupyter interactif avec visualisations des analytics NBA, graphiques des top joueurs et filtres par équipe/saison.

## 🔗 Dépendances

### Dépend de:
- ✅ **NBA-18** : Métriques
- ✅ **NBA-22** : ML
- ✅ **NBA-23** : Clustering

## ✅ Critères d'acceptation

### 1. Notebook Jupyter avec visualisations

**notebooks/01_nba_dashboard.ipynb:**

```python
# Cell 1: Setup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Cell 2: Charger données
@interact
def load_data(season=['2023-24', '2022-23', 'All']):
    df = spark.read.format("delta").load("data/silver/players_advanced/")
    if season != 'All':
        df = df.filter(col("season") == season)
    return df.toPandas()

# Cell 3: Top joueurs interactif
from ipywidgets import interact

@interact
def show_top_players(metric=['pts', 'per', 'ts_pct'], n=(5, 50, 5)):
    df = load_data('2023-24')
    top = df.nlargest(n, metric)
    
    fig = px.bar(top, x='full_name', y=metric, 
                 title=f'Top {n} joueurs - {metric.upper()}')
    fig.show()

# Cell 4: Scatter plot interactif
@interact
def scatter_plot(x=['pts', 'per'], y=['ts_pct', 'reb'], 
                 team=['All'] + list(teams)):
    df = load_data('2023-24')
    if team != 'All':
        df = df[df['team'] == team]
    
    fig = px.scatter(df, x=x, y=y, hover_data=['full_name'],
                     title=f'{x.upper()} vs {y.upper()}')
    fig.show()
```

---

### 2. Graphiques : top joueurs, tendances, comparaisons

**Types de graphiques:**
- **Bar charts**: Top scorers, meilleur PER
- **Scatter plots**: Corrélation stats (PTS vs TS%)
- **Line charts**: Tendances sur plusieurs saisons
- **Heatmaps**: Comparaison équipes
- **Box plots**: Distribution métriques

---

### 3. Interactif (filtres par équipe, saison)

**Widgets interactifs:**
```python
from ipywidgets import widgets

# Filtre équipe
team_dropdown = widgets.Dropdown(
    options=['All', 'LAL', 'GSW', 'BOS', ...],
    value='All',
    description='Équipe:'
)

# Filtre saison
season_slider = widgets.SelectionSlider(
    options=['2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24'],
    value='2023-24',
    description='Saison'
)

# Filtre métrique
metric_dropdown = widgets.Dropdown(
    options=['pts', 'reb', 'ast', 'per', 'ts_pct'],
    value='pts',
    description='Métrique:'
)
```

---

### 4. Export images/PDF possible

```python
# Export PNG
fig.write_image("exports/top_scorers.png", width=1200, height=800)

# Export PDF
!jupyter nbconvert --to pdf notebooks/01_nba_dashboard.ipynb

# Export HTML interactif
!jupyter nbconvert --to html notebooks/01_nba_dashboard.ipynb
```

## 📦 Livrables

- ✅ `notebooks/01_nba_dashboard.ipynb`
- ✅ `notebooks/02_ml_analysis.ipynb`
- ✅ `notebooks/03_clustering_viz.ipynb`
- ✅ `exports/*.png` - Graphiques exportés

## 🎯 Definition of Done

- [ ] Notebook interactif créé
- [ ] 5+ types de visualisations
- [ ] Filtres équipe/saison fonctionnels
- [ ] Export PNG/PDF fonctionnel
- [ ] Documenté et reproductible
