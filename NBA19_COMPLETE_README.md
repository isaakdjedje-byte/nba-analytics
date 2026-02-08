# NBA-19 Complete Mode - Instructions

## 🎯 Objectif
Traiter les **5 103 joueurs** pour trouver leur historique d'équipes (1946-2024) en **~3h45**.

## 📋 Architecture

```
Phase 1: Pre-validation (DEJA FAITE) ✅
   └── Segmentation en 3 cohortes (GOLD/SILVER/BRONZE)

Phase 2: Discovery complet (~3h)
   ├── Segment A (GOLD): 1 193 joueurs (~40 min)
   ├── Segment B (SILVER): 7 joueurs (~2 min)
   └── Segment C (BRONZE): 3 903 joueurs (~2h10)

Phase 3: Validation (~15 min)
   └── Cross-validation avec rosters 2018-2024

Phase 4: Enrichissement (~20 min)
   └── Career summaries + position inference

Phase 5: Consolidation (~10 min)
   └── Exports finaux (JSON)
```

## 🚀 Commande Unique

**Pour lancer tout le processus:**

```bash
python nba19_complete_orchestrator.py
```

**Ou par étapes individuelles:**

```bash
# Phase 2 seule (si tu veux juste le discovery)
python src/ingestion/nba19/ultimate_discovery/phase2_discovery_all.py

# Phase 3 seule (validation)
python src/ingestion/nba19/ultimate_discovery/phase3_validation.py

# etc.
```

## ⏱️ Timeline

| Heure | Phase | Durée | Cumulé |
|-------|-------|-------|--------|
| T+0:00 | Démarrage | - | - |
| T+0:40 | Fin Phase 2A (GOLD) | 40 min | 40 min |
| T+0:42 | Fin Phase 2B (SILVER) | 2 min | 42 min |
| T+2:32 | Fin Phase 2C (BRONZE) | 130 min | 2h52 |
| T+2:47 | Fin Phase 3 | 15 min | 3h07 |
| T+3:07 | Fin Phase 4 | 20 min | 3h27 |
| T+3:17 | Fin Phase 5 | 10 min | 3h37 |
| **T+3:37** | **TERMINÉ** | - | **~3h37** |

## 📁 Livrables

Créés dans `data/gold/nba19/`:

```
data/gold/nba19/
├── player_team_history_complete.json    # ~15-20 MB
│   └── Tous les mappings joueur-saison-équipe
├── team_season_rosters.json             # ~5 MB
│   └── Vue par équipe/saison
├── career_summaries.json                # ~2 MB
│   └── Résumés de carrière par joueur
├── quality_report.json                  # ~100 KB
│   └── Métriques de qualité
└── manual_review_queue.json             # ~50 KB
    └── Top 100 joueurs à valider manuellement
```

## 🛡️ Protection

Le système gère automatiquement:
- **Checkpoints**: Toutes les 50 joueurs (reprise possible)
- **Rate limiting**: 1 req / 2 sec (respect API)
- **Circuit breaker**: Pause si >10% erreurs
- **Retry**: 3 tentatives par joueur

## ⚠️ Prérequis

Avant de lancer:

1. **Espace disque**: Au moins 1 GB libre
2. **Connexion**: Internet stable pendant 4h
3. **Python**: nba-api installé (`pip install nba-api`)
4. **Phase 1**: Doit être déjà faite (segments créés)

## 🔄 Reprise après interruption

Si le processus s'arrête:

```bash
# Il reprend automatiquement depuis le dernier checkpoint
python nba19_complete_orchestrator.py
```

Les checkpoints sont dans `logs/nba19_discovery/checkpoints/`.

## 📊 Monitoring

Pendant l'exécution, tu verras:

```
[PROGRESS] 150/5103 (3%) - ETA: 3h 12m
[ 150/5103] Player Name          ... [OK] 12 equipes
[ 151/5103] Other Player         ... [FAIL] Pas de donnees
```

## 🎉 Fin du processus

Quand c'est terminé, tu verras:

```
[COMPLETE] Toutes les phases terminees!
Temps total: 3h 37m
Termine: 2026-02-08 02:24:00
```

## ❓ Questions fréquentes

**Q: Puis-je arrêter et reprendre plus tard?**  
R: Oui, les checkpoints sauvegardent la progression toutes les 50 joueurs.

**Q: Et si l'API rate limit?**  
R: Le script fait une pause de 30s toutes les 100 requêtes.

**Q: Combien de joueurs vont échouer?**  
R: Estimé 5-10% (joueurs sans données API ou erreurs).

**Q: Les données sont-elles fiables?**  
R: Oui, cross-validées avec les rosters 2018-2024 (ground truth).

## 🚀 GO !

```bash
python nba19_complete_orchestrator.py
```

Laisse tourner et reviens dans ~3h45 ! 🎉
