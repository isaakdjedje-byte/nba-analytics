# B4 - Critères de Retrait Wrapper

## 🎯 OBJECTIF
Définir les conditions précises de retrait du wrapper run_predictions.py

**Date de retrait planifiée:** 2026-03-10  
**Date de création:** 2026-02-10  
**Session:** B4 (J2)

---

## 📅 CRITÈRE 1: DATE FIXE

**Date de retrait obligatoire:** 10 mars 2026

### Pourquoi cette date ?
- Durée de transition: 4 semaines (suffisant pour adaptation)
- J1 clôturé le 2026-02-10
- J2 s'étend du 2026-02-10 au 2026-02-28
- Marge de sécurité: 1 semaine supplémentaire

### Conditions de déclenchement anticipé
Le retrait peut être anticipé si **TOUTES** ces conditions sont remplies:
1. ✅ Équipe informée et confirmée (email/ack)
2. ✅ Documentation mise à jour (README, CLI_REF)
3. ✅ Scripts d'automatisation migrés (cron, CI/CD)
4. ✅ Tests E2E passent avec nouvelle commande
5. ✅ Validation ORCH explicite

---

## ✅ CRITÈRE 2: CONDITIONS TECHNIQUES

### Pré-requis bloquants
```bash
# Condition 2.1: Wrapper actif et testé
python run_predictions.py --help 2>&1 | grep -q "obsolete" && echo "✓ Wrapper affiche warning"

# Condition 2.2: Nouveau script fonctionnel
python run_predictions_optimized.py --help > /dev/null && echo "✓ run_predictions_optimized OK"

# Condition 2.3: Chaîne canonique stable
python -c "from src.ml.pipeline.train_unified import UnifiedTrainer; from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2; from src.ml.pipeline.auto_retrain import AutoRetrainer; print('✓ Chaine ML stable')"

# Condition 2.4: Aucun usage critique du wrapper
grep -r "run_predictions.py" --include="*.sh" --include="*.py" . 2>/dev/null | grep -v "run_predictions_optimized" | grep -v "archive/" | grep -v "wrapper" | wc -l | xargs -I {} test {} -eq 0 && echo "✓ Aucun usage critique detecte"
```

### Conditions de validation
- [ ] Tests unitaires: 100% passent
- [ ] Tests E2E: 100% passent
- [ ] Smoke tests: 4/4 entrypoints OK
- [ ] Imports: Aucune erreur
- [ ] Performance: Pas de régression (>5%)

---

## 📢 CRITÈRE 3: COMMUNICATION

### 3.1: Notification préalable (J-7)
**Destinataires:**
- Équipe dev (email/Slack)
- Ops (cron jobs, déploiement)
- QA (tests à adapter)

**Contenu:**
```
Objet: [ACTION REQUIRED] Retrait wrapper run_predictions.py - 2026-03-10

Le wrapper run_predictions.py sera supprimé le 10 mars 2026.

Action requise:
Remplacez: python run_predictions.py [options]
Par:       python run_predictions_optimized.py [options]

Documentation: docs/execution/GATE_B4_MIGRATION_CHECKLIST.md
Checklist:     docs/execution/GATE_B4_MIGRATION_CHECKLIST.md

Contact: B (ML/Pipeline) pour questions.
```

### 3.2: Notification J-1
Rappel final avec:
- Date/heure exacte de retrait
- Procédure rollback (si problème)
- Contact urgence

### 3.3: Notification post-retrait (J+0)
Confirmation du retrait avec:
- Nouvelle baseline
- Tag git gate-b4-migration-complete
- Instructions en cas de problème

---

## 🛡️ CRITÈRE 4: ROLLBACK

### Procédure rollback (si problème post-retrait)
```bash
# Restaurer wrapper depuis backup
git checkout pre-gate-b2-cleanup -- run_predictions.py
# ou
cp archive/wrapper_backup_run_predictions_*.py run_predictions.py
```

### Critères de rollback
- [ ] Commandes cassées en production
- [ ] Scripts d'automatisation échouent
- [ ] Régression critique détectée

---

## 📊 DÉCISION FINALE

### Tableau de bord retrait

| Critère | Statut | Validation |
|---------|--------|------------|
| Date atteinte | ⏳ En attente | 2026-03-10 |
| Wrapper testé | ✅ OK | Warning affiché |
| Nouveau script OK | ✅ OK | --help fonctionne |
| Chaine ML stable | ✅ OK | 4/4 entrypoints |
| Équipe informée | ⏳ En attente | J-7 |
| Doc mise à jour | ⏳ En attente | README, CLI_REF |
| Tests passent | ✅ OK | 100% |
| Backup créé | ⏳ En attente | Archive/ |

### Validation finale ORCH requise
Avant suppression définitive:
- [ ] ACK ORCH sur checklist complète
- [ ] ACK équipe sur migration effectuée
- [ ] Validation tests E2E

---

## 📝 RÉSUMÉ EXÉCUTABLE

```bash
# Vérifier si prêt pour retrait
echo "=== VÉRIFICATION RETRAIT WRAPPER ===" && \
test -f run_predictions.py && echo "✓ Wrapper existe" && \
python run_predictions.py --help 2>&1 | grep -q "obsolete" && echo "✓ Warning affiché" && \
python run_predictions_optimized.py --help > /dev/null && echo "✓ Nouveau script OK" && \
python -c "from src.ml.pipeline.train_unified import UnifiedTrainer; print('✓ Chaine ML OK')" && \
echo "" && \
echo "STATUT: Prêt pour retrait le 2026-03-10"
```

---

**Prochaine action:** Exécuter checklist migration Phase 1
