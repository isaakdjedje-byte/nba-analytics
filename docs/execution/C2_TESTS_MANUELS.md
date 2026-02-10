[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# Guide Tests Manuels C2 - Scénarios 503

**Date:** 2026-02-10  
**Session:** C2 (Frontend Polish)  
**Objectif:** Vérifier gestion 503 betting dans l'interface

---

## 🎯 Scénarios à Tester

### Scénario 1: Page Betting - Service Disponible
**Actions:**
1. Ouvrir `/betting`
2. Vérifier affichage stats et paris actifs
3. Vérifier liste prédictions ≥70%

**Résultat attendu:**
- ✅ Stats affichées (bankroll, win rate, profit, active bets)
- ✅ Liste paris actifs visible
- ✅ Prédictions chargées
- ✅ Bouton "Placer un pari" fonctionnel

---

### Scénario 2: Page Betting - Service Indisponible (503)
**Simulation:** Backend betting répond 503

**Actions:**
1. Ouvrir `/betting` avec service betting down
2. Observer le message d'erreur

**Résultat attendu:**
- ✅ Message: "Service de paris temporairement indisponible"
- ✅ Icône ServerOff (jaune)
- ✅ Prédictions toujours visibles (isolation)
- ✅ Message: "Vous pouvez consulter les prédictions mais pas placer de paris"
- ✅ Bouton "Réessayer" disponible

---

### Scénario 3: Formulaire Pari - Erreur 503
**Actions:**
1. Sélectionner une prédiction
2. Ouvrir le formulaire de pari
3. Remplir stake/odds
4. Soumettre (avec service down)

**Résultat attendu:**
- ✅ Message erreur dans le modal: "Le service de paris est temporairement indisponible"
- ✅ Icône ServerOff (jaune)
- ✅ Formulaire reste ouvert
- ✅ Pas de fermeture brutale

---

### Scénario 4: Dashboard - Stats Indisponibles
**Actions:**
1. Ouvrir `/dashboard`
2. Vérifier affichage avec service betting down

**Résultat attendu:**
- ✅ Message erreur 503 affiché
- ✅ Analysis temporal toujours visible (si disponible)
- ✅ Bouton "Actualiser" fonctionnel

---

### Scénario 5: Récupération après 503
**Actions:**
1. Afficher page avec erreur 503
2. Cliquer "Réessayer"
3. Service redevient disponible

**Résultat attendu:**
- ✅ Chargement des données
- ✅ Disparition du message d'erreur
- ✅ Affichage normal des stats/paris

---

## 🔧 Comment Simuler 503

### Option 1: Backend (Développement)
```python
# Dans nba/api/main.py, temporairement:
@app.get("/api/v1/bets/stats")
def get_bets_stats():
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

### Option 2: Network DevTools
- Ouvrir DevTools (F12)
- Network tab
- Block URL pattern: `*/api/v1/bets/*`
- Recharger la page

### Option 3: Proxy/Mock
- Utiliser un proxy pour intercepter et retourner 503 sur /bets/*

---

## ✅ Checklist Validation

- [ ] Scénario 1: Page Betting normale OK
- [ ] Scénario 2: Message 503 betting affiché correctement
- [ ] Scénario 3: Modal pari gère erreur 503
- [ ] Scénario 4: Dashboard gère 503
- [ ] Scénario 5: Récupération après 503 fonctionne
- [ ] Prédictions visibles même si betting down
- [ ] Messages utilisateur clairs et actionnables
- [ ] Pas de crash/alert() brutaux

---

**Note:** Ces tests sont à réaliser manuellement dans un navigateur.
