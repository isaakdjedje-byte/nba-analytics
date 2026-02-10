[ARCHIVE STATUS]
Ce document est une preuve historique de cycle.
Source of truth finale: `docs/execution/FINAL_CLOSURE_SUMMARY.md`.
Ne pas utiliser comme statut global courant.

---

# Guide Déploiement Frontend C2

**Date:** 2026-02-10  
**Session:** C2  
**Version:** Frontend polish v1.0

---

## 🚀 Démarrage Application

### Prérequis
```bash
# Backend (dans un terminal)
cd /mnt/c/Users/isaac/nba-analytics
python -m nba.api.main

# Frontend (dans un autre terminal)
cd /mnt/c/Users/isaac/nba-analytics/frontend
npm install  # si première fois
npm run dev
```

### Accès
- Frontend: http://localhost:5173
- API: http://localhost:8000

---

## ✅ Scénarios de Test Manuel

### Scénario 1: Page Betting - Mode Normal
**URL:** http://localhost:5173/betting  
**Attendu:**
- Stats visibles (bankroll, win rate, profit, active bets)
- Liste prédictions ≥70% chargée
- Pari actifs affichés
- Bouton "Placer un pari" fonctionnel

**Validation:**
- [ ] Page se charge sans erreur console
- [ ] Stats s'affichent avec valeurs
- [ ] Prédictions listées
- [ ] Bouton refresh fonctionnel

---

### Scénario 2: Simulation 503 Betting
**Méthode:** Bloquer les requêtes `/api/v1/bets/*` via DevTools

**Étapes:**
1. Ouvrir DevTools (F12)
2. Network tab
3. Clic droit sur requête `/api/v1/bets/stats`
4. Block request URL
5. Recharger la page

**Attendu:**
- Message jaune: "Service de paris temporairement indisponible"
- Icône ServerOff
- Message: "Vous pouvez consulter les prédictions mais pas placer de paris"
- Prédictions toujours visibles (isolation OK)
- Bouton "Réessayer" présent

**Validation:**
- [ ] Message 503 affiché
- [ ] Prédictions accessibles
- [ ] Pas de paris actifs affichés
- [ ] Bouton retry fonctionnel après déblocage

---

### Scénario 3: Formulaire Pari avec 503
**Méthode:** Bloquer requêtes après ouverture modal

**Étapes:**
1. Page betting fonctionnelle
2. Sélectionner une prédiction (clic "Bet")
3. Remplir formulaire (stake: 10, odds: 1.85)
4. Bloquer requêtes `/api/v1/bets` via DevTools
5. Cliquer "Confirm"

**Attendu:**
- Message erreur dans modal: "Le service de paris est temporairement indisponible"
- Icône ServerOff (jaune)
- Formulaire reste ouvert
- Pas de fermeture brutale
- Message détaillé avec conseil

**Validation:**
- [ ] Erreur affichée dans modal
- [ ] Pas de alert() natif
- [ ] Formulaire intact
- [ ] Peut fermer et rouvrir

---

### Scénario 4: Dashboard avec 503
**URL:** http://localhost:5173/dashboard  
**Méthode:** Bloquer `/api/v1/bets/stats`

**Attendu:**
- Message erreur 503 affiché
- Analysis temporal visible (si disponible)
- Bouton "Actualiser" présent

**Validation:**
- [ ] Message 503 contextualisé
- [ ] Analysis chargée séparément
- [ ] Retry fonctionnel

---

### Scénario 5: Récupération après 503
**Étapes:**
1. Activer blocage 503
2. Charger page betting (voir erreur)
3. Débloquer requêtes
4. Cliquer "Réessayer"

**Attendu:**
- Chargement spinner
- Données s'affichent
- Message d'erreur disparaît
- Interface fonctionnelle

**Validation:**
- [ ] Retry fonctionne
- [ ] Données récupérées
- [ ] Pas d'erreur console

---

## 🔍 Vérifications Console

### Ouvrir Console (DevTools)
**Raccourci:** F12 → Console tab

### Vérifier Absence Erreurs
**Attendu:** Aucune erreur rouge liée à C2

**Erreurs acceptables:**
- Warnings React (StrictMode)
- 503 network (si test en cours)

**Erreurs CRITIQUES (bloquant):**
- TypeError: Cannot read property
- ReferenceError: useBetsApi is not defined
- Erreur import module

---

## 📸 Captures Écran Requises (pour rapport 16:02)

### Capture 1: Page Betting Normale
**Fichier:** `c2_betting_normal.png`  
**Contenu:** Stats + prédictions + paris

### Capture 2: Page Betting avec 503  
**Fichier:** `c2_betting_503.png`  
**Contenu:** Message jaune "Service indisponible" + prédictions visibles

### Capture 3: Modal Pari avec Erreur 503
**Fichier:** `c2_betform_503.png`  
**Contenu:** Modal ouvert avec message erreur jaune

### Capture 4: Console (preuve pas d'erreurs)
**Fichier:** `c2_console_clean.png`  
**Contenu:** Console vide ou uniquement warnings acceptables

---

## ✅ Checklist Validation Finale

### Fonctionnel
- [ ] Scénario 1: Betting normal OK
- [ ] Scénario 2: Betting 503 OK
- [ ] Scénario 3: BetForm 503 OK
- [ ] Scénario 4: Dashboard 503 OK
- [ ] Scénario 5: Récupération 503 OK

### Technique
- [ ] Aucune erreur console critique
- [ ] Types TypeScript valides
- [ ] Aucune régression navigation
- [ ] Responsive OK (mobile/desktop)

### Documentation
- [ ] Captures écran prises
- [ ] Rapport 16:02 prêt

---

## 🐛 Dépannage

### Erreur: "Cannot find module '../hooks/useApi'"
**Solution:** Vérifier que useApi.ts existe et exporte useBetsApi

### Erreur: "lucide-react" not found
**Solution:** `npm install lucide-react`

### Page blanche
**Solution:** 
1. Vérifier console erreurs
2. Vérifier backend démarré
3. Recharger (F5)

### 503 ne s'affiche pas
**Solution:** Vérifier que le blocage DevTools est actif sur la bonne URL pattern

---

**Document créé:** 2026-02-10 12:30  
**Session:** C2  
**Pour:** Tests manuels 16:02
