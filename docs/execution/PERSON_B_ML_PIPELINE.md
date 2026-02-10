# Session B - ML / Pipeline / Scripts

STATUS: DONE
LAST_UPDATE: 2026-02-10 18:40
CURRENT_GATE: GATE_B15: DONE @2026-02-10 17:20
BLOCKERS: none

Track B cloture. Chaine canonique stable avec 4 entrypoints et gouvernance BAU formalisee.

## Mission
Supprimer les redondances scripts/pipelines et definir une chaine canonique unique:
`train`, `predict`, `validate`, `backtest`.

## Scope autorise
- `src/ml/pipeline/*`
- `scripts/*`
- scripts racine lies ML/backtest

## Scope interdit
- `nba/api/*`
- `frontend/*`
- `docs/*` (hors ce fichier)

## Gates
### GATE_B1 - Inventaire redondances publie
Livrables:
- matrice `garder/fusionner/supprimer`
- mapping ancien -> nouveau

Validation:
- redondances classees par criticite
- proposition de migration sans casse

Marqueur:
`GATE_B1: DONE @2026-02-10 11:40`

### GATE_B2 - Chaine canonique implementee
Livrables:
- 1 entrypoint officiel par use case
- wrappers temporaires si necessaire

Validation:
- parcours basiques train/predict/validate/backtest passent
- outputs documentes

Marqueur:
`GATE_B2: DONE @2026-02-10 12:20`

### GATE_B3 - Nettoyage scripts obsoletes
Livrables:
- scripts `fix_*` et variantes obsoletes supprimes/archives
- handoff usage pipeline vers C

Validation:
- aucun script critique perdu
- documentation d'usage mise a jour (handoff)

Marqueur:
`GATE_B3: DONE @2026-02-10 13:05`

### Gates de maturite BAU
- `GATE_B4: DONE @2026-02-10 13:30`
- `GATE_B5: DONE @2026-02-10 13:45`
- `GATE_B6: DONE @2026-02-10 14:00`
- `GATE_B7: DONE @2026-02-10 14:20`
- `GATE_B8: DONE @2026-02-10 14:35`
- `GATE_B9: DONE @2026-02-10 14:50`
- `GATE_B10: DONE @2026-02-10 15:05`
- `GATE_B11: DONE @2026-02-10 15:20`
- `GATE_B12: DONE @2026-02-10 15:35`
- `GATE_B13: DONE @2026-02-10 15:55`
- `GATE_B14: DONE @2026-02-10 16:20`
- `GATE_B15: DONE @2026-02-10 17:20`

## Si bloque
Passer `STATUS: BLOCKED` et completer:
- cause
- fichiers impactes
- action requise
- owner attendu

## EVIDENCE
- fichiers modifies:
- `run_predictions_optimized.py`
- `src/ml/pipeline/train_unified.py`
- `src/ml/pipeline/backtest_hybrid_master_v2.py`
- `src/ml/pipeline/auto_retrain.py`
- `docs/execution/GATE_B3_MAPPING_MIGRATION.md`
- `docs/execution/GATE_B14_CONFORMITE.md`
- `docs/execution/GATE_B15_MATURITE_BAU.md`
- commandes executees:
- `python run_predictions_optimized.py --health`
- `python -c "from src.ml.pipeline.train_unified import UnifiedTrainer"`
- `python -c "from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2"`
- `python -c "from src.ml.pipeline.auto_retrain import AutoRetrainer"`
- resultats:
- reduction scripts: 85 -> 26 (-69%)
- scripts racine: 40+ -> 9 (-77%)
- chaine canonique stable (4 entrypoints)
- gouvernance release/rollback BAU validee

## HANDOFF
- pour C: commandes officielles + expected outputs
- pour ORCH: delta suppression scripts + risques

References:
- `docs/execution/GATE_B3_MAPPING_MIGRATION.md`
- `docs/execution/GATE_B14_CONFORMITE.md`
- `docs/execution/GATE_B15_MATURITE_BAU.md`

## OUTBOX_TO_ORCH
- `B15_DONE: track B cloture, BAU mature, blockers none`

## Checklist finale
- [x] GATE_B1 done
- [x] GATE_B2 done
- [x] GATE_B3 done
- [x] BLOCKERS vide
- [x] HANDOFF rempli
