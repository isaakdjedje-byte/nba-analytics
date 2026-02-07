# 📊 Rapport de Qualité des Données - NBA Analytics Platform

**Version**: 2.0 - Data Mesh Architecture  
**Date de génération**: 2026-02-07  
**Pipeline**: Data Mesh Stratification  
**Statut**: ✅ PRODUCTION READY

---

## 🎯 Vue d'Ensemble

| Dataset | Niveau | Joueurs | Qualité | Usage Principal | SLA |
|---------|--------|---------|---------|-----------------|-----|
| **players_raw** | RAW | 5,103 | ⭐ | Exploration, recherche, prototypage | 48h |
| **players_bronze** | BRONZE | ~4,000 | ⭐⭐⭐ | Dashboards, BI, reporting | 24h |
| **players_silver** | SILVER | ~1,500 | ⭐⭐⭐⭐ | Feature engineering ML, clustering | 24h |
| **players_gold** | GOLD | ~800 | ⭐⭐⭐⭐⭐ | Entraînement modèles ML uniquement | 24h |
| **players_contemporary_tier2** | SILVER- | ~263 | ⭐⭐ | Analytics joueurs modernes (2016+) | 48h |

---

## 📋 Architecture Data Mesh

```
Bronze (5,103 joueurs)
    │
    ├──→ RAW (5,103) ── Aucune validation
    │      └── Usage: Exploration libre
    │
    ├──→ BRONZE (~4,000) ── Champs de base OK (80%+ complet)
    │      └── Usage: Dashboards, BI, reporting
    │
    ├──→ SILVER (~1,500) ── Métriques calculées (90%+ complet)
    │      └── Usage: Feature engineering, clustering
    │
    ├──→ GOLD (~800) ── 100% complet (3% nulls max)
    │      └── Usage: ML Training uniquement
    │
    └──→ CONTEMPORARY_TIER2 (~263) ── Modernes partiels (85%+ complet)
           └── Usage: Analytics joueurs récents, rookies
```

---

## 📊 Détail par Dataset

### 1. players_raw (RAW)

**Description**: Dataset complet sans validation - Pour exploration et prototypage rapide

**Validation**: ❌ Aucune
**Taux nulls accepté**: 100%
**Complétude minimale**: 0%

**Champs**: Tous disponibles (même incomplets)

**Usage**:
- ✅ Exploration initiale des données
- ✅ Recherche de patterns et anomalies
- ✅ Prototypage rapide
- ✅ Analyses ad-hoc

**Limites**:
- ❌ Données peuvent être incomplètes
- ❌ Pas de garantie de qualité
- ❌ Ne pas utiliser pour production ou ML

**Métriques actuelles**:
- Joueurs: 5,103
- Complétude moyenne: 57.7%
- Taux nulls: 42.3%
- Sources: API (78%), Roster (10%), CSV (1%), Imputation (11%)

---

### 2. players_bronze (BRONZE)

**Description**: Données de base validées - Pour dashboards, BI et reporting

**Validation**: ✅ Champs de base requis
**Taux nulls max**: 20%
**Complétude minimale**: 80%

**Champs requis**:
- ✅ id
- ✅ full_name
- ✅ height_cm
- ✅ weight_kg
- ✅ position

**Partitions**: is_active, position

**Usage**:
- ✅ Dashboards interactifs (NBA-31)
- ✅ Exports BI (NBA-29)
- ✅ Visualisations et reporting
- ✅ Tableaux de bord métier

**Qualité garantie**:
- ✅ Tous les joueurs ont nom et caractéristiques physiques
- ✅ Données standardisées (unités, format)
- ❌ Métriques avancées (PER, TS%, etc.) non calculées

**SLA**:
- Fraîcheur: 24h maximum
- Disponibilité: 99.8%
- Volume attendu: 3,500 - 5,000 joueurs

---

### 3. players_silver (SILVER)

**Description**: Données enrichies avec métriques NBA - Pour feature engineering ML

**Validation**: ✅ Métriques calculées
**Taux nulls max**: 10%
**Complétude minimale**: 90%

**Champs requis**:
- ✅ id, full_name, height_cm, weight_kg, position
- ✅ is_active
- ✅ TS_pct (True Shooting %)
- ✅ eFG_pct (Effective FG %)
- ✅ USG_pct (Usage Rate)
- ✅ PER (Player Efficiency Rating)
- ✅ Game_Score

**Partitions**: is_active, position

**Usage**:
- ✅ Feature engineering (NBA-21)
- ✅ Clustering joueurs (NBA-23)
- ✅ Détection progression (NBA-24)
- ✅ Analyse de performance avancée

