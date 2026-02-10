# B12 - Gouvernance Release ML

## CRITÈRES GO/NO-GO RELEASE

### GO (Tous obligatoires)
- [ ] Tests unitaires: 100% pass
- [ ] 4 entrypoints importables
- [ ] Documentation à jour
- [ ] Review code validée
- [ ] Backups créés

### NO-GO (Bloquants)
- [ ] Échec tests critiques
- [ ] Régression détectée
- [ ] Dépendances cassées
- [ ] Pas de backup

## CHECKLIST PRÉ-RELEASE

1. **Validation technique**
   - Tests: `pytest tests/unit/ -q`
   - Entrypoints: 4/4 fonctionnels
   - Imports: Aucune erreur

2. **Documentation**
   - README mis à jour
   - Changelog complété
   - Runbook valide

3. **Backup**
   - `cp -r models/unified/ backup/models_$(date +%Y%m%d)`
   - Tag git: `git tag pre-release-$(date +%Y%m%d)`

4. **Fenêtre validation**
   - Durée: 2 heures
   - Tests E2E: obligatoires
   - Rollback testé: oui

## ROLLBACK READINESS

### Procédure (2 minutes)
```bash
# Restauration rapide
git checkout pre-release-$(date +%Y%m%d) -- src/ml/
cp -r backup/models_$(date +%Y%m%d)/ models/unified/
```

### Points de restauration
- Tag: `B7_VALIDATED` (baseline stable)
- Backup: `backup/models_YYYYMMDD/`
- Dernier: `pre-release-$(date +%Y%m%d)`

### Test rollback
```bash
# Validation
python run_predictions_optimized.py --health
python -c "from src.ml.pipeline.train_unified import UnifiedTrainer"
```

## GOVERNANCE ROUTINE

**Release mineure:** Weekly (lundi)
**Release majeure:** Monthly (1er)
**Hotfix:** Sur demande ORCH

**Responsable:** B (ML Team)
**Validation:** Tests auto + Review ORCH
**Rollback:** Disponible immédiat

---
**B12 COMPLETED** - Gouvernance ML formalisée
