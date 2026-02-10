# Session A - API / Backend

STATUS: DONE
LAST_UPDATE: 2026-02-10 18:40
CURRENT_GATE: GATE_A16: DONE @2026-02-10 17:06
BLOCKERS: none

Track A cloture. Contrat API v1 maintenu inchange (endpoints/payloads/deprecated) jusqu'a A16.

## Mission
Unifier l'API backend et supprimer les redondances entre routes et services.

## Scope autorise
- `nba/api/*`
- `nba/services/*`
- `nba/models/*`
- ajustements minimaux dans tests API si strictement necessaires

## Scope interdit
- `src/ml/*`
- `frontend/*`
- `docs/*` (hors ce fichier)

## Gates
### GATE_A1 - Contrat API v1 publie
Livrables:
- liste endpoints finaux
- endpoints deprecies
- schema de reponse standardise

Validation:
- exemples payloads JSON fournis
- compatibilite backward explicitee

Marqueur:
`GATE_A1: DONE @2026-02-10 11:45`

### Contrat API v1 (publie)

Version contrat: `v1`  
Base URL: `http://localhost:8000`  
Prefix stable: `/api/v1`

#### Endpoints finaux (canon)
- `GET /`
- `GET /health`
- `GET /api/v1/datasets`
- `GET /api/v1/datasets/{dataset_name}`
- `POST /api/v1/export`
- `POST /api/v1/catalog/scan`
- `GET /api/v1/predictions`
- `POST /api/v1/bets`
- `POST /api/v1/bets/update`
- `GET /api/v1/bets`
- `GET /api/v1/bets/stats`
- `GET /api/v1/analysis/temporal`
- `GET /api/v1/calendar/today`
- `GET /api/v1/calendar/date/{date_str}`
- `GET /api/v1/calendar/day/{date_str}`
- `GET /api/v1/calendar/month/{year}/{month}`
- `GET /api/v1/calendar/week/{date_str}`
- `GET /api/v1/calendar/range?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/v1/calendar/matches/{date_str}`
- `GET /api/v1/calendar/stats/{season}`
- `GET /api/v1/calendar/seasons`
- `POST /api/v1/calendar/refresh`

#### Endpoints deprecies (v1)
- `GET /api/v1/predictions?view=week` -> deprecie (compat maintenue), preferer `GET /api/v1/calendar/week/{date_str}`

#### Schema de reponse standardise
- Erreur standard FastAPI: `{ "detail": "<message>" }`
- Reponses success: objet JSON avec champs metier explicites (`status`, `count`, `predictions`, `bets`, `days`, etc.)
- Types date: ISO-8601 (`YYYY-MM-DD` pour jour, datetime ISO pour horodatage)

#### Payload examples JSON

`GET /api/v1/predictions?min_confidence=0.7`
```json
{
  "predictions": [
    {
      "home_team": "Boston Celtics",
      "away_team": "New York Knicks",
      "prediction": "Home Win",
      "proba_home_win": 0.74,
      "confidence": 0.79,
      "recommendation": "HIGH_CONFIDENCE",
      "game_date": "2026-02-10",
      "game_time_us": "19:00",
      "game_time_fr": "01:00"
    }
  ],
  "count": 1,
  "date": "2026-02-10T11:00:00",
  "view": "day"
}
```

`GET /api/v1/calendar/date/2026-02-10?view_mode=day&season=2025-26`
```json
{
  "season": "2025-26",
  "view_mode": "day",
  "start_date": "2026-02-10",
  "end_date": "2026-02-10",
  "today": "2026-02-10",
  "days": [
    {
      "date": "2026-02-10",
      "day_name": "Mardi",
      "match_count": 4,
      "matches": []
    }
  ],
  "total_matches": 4,
  "matches_completed": 2,
  "overall_accuracy": 0.5,
  "has_previous": true,
  "has_next": true,
  "data_sources": ["backtest", "prediction", "api"]
}
```

`POST /api/v1/bets`
```json
{
  "date": "2026-02-10",
  "match": "Celtics vs Knicks",
  "prediction": "Home Win",
  "stake": 25.0,
  "odds": 1.85
}
```

Reponse:
```json
{
  "success": true,
  "bet_id": "bet_001"
}
```

#### Compatibilite backward (explicite)
- Tous les endpoints `v1` existants restent disponibles avec les memes chemins.
- Le flux frontend actuel reste compatible sans changement de route (consommation principale via `calendar/*` deja en place).
- Seule deprecation fonctionnelle annoncee: usage de `view=week` sur `/predictions` (support maintenu en v1, migration recommandee vers `/calendar/week/{date_str}`).

### GATE_A2 - API unifiee implementee
Livrables:
- doublons routes fusionnes/supprimes
- logique commune factorisee en services

Validation:
- tests API cibles passent
- reponse stable pour frontend

Marqueur:
`GATE_A2: DONE @2026-02-10 11:47`