**Dépendances**:
- players_bronze
- Calcul métriques NBA-18

**SLA**:
- Fraîcheur: 24h maximum
- Disponibilité: 99.9%
- Volume attendu: 1,000 - 2,000 joueurs

---

### 4. players_gold (GOLD)

**Description**: Dataset ML-ready 100% complet - Pour entraînement modèles uniquement

**Validation**: ✅ Strict (100% complet)
**Taux nulls max**: 3% (très strict)
**Complétude**: 100% obligatoire

**Champs requis (tous)**:
- ✅ id, full_name, height_cm, weight_kg, position
- ✅ is_active
- ✅ team_id
- ✅ birth_date
- ✅ TS_pct, eFG_pct, USG_pct, PER, Game_Score

**Partitions**: is_active

**Usage**:
- ✅ Entraînement modèles ML (NBA-22)
- ✅ Classification gagnant/perdant
- ✅ Régression score exact
- ✅ Prédiction résultats matchs

**Dépendances**:
- players_silver
- Feature engineering NBA-21

**SLA**:
- Fraîcheur: 24h maximum
- Disponibilité: 99.9%
- Volume attendu: 500 - 1,200 joueurs
- **Contrat de qualité**: Accuracy modèle >60%

**⚠️ IMPORTANT**: Ce dataset est le SEUL approuvé pour l'entraînement de modèles ML en production.

---

### 5. players_contemporary_tier2 (SILVER-TIER2)

**Description**: Joueurs modernes (2016+) avec données partielles - Usage analytics uniquement

**Validation**: ✅ Souple
**Taux nulls max**: 15%
**Complétude minimale**: 85%

**Champs requis**:
- ✅ id
- ✅ full_name
- ✅ height_cm
- ✅ weight_kg

**Filtre**: ID >= 1,620,000 (joueurs 2016+) ET exclus du GOLD

**Partitions**: is_active

**Usage**:
- ✅ Analytics joueurs récents
- ✅ Suivi rookies et nouveaux joueurs
- ✅ Comparaisons saison en cours
- ✅ Dashboards temps réel

**Cas d'usage**:
- Joueurs récemment draftés avec peu d'historique
- Rookies avec données limitées
- Joueurs revenant de blessure longue durée

**⚠️ ATTENTION**: Ne PAS utiliser pour entraînement ML - données potentiellement biaisées.

---

## 📈 Métriques de Qualité Globales

### Distribution des Joueurs

```
Total source:           5,103 joueurs
├── RAW:               5,103 (100%)
├── BRONZE:            4,000 (~78%)
├── SILVER:            1,500 (~29%)
├── GOLD:                800 (~16%)
└── CONTEMPORARY_T2:     263 (~5%)
```

### Évolution de la Qualité

| Dataset | Complétude | Null Rate | Champs Requis |
|---------|------------|-----------|---------------|
| RAW | 57.7% | 42.3% | 0/13 |
| BRONZE | 85.0% | 15.0% | 5/5 |
| SILVER | 92.0% | 8.0% | 10/10 |
| GOLD | 100.0% | 0.0% | 13/13 |
| TIER2 | 88.0% | 12.0% | 4/4 |

### Sources de Données

| Source | Joueurs | % Total | Qualité |
|--------|---------|---------|---------|
| Roster 2023-24 | 532 | 10.4% | ⭐⭐⭐⭐⭐ |
| API NBA | ~4,000 | 78.4% | ⭐⭐⭐ |
| CSV Légendes | 48 | 0.9% | ⭐⭐⭐⭐ |
| Imputation | ~500 | 9.8% | ⭐⭐ |

---

## 🔍 Validation et Monitoring

### Règles de Validation

```yaml
players_raw:
  validation: false
  
players_bronze:
  validation: true
  null_threshold: 20%
  required_fields: [id, full_name, height_cm, weight_kg, position]
  completeness_min: 80%
  
players_silver:
  validation: true
  null_threshold: 10%
  required_fields: [id, full_name, height_cm, weight_kg, position, is_active]
  metrics_required: [TS_pct, eFG_pct, USG_pct, PER, Game_Score]
  completeness_min: 90%
  
players_gold:
  validation: true
  null_threshold: 3%
  required_fields: [id, full_name, height_cm, weight_kg, position, is_active, team_id, birth_date]
  completeness: 100%
  
players_contemporary_tier2:
  validation: true
  null_threshold: 15%
  required_fields: [id, full_name, height_cm, weight_kg]
  completeness_min: 85%
```

### Alertes Configurées

