# PokéMako — Pokédex Analytics

Un Pokédex stratégique augmenté par la data science.

> **Question centrale :** « Peut-on mesurer objectivement la puissance d'un Pokémon et prédire l'issue d'un combat ? »

---

## Stack technique

| Couche | Technologie |
|---|---|
| Source de données | PokéAPI |
| ETL & analyse | Python, pandas |
| Base de données | PostgreSQL |
| Cache | Redis |
| Backend | FastAPI |
| Machine Learning | scikit-learn |
| Visualisations | Plotly |
| MLOps | MLflow, Dagshub |
| Frontend | React, Tailwind CSS v4 (PWA) |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Qualité du code | Ruff, Prettier, pre-commit |
| Infrastructure | Terraform |

---

## Architecture

```
PokéAPI → ETL Python → PostgreSQL → FastAPI → Redis (cache) → Frontend React
                                        ↓
                               Simulateur Monte Carlo
                                        ↓
                               Dataset ML synthétique
                                        ↓
                          MLflow / Dagshub (tracking des runs)
```

---

## Démarrage rapide

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré
- [VS Code](https://code.visualstudio.com/) avec l'extension **Dev Containers**

### Lancer le projet

```bash
git clone git@github.com:mayandre95/Pokedex.git
cd Pokedex
cp .env.example .env        # remplir les valeurs dans .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Ouvrir en Dev Container

1. Ouvrir le dossier dans VS Code
2. Accepter la notification « Reopen in Container »
3. Python, Node, Ruff, Prettier et les extensions VS Code sont installés automatiquement

---

## Structure du projet

```
pokemako/
├── api/            # Backend FastAPI — endpoints REST, rate limiting, auth
├── etl/            # Ingestion PokéAPI → PostgreSQL
├── ml/             # Entraînement des modèles, scripts scikit-learn
├── frontend/       # React + Tailwind CSS v4 (Vite)
├── data/           # Données brutes et exports (gitignored)
├── docs/           # Documentation technique
├── .devcontainer/  # Dev Container VS Code
├── .github/        # GitHub Actions (CI/CD)
├── .env.example    # Variables d'environnement (template)
├── docker-compose.yml
└── requirements.txt
```

---

## Variables d'environnement

Copier `.env.example` en `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

Le fichier `.env` n'est jamais commité (voir `.gitignore`).

---

## Qualité du code

Le projet utilise **pre-commit** pour garantir la qualité à chaque commit.

```bash
# Installer les hooks (fait automatiquement dans le Dev Container)
pip install pre-commit
pre-commit install

# Lancer manuellement sur tous les fichiers
pre-commit run --all-files
```

| Outil | Périmètre |
|---|---|
| Ruff | Python — lint + format |
| Prettier | JS / CSS / JSON — format |
| check-yaml | Fichiers YAML |
| check-added-large-files | Bloque les fichiers > 500KB |