### GATE_A3 - Stabilisation API v1 post-unification
Livrables:
- contrat API v1 fige (endpoints + payloads + deprecated)
- tests de non-regression renforces sur `/api/v1/predictions` et routes betting
- validation explicite du mode degrade `503` betting sans impact autres routes
- note finale de compatibilite + criteres de sortie A3

Validation:
- suite de tests integration API verte
- routes v1 attendues strictement verifiees (22 routes)
- payloads predictions (day + week legacy) verifies
- mode degrade 503 betting verifie + routes non-betting intactes

Marqueur:
`GATE_A3: DONE @2026-02-10 11:52`

### GATE_A5 - Hardening backend non-intrusif
Livrables:
- robustesse des chemins d'erreur critiques renforcee (logging + garde-fous)
- validation comportement degrade betting reconfirmee
- note de hardening publiable pour support C4

Validation:
- aucun changement de contrat API v1 (endpoints/payloads/deprecated)
- tests de non-regression + tests chemins d'exception verts
- comportement degrade `503` betting confirme sans impact autres routes

Marqueur:
`GATE_A5: DONE @2026-02-10 13:08`

### GATE_A7 - Hardening final backend + runbook incident
Livrables:
- verification finale chemins `422/503/500`
- checks observabilite (`X-Request-ID`, logs exploitables)
- runbook incident court (triage + actions)

Validation:
- aucun changement de contrat API v1 (endpoints/payloads/deprecated)
- tests integration backend verts avec controles observabilite
- modes de degradation stables confirmes

Marqueur:
`GATE_A7: DONE @2026-02-10 13:35`

### GATE_A8 - Monitoring backend post-release
Livrables:
- verification continue des chemins `422/503/500`
- controle `X-Request-ID` + logs exploitables
- procedure d'escalade rapide en cas d'anomalie

Validation:
- aucun changement de contrat API v1 (endpoints/payloads/deprecated)
- tests monitoring dedies verts
- observabilite runtime verifiee (correlation id + logs structurables)

Marqueur:
`GATE_A8: DONE @2026-02-10 13:47`

### GATE_A9 - Alerting backend + drill incident
Livrables:
- verification alerting sur `422/503/500`
- drill incident court avec correlation `X-Request-ID`
- note finale d'exploitation (triage + seuils d'escalade)

Validation:
- aucun changement de contrat API v1 (endpoints/payloads/deprecated)
- suite de tests alerting/monitoring verte
- correlation `X-Request-ID` verifiee de bout en bout

Marqueur:
`GATE_A9: DONE @2026-02-10 14:10`

### GATE_A10 - SLO backend + runbook final
Livrables:
- seuils SLO/SLA pour erreurs `422/503/500` + temps de triage
- runbook incident finalise (triage/actions/escalade)
- preuve de stabilite monitoring (`X-Request-ID` + logs exploitables)

Validation:
- aucun changement de contrat API v1 (endpoints/payloads/deprecated)
- suites monitoring/alerting stables
- drills correlation `X-Request-ID` verifies

Marqueur:
`GATE_A10: DONE @2026-02-10 14:26`

### GATE_A11 - Controle observabilite/SLO en routine
Livrables:
- verification indicateurs `422/503/500` sur fenetre de routine
- verification correlation `X-Request-ID` et qualite logs
- mini rapport de conformite operations

Validation:
- aucun changement du contrat API v1
- tests monitoring/alerting/SLO passes
- conformite SLO/SLA operationnelle confirmee

Marqueur:
`GATE_A11: DONE @2026-02-10 15:51`

### GATE_A12 - Optimisation alerting/observabilite
Livrables:
- reduction du bruit alerting (faux positifs)
- seuils et severites ajustes
- mini-bilan MTTR / qualite du signal

Validation:
- aucun changement du contrat API v1
- alerting affine et verifie en tests
- qualite signal amelioree sans perte de detection critique

Marqueur:
`GATE_A12: DONE @2026-02-10 16:08`

### GATE_A13 - Fiabilite backend long-run
Livrables:
- revue tendances SLO/SLA (`422/503/500`) sur fenetres routine
- verification qualite signal alerting (bruit vs criticite)
- drill incident court (`X-Request-ID` + temps de triage)

Validation:
- aucun changement du contrat API v1
- tendance SLO/SLA stable sur plusieurs fenetres
- correlation et triage incident verifies

Marqueur:
`GATE_A13: DONE @2026-02-10 16:32`

### GATE_A14 - Stabilite routine + calibration alerting
Livrables:
- verification tendances `422/503/500` en routine
- calibration seuils/severites alerting
- mini rapport impact (bruit/signal/temps triage)

Validation:
- aucun changement du contrat API v1
- suite fiabilite/observabilite verte
- reduction bruit sans perte de detection critique

Marqueur:
`GATE_A14: DONE @2026-02-10 16:40`

### GATE_A15 - Conformite operationnelle backend
Livrables:
- controle SLO/SLA sur `422/503/500`
- verification qualite signal alerting (bruit/criticite)
- drill runbook court avec correlation `X-Request-ID`

