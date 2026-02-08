# NBA-21: Feature Engineering Documentation

**Status:** ✅ Complete  
**Date:** 2026-02-08  
**Engineer:** 10x Mode Activated

---

## 📊 Overview

NBA-21 transforms raw box score data into ML-ready matchup features. This pipeline creates **48 features** from **8,871 NBA games** across **7 seasons** (2018-2025).

**Performance:** Pipeline completes in ~12 seconds

---

## 🎯 Features Created

### 1. Core Matchup Features (24)

#### Home Team Features (12)
- `home_score` - Points scored by home team
- `home_win_pct` - Season win percentage
- `home_win_pct_last_5` - Win % over last 5 games
- `home_wins_last_10` - Number of wins in last 10 games
- `home_avg_pts_last_5/10/20` - Average points over last 5/10/20 games
- `home_avg_pts_season` - Season average points
- `home_rest_days` - Days since last game
- `home_is_back_to_back` - Flag for consecutive games
- `home_ts_pct` - True Shooting percentage
- `home_efg_pct` - Effective Field Goal percentage
- `home_game_score` - Hollinger Game Score
- `home_trend` - Recent form vs season average

#### Away Team Features (12)
Same features as home team, prefixed with `away_`

### 2. Head-to-Head Features (4)

**Critical:** Calculated using only historical data (no data leakage)

- `h2h_games` - Number of previous meetings
- `h2h_home_wins` - Home team wins in H2H history
- `h2h_home_win_rate` - Win rate in H2H (neutral 0.5 for first meetings)
- `h2h_avg_margin` - Average point differential in H2H

### 3. Interaction Features (6)

- `point_diff` - Home score minus away score
- `rest_advantage` - Home rest days minus away rest days
- `win_pct_diff` - Win percentage differential
- `pts_diff_last_5` - Points average differential (last 5)
- `ts_pct_diff` - True Shooting differential
- `trend_diff` - Form trend differential

### 4. Target Variable

- `target` - Binary: 1 if home team wins, 0 if away team wins
- Home win rate: **55.8%** (validates home court advantage)

---

## 🔄 Data Flow

```
Box Score Format (2 rows/game)
    ↓
Transform to Matchup Format (1 row/game)
    ↓
Calculate H2H Features (historical only)
    ↓
Create Interaction Features
    ↓
Save to Gold Layer
```

---

## 📁 Output Files

| File | Description | Size |
|------|-------------|------|
| `features_all.parquet` | Complete dataset (8,871 games) | ~2.5 MB |
| `features_2018-19.parquet` | Season 2018-19 (1,312 games) | ~400 KB |
| `features_2019-20.parquet` | Season 2019-20 (1,142 games) | ~350 KB |
| `features_2020-21.parquet` | Season 2020-21 (1,165 games) | ~350 KB |
| `features_2021-22.parquet` | Season 2021-22 (1,317 games) | ~400 KB |
| `features_2022-23.parquet` | Season 2022-23 (1,314 games) | ~400 KB |
| `features_2023-24.parquet` | Season 2023-24 (1,312 games) | ~400 KB |
| `features_2024-25.parquet` | Season 2024-25 (1,309 games) | ~400 KB |
| `metadata.json` | Feature metadata and statistics | ~5 KB |

---

## 🧪 Validation Results

All 11 tests passed:

✅ **Data Loaded** - 8,871 records verified  
✅ **No Null Target** - Target variable complete  
✅ **Target Distribution** - Home win rate: 55.8% (expected range)  
✅ **No Data Leakage** - H2H features use only historical data  
✅ **Temporal Consistency** - Games ordered chronologically  
✅ **Feature Ranges** - All features within expected ranges  
✅ **Home/Away Balance** - No games with same team  
✅ **Point Diff Consistency** - Matches score calculation  
✅ **Target Consistency** - Matches winner  
✅ **Required Features** - All 13 required features present  
✅ **Multiple Seasons** - 7 seasons available for temporal split

---

## 🚀 Usage

### Run Pipeline

```bash
python src/pipeline/nba21_feature_engineering.py
```

### Load Features for ML

```python
import pandas as pd

# Load all features
df = pd.read_parquet("data/gold/ml_features/features_all.parquet")

# Or load specific season
df_2024 = pd.read_parquet("data/gold/ml_features/features_2023-24.parquet")

# Temporal split for training
train = df[df['season'].isin(['2018-19', '2019-20', '2020-21', '2021-22'])]
val = df[df['season'] == '2022-23']
test = df[df['season'] == '2023-24']
```

### Get Feature List

```python
from src.pipeline.nba21_feature_engineering import NBA21FeatureEngineer

engineer = NBA21FeatureEngineer()
features = engineer.get_feature_columns()
print(f"Total features: {len(features)}")
```

---

## 📈 Statistics

- **Total Games:** 8,871
- **Unique Games:** 8,871 (1 per matchup)
- **Seasons:** 7 (2018-19 to 2024-25)
- **Total Features:** 48
- **H2H Coverage:** 8,436 games (95.1%) have H2H history
- **Avg H2H Games:** 11.1 previous meetings
- **Pipeline Runtime:** ~12 seconds

---

## ⚠️ Important Notes

1. **No Data Leakage** - All H2H features calculated using only data BEFORE each game
2. **Temporal Order** - Games are sorted chronologically within each season
3. **Home Advantage** - 55.8% home win rate validates realistic target distribution
4. **Missing Team Names** - Some parquet files lack team name columns (IDs always present)

---

## 🔗 Dependencies

- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `pyarrow` - Parquet I/O

---

**Ready for NBA-22: Machine Learning Classification** 🎯
