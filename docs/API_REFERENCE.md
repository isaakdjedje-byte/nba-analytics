# Référence API - NBA Analytics Platform

**Version**: 2.0.0  
**Base URL**: `http://localhost:8000`  
**Documentation interactive**: [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)

---

## 🔐 Authentification

Actuellement, l'API ne requiert pas d'authentification (mode développement).

**Headers requis**:
```http
Content-Type: application/json
```

---

## 📋 Endpoints

### 1. Informations

#### GET /
Retourne les informations de base de l'API.

**Requête**:
```bash
curl http://localhost:8000/
```

**Réponse** (200 OK):
```json
{
  "message": "NBA Analytics API",
  "version": "2.0.0"
}
```

---

#### GET /health
Health check pour monitoring.

**Requête**:
```bash
curl http://localhost:8000/health
```

**Réponse** (200 OK):
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "2.0.0",
  "timestamp": "2024-02-08T20:30:00"
}
```

**Codes de statut**:
- `200`: Service opérationnel
- `503`: Service indisponible

---

### 2. Datasets

#### GET /api/v1/datasets
Liste tous les datasets disponibles dans le catalogue.

**Requête**:
```bash
curl http://localhost:8000/api/v1/datasets
```

**Réponse** (200 OK):
```json
[
  {
    "name": "players",
    "format": "parquet",
    "record_count": 5103,
    "last_updated": "2024-02-08T20:26:29"
  },
  {
    "name": "teams",
    "format": "parquet",
    "record_count": 30,
    "last_updated": "2024-02-08T20:26:28"
  }
]
```

**Paramètres de requête**:
Aucun

**Codes de statut**:
- `200`: Succès
- `500`: Erreur serveur

---

#### GET /api/v1/datasets/{name}
Retourne les détails d'un dataset spécifique.

**Requête**:
```bash
curl http://localhost:8000/api/v1/datasets/players
```

**Réponse** (200 OK):
```json
{
  "name": "players",
  "format": "parquet",
  "path": "data/gold/players.parquet",
  "record_count": 5103,
  "size_bytes": 1048576,
  "last_updated": "2024-02-08T20:26:29",
  "schema": {
    "id": "int64",
    "name": "object",
    "season": "object",
    "points": "float64"
  },
  "metadata": {
    "source": "nba-api",
    "columns": 15
  }
}
```

**Paramètres de chemin**:
| Nom | Type | Description |
|-----|------|-------------|
| name | string | Nom du dataset |

**Codes de statut**:
- `200`: Dataset trouvé
- `404`: Dataset non trouvé

---

### 3. Export

#### POST /api/v1/export
Exporte un dataset dans le format demandé.

**Requête**:
```bash
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "players",
    "format": "csv",
    "partition_by": null
  }'
```

**Body**:
```json
{
  "dataset": "players",
  "format": "csv",
  "partition_by": "season"
}
```

**Champs**:
| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| dataset | string | ✅ | Nom du dataset |
| format | string | ❌ | Format d'export (parquet, csv, json). Défaut: parquet |
| partition_by | string | ❌ | Colonne de partitionnement |

**Formats supportés**:
- `parquet`: Format colonnaire compressé (recommandé)
- `csv`: CSV avec headers UTF-8
- `json`: JSON format records

**Réponse** (200 OK):
```json
{
  "status": "success",
  "path": "data/exports/players.csv",
  "dataset": "players",
  "format": "csv",
  "partition_by": null
}
```

**Réponse** (404 Not Found):
```json
{
  "detail": "Dataset not found"
}
```

**Codes de statut**:
- `200`: Export réussi
- `404`: Dataset non trouvé
- `400`: Format invalide
- `500`: Erreur lors de l'export

---

### 4. Catalogue

#### POST /api/v1/catalog/scan
Scanne le répertoire data/gold et met à jour le catalogue.

**Requête**:
```bash
curl -X POST http://localhost:8000/api/v1/catalog/scan
```

**Réponse** (200 OK):
```json
{
  "status": "success",
  "datasets_found": 17,
  "scanned_at": "2024-02-08T20:30:00"
}
```

**Codes de statut**:
- `200`: Scan terminé
- `500`: Erreur lors du scan

---

## 📊 Modèles de Données

### DatasetInfo

```json
{
  "name": "string",
  "format": "string",
  "path": "string",
  "record_count": "integer",
  "size_bytes": "integer",
  "last_updated": "datetime",
  "schema": "object",
  "metadata": "object"
}
```

### ExportRequest

```json
{
  "dataset": "string",
  "format": "string",
  "partition_by": "string"
}
```

### ExportResponse

```json
{
  "status": "string",
  "path": "string",
  "dataset": "string",
  "format": "string",
  "partition_by": "string"
}
```

---

## 🧪 Exemples d'Utilisation

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Lister datasets
response = requests.get(f"{BASE_URL}/api/v1/datasets")
datasets = response.json()
print(f"{len(datasets)} datasets disponibles")

# Exporter en CSV
export_data = {
    "dataset": "players",
    "format": "csv"
}
response = requests.post(
    f"{BASE_URL}/api/v1/export",
    json=export_data
)
result = response.json()
print(f"Exporté: {result['path']}")

# Scanner catalogue
response = requests.post(f"{BASE_URL}/api/v1/catalog/scan")
scan_result = response.json()
print(f"Datasets trouvés: {scan_result['datasets_found']}")
```

### JavaScript (Fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Lister datasets
fetch(`${BASE_URL}/api/v1/datasets`)
  .then(res => res.json())
  .then(datasets => console.log(`${datasets.length} datasets`));

// Exporter
fetch(`${BASE_URL}/api/v1/export`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    dataset: 'players',
    format: 'csv'
  }),
})
.then(res => res.json())
.then(result => console.log(`Exporté: ${result.path}`));
```

### curl

```bash
# Lister tous les datasets
curl http://localhost:8000/api/v1/datasets | jq

# Exporter en Parquet (défaut)
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{"dataset": "players"}'

# Exporter en CSV avec partitionnement
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "players",
    "format": "csv",
    "partition_by": "season"
  }'

# Scanner et mettre à jour le catalogue
curl -X POST http://localhost:8000/api/v1/catalog/scan

# Health check
curl http://localhost:8000/health
```

---

## 🔧 Codes d'Erreur

| Code | Description | Exemple |
|------|-------------|---------|
| 200 | Succès | OK |
| 400 | Requête invalide | Format non supporté |
| 404 | Non trouvé | Dataset inexistant |
| 422 | Validation échouée | JSON malformé |
| 500 | Erreur serveur | Exception non gérée |
| 503 | Service indisponible | Database down |

---

## 📈 Rate Limiting

Actuellement, aucune limite de rate n'est appliquée (mode développement).

**Recommandé pour production**:
- 100 req/min par IP
- 1000 req/min global

---

## 🔄 Versioning

L'API suit le versioning sémantique dans l'URL:
- `/api/v1/` - Version actuelle (stable)
- `/api/v2/` - Future version (breaking changes)

---

## 🔗 Liens Utiles

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Swagger UI](http://localhost:8000/docs)
- [OpenAPI JSON](http://localhost:8000/openapi.json)

---

*Dernière mise à jour: 08/02/2026*