Validation:
- aucun changement du contrat API v1
- suite conformite operationnelle verte
- correlation + triage incident verifies

Marqueur:
`GATE_A15: DONE @2026-02-10 16:58`

### GATE_A16 - Revue maturite backend operationnelle
Livrables:
- verification tendances `422/503/500` sur fenetres routine
- revue qualite signal alerting (bruit vs criticite)
- drill incident court avec correlation `X-Request-ID`

Validation:
- aucun changement du contrat API v1
- suite maturite backend verte
- triage et correlation incident confirmes

Marqueur:
`GATE_A16: DONE @2026-02-10 17:06`

#### Mini rapport maturite operations (A16)
- Tendances routine: 4 fenetres conformes (`422<=10%`, `503<=3%`, `500<=1%`).
- Qualite signal: bruit non critique contenu (422 sous seuil), criticite 500 preservee en severite `error`.
- Drill incident: correlation `X-Request-ID` verifiee et triage <= 5 secondes.

#### Mini rapport conformite operations (A15)
- SLO/SLA: conformes sur fenetre de routine (`422<=10%`, `503<=3%`, `500<=1%`).
- Qualite signal: bruit non-critique maintenu sous seuil; criticite `500` preservee en `error`.
- Drill runbook: correlation `X-Request-ID` verifiee et triage <= 5s.

#### Mini rapport impact (A14)
- Tendances: SLO `422/503/500` maintenus conformes sur la suite long-run.
- Calibration: `503` betting passe a seuil 2/5 min (au lieu de 1) pour reduire le bruit transitoire.
- Severites: `500=error`, `503=warning`, `422=warning` sur seuil, inchanges sur criticite.
- Impact MTTR: triage cible <= 5 min conserve via correlation `X-Request-ID` et logs enrichis (`threshold`, `window_count`).

#### Mini rapport conformite operations (A13)
- Tendances SLO/SLA: 3 fenetres synthetiques conformes (`422<=10%`, `503<=3%`, `500<=1%`).
- Qualite signal: `422` en dessous seuil -> bruit non critique; `500` -> alerte immediate `error`.
- Drill incident: correlation `X-Request-ID` verifiee et triage <= 5 secondes en test.

#### Mini-bilan MTTR / qualite signal (A12)
- Bruit reduit: `422` n'emet plus une alerte immediate a chaque occurrence (seuil fenetre 5 min applique).
- Severites ajustees: `500` -> `error`, `503` -> `warning`, `422` -> `warning` seulement au depassement de seuil.
- Detection conservee: `500/503` restent alertes immediates (pas de perte sur incidents critiques).
- MTTR cible conserve: triage <= 5 min via correlation `X-Request-ID` + logs structurables.

#### Mini rapport conformite operations (A11)
- Fenetre routine synthetique validee: 121 requetes totales (117 `200`, 2 `422`, 1 `503`, 1 `500`).
- Taux observes: `422=1.65%`, `503=0.83%`, `500=0.83%`.
- Conformite SLO A10: OK (`422<=10%`, `503<=3%`, `500<=1%`).
- Correlation observabilite: `X-Request-ID` conserve en reponse; logs `Request completed` et `Alert condition detected` exploitables.

#### SLO/SLA exploitation (A10)
- **SLO erreurs 500**: <= 1% des requetes sur fenetre 15 min; au-dela, incident P1.
- **SLO erreurs 503 betting**: <= 3% des requetes betting sur fenetre 15 min; au-dela, incident P1 si impact > 15 min.
- **SLO erreurs 422**: <= 10% des requetes d'endpoint cible; au-dela, alerte P2 (suspect regression client/contrat).
- **SLA triage initial**: <= 5 min avec `X-Request-ID`, endpoint, status, timestamp.
- **SLA escalade ORCH**: <= 15 min si seuil depasse ou impact transverse.

#### Runbook final (A10)
- **Step 1 - Detect**: identifier statut dominant (`422/503/500`) + endpoint impacte.
- **Step 2 - Correlate**: extraire `X-Request-ID` reponse et retrouver logs associes (`Request completed`, `Alert condition detected`).
- **Step 3 - Isolate**:
  - `503`: verifier si limite a `/api/v1/bets*` ou etendu transverse.
  - `500`: verifier exception backend et source donnees (predictions/csv/json).
  - `422`: verifier payload client (champ/type/contrainte metier).
- **Step 4 - Act**:
  - `503` betting: maintien mode degrade + verification backend betting.
  - `500`: corriger source erreur + retest endpoint.
  - `422`: correction client + replay.
- **Step 5 - Escalate**: notifier ORCH immediatement si seuil SLO depasse ou si impact transverse > 15 min.