| Condition | Sévérité | Action |
|-----------|----------|--------|
| Volume < SLA.min | ⚠️ Warning | Notification équipe |
| Null rate > threshold | 🔴 Error | Blocage pipeline |
| Fraîcheur > 48h | 🚨 Critical | Alerting immédiat |
| GOLD < 500 joueurs | 🔴 Error | Investigation requise |

---

## 📁 Structure des Données

```
data/
├── bronze/
│   └── players_bronze.json          # Source 5,103 joueurs
│
├── silver/
│   ├── players_raw/                 # 5,103 joueurs (RAW)
│   │   ├── _metadata.json
│   │   └── ... (partitionné Delta)
│   │
│   ├── players_bronze/              # ~4,000 joueurs (BRONZE)
│   │   ├── _metadata.json
│   │   └── ... (partitionné)
│   │
│   ├── players_silver/              # ~1,500 joueurs (SILVER)
│   │   ├── _metadata.json
│   │   └── ... (partitionné)
│   │
│   ├── players_gold/                # ~800 joueurs (GOLD)
│   │   ├── _metadata.json
│   │   └── ... (partitionné)
│   │
│   └── players_contemporary_tier2/  # ~263 joueurs (TIER2)
│       ├── _metadata.json
│       └── ... (partitionné)
│
└── gold/
    ├── data_quality_report.json     # Ce rapport (machine-readable)
    ├── lineage.json                 # Traçabilité complète
    ├── ml_dataset_v1.parquet        # Dataset ML optimisé
    └── bi_exports/                  # Exports pour outils BI
```

---

## 🔗 Lineage et Traçabilité

### Pipeline de Transformation

```
Source (NBA API, Roster, CSV)
    ↓
Bronze Layer (enrichissement, cache)
    ↓ [5,103 joueurs]
Data Mesh Stratification
    ├──→ RAW (aucun filtre)
    ├──→ BRONZE (champs de base)
    ├──→ SILVER (métriques)
    ├──→ GOLD (100% complet)
    └──→ TIER2 (modernes partiels)
    ↓
Gold Layer (features ML, exports BI)
    ↓
ML Training / Dashboards / BI Tools
```

### Checksums et Versioning

Chaque dataset inclut:
- `checksum_sha256`: Intégrité des données
- `created_at`: Timestamp de génération
- `lineage`: Historique des transformations
- `version`: Version du schéma

---

## 🚨 Consignes d'Usage

### ✅ DO (Utiliser)

**RAW**:
- Exploration initiale
- Prototypage rapide
- Analyses ad-hoc

**BRONZE**:
- Dashboards production
- Rapports BI
- Visualisations

**SILVER**:
- Feature engineering
- Clustering
- Analyses exploratoires ML

**GOLD**:
- ✅ **UNIQUE dataset approuvé pour ML training**
- Modèles de prédiction
- Production ML

**TIER2**:
- Analytics temps réel
- Suivi rookies
- Dashboards modernes

### ❌ DON'T (Ne pas utiliser)

**RAW**:
- ❌ Ne pas utiliser pour production
- ❌ Ne pas utiliser pour ML

**BRONZE**:
- ❌ Ne pas utiliser pour entraînement ML
- ❌ Ne pas utiliser pour prédiction

**SILVER**:
- ❌ Ne pas utiliser pour production ML sans validation supplémentaire

**TIER2**:
- ❌ **Ne JAMAIS utiliser pour entraînement ML**
- ❌ Données potentiellement biaisées (joueurs récents)

---

## 📞 Contacts et Support

**Équipe Data**: data-team@nba.com  
**Owner ML**: ml-team@nba.com  
**Owner BI**: bi-team@nba.com  
**On-call**: +1-XXX-XXX-XXXX

---

## 📝 Notes et Évolutions

### Version 2.0 (2026-02-07)
- Migration vers Architecture Data Mesh
- Introduction 5 datasets avec qualité explicite
- Ajout sous-catégorie CONTEMPORARY_TIER2
- Validation stricte GOLD (3% nulls max)
- Lineage tracking complet

### Roadmap
- **v2.1**: Ajout monitoring automatique
- **v2.2**: Intégration tests CI/CD
- **v3.0**: Migration vers Delta Lake UniForm (Iceberg compat)

---

**Dernière mise à jour**: 2026-02-07 10:43:00 UTC  
**Généré automatiquement par**: Data Mesh Stratifier v2.0  
**Prochaine génération**: Après chaque exécution pipeline

---

*Ce document est la source de vérité pour la qualité des données NBA Analytics Platform.*
*Pour toute question, contacter l'équipe Data.*
