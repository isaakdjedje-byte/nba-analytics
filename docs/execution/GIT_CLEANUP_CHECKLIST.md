# Git Cleanup Checklist

Date: 2026-02-10

## Objectif
Reduire le bruit Git local en excluant les artefacts runtime (logs, db, exports temporaires, rapports generes).

## Changements appliques
- `.gitignore` mis a jour pour ignorer:
  - logs (`*.log`, `logs/`)
  - bases locales (`*.db`, `*.sqlite`, `*.sqlite3`)
  - artefacts predictions (`predictions/predictions_optimized_*.{csv,json}` etc.)
  - artefacts reports (`reports/2024-25/`, `reports/2025-26/`, `reports/assets/`, `reports/figures/`)
  - artefacts demo (`demo_exports/`)
  - fichier local `cron_job_nba.txt`

## Etapes recommandees (apres merge)
1. Verifier les fichiers ignores:
   - `git status --short`
2. Si des artefacts deja suivis doivent etre desuivis sans suppression locale:
   - `git rm --cached <path>`
   - exemple: `git rm --cached reports/index.html`
3. Revalider:
   - `git status --short`

## Note
Le `.gitignore` n'affecte pas les fichiers deja suivis. Il evite surtout les nouvelles remontees d'artefacts runtime.