#### Note finale d'exploitation (A9)
- Alerting: emission d'un signal log `Alert condition detected` sur `422`, `500`, `503` avec champs `request_id`, `path`, `status_code`, `duration_ms`.
- Drill incident: verification automatisee qu'un incident `500` peut etre corre9le via `X-Request-ID` entre reponse et logs.
- Seuils d'escalade ORCH:
  - `500` repete (>=3 sur 10 min) sur un endpoint critique -> escalade immediate.
  - `503` betting continu (>15 min) ou extension hors betting -> escalade immediate.
  - `422` en hausse brutale (suspect regression client) -> alerte ORCH + sync C.

#### Procedure d'escalade rapide (A8)
- Detection: alerte sur pic `5xx` ou repetition `503` betting ou `422` anormaux.
- Triage en 5 min: recuperer `X-Request-ID`, endpoint, status, timestamp.
- Isolation: verifier si incident limite betting (`/api/v1/bets*`) ou transverse (`/health`, `/api/v1/predictions`).
- Action immediate:
  - `503` betting: verifier backend betting, maintenir service degrade (autres routes doivent rester stables).
  - `500` predictions: verifier integrite du fichier predictions et logs d'exception.
  - `422`: corriger payload client (champ/type) et rejouer.
- Escalade ORCH immediate si impact transverse > 15 min ou erreur critique repetee.

#### Runbook incident court (A7)
- **422 validation**: verifier payload (champs/types) -> corriger client et rejouer requete.
- **503 betting**: verifier disponibilite backend betting + logs `Betting backend unavailable`; confirmer routes non-betting (`/health`, `/api/v1/predictions`) restent saines.
- **500 predictions**: verifier integrite source predictions (`predictions` doit etre une liste JSON) + logs d'exception, corriger source amont.
- **Correlation incident**: recuperer `X-Request-ID` de la reponse et filtrer les logs avec cet id pour suivi bout-en-bout.

#### Note de hardening A5 (publiee)
- Observabilite: ajout de logs explicites sur chemins d'erreur critiques (`predictions`, `export`, `betting`, `analysis`, startup betting).
- Garde-fous: validation payload betting deja etendue (`stake >= 0`, `odds >= 1`) et traçage des rejets.
- Robustesse payload predictions: verification du type `predictions` (liste attendue) avec erreur explicite si payload corrompu.
- Degrade mode betting reconfirme: indisponibilite backend betting isolee en `503` sur routes betting uniquement.
- Compatibilite: aucun endpoint/methode/shape de reponse v1 modifie.

#### Note finale de compatibilite (A3)
- Contrat API `v1` gele: aucun changement de path, methode, structure de payload ou semantics pour les 22 endpoints publies.
- Deprecation maintenue en compatibilite: `GET /api/v1/predictions?view=week` reste supporte en v1; migration recommandee vers `GET /api/v1/calendar/week/{date_str}`.
- Stabilite operationnelle: indisponibilite du backend betting isolee aux routes betting via `503`; aucune regression observee sur `health`, `predictions`, `datasets`, `calendar`, `analysis`.

#### Criteres de sortie A3
- [x] Contrat v1 fige et liste d'endpoints verrouillee
- [x] Non-regression `/api/v1/predictions` couverte (day + week legacy)
- [x] Non-regression routes betting couverte (mode nominal)
- [x] Mode degrade `503` betting couvert
- [x] Confirmation explicite "503 sans impact autres routes" couverte
- [x] Suite `tests/integration/test_api.py` verte

## Si bloque
Passer `STATUS: BLOCKED` et completer:
- cause
- fichiers impactes
- action requise
- owner attendu

## EVIDENCE
- fichiers modifies:
  - `docs/execution/PERSON_A_API_BACKEND.md`
  - `nba/api/main.py`
  - `nba/services/catalog_service.py`
  - `nba/services/predictions_service.py`
  - `nba/services/betting_service.py`
  - `nba/services/analysis_service.py`
  - `tests/integration/test_api.py`
  - `nba/services/betting_service.py` (A4)
  - `nba/services/analysis_service.py` (A4)
  - `nba/api/main.py` (A4)
  - `tests/integration/test_api.py` (A4)
  - `nba/services/predictions_service.py` (A5)
  - `nba/services/betting_service.py` (A5)
  - `nba/services/analysis_service.py` (A5)
  - `nba/api/main.py` (A5)
  - `tests/integration/test_api.py` (A5)
  - `nba/api/main.py` (A6)
  - `nba/services/predictions_service.py` (A6)
  - `nba/services/betting_service.py` (A6)
  - `nba/services/analysis_service.py` (A6)
  - `tests/integration/test_api.py` (A6)
  - `tests/integration/test_api.py` (A7)
  - `tests/integration/test_api_monitoring.py` (A8)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A8)
  - `nba/api/main.py` (A9)
  - `tests/integration/test_api_alerting.py` (A9)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A9)
  - `tests/integration/test_api_alerting.py` (A10)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A10)
  - `tests/integration/test_api_slo.py` (A11)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A11)
  - `nba/api/main.py` (A12)
  - `tests/integration/test_api_alerting.py` (A12)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A12)
  - `tests/integration/test_api_reliability_longrun.py` (A13)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A13)
  - `nba/api/main.py` (A14)
  - `tests/integration/test_api_alerting.py` (A14)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A14)
  - `tests/integration/test_api_operational_compliance.py` (A15)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A15)
  - `tests/integration/test_api_maturity.py` (A16)
  - `docs/execution/PERSON_A_API_BACKEND.md` (A16)
