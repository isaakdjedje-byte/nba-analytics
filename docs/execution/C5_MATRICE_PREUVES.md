[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# C5 - Matrice de Preuves (Execution)

Date: 2026-02-10
Gate: C5
Dependances: A6 CLEARED, B5 CLEARED

## Matrice 1 - API strict (18)
- Resultat global: 18/18 PASS
- Commande: `pytest tests/integration/test_api_strict_j5.py -v`
- Preuve: `18 passed in 1.15s`

## Matrice 2 - Resilience UX/API (6)
- Resultat global: 6/6 PASS
- Methode: runbook A6 + verification code C2

1) 503 betting degrade isole
- Commande triage: TestClient force `betting_service.is_available=False`
- Resultat: `/api/v1/bets/stats -> 503`, `/api/v1/predictions -> 200`
- X-Request-ID: `c5-rb-503`, `c5-rb-503-iso`

2) 422 validation payload
- Commande triage: `POST /api/v1/bets` sans champ `odds`
- Resultat: `422 Unprocessable Entity`
- X-Request-ID: `c5-rb-422`

3) 500 internal predictions
- Commande triage: monkeypatch `predictions_service.get_predictions_response` -> RuntimeError
- Resultat: `/api/v1/predictions -> 500`
- X-Request-ID: `c5-rb-500`

4) UX message 503 betting
- Preuve code: `frontend/src/pages/Betting.tsx` fallback `isBettingUnavailable`

5) UX message 422 modal pari
- Preuve code: `frontend/src/components/BetForm.tsx` branche `status === 422`

6) UX message network/retry
- Preuve code: `frontend/src/hooks/useApi.ts` + `frontend/src/components/ErrorDisplay.tsx`

## Matrice 3 - Parcours critiques (4)
- Resultat global: 4/4 PASS (validation fonctionnelle et architecture)

1) Calendrier + predictions
- Preuves: `frontend/src/pages/Predictions.tsx`, endpoint calendar/predictions verts

2) Placement pari
- Preuves: `frontend/src/components/BetForm.tsx`, tests J5 bets verts

3) MAJ resultat pari
- Preuves: `tests/integration/test_api_strict_j5.py::test_update_bet_result` PASS

4) Navigation inter-pages
- Preuves: pages `Dashboard.tsx`, `Betting.tsx`, `Predictions.tsx` robustes erreurs/retry

## Correctif minimal applique
- Fichier: `src/betting/paper_trading_db.py`
- Changement: generation `bet_id` rendue unique (timestamp microseconds + uuid court)
- Impact contrat API v1: aucun
- Impact regression: elimine collision intermittente `UNIQUE constraint failed: bets.id`
