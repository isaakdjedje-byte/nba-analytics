[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# C4 - Campagne Non-Régression Full

**Session:** C4 (Validation Finale UX/API)  
**Date début:** 2026-02-10 13:05  
**Durée estimée:** 4h  
**Statut:** IN_PROGRESS (préparation)  
**Dépendances:** A5 (hardening backend), B4 (mapping/migration final)

---

## 🎯 OBJECTIFS C4

### 1. Campagne Non-Régression API
- Réexécuter lot tests stricts complet (18/18)
- Valider stabilité contrat API v1 final
- Vérifier endpoints critiques (predictions, bets, analysis, calendar)

### 2. Validation UX Erreurs/503
- Scénarios erreurs (422, 503, 500, network)
- Gestion 503 betting (isolation parcours)
- Messages utilisateur contextuels
- Boutons retry fonctionnels

### 3. Parcours Critiques
- Visualisation calendrier + prédictions
- Placement pari paper trading
- Mise à jour résultat pari
- Navigation inter-pages

---

## 🔒 DÉPENDANCES EXTERNES

### A5 - Backend Hardening Note
**Statut:** ⏳ WAITING  
**Attendu:**
- Notes de hardening backend
- Optimisations performances API
- Corrections bugs mineurs identifiés
- Validation contrat API v1 final

### B4 - Mapping/Migration Final
**Statut:** ⏳ WAITING  
**Attendu:**
- Mapping final données frontend
- Migration schémas si applicable
- Documentation intégration
- Validation compatibilité B4→C4

---

## 📋 MATRICE DE PREUVES

### Matrice 1: Tests API Stricts
| Endpoint | Méthode | Test J5 | Statut C4 | Preuve |
|----------|---------|---------|-----------|--------|
| /api/v1/predictions | GET | test_predictions_endpoint_exists | ⏳ | |
| /api/v1/predictions | GET | test_predictions_schema_valid | ⏳ | |
| /api/v1/predictions | GET | test_predictions_min_confidence_filter | ⏳ | |
| /api/v1/predictions | GET | test_predictions_view_week_deprecated | ⏳ | |
| /api/v1/predictions | GET | test_predictions_team_filter | ⏳ | |
| /api/v1/predictions | GET | test_predictions_field_types | ⏳ | |
| /api/v1/bets | POST | test_place_bet_success | ⏳ | |
| /api/v1/bets | POST | test_place_bet_invalid_stake_negative | ⏳ | |
| /api/v1/bets | POST | test_place_bet_invalid_odds_low | ⏳ | |
| /api/v1/bets | GET | test_get_bets_list | ⏳ | |
| /api/v1/bets | POST | test_update_bet_result | ⏳ | |
| /api/v1/bets/stats | GET | test_get_bets_stats | ⏳ | |
| /api/v1/bets | - | test_betting_degradation_503 | ⏳ | |
| /api/v1/analysis/temporal | GET | test_analysis_temporal_exists | ⏳ | |
| /api/v1/analysis/temporal | GET | test_analysis_temporal_schema | ⏳ | |
| E2E | - | test_prediction_to_bet_flow | ⏳ | |
| E2E | - | test_deprecated_view_week_still_works | ⏳ | |

**Total:** 18 tests  
**Objectif:** 18/18 PASS ✅

### Matrice 2: Scénarios UX Erreurs
| Scénario | Page | Type Erreur | Attendu | Statut C4 | Preuve |
|----------|------|-------------|---------|-----------|--------|
| 503 betting indisponible | Betting | 503 | Message jaune + prédictions visibles | ⏳ | |
| 503 service temporaire | Dashboard | 503 | ErrorDisplay + retry | ⏳ | |
| 422 validation stake | BetForm | 422 | Message erreur modal | ⏳ | |
| 422 validation odds | BetForm | 422 | Message erreur modal | ⏳ | |
| Erreur réseau | Global | Network | Message connection | ⏳ | |
| Retry après erreur | All | - | Fonctionnel | ⏳ | |

**Total:** 6 scénarios  
**Objectif:** 6/6 PASS ✅

### Matrice 3: Parcours Critiques
| Parcours | Étapes | Départ | Arrivée | Statut C4 | Preuve |
|----------|--------|--------|---------|-----------|--------|
| Visualisation calendrier | 1. Charger /predictions<br>2. Naviguer calendrier<br>3. Sélectionner date<br>4. Voir matchs | /predictions | Détail jour | ⏳ | |
| Placement pari | 1. Voir prédictions<br>2. Sélectionner match<br>3. Ouvrir formulaire<br>4. Valider pari | Liste prédictions | Paris actifs | ⏳ | |
| Mise à jour résultat | 1. Voir paris actifs<br>2. Cliquer Win/Loss<br>3. Confirmer | Paris actifs | Historique mis à jour | ⏳ | |
| Navigation inter-pages | 1. Dashboard<br>2. Betting<br>3. Predictions<br>4. Retour | Dashboard | Toutes pages | ⏳ | |

**Total:** 4 parcours  
**Objectif:** 4/4 PASS ✅

---

## ⏱️ PLANNING C4

### Phase 1: Préparation (Maintenant - Réception A5/B4)
- [x] Créer documentation C4
- [x] Préparer matrices de preuves
- [ ] Analyse préliminaire dépendances
- [ ] Attente signaux A5_VALIDATED et B4_VALIDATED

### Phase 2: Exécution (Dès A5/B4 reçus - ~2h)
- [ ] Réexécution tests J5 complets (18 tests)
- [ ] Validation scénarios UX erreurs/503 (6 scénarios)
- [ ] Tests parcours critiques (4 parcours)
- [ ] Documentation résultats

### Phase 3: Validation (~1h)
- [ ] Compilation preuves
- [ ] Vérification non-régression
- [ ] Rapport final C4
- [ ] Proposition C4_DONE

---

## 📁 DOCUMENTATION PRÉPARÉE

1. **C4_PLAN.md** (ce document) - Planning et matrices
2. **C4_MATRICE_PREUVES.md** - Détail matrices (à créer)
3. **C4_RAPPORT.md** - Template rapport final (à créer)

---

## 🚨 POINTS DE VIGILANCE

### Risques Identifiés
1. **A5/B4 en retard** - Impact: décalage C4
   - Mitigation: Préparation en amont, exécution rapide dès réception
   
2. **Régression A5** - Impact: tests J5 échouent
   - Mitigation: Campagne non-régression complète, signalement immédiat
   
3. **Incompatibilité B4** - Impact: mapping frontend cassé
   - Mitigation: Tests parcours critiques, validation B4→C4

### Critères Succès C4
- ✅ Tests J5: 18/18 PASS
- ✅ Scénarios UX: 6/6 PASS
- ✅ Parcours critiques: 4/4 PASS
- ✅ Aucune régression identifiée
- ✅ Documentation complète

---

## 📊 INDICATEURS CLÉS

| Indicateur | Cible | Baseline | Tolérance |
|------------|-------|----------|-----------|
| Tests J5 passed | 18/18 | 18/18 | 0 échec |
| Scénarios UX passed | 6/6 | 5/6 (C2) | +1 |
| Parcours critiques passed | 4/4 | 4/4 (C2) | 0 échec |
| Temps exécution | <2h | - | ±30min |
| Documentation | 100% | 100% | - |

---

**Document créé:** 2026-02-10 13:05  
**Session:** C4  
**Statut:** Préparation - Attente A5/B4  
**Prochaine action:** Réception dépendances → Exécution C4