- commandes executees:
  - `python -c "from pathlib import Path; import re; ..."` (inventaire endpoints)
  - `pytest tests/integration/test_api.py -q`
  - `python -m py_compile nba/api/main.py nba/services/catalog_service.py nba/services/predictions_service.py nba/services/betting_service.py nba/services/analysis_service.py`
  - `python -c "... count endpoint decorators ..."` (22 endpoints)
  - `python -c "... TestClient + simulated betting unavailable ..."` (verification 503)
  - `pytest tests/integration/test_api.py -q` (suite renforcee A3)
  - `python -m py_compile nba/api/main.py nba/services/catalog_service.py nba/services/predictions_service.py nba/services/betting_service.py nba/services/analysis_service.py tests/integration/test_api.py`
  - `pytest tests/integration/test_api.py -q` (A4)
  - `python -c "... smoke checks A4 corrected betting and analysis cases ..."`
  - `pytest tests/integration/test_api.py -q` (A5 hardening)
  - `python -m py_compile nba/api/main.py nba/services/predictions_service.py nba/services/betting_service.py nba/services/analysis_service.py tests/integration/test_api.py`
  - `pytest tests/integration/test_api.py -q` (A6 observabilite)
  - `python -m py_compile nba/api/main.py tests/integration/test_api.py` (A6)
  - `pytest tests/integration/test_api.py -q` (A7 final)
  - `python -m py_compile nba/api/main.py tests/integration/test_api.py` (A7)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py -q` (A8)
  - `python -m py_compile tests/integration/test_api.py tests/integration/test_api_monitoring.py nba/api/main.py` (A8)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py -q` (A9)
  - `python -m py_compile nba/api/main.py tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py` (A9)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py -q` (A10)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py -q` (A11)
  - `pytest tests/integration/test_api_alerting.py tests/integration/test_api_monitoring.py tests/integration/test_api_slo.py tests/integration/test_api.py -q` (A12)
  - `python -m py_compile nba/api/main.py tests/integration/test_api_alerting.py tests/integration/test_api_monitoring.py tests/integration/test_api_slo.py tests/integration/test_api.py` (A12)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py -q` (A13)
  - `python -m py_compile nba/api/main.py tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py` (A13)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py -q` (A14)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py tests/integration/test_api_operational_compliance.py -q` (A15)
  - `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py tests/integration/test_api_operational_compliance.py tests/integration/test_api_maturity.py -q` (A16)
- resultats:
  - 22 endpoints inventoriees et alignees sur contrat v1
  - logique API factorisee en services (`catalog`, `predictions`, `betting`, `analysis`) et endpoint `main.py` simplifie
  - endpoint `GET /api/v1/predictions` unifie avec filtre date + compat legacy `view=week`
  - betting isole via import lazy (degrade en `503` si backend betting indisponible, sans casser le boot API)
  - tests API integration (suite renforcee A3): 10/10 PASS
  - validation syntaxe modules API/services: PASS
  - verification explicite degradation betting: `GET /api/v1/bets/stats` retourne `503` si backend indisponible
  - freeze contrat v1 automatise en test: liste stricte des 22 routes verifiee
  - payload predictions non-regression verifies: `view=day` + `view=week` legacy
  - confirmation explicite: mode `503` betting n'impacte pas `/health` ni `/api/v1/predictions`
  - A4 case 1 corrige: `POST /api/v1/bets` rejette `stake < 0` -> `400`
  - A4 case 1 corrige: `POST /api/v1/bets` rejette `odds < 1` -> `400`
  - A4 case 2 corrige: `GET /api/v1/analysis/temporal` renvoie `200` sans `error` avec colonnes source `predicted/actual`
  - tests integration apres A4: 13/13 PASS
  - A5 chemins d'erreur verifies: predictions internal error -> `500` detail; temporal error path -> `200` + `error`
  - A5 suite integration: 15/15 PASS
  - A5 syntax check: PASS
  - A5 degradation betting reconfirmee: `503` isole, routes non-betting inchangées
  - A6 observabilite: middleware requete ajoute (request id + latence + status) sur toutes routes
  - A6 logs erreurs: startup betting, export, predictions, betting, analysis traces explicitement
  - A6 robustesse payload predictions: garde-fou type `predictions` liste
  - A6 degradation paths stables verifies: `503` betting, `422` validation, `500` internal predictions
  - A6 suite integration: 15/15 PASS
  - A7 observabilite verifiee: propagation `X-Request-ID` entrant + presence systematique en reponse
  - A7 logs verifiees: emission `Request completed` captee en test
  - A7 chemins finaux verifies: `422`, `503`, `500` stables
  - A7 suite integration: 17/17 PASS
  - A8 monitoring: couverture dediee des chemins `422/503/500` avec `X-Request-ID`
  - A8 logs: verification champs exploitables (`request_id`, `path`, `status_code`) sur `Request completed`
  - A8 suite integration: 21/21 PASS
  - A9 alerting: warning log `Alert condition detected` verifie sur `422/503/500`
  - A9 drill incident: correlation `X-Request-ID` verifiee sur incident `500`
  - A9 suite integration: 25/25 PASS
  - A10 SLO/SLA definis: seuils erreurs `422/503/500`, SLA triage <= 5 min, SLA escalade <= 15 min
  - A10 runbook finalise: detect/correlate/isolate/act/escalate
  - A10 stabilite monitoring confirmee: `X-Request-ID` + logs exploitables verifies en tests
  - A11 conformite routine: SLO `422/503/500` respectes sur fenetre synthetique
  - A11 suite integration: 26/26 PASS
  - A12 reduction bruit: alerting `422` passe en seuil (5 min) pour eviter faux positifs unitaires
  - A12 severites ajustees: `500=error`, `503=warning`, `422=warning` au depassement de seuil
  - A12 mini-bilan MTTR signal: triage <= 5 min maintenu, qualite signal amelioree sans perte de detection critique
  - A12 suite integration: 27/27 PASS
  - A13 tendances long-run: 3 fenetres SLO/SLA conformes (`422<=10%`, `503<=3%`, `500<=1%`)
  - A13 qualite signal: bruit 422 contenu, criticite 500 preservee en alerte `error`
  - A13 drill incident: correlation `X-Request-ID` + triage <= 5s verifie
  - A13 suite integration: 30/30 PASS
  - A14 calibration signal: `503` betting alerte au 2e evenement (seuil 2/5 min), reduisant bruit unitaire
  - A14 observabilite: logs alerting enrichis (`threshold`, `window_count`) pour triage rapide
  - A14 suite integration: 30/30 PASS
  - A15 conformite operationnelle: controle SLO/SLA `422/503/500` valide en routine
  - A15 qualite signal: bruit non-critique filtre, criticite preservee
  - A15 drill runbook: correlation `X-Request-ID` + triage <= 5s valide
  - A15 suite integration: 33/33 PASS
  - A16 tendances routine: 4 fenetres SLO/SLA conformes
  - A16 qualite signal: bruit sous controle, criticite preservee
  - A16 drill incident: correlation `X-Request-ID` + triage <= 5s valide
  - A16 suite integration: 36/36 PASS

## HANDOFF
- pour C: contrat API v1 gele pour freeze frontend
  - endpoints finaux: section "Contrat API v1 (publie)"
  - endpoint deprecie: `GET /api/v1/predictions?view=week`
  - payload examples: sections JSON ci-dessus (`predictions`, `calendar/date`, `bets`)
- pour ORCH: liste fichiers + tests executes + risques
  - fichier: `docs/execution/PERSON_A_API_BACKEND.md`
  - tests: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py tests/integration/test_api_operational_compliance.py tests/integration/test_api_maturity.py -q` (36/36 PASS, suite A16)
  - risque ouvert: none (dette import typing `src/ml/pipeline/tracking_roi.py` reste suivie hors scope A)
  - runbook C5 (support):
    - `503`: verifier disponibilite backend betting + logs `Betting backend unavailable`
    - `422`: verifier payload invalide (champ manquant/type) + corriger client
    - `500` predictions: verifier integrite fichier predictions (`predictions` doit etre une liste)
    - Correlation: utiliser header `X-Request-ID` pour tracer une requete de bout en bout

