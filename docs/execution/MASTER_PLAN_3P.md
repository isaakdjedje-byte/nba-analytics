# Master Plan - 3 personnes + 1 orchestrateur

## Objectif
Stabiliser NBA Analytics, supprimer les redondances de code/docs/API, et obtenir une base release-ready.

## Equipe
- Session A: API/Backend
- Session B: ML/Pipeline/Scripts
- Session C: QA/Frontend/Docs
- Session ORCH: Orchestrateur (pilotage global)

## Duree
8 jours (J1 a J8)

## Regles de collaboration
1. Une branche Git par session.
2. Une zone de fichiers claire par session.
3. Pas de changement hors scope sans validation ORCH.
4. Toute progression se fait avec les marqueurs `GATE_*`.
5. Toute dependance bloquante doit etre tracee dans `BLOCKERS`.

## Travail simultane sur le meme PC (recommande)
Utiliser des worktrees pour eviter les conflits entre sessions Opencode:

```bash
git worktree add ../nba-A -b feat/a-api-unification
git worktree add ../nba-B -b feat/b-pipeline-dedup
git worktree add ../nba-C -b feat/c-qa-frontend-docs
git worktree add ../nba-ORCH -b chore/orchestrator-tracking
```

## Convention de statut (obligatoire)
Valeurs autorisees:
- `TODO`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`

Chaque fichier personne doit contenir:
- `STATUS:`
- `LAST_UPDATE:`
- `CURRENT_GATE:`
- `BLOCKERS:`
- `EVIDENCE:`
- `OUTBOX_TO_ORCH:`

## Gates globaux
- `GATE_A1`: contrat API v1 publie par A
- `GATE_B1`: matrice de redondance scripts publiee par B
- `GATE_C1`: baseline QA/docs publiee par C

- `GATE_A2`: endpoints API unifies + services communs
- `GATE_B2`: chaine canonique `train/predict/validate/backtest`
- `GATE_C2`: frontend aligne API v1 + tests stricts v1

- `GATE_A3`: nettoyage backend obsolete
- `GATE_B3`: nettoyage scripts obsoletes
- `GATE_C3`: docs unifiees + validation finale QA

- `GATE_FINAL`: validation finale ORCH

## Dependances
- C attend `GATE_A1` pour figer le contrat API.
- C attend `GATE_B2` pour la finalisation docs/QA pipeline.

## Plan par jour
### J1-J2
- A: cartographie doublons API + contrat v1
- B: inventaire scripts redondants + mapping ancien->nouveau
- C: baseline tests permissifs + audit contradictions docs

### J3-J5
- A: unification backend/API
- B: refactor pipelines/scripts vers chaines canoniques
- C: alignement frontend + durcissement tests

### J6-J7
- A/B: suppression obsoletes apres verification
- C: harmonisation docs + non-regression complete

### J8
- ORCH: consolidation, validation finale, go/no-go

## Critere de done global
- 0 endpoint backend doublon fonctionnel
- -50% scripts redondants minimum
- 100% tests d'integration critiques en assertions strictes
- 0 contradiction majeure dans docs de pilotage

## Verification inter-session (quand quelqu'un attend)
1. Ouvrir le fichier de la session cible dans `docs/execution/`.
2. Verifier:
   - gate attendu marque `DONE`
   - section `EVIDENCE` remplie
   - section `HANDOFF` remplie
3. Verifier les artefacts/files listés dans `EVIDENCE`.
4. Executer les commandes de validation fournies.

## Fichiers de pilotage
- `docs/execution/PERSON_A_API_BACKEND.md`
- `docs/execution/PERSON_B_ML_PIPELINE.md`
- `docs/execution/PERSON_C_QA_FRONT_DOCS.md`
- `docs/execution/ORCHESTRATOR_SESSION.md`
- `docs/execution/MESSAGE_FORMAT.md`
- `docs/execution/PROMPTS/`
