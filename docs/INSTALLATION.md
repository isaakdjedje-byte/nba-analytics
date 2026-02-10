# Installation - NBA Analytics Platform

Guide complet d'installation et de configuration de la plateforme d'analytics NBA.

## Prérequis

### Système

- **OS** : Windows 10+, macOS 10.15+, ou Linux (Ubuntu 20.04+)
- **Python** : 3.11+ (⚠️ Python 3.14 n'est PAS supporté)
- **pip** : 21.0+
- **Git** : 2.30+
- **RAM** : 4GB minimum (8GB recommandé)
- **Espace disque** : 10GB minimum (20GB recommandé pour 7 saisons)
- **Java** : 11+ (requis pour PySpark)

### Vérification prérequis

**⚠️ IMPORTANT: Python 3.11 ou 3.12 requis (pas 3.14+)**

```bash
# Vérifier Python
python --version  # Doit afficher 3.11.x ou 3.12.x

# Si vous avez Python 3.14, utilisez pyenv ou installer Python 3.11
# Windows: python3.11 --version
# Mac/Linux: python3.11 --version

# Vérifier pip
pip --version

# Vérifier Git
git --version

# Vérifier Java (pour Spark)
java -version  # Doit afficher 11.x ou supérieur
```

## Installation étape par étape

### 1. Cloner le repository

```bash
# Cloner le projet
git clone https://github.com/isaakdjedje-byte/nba-analytics.git

# Entrer dans le dossier
cd nba-analytics
```

### 2. Créer l'environnement virtuel

**Windows (cmd/powershell):**
```bash
# Créer environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate

# Vérifier activation
which python  # Doit afficher: .../venv/Scripts/python.exe
```

**Windows (PowerShell avec restrictions):**
```powershell
# Si erreur d'exécution, autoriser temporairement
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Puis activer
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
# Créer environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Vérifier activation
which python  # Doit afficher: .../venv/bin/python
```

### 3. Installer les dépendances

```bash
# Installer tous les packages requis
pip install -r requirements.txt
```

**Contenu de requirements.txt :**
```txt
pyspark==3.5.0
delta-spark==3.0.0
nba-api==1.1.11
pandas==2.1.4
numpy==1.26.2
pytest==7.4.3
pytest-cov==4.1.0
jupyterlab==4.0.9
requests==2.31.0
```

### 4. Vérifier l'installation

**Test Python :**
```bash
# Vérifier PySpark
python -c "import pyspark; print(f'PySpark version: {pyspark.__version__}')"

# Vérifier Delta Lake
python -c "import delta; print('Delta Lake OK')"

# Vérifier nba-api
python -c "from nba_api.stats.static import players; print('nba-api OK')"

# Vérifier pandas
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
```

**Test complet :**
```bash
# Lancer les tests unitaires
pytest tests/ -v --tb=short

# Ou utiliser le script fourni
./scripts/run_tests.sh  # Linux/Mac
scripts\run_tests.bat   # Windows
```

### 5. Configuration environnement

**Fichier .env (NOUVEAU - Recommandé) :**

```bash
# Copier le template
cp .env.example .env

# Modifier avec vos valeurs
nano .env  # ou code .env
```

**Contenu minimum .env :**
```bash
ENVIRONMENT=development
API_PORT=8000
DATABASE_URL=postgresql://nba:nba@localhost:5432/nba
DATA_ROOT=data
MODEL_PATH=models
PREDICTIONS_PATH=predictions
```

**Variables d'environnement (méthode alternative) :**

**Windows (PowerShell):**
```powershell
# Définir SPARK_HOME si Spark installé séparément
$env:SPARK_HOME = "C:\path\to\spark"

# Ajouter src au PYTHONPATH
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\src"

# Vérifier
$env:PYTHONPATH
```

**Windows (cmd):**
```cmd
set SPARK_HOME=C:\path\to\spark
set PYTHONPATH=%PYTHONPATH%;%CD%\src
```

**macOS/Linux:**
```bash
# Ajouter à ~/.bashrc ou ~/.zshrc
export SPARK_HOME=/path/to/spark
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Recharger la configuration
source ~/.bashrc  # ou ~/.zshrc
```

### 6. Configuration Git (important pour Windows)

```bash
# Configurer Git pour gérer les fins de ligne Windows/Unix
git config --global core.autocrlf true

# Vérifier configuration
git config --global core.autocrlf  # Doit afficher: true
```

## Installation avec Docker (Recommandé)

### Prérequis Docker

- **Docker** : 24.0+
- **Docker Compose** : 2.20+

### Démarrage rapide

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les conteneurs en cours
docker-compose ps

# Voir les logs
docker-compose logs -f spark-nba
```

### Accès aux services Docker

| Service | URL | Description |
|---------|-----|-------------|
| Jupyter Lab | http://localhost:8888 | Notebooks interactifs |
| Spark UI | http://localhost:4040 | Interface Spark |
| Spark Master | http://localhost:8080 | Master Spark |

### Commandes Docker utiles

```bash
# Arrêter les services
docker-compose down

# Reconstruire les images
docker-compose up -d --build

# Entrer dans le conteneur Spark
docker-compose exec spark-nba bash

# Exécuter les tests dans Docker
docker-compose run test

# Voir logs d'un service spécifique
docker-compose logs spark-nba
```

## Structure du projet

```
nba-analytics/
├── src/                        # Code source Python
│   ├── ingestion/              # Scripts d'ingestion données
│   │   ├── fetch_nba_data.py
│   │   └── nba_api_client.py
│   ├── utils/                  # Utilitaires
│   │   └── helpers.py
│   └── config/                 # Configuration
│       └── settings.py
├── tests/                      # Tests unitaires
│   ├── test_ingestion.py
│   └── test_utils.py
├── docs/                       # Documentation
│   ├── API_INGESTION.md
│   ├── INSTALLATION.md
│   ├── EXAMPLES.md
│   └── stories/                # Stories détaillées
├── data/                       # Données (créé automatiquement)
│   ├── raw/                    # Données brutes JSON
│   └── processed/              # Données traitées Delta Lake
├── scripts/                    # Scripts utilitaires
│   ├── run_tests.sh            # Linux/Mac
│   └── run_tests.bat           # Windows
├── notebooks/                  # Jupyter notebooks
├── docker-compose.yml          # Configuration Docker
├── Dockerfile                  # Image Docker personnalisée
├── requirements.txt            # Dépendances Python
└── README.md                   # Vue d'ensemble projet
```

## Dépannage

### Erreur : "No module named 'pyspark'"

**Cause** : Environnement virtuel non activé ou installation incomplète

**Solution :**
```bash
# Vérifier activation environnement
which python

# Si pas de venv, l'activer
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate     # Windows

# Réinstaller PySpark
pip install pyspark==3.5.0
```

### Erreur : "JAVA_HOME not set"

**Cause** : Java non installé ou variable d'environnement non définie

**Solution Windows :**
```powershell
# Télécharger Java 11 (Eclipse Temurin)
# https://adoptium.net/

# Définir JAVA_HOME
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-11"

# Ajouter au PATH
$env:PATH = "$env:PATH;$env:JAVA_HOME\bin"

# Vérifier
java -version
```

**Solution macOS/Linux :**
```bash
# Installer Java 11
# macOS avec Homebrew
brew install openjdk@11

# Ubuntu/Debian
sudo apt-get install openjdk-11-jdk

# Configurer JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
```

### Erreur : "Rate limit exceeded"

**Cause** : Trop de requêtes vers l'API NBA

**Solution :**
```python
import time

# Ajouter un délai entre les requêtes
time.sleep(2)  # 2 secondes minimum

# Utiliser la fonction de retry
from src.ingestion.fetch_nba_data import fetch_with_retry
data = fetch_with_retry(endpoint, max_retries=3)
```

### Erreur : "ModuleNotFoundError: No module named 'src'"

**Cause** : PYTHONPATH non configuré

**Solution :**
```bash
# Windows (PowerShell)
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\src"

# Mac/Linux
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Ou exécuter depuis la racine du projet
cd /path/to/nba-analytics
python -m src.ingestion.fetch_nba_data
```

### Erreur Git : "LF will be replaced by CRLF"

**Cause** : Conflit de fins de ligne Windows/Unix

**Solution :**
```bash
# Configurer Git
git config --global core.autocrlf true

# Pour ce repository uniquement
git config core.autocrlf true

# Ignorer les avertissements temporairement
git config --global core.safecrlf false
```

### Erreur Docker : "port is already allocated"

**Cause** : Un autre service utilise le port

**Solution :**
```bash
# Trouver le processus utilisant le port
# Windows
netstat -ano | findstr :8888

# Mac/Linux
lsof -i :8888

# Arrêter Docker et libérer les ports
docker-compose down
docker system prune -f

# Relancer
docker-compose up -d
```

### Erreur : "No module named 'joblib'"

**Cause** : Dépendances ML non installées ou mauvaise version Python

**Solution :**
```bash
# Vérifier que vous utilisez Python 3.11
python3.11 --version

# Installer dans Python 3.11 spécifiquement
python3.11 -m pip install joblib scikit-learn xgboost pandas numpy

# Vérifier l'installation
python3.11 -c "import joblib; print('OK')"
```

### Erreur : "Python 3.14 not supported"

**Cause** : Version Python incompatible avec PySpark

**Solution :**
```bash
# Vérifier version Python
python --version

# Si 3.14, installer Python 3.11 ou 3.12
# Windows : Télécharger depuis python.org
# Mac : brew install python@3.11
# Linux : sudo apt-get install python3.11

# Recréer l'environnement virtuel avec bonne version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Vérification post-installation

### Test de bout en bout

```bash
# 1. Vérifier l'import des modules principaux
python -c "
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import LeagueGameFinder
from pyspark.sql import SparkSession
import pandas as pd
print('✅ Tous les imports OK')
"

# 2. Tester connexion API
python -c "
from nba_api.stats.static import players
all_players = players.get_players()
print(f'✅ Connexion API OK - {len(all_players)} joueurs trouvés')
"

# 3. Tester Spark
python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('Test').getOrCreate()
print(f'✅ Spark OK - version {spark.version}')
spark.stop()
"

# 4. Lancer un test simple
python -c "
from src.ingestion.fetch_nba_data import fetch_season_games
games = fetch_season_games('2023-24', limit=10)
print(f'✅ Pipeline ingestion OK - {len(games)} matchs récupérés')
"
```

### Test avec Docker

```bash
# Vérifier que tous les services sont up
docker-compose ps

# Tester Jupyter
curl http://localhost:8888

# Tester Spark UI
curl http://localhost:4040

# Lancer les tests dans Docker
docker-compose exec spark-nba pytest tests/ -v
```

## Mise à jour

### Mettre à jour les dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Réinstaller requirements
pip install -r requirements.txt --upgrade

# Mettre à jour un package spécifique
pip install --upgrade nba-api
```

### Mettre à jour Docker

```bash
# Reconstruire avec les dernières versions
docker-compose down
docker-compose pull
docker-compose up -d --build
```

## Support

### Ressources

- [Documentation API](API_INGESTION.md)
- [Exemples d'utilisation](EXAMPLES.md)
- [Guide des tests](TESTING.md)
- [Journal du projet](memoir.md)

### Contacts

- **Issues GitHub** : https://github.com/isaakdjedje-byte/nba-analytics/issues
- **Documentation nba-api** : https://github.com/swar/nba_api

---

**Dernière mise à jour** : 2026-02-09  
**Version** : 2.0  
**Ticket associé** : NBA-16, NBA-29 (Configuration centralisée)
