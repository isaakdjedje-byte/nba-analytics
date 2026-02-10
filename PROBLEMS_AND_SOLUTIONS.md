# 🔧 PROBLÈMES CONNUS ET SOLUTIONS

**Dernière mise à jour :** 09/02/2026  
**Session :** Dashboard & Predictions Implementation

---

## 🔴 PROBLÈMES CRITIQUES (À RÉSOUDRE IMMÉDIATEMENT)

### **1. Champs Date Non Visibles dans l'API**

**Statut :** 🔄 En cours de correction  
**Impact :** Les prédictions ne montrent pas les horaires des matchs

**Symptômes :**
```bash
curl http://localhost:8000/api/v1/predictions
# Retourne : {"game_date": null, "game_time_fr": null}
```

**Causes possibles :**
- [ ] Cache Python (module non rechargé)
- [ ] Fichier JSON pas lu correctement
- [ ] Modèle Pydantic mal appliqué
- [ ] Processus backend ancien toujours actif

**Solutions à tester :**

```bash
# 1. Kill complet de tous les processus Python
taskkill /F /IM python.exe
taskkill /F /IM python
sleep 3

# 2. Vérifier aucun processus ne tourne
ps aux | grep python | grep -v grep

# 3. Redémarrage frais
python -m nba.api.main

# 4. Test avec curl
curl -s "http://localhost:8000/api/v1/predictions?min_confidence=0" | \
  python -c "import sys,json;d=json.load(sys.stdin);print('game_date:',d['predictions'][0].get('game_date'))"
```

**Vérification :**
- [ ] La réponse doit contenir : `"game_date": "2026-02-09"`
- [ ] La réponse doit contenir : `"game_time_fr": "01:00"`

---

### **2. Dashboard Affiche Vide ou "null"**

**Statut :** 🔄 En cours de correction  
**Impact :** Impossible de voir les stats paper trading

**Symptômes :**
- Dashboard affiche des valeurs vides
- Ou affiche "null" au lieu de "0"

**Solutions :**

```bash
# Vérifier que paper_trading_db.py est bien modifié
cat src/betting/paper_trading_db.py | grep -A 10 "def get_stats"

# Doit contenir :
# - Valeurs par défaut à 0
# - Boucle for remplaçant None par 0

# Redémarrer backend
taskkill /F /IM python.exe
python -m nba.api.main

# Test API
curl http://localhost:8000/api/v1/bets/stats
# Doit retourner : {"total_bets": 0, "win_rate": 0.0, ...}
```

---

## 🟡 PROBLÈMES MOYENS (À RÉSOUDRE BIENTÔT)

### **3. Port Déjà Utilisé (Erreur 10048)**

**Erreur :**
```
[WinError 10048] only one usage of each socket address is normally permitted
```

**Solution :**
```bash
# Windows
npx kill-port 8000 5173
# ou
netstat -ano | findstr ":8000"
taskkill /F /PID <PID>

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

### **4. Frontend Pas de Hot Reload**

**Symptômes :**
- Modifications fichiers non visibles
- Ancien code encore affiché

**Solutions :**
```bash
# Vider cache Vite
cd frontend
rm -rf node_modules/.vite
npm run dev -- --host

# Ou redémarrage complet
Ctrl+C  # Arrêter
cd .. && cd frontend  # Recharger
npm run dev -- --host
```

---

## 🟢 PROBLÈMES FAIBLES (PEUVENT ATTENDRE)

### **5. Navigateur Intégré Ne Peut Pas Accéder à Localhost**

**Impact :** Tests visuels difficiles depuis l'environnement de développement

**Solution :** Utiliser navigateur externe
```
# Au lieu de : MCP_DOCKER_browser_navigate
# Utiliser : Chrome, Edge, Firefox directement
http://localhost:5173
```

---

### **6. Unicode Error dans Terminal Windows**

**Erreur :**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution :** Utiliser uniquement ASCII dans les commandes
```bash
# ❌ Éviter : print('✓ OK')
# ✅ Utiliser : print('OK')
```

---

## 📋 CHECKLIST DE DÉMARRAGE

Avant de lancer le projet, vérifier :

```bash
# 1. Ports libres ?
netstat -ano | findstr ":8000 :5173" | wc -l
# Doit retourner 0

# 2. Processus Python arrêtés ?
tasklist | findstr "python"
# Doit retourner vide

# 3. Fichier prédictions avec dates existe ?
ls -lh predictions/predictions_20260209*.json
# Doit afficher le fichier

# 4. Dépendances frontend installées ?
cd frontend && ls node_modules | head -5
# Doit afficher des dossiers

# 5. Backend démarre sans erreur ?
python -m nba.api.main 2>&1 | head -10
# Doit afficher : "Application startup complete"
```

---

## 🎯 PROCEDURE DE DEBUG

### **Si Dashboard Vide :**

```bash
# 1. Vérifier backend répond
curl http://localhost:8000/health

# 2. Vérifier stats retournées
curl http://localhost:8000/api/v1/bets/stats

# 3. Vérifier prédictions retournées
curl "http://localhost:8000/api/v1/predictions?min_confidence=0"

# 4. Vérifier logs backend
tail -20 backend.log

# 5. Vérifier logs frontend
cd frontend && cat frontend.log | tail -20
```

### **Si Predictions Ne Charge Pas :**

```bash
# 1. Vérifier API accessible
curl http://localhost:8000/api/v1/predictions

# 2. Vérifier structure JSON
# Doit contenir : predictions[], count, view

# 3. Vérifier dates présentes
# Doit contenir : game_date, game_time_fr

# 4. Si dates manquantes → Voir Problème #1
```

---

## 🆘 CONTACT ET SUPPORT

**En cas de problème persistant :**

1. **Vérifier ce fichier** : `PROBLEMS_AND_SOLUTIONS.md`
2. **Consulter les logs** : `backend.log`, `frontend.log`
3. **Redémarrage complet** : Kill all + restart
4. **Session de debug** : Planifier avec l'équipe

---

## ✅ STATUT ACTUEL (09/02/2026 21:00)

| Problème | Statut | Priorité |
|----------|--------|----------|
| Champs date API | 🔄 En correction | 🔴 Critique |
| Dashboard vide | 🔄 En correction | 🔴 Critique |
| Port occupé | ✅ Solutionné | 🟡 Moyen |
| Hot reload | ✅ Solutionné | 🟡 Moyen |
| Navigateur intégré | ✅ Contournement | 🟢 Faible |
| Unicode | ✅ Solutionné | 🟢 Faible |

---

*Prochaine mise à jour : Après résolution des problèmes critiques*
