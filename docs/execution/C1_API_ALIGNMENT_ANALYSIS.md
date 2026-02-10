[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# Analyse Frontend-Backend API - Préparation J5

**Date:** 2026-02-10  
**Session:** C (QA/Frontend/Docs)  
**Status:** Analyse préliminaire pour J5 (attente A1_VALIDATED)  

---

## 🔍 MISMATCH IDENTIFIÉ

### Endpoints Frontend (api.ts) vs Backend (main.py + routers)

#### ✅ ENDPOINTS ALIGNÉS (Fonctionnels)

| Endpoint Frontend | Endpoint Backend | Statut |
|-------------------|------------------|--------|
| `/api/v1/calendar/today` | ✅ `/api/v1/calendar/today` | OK |
| `/api/v1/calendar/date/{date}` | ✅ `/api/v1/calendar/date/{date_str}` | OK |
| `/api/v1/calendar/week/{date}` | ✅ (via calendar router) | À vérifier |
| `/api/v1/calendar/month/{year}/{month}` | ✅ (via calendar router) | À vérifier |
| `/api/v1/calendar/range` | ✅ (via calendar router) | À vérifier |
| `/api/v1/calendar/stats/{season}` | ✅ (via calendar router) | À vérifier |
| `/api/v1/calendar/refresh` | ✅ `/api/v1/calendar/refresh` | OK |

#### ❌ ENDPOINTS MANQUANTS (Frontend attend, Backend non implémenté)

| Endpoint Frontend | Usage Frontend | Impact | Action A1 Requise |
|-------------------|----------------|--------|-------------------|
| `/api/v1/predictions` | Liste prédictions | **CRITIQUE** | Définir contrat |
| `/api/v1/predictions?min_confidence={n}` | Filtre confiance | **CRITIQUE** | Définir schema |
| `/api/v1/predictions?view=week` | Vue semaine | **CRITIQUE** | Définir format |
| `/api/v1/bets` | Placer paris | Majeur | Endpoints CRUD |
| `/api/v1/bets/update` | Màj résultats | Majeur | Endpoint update |
| `/api/v1/bets/stats` | Stats paris | Mineur | Endpoint analytics |
| `/api/v1/analysis/temporal` | Analyse temporelle | Mineur | Endpoint analytics |

---

## 📋 DÉTAIL ENDPOINTS CALENDAR (Vérifiés)

**Fichier:** `nba/api/routers/calendar.py`

```python
GET /api/v1/calendar/today?view_mode={day|week|month}
GET /api/v1/calendar/date/{date_str}?view_mode={day|week|month}&season=2025-26
GET /api/v1/calendar/day/{date_str}
GET /api/v1/calendar/week/{date_str}
GET /api/v1/calendar/month/{year}/{month}
GET /api/v1/calendar/range?start={date}&end={date}&season=2025-26
GET /api/v1/calendar/stats/{season}
POST /api/v1/calendar/refresh
```

**Frontend correspondant:**
```typescript
// api.ts - Tous les endpoints calendar sont définis
calendarApi.getToday(viewMode)
calendarApi.getByDate(date, viewMode, season)
calendarApi.getWeek(date, season)
calendarApi.getMonth(year, month, season)
calendarApi.getRange(start, end, season)
calendarApi.getSeasonStats(season)
calendarApi.refresh()
```

✅ **Calendar: Frontend et Backend alignés**

---

## ⚠️ ENDPOINTS PREDICTIONS (À DÉFINIR)

**Frontend attend:**
```typescript
// api.ts - Lignes 11-16
predictionsApi.getAll(minConfidence)      // GET /api/v1/predictions
predictionsApi.getWeek(minConfidence)     // GET /api/v1/predictions?view=week
predictionsApi.getByDate(date, view)      // GET /api/v1/calendar/date/{date}
```

**Backend actuel:** ❌ Non implémenté dans `main.py`

**Besoin A1:**
- [ ] Définir endpoint `/api/v1/predictions`
- [ ] Définir paramètres: `min_confidence`, `view`, `date`
- [ ] Définir schema réponse Prediction:
  ```python
  class Prediction(BaseModel):
      home_team: str
      away_team: str
      prediction: str
      proba_home_win: float
      confidence: float
      recommendation: str
      game_date: Optional[str]
      game_time_us: Optional[str]
      game_time_fr: Optional[str]
  ```

---

## ⚠️ ENDPOINTS BETS (À DÉFINIR)

**Frontend attend:**
```typescript
// api.ts - Lignes 44-50
betsApi.place(bet)              // POST /api/v1/bets
betsApi.update(betId, result)   // POST /api/v1/bets/update
betsApi.getAll(status, limit)   // GET /api/v1/bets
betsApi.getStats()              // GET /api/v1/bets/stats
```

**Backend actuel:** ✅ Partiellement implémenté dans `main.py` (lignes 111-180)
- `POST /api/v1/bets` - ✅ Implémenté
- `POST /api/v1/bets/update` - ✅ Implémenté
- `GET /api/v1/bets` - ✅ Implémenté
- `GET /api/v1/bets/stats` - ✅ Implémenté

⚠️ **Bets: Implémenté mais à valider avec contrat A1**

---

## ⚠️ ENDPOINTS ANALYSIS (À DÉFINIR)

**Frontend attend:**
```typescript
// api.ts - Ligne 53
analysisApi.getTemporal()       // GET /api/v1/analysis/temporal
```

**Backend actuel:** ❌ Non implémenté

**Besoin A1:**
- [ ] Définir endpoint `/api/v1/analysis/temporal`
- [ ] Définir schema réponse

---

## 📊 MATRICE ALIGNEMENT

| Domaine | Endpoints | Alignés | Manquants | Impact |
|---------|-----------|---------|-----------|--------|
| **Calendar** | 8 | 8 | 0 | ✅ OK |
| **Predictions** | 3 | 0 | 3 | 🔴 CRITIQUE |
| **Bets** | 4 | 4 | 0 | ⚠️ À valider |
| **Analysis** | 1 | 0 | 1 | 🟡 Mineur |
| **TOTAL** | 16 | 12 | 4 | 75% |

---

## 🎯 ACTIONS REQUISES (Post A1_VALIDATED)

### Priorité 1: Predictions (J5)
**Dès réception contrat API A1:**
1. Créer/valider `/api/v1/predictions` et variants
2. Valider schema Prediction avec frontend
3. Ajouter tests stricts sur codes 200 + schema

### Priorité 2: Validation Bets (J5)
1. Vérifier contrat bets avec A1
2. Valider comportement edge cases
3. Tests stricts CRUD

### Priorité 3: Analysis (J6)
1. Implémenter si confirmé par A1
2. Ou supprimer du frontend si non prioritaire

---

## 🔧 PRÉPARATION TESTS STRICTS (J5)

**Modèle d'assertion à appliquer:**

```python
# AVANT (trop permissif)
assert response.status_code in [200, 404, 500]

# APRÈS (strict)
assert response.status_code == 200
assert response.json()["home_team"] is not None
assert isinstance(response.json()["confidence"], float)
assert 0 <= response.json()["confidence"] <= 1
```

**Pattern de validation schema:**
```python
from pydantic import BaseModel

class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    confidence: float
    
def test_prediction_schema():
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    # Validation automatique via Pydantic
    PredictionResponse(**response.json())
```

---

## 📁 FICHIERS CONCERNÉS

### Backend (Scope A1)
- `nba/api/main.py` - Routes existantes
- `nba/api/routers/calendar.py` - ✅ À jour
- `nba/api/routers/predictions.py` - 🔴 À créer/définir

### Frontend (Scope C)
- `frontend/src/lib/api.ts` - Client API (aligné Calendar, attend Predictions)
- `frontend/src/pages/Predictions.tsx` - Dépend de /predictions
- `frontend/src/components/predictions/DayView.tsx` - Dépend de /predictions

### Tests (Scope C)
- `tests/integration/test_api.py` - À durcir dès A1_VALIDATED

---

## ⏳ ATTENTE A1_VALIDATED

**Bloqué jusqu'à:**
- Contrat API v1 (endpoints + payloads)
- Liste endpoints finaux vs dépréciés
- Exemples payloads JSON
- Compatibilité backward explicite

**Dès réception:**
- Basculer immédiatement sur durcissement tests
- Aligner frontend si écarts
- Marquer J5 comme DONE dans tracking

---

**Document créé:** 2026-02-10  
**Dernière mise à jour:** 2026-02-10  
**Statut:** Analyse préliminaire complète, prêt pour J5
