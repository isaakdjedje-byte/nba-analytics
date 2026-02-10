# B4 - Checklist de Migration Executable

## 📋 OBJECTIF
Finaliser la readiness migration ML avec checklist opérationnelle pas-à-pas.

**Date création:** 2026-02-10  
**Session:** B4 (J2)  
**Statut:** IN_PROGRESS

---

## ✅ CHECKLIST MIGRATION - PHASE 1: PRÉPARATION (J-7 avant retrait)

### Étape 1.1: Audit utilisation wrapper
```bash
# Vérifier les logs d'utilisation du wrapper
# Chercher les appels à run_predictions.py dans:
# - cron jobs
# - scripts d'automatisation
# - documentation utilisateur
# - CI/CD pipelines

grep -r "run_predictions.py" --include="*.sh" --include="*.py" --include="*.md" --include="*.txt" . 2>/dev/null | grep -v "run_predictions_optimized" | grep -v "archive/" | head -20
```
**Validation:** Liste des usages identifiés → remplacer par run_predictions_optimized.py

### Étape 1.2: Test complet chaîne canonique
```bash
# Test 1: Entrypoint PREDICT
echo "=== TEST PREDICT ===" && \
python run_predictions_optimized.py --help && \
echo "✓ PREDICT OK"

# Test 2: Entrypoint TRAIN
echo "=== TEST TRAIN ===" && \
python -c "from src.ml.pipeline.train_unified import UnifiedTrainer; t=UnifiedTrainer(); print('✓ TRAIN OK')"

# Test 3: Entrypoint BACKTEST
echo "=== TEST BACKTEST ===" && \
python -c "from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2; b=HybridBacktesterV2(); print('✓ BACKTEST OK')"

# Test 4: Entrypoint RETRAIN
echo "=== TEST RETRAIN ===" && \
python -c "from src.ml.pipeline.auto_retrain import AutoRetrainer; r=AutoRetrainer(); print('✓ RETRAIN OK')"
```
**Validation:** 4/4 tests passent

### Étape 1.3: Vérifier imports transitifs
```bash
# Test imports complets
python -c "
import sys
sys.path.insert(0, 'src/ml/pipeline')

# Chaine PREDICT
from daily_pipeline import DailyPredictionPipeline
from tracking_roi import ROITracker
from nba_live_api import get_today_games
print('✓ Chaine PREDICT OK')

# Chaine TRAIN
from src.ml.pipeline.train_unified import UnifiedTrainer
from src.ml.pipeline.feature_engineering_v3 import FeatureEngineeringV3
print('✓ Chaine TRAIN OK')

# Chaine BACKTEST
from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2
from src.ml.pipeline.live_feature_engineer import LiveFeatureEngineer
print('✓ Chaine BACKTEST OK')

# Chaine RETRAIN
from src.ml.pipeline.auto_retrain import AutoRetrainer
from src.ml.pipeline.model_versioning import ModelVersionManager
from src.ml.pipeline.drift_monitoring import DataDriftMonitor
print('✓ Chaine RETRAIN OK')

print('\\n✅ Toutes les chaines fonctionnelles')
"
```
**Validation:** Aucune erreur d'import

---

## ✅ CHECKLIST MIGRATION - PHASE 2: COMMUNICATION (J-3 avant retrait)

### Étape 2.1: Notification équipe
- [ ] Email/Slack à l'équipe avec:
  - Date de retrait: 2026-03-10
  - Commandes à remplacer
  - Documentation migration
- [ ] Mise à jour README.md section "Démarrage rapide"
- [ ] Mise à jour docs/CLI_REFERENCE.md

### Étape 2.2: Mise à jour documentation
```bash
# Vérifier que la doc mentionne run_predictions_optimized
grep -l "run_predictions" docs/*.md | xargs -I {} sed -i 's/run_predictions\.py/run_predictions_optimized.py/g' {}

# Vérifier scripts et configs
grep -r "run_predictions\.py" --include="*.sh" --include="*.py" . 2>/dev/null | grep -v "archive/" | grep -v "^Binary"
```

---

## ✅ CHECKLIST MIGRATION - PHASE 3: RETRAIT WRAPPER (J-0)

### Étape 3.1: Backup wrapper
```bash
# Créer backup du wrapper avant suppression
cp run_predictions.py archive/wrapper_backup_run_predictions_$(date +%Y%m%d).py
```

### Étape 3.2: Suppression wrapper
```bash
# Supprimer le wrapper (après validation complète)
rm run_predictions.py
```

### Étape 3.3: Vérification post-retrait
```bash
# Tester que le wrapper n'existe plus
test ! -f run_predictions.py && echo "✓ Wrapper supprimé"

# Tester que l'ancienne commande ne fonctionne plus
python run_predictions.py --help 2>&1 | grep -q "No such file" && echo "✓ Ancienne commande bloquée"

# Tester que la nouvelle commande fonctionne
python run_predictions_optimized.py --help > /dev/null && echo "✓ Nouvelle commande OK"
```

---

## ✅ CHECKLIST MIGRATION - PHASE 4: VALIDATION FINALE

### Étape 4.1: Tests non-régression
```bash
# Exécuter tests unitaires
python -m pytest tests/unit/test_ml_pipeline.py -v 2>&1 | tail -20

# Vérifier qu'aucun test ne mentionne run_predictions.py
grep -r "run_predictions\.py" tests/ 2>/dev/null || echo "✓ Tests nettoyés"
```

### Étape 4.2: Validation chaîne complète
```bash
# Test E2E simplifié
python -c "
from src.ml.pipeline.train_unified import UnifiedTrainer
from src.ml.pipeline.backtest_hybrid_master_v2 import HybridBacktesterV2
from src.ml.pipeline.auto_retrain import AutoRetrainer

print('✓ Imports canoniques OK')
print('✓ Chaîne ML complète fonctionnelle')
"
```

### Étape 4.3: Tag git
```bash
# Créer tag de validation
git tag -a gate-b4-migration-complete -m "B4: Wrapper retire, migration ML complete"
```

---

## 📊 CRITÈRES DE SUCCÈS B4

### Obligatoires (bloquants)
- [ ] Wrapper testé et fonctionnel (warning affiché)
- [ ] 4 entrypoints canoniques opérationnels
- [ ] Checklist migration documentée et exécutable
- [ ] Aucune régression sur chaîne ML

### Qualité
- [ ] Documentation mise à jour (README, CLI_REF)
- [ ] Équipe notifiée (date, procédure)
- [ ] Tests unitaires passent
- [ ] Backup wrapper créé

### Post-migration
- [ ] Wrapper supprimé
- [ ] Tag git créé
- [ ] Validation finale OK

---

## 🔍 COMMANDES DE VÉRIFICATION RAPIDE

```bash
# Vérifier état actuel
echo "=== ÉTAT B4 ===" && \
echo "Wrapper existe:" && test -f run_predictions.py && echo "OUI (actif)" || echo "NON (déjà retiré)" && \
echo "" && \
echo "Scripts canoniques:" && \
ls -1 run_predictions_optimized.py src/ml/pipeline/train_unified.py src/ml/pipeline/backtest_hybrid_master_v2.py src/ml/pipeline/auto_retrain.py 2>/dev/null | wc -l && echo "entrypoints présents" && \
echo "" && \
echo "Archive:" && \
ls archive/ | wc -l && echo "scripts archivés"
```

---

**Prochaine étape:** Exécuter la Phase 1 (audit + tests)
