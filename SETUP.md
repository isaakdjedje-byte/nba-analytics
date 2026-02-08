# NBA Analytics - Setup Guide

Guide complet de configuration de l'environnement de développement.

## 🎯 Solution choisie : Virtual Environment

Pour éviter les conflits entre Python 3.11 (projet) et Python 3.14 (autres projets), nous utilisons un **virtual environment isolé**.

### Avantages
- ✅ Isolation complète du projet
- ✅ Pas de conflits avec d'autres projets Python
- ✅ Reproductible sur toute machine
- ✅ Standard industriel

---

## 🚀 Installation Rapide (Automatique)

### 1. Ouvrir un terminal Git Bash

### 2. Lancer le setup
```bash
cd ~/nba-analytics
./setup_venv.sh
```

**Cela va automatiquement :**
- Créer un virtual environment Python 3.11
- Installer toutes les dépendances
- Créer le kernel Jupyter
- Configurer l'environnement

### 3. Vérifier l'installation
```bash
source .venv/Scripts/activate
python --version  # Doit afficher 3.11.x
```

---

## 📚 Utilisation Quotidienne

### Démarrer Jupyter Notebook

**Méthode 1 : Script automatique**
```bash
./start_jupyter.sh
```

**Méthode 2 : Alias bash (après `source ~/.bashrc`)**
```bash
nba-notebook
```

**Méthode 3 : Manuelle**
```bash
source .venv/Scripts/activate
jupyter notebook
```

### Activer l'environnement
```bash
# Alias
nba-venv

# Ou manuellement
source ~/nba-analytics/.venv/Scripts/activate
```

### Désactiver l'environnement
```bash
deactivate
```

---

## 📁 Structure du Virtual Environment

```
nba-analytics/
├── .venv/                      # Virtual environment (ne pas modifier)
│   ├── Scripts/               # Exécutables Windows
│   ├── Lib/                   # Packages Python
│   └── pyvenv.cfg            # Configuration
├── .jupyter_runtime/          # Runtime Jupyter local
├── setup_venv.sh             # Script de setup
├── start_jupyter.sh          # Script de démarrage
└── requirements.txt          # Dépendances
```

---

## 🛠️ Commandes Utiles

### Vérifier les packages installés
```bash
source .venv/Scripts/activate
pip list
```

### Mettre à jour les dépendances
```bash
source .venv/Scripts/activate
pip install -r requirements.txt --upgrade
```

### Réinstaller le venv (si problème)
```bash
rm -rf .venv
./setup_venv.sh
```

### Vérifier quel Python est utilisé
```bash
which python
# Doit afficher : /c/Users/isaac/nba-analytics/.venv/Scripts/python
```

---

## 🔧 Dépannage

### Problème : "ModuleNotFoundError"
**Solution :**
```bash
source .venv/Scripts/activate
pip install <package-manquant>
```

### Problème : Permission denied sur Jupyter
**Solution :** Le script `start_jupyter.sh` utilise déjà un dossier runtime local (`.jupyter_runtime/`)

### Problème : Conflit de ports
**Solution :** Le script détecte automatiquement un port libre (8888, 8889, 8890...)

### Problème : Python 3.14 au lieu de 3.11
**Solution :** Vérifier que le venv est activé
```bash
which python  # Doit contenir .venv/Scripts/python
```

---

## 📝 Aliens Bash (Optionnel)

Ajoutez à votre `~/.bashrc` pour des raccourcis rapides :

```bash
# Raccourcis NBA Analytics
alias nba='cd ~/nba-analytics && source .venv/Scripts/activate'
alias nba-setup='~/nba-analytics/setup_venv.sh'
alias nba-notebook='~/nba-analytics/start_jupyter.sh'
```

Puis rechargez :
```bash
source ~/.bashrc
```

---

## ✅ Vérification Finale

Testez que tout fonctionne :

```bash
# 1. Setup
./setup_venv.sh

# 2. Activation
source .venv/Scripts/activate

# 3. Test packages
python -c "import pandas; import matplotlib; import sklearn; print('OK')"

# 4. Test NBA-22
python src/ml/nba22_train.py

# 5. Lancer Jupyter
./start_jupyter.sh
```

Ouvrez `notebooks/04_nba22_results.ipynb` dans Jupyter et cliquez sur **"Run All"**.

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifier que Python 3.11 est installé : `pyenv versions`
2. Supprimer et recréer le venv : `rm -rf .venv && ./setup_venv.sh`
3. Vérifier les logs d'erreur dans le terminal

---

**Environnement configuré avec succès !** 🎉
