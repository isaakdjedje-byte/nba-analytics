# Release Triage Plan

Date: 2026-02-10

## Objectif
Isoler les changements prets a livrer maintenant, sans melanger les modifications runtime/code en cours.

## Baseline deja committee
- `39d6f56` - docs: finalize multi-session closure and normalize C archives
- `4635dac` - chore: add gitignore rules for runtime artifacts

Ces deux commits sont consideres comme le lot "release docs/ops".

## Include now (release-ready)
- `.gitignore`
- `README.md`
- `docs/INDEX.md`
- `docs/JIRA_BACKLOG.md`
- `docs/CHANGELOG.md`
- `docs/execution/**`

## Defer (a ne pas inclure dans ce lot)
- Donnees et artefacts runtime: `data/**`, `predictions/**`, `reports/**`, `*.db`, `*.log`
- Code applicatif en mouvement: `src/**`, `nba/**`, `frontend/**`, `tests/**`
- Archives/scripts one-shot: `archive/**`, scripts legacy racine

## Strategie recommandee
1. Publier d'abord le lot docs/ops (les 2 commits ci-dessus).
2. Ouvrir ensuite une branche de stabilisation code pour traiter le reste par lots fonctionnels.

## Commandes utiles

```bash
# Creer une branche release pour le lot docs/ops
git branch release/closure-docs 4635dac

# Verifier le contenu de la branche
git log --oneline --decorate -2 release/closure-docs
```

## Notes
- Cette approche evite les commits "fourre-tout".
- Elle preserve le travail en cours non committe.
