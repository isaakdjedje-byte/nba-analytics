[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# Livrable C1 - Audit QA/Docs

**GATE:** C1  
**DATE:** 2026-02-10  
**STATUT:** Préparation complétée (attente A1_VALIDATED)  

---

## 1. LISTE DES TESTS PERMISSIFS À CORRIGER

### 🔴 CRITIQUE (12 cas) - À corriger J3

| Fichier | Ligne | Problème | Correction Proposée | Impact |
|---------|-------|----------|---------------------|--------|
| `tests/e2e/test_docker.py` | 121 | `assert True` inconditionnel | Vérifier retour socket réel | Docker peut être down sans échec test |
| `tests/e2e/test_docker.py` | 132 | `assert True` inconditionnel | Vérifier retour socket réel | Docker peut être down sans échec test |
| `tests/e2e/test_docker.py` | 143 | `assert True` inconditionnel | Vérifier retour socket réel | Docker peut être down sans échec test |
| `tests/integration/test_api.py` | 91 | `assert status in [200,404]` | Accepter uniquement 200, 404 si testé explicitement | Tests passe même si endpoint cassé |
| `tests/integration/test_api.py` | 120 | `assert status in [200,404,500]` | Valider comportement attendu précis | Accepte erreurs serveur comme succès |
| `tests/integration/test_api.py` | 130 | `assert status in [200,404,500]` | Idem | Accepte erreurs serveur comme succès |
| `tests/integration/test_api.py` | 140 | `assert status in [400,422,500]` | Valider code précis attendu | Trop permissif |
| `tests/integration/test_api.py` | 161 | `assert status in [200,500]` | Accepter uniquement 200 | Accepte erreurs serveur comme succès |
| `tests/test_clean_players.py` | 185 | `assert True` inconditionnel | Vérifier import avec `assert callable(PlayersDataCleaner)` | Import peut échouer silencieusement |
| `tests/test_nba19_integration.py` | 157 | `assert True` après try/except vide | Vérifier exception levée explicitement | Exception non détectée |
| `tests/test_ml_pipeline_critical.py` | 398-405 | Assertions tautologiques | Supprimer ou remplacer par validation métier | Tests sans valeur ajoutée |
| `tests/test_integration.py` | 33 | `except: pass` vide | Logger ou propager l'erreur | Erreurs masquées |

### 🟡 MAJEUR (14 cas) - À corriger J3-J4

| Fichier | Problème | Nbre | Description |
|---------|----------|------|-------------|
| `tests/test_schema_evolution.py` | `pytest.skip` module-level | 1 | Skip Python 3.14 (acceptable mais doit être documenté) |
| `tests/test_nba21_features.py` | `pytest.skip` sans données | 1 | Skip si features manquantes (doit tenter création) |
| `tests/test_integration.py` | `pytest.skip` sans données | 3 | Skip si GOLD Premium indisponible (mock manquant) |
| `tests/test_nba19_integration.py` | `pytest.skip` sans données | 3 | Skip si données joueurs/matchs manquantes |
| `tests/test_stratification.py` | `pytest.skip` sans données | 1 | Skip si données test indisponibles |
| `tests/test_advanced_metrics.py` | `try/except` multiples | 5 | Attrape exceptions sans assertion (masquage erreurs) |

### 🟢 MINEUR (8 cas) - À corriger J6

- Tests avec assertions faibles (non-strictes)
- Commentaires `# TODO` ou `# FIXME` non résolus
- Tests avec tolerances trop larges

---

## 2. CONTRADICTIONS DOCUMENTAIRES IDENTIFIÉES

### 🔴 MAJEUR - Version du Projet

| Document | Version Déclarée | Incohérence |
|----------|------------------|-------------|
| `README.md` | Non spécifiée | Aucune version mentionnée |
| `CHANGELOG.md` | 2.0.0 | Référence version calendrier V2 |
| `ARCHITECTURE_V2.md` | 2.0.1 | Dit "Production Ready" |
| `API_REFERENCE.md` | 2.0.0 | API version 2.0.0 |
| `docs/agent.md` | 10.0 | "PROJET 100% COMPLET" |
| `nba/config.py` | 2.0.0 | Settings.version = "2.0.0" |

**Source of Truth proposée:** `CHANGELOG.md` (2.0.0)

### 🔴 MAJEUR - Statut du Projet

| Document | Statut | Incohérence |
|----------|--------|-------------|
| `docs/agent.md` | "100% COMPLET - TOUTES LES STORIES TERMINÉES" | Déclare tout fini |
| `docs/INDEX.md` | "PROJET 100% COMPLET" | Même message |
| `CHANGELOG.md` | "Version 2.0.0 - Système Calendrier V2" | Suggère évolution continue |
| `docs/execution/*.md` | STATUS: TODO/IN_PROGRESS | Les gates montrent travail en cours |
| `docs/JIRA_BACKLOG.md` | Stories NBA-18 à NBA-22-3 en "To Do" | Conflit avec "100% complet" |

**Anomalie:** "100% complet" vs gates TODO et stories en cours

### 🟡 MINEUR - Dates et Terminologie

| Élément | Valeurs | Standardisation |
|---------|---------|-----------------|
| Format dates | "10 Février 2026" vs "2026-02-10" vs "09/02/2026" | Uniformiser ISO 8601 |
| Terme "complet" | "complet", "COMPLET", "terminé", "TERMINÉ" | Uniformiser "TERMINÉ" |
| Nombre tests | "67+ tests", "67+ automatisés", "78+ tests" | Vérifier et fixer nombre exact |
| Accuracy | "83.03%" vs "76.76%" vs "77.77%" | Contextualiser (modèle/scenario) |

---

## 3. PLAN DE CORRECTION J3-J7

### J3 - Correction Tests Critiques
**Objectif:** Éliminer faux positifs

**Tâches:**
1. `test_docker.py`:121,132,143 - Remplacer `assert True` par vérification réelle
2. `test_api.py` - Restreindre assertions aux codes attendus précis
3. `test_clean_players.py`:185 - Assertion sur import explicite
4. `test_nba19_integration.py`:157 - Gestion d'erreur explicite
5. `test_ml_pipeline_critical.py`:398-405 - Supprimer assertions tautologiques

**Validation:** Tous les tests doivent pouvoir échouer si comportement incorrect

### J4 - Unification Documentation
**Objectif:** Aligner versions et statuts

**Tâches:**
1. Harmoniser version: 2.0.0 partout
2. Clarifier statut: "Phase stabilisation/refactoring (J1-J8)" vs "100% feature-complete"
3. Mettre à jour JIRA_BACKLOG.md: passer stories complétées à "Done"
4. Standardiser dates au format ISO

### J5 - Durcissement Tests API
**Objectif:** Assertions strictes sur contrat API

**⚠️ ATTENDRE A1_VALIDATED**

**Tâches:**
1. Récupérer contrat API v1 (endpoints, payload schema)
2. Remplacer `assert status in [200,404,500]` par validations strictes
3. Ajouter validation schema JSON des réponses
4. Tests frontend: valider mapping exact endpoints

**Livrable:** Tests API avec assertions strictes sur codes + payloads

### J6 - Corrections Mineures
**Objectif:** Polissage

**Tâches:**
1. Résoudre TODO/FIXME dans tests
2. Uniformiser terminologie (complet/terminé/done)
3. Ajuster tolerances tests si nécessaire
4. Documentation des pytest.skip légitimes

### J7 - Validation Finale
**Objectif:** Marquer C1 comme DONE

**Tâches:**
1. Exécuter suite tests complète
2. Vérifier cohérence docs
3. Remplir section EVIDENCE
4. Émettre marqueur `GATE_C1: DONE @YYYY-MM-DD HH:MM`

---

## 4. ÉLÉMENTS BLOQUÉS PAR A1

| Élément | Dépendance | Action après A1_VALIDATED |
|---------|------------|---------------------------|
| Tests API stricts | Contrat API v1 | Remplacer OR logique par assertions précises |
| Validation schema | Payloads exemples | Ajouter validation JSON schema |
| Frontend alignment | Endpoints finaux | Mettre à jour frontend/src/lib/api.ts |
| Tests integration E2E | API stable | Créer tests bout-en-bout frontend-backend |

---

## 5. CHECKLIST PRÉ-EXÉCUTION

- [x] Audit tests permissifs réalisé
- [x] Liste contradictions docs établie
- [ ] Créer fichier de suivi corrections (tracking.md)
- [ ] Préparer branches git pour J3-J7
- [ ] Documenter dépendances A1 dans BLOCKERS

---

**PRÊT POUR EXÉCUTION J3** (sauf éléments dépendants A1)

**Prochaine action:** Attendre 15:00 ou A1_VALIDATED