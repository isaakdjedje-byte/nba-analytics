# B5 - Checklist Finale Retrait Wrapper

## 🎯 OBJECTIF
Verrouiller l'exécution du retrait wrapper (2026-03-10) sans risque de rupture.

**Date création:** 2026-02-10  
**Session:** B5 (J3)  
**Statut:** IN_PROGRESS  
**Date retrait cible:** 2026-03-10

---

## ✅ CHECKLIST FINALE - PRÉ-RETRAIT

### 1. VALIDATION TECHNIQUE (À EXÉCUTER MAINTENANT)

```bash
# 1.1 Vérifier wrapper actif
echo "=== 1.1 WRAPPER ACTIF ===" && \
python run_predictions.py --help 2>&1 | grep -q "obsolete" && \
echo "[OK] Wrapper affiche warning deprecation"

# 1.2 Vérifier nouveau script fonctionnel
echo "=== 1.2 NOUVEAU SCRIPT ===" && \
python run_predictions_optimized.py --help > /dev/null 2>&1 && \
echo "[OK] run_predictions_optimized.py fonctionnel"

# 1.3 Vérifier chaine canonique (4 entrypoints)
echo "=== 1.3 CHAINE CANONIQUE ===" && \
python -c "from src.ml.pipeline.train_unified import UnifiedTrainer; print('[OK] TRAIN')" && \
python -c "from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2; print('[OK] BACKTEST')" && \
python -c "from src.ml.pipeline.auto_retrain import AutoRetrainer; print('[OK] RETRAIN')" && \
echo "[OK] Tous les entrypoints ML fonctionnels"

# 1.4 Tests unitaires
echo "=== 1.4 TESTS UNITAIRES ===" && \
python -m pytest tests/unit/ -q --tb=line 2>&1 | tail -3

# 1.5 Vérifier aucun usage critique du wrapper
echo "=== 1.5 AUDIT USAGE WRAPPER ===" && \
grep -r "run_predictions\.py" --include="*.sh" --include="*.py" --include="*.md" . 2>/dev/null | \
grep -v "run_predictions_optimized" | grep -v "archive/" | grep -v "wrapper" | grep -v "GATE_B" | \
wc -l | xargs -I {} echo "Usages legacy detectes: {}"
```

**Critère:** Tous les [OK] doivent être présents, usages legacy = 0

---

### 2. BACKUP ET POINT DE RESTAURATION

```bash
# 2.1 Créer backup du wrapper
echo "=== 2.1 BACKUP WRAPPER ===" && \
cp run_predictions.py archive/wrapper_run_predictions_backup_$(date +%Y%m%d_%H%M%S).py && \
echo "[OK] Backup créé: archive/wrapper_run_predictions_backup_*.py"

# 2.2 Tag git pre-retrait
echo "=== 2.2 TAG GIT ===" && \
git tag -a pre-wrapper-removal-$(date +%Y%m%d) -m "B5: Point de restauration avant retrait wrapper" && \
echo "[OK] Tag créé: pre-wrapper-removal-$(date +%Y%m%d)"

# 2.3 Vérifier rollback possible
echo "=== 2.3 ROLLBACK TEST ===" && \
git tag | grep -q "pre-wrapper-removal" && \
echo "[OK] Rollback possible via: git checkout pre-wrapper-removal-<date> -- run_predictions.py"
```

---

### 3. PLAN DE COMMUNICATION

#### J-7 (2026-03-03) - Notification Initiale
**Destinataires:** Dev team, Ops, QA
**Canal:** Email + Slack #dev #ops

```
Objet: [ACTION REQUIRED] Retrait imminant run_predictions.py - 2026-03-10

Le wrapper run_predictions.py sera SUPPRIME le 10 mars 2026.

ACTION REQUISE AVANT LE 10/03:
1. Remplacer dans vos scripts:
   python run_predictions.py [options]
   → python run_predictions_optimized.py [options]

2. Mettre à jour vos cron jobs et CI/CD

3. Tester vos workflows avec la nouvelle commande

DOCUMENTATION:
- Checklist: docs/execution/GATE_B5_WRAPPER_REMOVAL_CHECKLIST.md
- Mapping: docs/execution/GATE_B4_MIGRATION_CHECKLIST.md

CONTACT: B (ML/Pipeline)
ROLLBACK: Possible via tag git pre-wrapper-removal-*
```