## OUTBOX_TO_ORCH
- [MSG_ID] A-20260210-A16
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A16_VALIDATED - revue maturite backend operationnelle
- [BODY]
- - Reference livraison: HEAD `88ea395` + changeset local A16 (`tests/integration/test_api_maturity.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py tests/integration/test_api_operational_compliance.py tests/integration/test_api_maturity.py -q` -> `36/36 PASS`
- - Tendances `422/503/500`: conformes sur fenetres routine, qualite signal alignee bruit vs criticite
- - Drill incident: correlation `X-Request-ID` et triage <= 5s verifies
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A15
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A15_VALIDATED - conformite operationnelle backend
- [BODY]
- - Reference livraison: HEAD `88ea395` + changeset local A15 (`tests/integration/test_api_operational_compliance.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py tests/integration/test_api_operational_compliance.py -q` -> `33/33 PASS`
- - Controle operationnel: SLO/SLA `422/503/500` valides, qualite signal alignee bruit/criticite
- - Drill runbook: correlation `X-Request-ID` + triage court valide
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A14
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A14_VALIDATED - stabilite routine + calibration alerting
- [BODY]
- - Reference livraison: HEAD `24f1624` + changeset local A14 (`nba/api/main.py`, `tests/integration/test_api_alerting.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py -q` -> `30/30 PASS`
- - Calibration: `503` betting passe a seuil 2/5 min, severites maintenues (`500=error`, `503=warning`, `422=warning` sur seuil)
- - Impact: bruit reduit, signal critique preserve, triage rapide maintenu via `X-Request-ID`
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A13
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A13_VALIDATED - fiabilite backend long-run
- [BODY]
- - Reference livraison: HEAD `24f1624` + changeset local A13 (`tests/integration/test_api_reliability_longrun.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py tests/integration/test_api_reliability_longrun.py -q` -> `30/30 PASS`
- - Tendances SLO/SLA: 3 fenetres conformes sur `422/503/500`, bruit `422` contenu, criticite `500` preservee
- - Drill incident: correlation `X-Request-ID` verifiee avec triage <= 5s
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A12
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A12_VALIDATED - optimisation alerting/observabilite
- [BODY]
- - Reference livraison: HEAD `3062700` + changeset local A12 (`nba/api/main.py`, `tests/integration/test_api_alerting.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py -q` -> `27/27 PASS`
- - Qualite signal: bruit `422` reduit via seuil fenetre, severites ajustees (`500=error`, `503=warning`, `422=warning` sur seuil)
- - Mini-bilan MTTR: triage <= 5 min maintenu, correlation `X-Request-ID` + logs exploitables confirmee
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A1
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A1_VALIDATED - contrat API v1 publie
- [BODY]
- - Gate A1 franchie: contrat API v1 publie (endpoints finaux + deprecated + payloads + compatibilite backward)
- - Handoff C pret pour freeze frontend API
- [ACTION_REQUIRED] non
- 
  - [MSG_ID] A-20260210-A9
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A9_VALIDATED - alerting backend + drill incident
- [BODY]
- - Reference livraison: HEAD `3062700` + changeset local A9 (`nba/api/main.py`, `tests/integration/test_api_alerting.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py -q` -> `25/25 PASS`
- - Preuves alerting: signal log `Alert condition detected` confirme sur chemins `422/503/500`
- - Preuves drill incident: correlation `X-Request-ID` verifiee entre reponse et logs sur incident `500`
- - Note finale d'exploitation publiee (triage + seuils d'escalade)
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A11
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A11_VALIDATED - controle observabilite/SLO en routine
- [BODY]
- - Reference livraison: HEAD `3062700` + changeset local A11 (`tests/integration/test_api_slo.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py tests/integration/test_api_slo.py -q` -> `26/26 PASS`
- - Conformite operations: fenetre routine 121 req (`422=1.65%`, `503=0.83%`, `500=0.83%`) sous SLO
- - Correlation/logs: `X-Request-ID` + logs `Request completed` et `Alert condition detected` exploitables
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A10
- [FROM] A
- [TO] ORCH
  - [TYPE] INFO
  - [PRIORITY] P1
  - [SUBJECT] A10_VALIDATED - SLO backend + runbook final
  - [BODY]
  - - Reference livraison: HEAD `3062700` + changeset local A10 (`tests/integration/test_api_alerting.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
  - - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py tests/integration/test_api_alerting.py -q` -> `25/25 PASS`
  - - SLO/SLA publies: seuils `422/503/500` + triage <= 5 min + escalade <= 15 min
  - - Runbook final publie: triage/actions/escalade
  - - Stabilite monitoring prouvee: `X-Request-ID` + logs exploitables
  - - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
  - [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A8
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A8_VALIDATED - monitoring backend post-release
- [BODY]
- - Reference livraison: HEAD `3062700` + changeset local A8 (`tests/integration/test_api_monitoring.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py tests/integration/test_api_monitoring.py -q` -> `21/21 PASS`
- - Preuves monitoring: chemins `422/503/500` verifies en continu, `X-Request-ID` controle, logs exploitables verifies
- - Procedure d'escalade rapide publiee (triage + actions + seuil escalade)
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A7
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A7_VALIDATED - hardening final backend + runbook incident
- [BODY]
- - Reference livraison: HEAD `4f1a9cc` + changeset local A7 (`tests/integration/test_api.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Tests cibles: `pytest tests/integration/test_api.py -q` -> `17/17 PASS`; `python -m py_compile nba/api/main.py tests/integration/test_api.py` -> PASS
- - Preuves finales: chemins `422/503/500` verifies; `X-Request-ID` propage et present en reponse; logs `Request completed` captes
- - Runbook incident court publie (triage + actions)
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A6
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A6_VALIDATED - observabilite backend non-intrusive
- [BODY]
- - Reference livraison: HEAD `4f1a9cc` + changeset local A6 (`nba/api/main.py`, `nba/services/predictions_service.py`, `nba/services/betting_service.py`, `nba/services/analysis_service.py`, `tests/integration/test_api.py`)
- - Tests cibles: `pytest tests/integration/test_api.py -q` -> `15/15 PASS`; `python -m py_compile nba/api/main.py tests/integration/test_api.py` -> PASS
- - Preuves runtime: header `X-Request-ID` present, logs parcours critiques, chemins de degradation stables (`503/422/500`) verifies
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A5
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A5_VALIDATED - hardening backend non-intrusif
- [BODY]
- - Reference livraison: HEAD `4f1a9cc` + changeset local A5 (`nba/api/main.py`, `nba/services/predictions_service.py`, `nba/services/betting_service.py`, `nba/services/analysis_service.py`, `tests/integration/test_api.py`)
- - Tests cibles: `pytest tests/integration/test_api.py -q` -> `15/15 PASS`; `python -m py_compile ...` -> PASS
- - Preuves cas hardening: chemins d'exception critiques verifies (`/api/v1/predictions` 500 detail sur erreur interne, `/api/v1/analysis/temporal` error path stable), degradation betting `503` reconfirmee sans impact `/health` et `/api/v1/predictions`
- - Contrat API v1 preserve: endpoints/payloads/deprecated inchanges
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A4
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A4_VALIDATED - correctifs backend J5 strict
- [BODY]
- - Reference livraison: HEAD `4f1a9cc` + changeset local A4 (`nba/services/betting_service.py`, `nba/services/analysis_service.py`, `nba/api/main.py`, `tests/integration/test_api.py`)
- - Tests cibles: `pytest tests/integration/test_api.py -q` -> `13/13 PASS`
- - Preuves cas corriges: `stake<0` -> `400`, `odds<1` -> `400`, `/api/v1/analysis/temporal` -> `200` sans erreur `prediction`
- - Contrat v1 inchange: aucun changement endpoints/payloads/deprecated
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A2
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A2_VALIDATED - implementation API unifiee
- [BODY]
- - Gate A2 franchie: logique API factorisee en services (`catalog`, `predictions`, `betting`, `analysis`) avec endpoints v1 inchanges
- - Reference livraison: HEAD `4f1a9cc` + changeset local A2 (`nba/api/main.py`, `nba/services/*`, `tests/integration/test_api.py`)
- - Endpoints couverts (22): `/`, `/health`, `/api/v1/datasets`, `/api/v1/datasets/{dataset_name}`, `/api/v1/export`, `/api/v1/catalog/scan`, `/api/v1/predictions`, `/api/v1/bets`, `/api/v1/bets/update`, `/api/v1/bets`, `/api/v1/bets/stats`, `/api/v1/analysis/temporal`, `/api/v1/calendar/today`, `/api/v1/calendar/date/{date_str}`, `/api/v1/calendar/day/{date_str}`, `/api/v1/calendar/month/{year}/{month}`, `/api/v1/calendar/week/{date_str}`, `/api/v1/calendar/range`, `/api/v1/calendar/matches/{date_str}`, `/api/v1/calendar/stats/{season}`, `/api/v1/calendar/seasons`, `/api/v1/calendar/refresh`
- - Comportement confirme: si backend betting indisponible, endpoints betting repondent `503` sans impacter les autres routes API
- [ACTION_REQUIRED] non
- 
- [MSG_ID] A-20260210-A3
- [FROM] A
- [TO] ORCH
- [TYPE] INFO
- [PRIORITY] P1
- [SUBJECT] A3_VALIDATED - stabilisation API v1 post-unification
- [BODY]
- - Gate A3 franchie: contrat API v1 fige + non-regression predictions/betting renforcee + mode degrade 503 confirme
- - Reference livraison: HEAD `4f1a9cc` + changeset local A3 (`tests/integration/test_api.py`, `docs/execution/PERSON_A_API_BACKEND.md`)
- - Endpoints v1 couverts (22) verifies par test de freeze: `/`, `/health`, `/api/v1/datasets`, `/api/v1/datasets/{dataset_name}`, `/api/v1/export`, `/api/v1/catalog/scan`, `/api/v1/predictions`, `/api/v1/bets`, `/api/v1/bets/update`, `/api/v1/bets`, `/api/v1/bets/stats`, `/api/v1/analysis/temporal`, `/api/v1/calendar/today`, `/api/v1/calendar/date/{date_str}`, `/api/v1/calendar/day/{date_str}`, `/api/v1/calendar/month/{year}/{month}`, `/api/v1/calendar/week/{date_str}`, `/api/v1/calendar/range`, `/api/v1/calendar/matches/{date_str}`, `/api/v1/calendar/stats/{season}`, `/api/v1/calendar/seasons`, `/api/v1/calendar/refresh`
- - Comportement 503 betting confirme: routes betting -> `503` si backend indisponible; routes non-betting (`/health`, `/api/v1/predictions`) restent `200`
- [ACTION_REQUIRED] non

## Checklist finale
- [x] GATE_A1 done
- [x] GATE_A2 done
- [x] GATE_A3 done
- [x] BLOCKERS vide
- [x] HANDOFF rempli
