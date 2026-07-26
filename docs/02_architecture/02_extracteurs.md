## Organisation des extracteurs

Le module `extractors` est organisé par famille de sources. Chaque famille possède un moteur commun (`*_extractor.py`) et des extracteurs spécialisés pour chaque fournisseur ou dataset.

```text
src/
└── extractors/
    ├── __init__.py
    │
    ├── core/
    │   ├── __init__.py
    │   ├── extractor_models.py
    │   ├── extractor_exceptions.py
    │   ├── extractor_configuration.py
    │   ├── extractor_executor.py
    │   ├── extractor_results.py
    │   └── extractor_runner.py
    │
    ├── apis/
    │   ├── __init__.py
    │   ├── api_extractor.py
    │   ├── api_adapter.py
    │   └── sources/
    │       ├── __init__.py
    │       ├── currents_extractor.py
    │       ├── gdelt_extractor.py
    │       ├── gnews_extractor.py
    │       ├── google_fact_check_extractor.py
    │       ├── guardian_extractor.py
    │       ├── mediastack_extractor.py
    │       ├── newsapi_extractor.py
    │       └── newsdata_extractor.py
    │
    ├── datasets/
    │   ├── __init__.py
    │   ├── dataset_extractor.py
    │   ├── dataset_adapter.py
    │   └── sources/
    │       ├── __init__.py
    │       ├── coaid_extractor.py
    │       ├── fakeddit_extractor.py
    │       ├── fakenewsmnet_extractor.py
    │       └── isot_extractor.py
    │
    ├── rss/
    │   ├── __init__.py
    │   ├── rss_extractor.py
    │   ├── rss_parser.py
    │   └── rss_models.py
    │
    ├── scrapers/
    │   ├── __init__.py
    │   ├── scraper_extractor.py
    │   ├── scraper_adapter.py
    │   └── sources/
    │
    └── social/
        ├── __init__.py
        ├── social_extractor.py
        ├── social_adapter.py
        └── sources/
```

## Responsabilités des modules

### `core/`

Composants communs à tous les extracteurs.

| Module | Responsabilité |
|---------|----------------|
| `extractor_models.py` | Modèles et structures de données communes aux extracteurs. |
| `extractor_exceptions.py` | Exceptions métier communes (quota, authentification, arrêt contrôlé, etc.). |
| `extractor_configuration.py` | Chargement, validation et normalisation des configurations des sources. |
| `extractor_executor.py` | Exécution sécurisée d'un extracteur avec gestion des erreurs et des journaux. |
| `extractor_results.py` | Construction et normalisation des résultats d'extraction. |
| `extractor_runner.py` | Orchestration de l'exécution des différentes familles d'extracteurs. |

---

### `apis/`

Extraction des sources accessibles via une API HTTP.

| Module | Responsabilité |
|---------|----------------|
| `api_extractor.py` | Moteur commun aux API (requêtes HTTP, pagination, retries, erreurs, normalisation). |
| `api_adapter.py` | Contrat commun permettant d'intégrer une nouvelle API. |
| `sources/*.py` | Implémentation spécifique à chaque fournisseur d'API. |

---

### `datasets/`

Extraction des jeux de données locaux.

| Module | Responsabilité |
|---------|----------------|
| `dataset_extractor.py` | Moteur commun de lecture des datasets (CSV, TSV, JSON, chunks, etc.). |
| `dataset_adapter.py` | Contrat commun permettant d'intégrer un nouveau dataset. |
| `sources/*.py` | Adaptation propre à chaque dataset (colonnes, labels, formats). |

---

### `rss/`

Extraction des flux RSS.

| Module | Responsabilité |
|---------|----------------|
| `rss_extractor.py` | Moteur générique d'extraction des flux RSS. |
| `rss_parser.py` | Analyse et normalisation des flux XML/RSS. |
| `rss_models.py` | Modèles spécifiques au domaine RSS. |

---

### `scrapers/`

Extraction des sites web par scraping.

| Module | Responsabilité |
|---------|----------------|
| `scraper_extractor.py` | Moteur commun des scrapers (HTTP, pagination, robots.txt, délais, etc.). |
| `scraper_adapter.py` | Contrat commun des extracteurs de sites web. |
| `sources/` | Implémentations propres à chaque site web. |

---

### `social/`

Extraction des plateformes sociales.

| Module | Responsabilité |
|---------|----------------|
| `social_extractor.py` | Moteur commun des réseaux sociaux. |
| `social_adapter.py` | Contrat commun permettant d'intégrer un nouveau réseau social. |
| `sources/` | Implémentations spécifiques à chaque plateforme (Mastodon, Reddit, Bluesky, etc.). |

## Architecture générale

L'architecture suit une séparation claire des responsabilités :

- **`core`** : composants communs à tous les extracteurs.
- **Famille** (`apis`, `datasets`, `rss`, `scrapers`, `social`) : moteur commun au type de source.
- **`adapter`** : contrat technique partagé par les implémentations d'une même famille.
- **`sources`** : logique spécifique à chaque fournisseur ou source de données.

Cette organisation facilite l'ajout de nouvelles sources tout en limitant la duplication de code et en mutualisant les traitements communs.