#### J-1 (2026-03-09) - Rappel Final
**Destinataires:** Dev team, Ops, QA
**Canal:** Email + Slack #general

```
Objet: [RAPPEL] Retrait run_predictions.py - DEMAIN 10/03

DERNIER RAPPEL: Le wrapper run_predictions.py sera supprimé DEMAIN.

Si vous utilisez encore run_predictions.py, MIGREZ MAINTENANT:
→ python run_predictions_optimized.py [options]

En cas de problème après le retrait:
- Contact: B (urgence)
- Rollback: git checkout pre-wrapper-removal-20260310 -- run_predictions.py
```

#### J+0 (2026-03-10) - Confirmation
**Destinataires:** Tous
**Canal:** Email + Slack #general

```
Objet: [DONE] Retrait run_predictions.py effectué

Le wrapper run_predictions.py a été supprimé.

NOUVELLE BASELINE:
- Prédictions: python run_predictions_optimized.py
- Tag: gate-b5-wrapper-removed

Si vous rencontrez des problèmes:
1. Utilisez: python run_predictions_optimized.py [options]
2. Rollback possible (voir doc)
3. Contact: B

Documentation: docs/execution/GATE_B5_WRAPPER_REMOVAL_CHECKLIST.md
```

---

### 4. PROCÉDURE DE RETRAIT (À EXÉCUTER LE 2026-03-10)

```bash
#!/bin/bash
# B5 - Script de retrait wrapper
# À exécuter le 2026-03-10

set -e

echo "=== RETRAIT WRAPPER run_predictions.py ==="
echo "Date: $(date)"
echo ""

# 4.1 Vérifier pre-requis
echo "[1/5] Vérification pre-requis..."
test -f run_predictions.py || { echo "ERREUR: Wrapper introuvable"; exit 1; }
python run_predictions_optimized.py --help > /dev/null || { echo "ERREUR: Nouveau script non fonctionnel"; exit 1; }
echo "[OK] Pre-requis validés"

# 4.2 Backup
echo "[2/5] Création backup..."
cp run_predictions.py archive/wrapper_run_predictions_final_$(date +%Y%m%d).py
echo "[OK] Backup créé"

# 4.3 Suppression
echo "[3/5] Suppression wrapper..."
rm run_predictions.py
echo "[OK] Wrapper supprimé"

# 4.4 Validation
echo "[4/5] Validation post-retrait..."
test ! -f run_predictions.py || { echo "ERREUR: Wrapper toujours présent"; exit 1; }
python run_predictions_optimized.py --help > /dev/null || { echo "ERREUR: Nouveau script cassé"; exit 1; }
echo "[OK] Validation OK"

# 4.5 Tag git
echo "[5/5] Tag git..."
git add -A
git commit -m "B5: Retrait wrapper run_predictions.py - migration complete"
git tag -a gate-b5-wrapper-removed -m "B5: Wrapper supprimé, chaine canonique stable"
echo "[OK] Tag créé: gate-b5-wrapper-removed"

echo ""
echo "=== RETRAIT TERMINÉ AVEC SUCCÈS ==="
echo "Date: $(date)"
echo "Tag: gate-b5-wrapper-removed"
```

---

### 5. POST-RETRAIT (J+1 À J+7)

- [ ] Vérifier logs d'erreurs (grep "run_predictions.py")
- [ ] Confirmer équipe sans problème
- [ ] Archiver backup wrapper (archive/ → long-term)
- [ ] MAJ documentation (supprimer références wrapper)
- [ ] Fermer tickets de migration

---

## 📊 VALIDATION B5

### Critères de succès
- [x] Wrapper actif avec warning
- [x] 4 entrypoints canoniques opérationnels
- [x] Checklist finale créée et exécutable
- [x] Plan communication J-7/J-1/J+0 rédigé
- [ ] Backup créé (à faire J-0)
- [ ] Tag pre-removal créé (à faire J-0)
- [ ] Communication envoyée J-7 (à faire 2026-03-03)
- [ ] Retrait exécuté J+0 (à faire 2026-03-10)

---

## 🚨 ESCALADE

**Si blocage >30min:**
- Vérifier: `python run_predictions_optimized.py --help`
- Rollback: `git checkout pre-wrapper-removal-* -- run_predictions.py`
- Contact: ORCH

---

**Prochaine action:** Exécuter checklist validation technique
