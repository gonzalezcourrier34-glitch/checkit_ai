## Organisation des extracteurs

Le module `extractors` regroupe les composants utilisés pour collecter les données depuis les différentes sources de **CheckIt.AI**.

J’ai organisé ce module par famille de sources afin de séparer les traitements propres aux API, aux datasets, aux flux RSS, aux sites web et aux réseaux sociaux.

Chaque famille contient :

- des composants communs à son type de source ;
- un adaptateur chargé de convertir les données vers le format attendu ;
- un moteur d’extraction lorsque plusieurs traitements doivent être mutualisés ;
- un dossier `source` contenant les fichiers propres à chaque fournisseur.

```text
src/
└── extractors/
    ├── __init__.py
    │
    ├── core/
    │   ├── __init__.py
    │   ├── extractor_configuration.py
    │   ├── extractor_executor.py
    │   ├── extractor_models.py
    │   ├── extractor_results.py
    │   ├── extractor_runner.py
    │   └── extractor_service.py
    │
    ├── apis/
    │   ├── __init__.py
    │   ├── api_adapter.py
    │   ├── api_extractor.py
    │   └── source/
    │       ├── __init__.py
    │       ├── currents_extractor.py
    │       ├── gdelt_extractor.py
    │       ├── gnews_extractor.py
    │       ├── google_fact_check_extractor.py
    │       ├── newsapi_extractor.py
    │       └── newsdata_extractor.py
    │
    ├── datasets/
    │   ├── __init__.py
    │   ├── dataset_adapter.py
    │   ├── dataset_engine.py
    │   ├── dataset_file_utils.py
    │   ├── dataset_text_utils.py
    │   └── source/
    │       ├── __init__.py
    │       ├── coaid_extractor.py
    │       ├── fakeddit_extractor.py
    │       ├── fakenewsnet_extractor.py
    │       └── isot_extractor.py
    │
    ├── rss/
    │   ├── __init__.py
    │   ├── rss_adapter.py
    │   └── rss_extractor.py
    │
    ├── scrapers/
    │   ├── __init__.py
    │   ├── scraper_adapter.py
    │   ├── scraper_article_utils.py
    │   ├── scraper_engine.py
    │   ├── scraper_extractor.py
    │   ├── scraper_http_utils.py
    │   ├── scraper_metadata_utils.py
    │   ├── scraper_selector_utils.py
    │   ├── scraper_url_utils.py
    │   └── source/
    │       ├── __init__.py
    │       ├── afp_factuel_extractor.py
    │       ├── full_fact_extractor.py
    │       └── reuters_fact_check_extractor.py
    │
    └── social/
        ├── __init__.py
        ├── social_adapter.py
        ├── social_engine.py
        ├── social_extractor.py
        └── source/
            ├── __init__.py
            ├── mastodon_extractor.py
            └── reddit_extractor.py
```

Cette organisation me permet de mutualiser les traitements communs tout en conservant un fichier spécifique pour chaque source de données.

---

## Responsabilités des modules

### Module `core`

Le dossier `core` contient les composants utilisés par l’ensemble des familles d’extracteurs.

| Module | Rôle dans le projet |
|---|---|
| `extractor_configuration.py` | Charge et prépare les paramètres nécessaires à l’exécution des extracteurs. |
| `extractor_executor.py` | Exécute les extracteurs et encadre leur traitement. |
| `extractor_models.py` | Définit les structures de données communes utilisées pendant les extractions. |
| `extractor_results.py` | Construit et regroupe les résultats produits par les extracteurs. |
| `extractor_runner.py` | Lance un extracteur et suit son exécution. |
| `extractor_service.py` | Coordonne l’exécution des différentes familles d’extracteurs. |

J’ai regroupé ces composants dans `core` car ils ne dépendent pas d’un type de source particulier.

Ils permettent notamment d’utiliser un fonctionnement commun pour :

- la préparation de la configuration ;
- l’exécution des extracteurs ;
- le suivi des statuts ;
- la collecte des résultats ;
- la journalisation des traitements.

---

### Module `apis`

Le dossier `apis` contient les composants utilisés pour interroger les sources accessibles à travers une API HTTP.

| Module | Rôle dans le projet |
|---|---|
| `api_extractor.py` | Regroupe les traitements communs nécessaires à l’extraction depuis une API. |
| `api_adapter.py` | Adapte les données retournées par une API vers le format commun utilisé par CheckIt.AI. |
| `source/*.py` | Contient les traitements propres à chaque fournisseur d’API. |

Les fichiers présents dans `source` correspondent aux API intégrées au projet, notamment :

- Currents ;
- GDELT ;
- GNews ;
- Google Fact Check ;
- NewsAPI ;
- NewsData.

Cette séparation me permet d’utiliser une base commune pour les appels aux API tout en conservant la logique propre à chaque fournisseur dans un fichier dédié.

---

### Module `datasets`

Le dossier `datasets` contient les traitements utilisés pour lire les jeux de données académiques ou locaux.

| Module | Rôle dans le projet |
|---|---|
| `dataset_adapter.py` | Adapte les lignes d’un dataset vers le schéma standard des articles. |
| `dataset_engine.py` | Orchestre la lecture et le traitement des datasets. |
| `dataset_file_utils.py` | Regroupe les fonctions liées à la lecture et à la manipulation des fichiers de données. |
| `dataset_text_utils.py` | Fournit les traitements textuels utilisés pendant l’import des datasets. |
| `source/*.py` | Contient l’adaptation propre à chaque dataset. |

Les datasets actuellement représentés dans cette famille sont :

- COAID ;
- Fakeddit ;
- FakeNewsNet ;
- ISOT.

Chaque dataset possède sa propre structure de fichiers et ses propres colonnes. Les fichiers spécialisés permettent donc de convertir leurs données vers le format commun de CheckIt.AI.

---

### Module `rss`

Le dossier `rss` contient les composants nécessaires à l’extraction des flux RSS.

| Module | Rôle dans le projet |
|---|---|
| `rss_extractor.py` | Réalise l’extraction des publications depuis les flux RSS configurés. |
| `rss_adapter.py` | Convertit les entrées RSS vers le schéma commun des articles. |

J’ai conservé une organisation plus compacte pour cette famille, car les différentes sources RSS partagent un format d’entrée relativement proche.

Les différences entre les flux sont principalement gérées à partir de leur configuration.

---

### Module `scrapers`

Le dossier `scrapers` contient les traitements utilisés pour extraire les publications directement depuis des pages web.

| Module | Rôle dans le projet |
|---|---|
| `scraper_adapter.py` | Adapte les données extraites d’une page vers le schéma commun des articles. |
| `scraper_article_utils.py` | Regroupe les fonctions propres à la construction et au traitement des articles extraits. |
| `scraper_engine.py` | Orchestre le traitement des pages et des publications détectées. |
| `scraper_extractor.py` | Lance l’extraction des sites configurés. |
| `scraper_http_utils.py` | Gère les requêtes HTTP nécessaires au téléchargement des pages. |
| `scraper_metadata_utils.py` | Extrait et prépare les métadonnées présentes dans les pages. |
| `scraper_selector_utils.py` | Regroupe les fonctions utilisées pour appliquer les sélecteurs HTML. |
| `scraper_url_utils.py` | Traite et normalise les URL rencontrées pendant le scraping. |
| `source/*.py` | Contient la logique propre à chaque site web. |

Les extracteurs spécialisés présents dans cette famille concernent :

- AFP Factuel ;
- Full Fact ;
- Reuters Fact Check.

Cette organisation évite de répéter les fonctions communes de téléchargement, de sélection HTML, de traitement des URL et de préparation des métadonnées dans chaque scraper.

---

### Module `social`

Le dossier `social` contient les composants utilisés pour collecter les publications provenant de plateformes sociales.

| Module | Rôle dans le projet |
|---|---|
| `social_adapter.py` | Adapte les publications sociales vers le schéma commun des articles. |
| `social_engine.py` | Regroupe les traitements communs nécessaires à l’extraction des plateformes sociales. |
| `social_extractor.py` | Lance l’extraction des sources sociales configurées. |
| `source/*.py` | Contient la logique propre à chaque plateforme. |

Les plateformes actuellement représentées sont :

- Mastodon ;
- Reddit.

Les données retournées par ces plateformes ne possèdent pas toujours la même structure que les articles d’actualité. L’adaptateur social permet donc de les convertir avant leur intégration dans le pipeline.

---

## Architecture générale des extracteurs

L’organisation du module repose sur quatre niveaux.

```mermaid
flowchart LR
    A[Core commun] --> B[Famille d'extracteurs]
    B --> C[Moteur et adaptateur]
    C --> D[Extracteur propre à la source]
    D --> E[Article standard CheckIt.AI]
```

### Niveau commun

Le dossier `core` fournit les composants partagés par tous les extracteurs.

Il s’occupe principalement de leur configuration, de leur exécution et de la construction des résultats.

### Niveau famille

Chaque famille regroupe les traitements liés à un type de source :

- `apis` ;
- `datasets` ;
- `rss` ;
- `scrapers` ;
- `social`.

### Niveau moteur et adaptateur

Le moteur regroupe les traitements communs à une famille.

L’adaptateur convertit les données propres à la source vers le format attendu par CheckIt.AI.

### Niveau source

Le dossier `source` contient les traitements spécifiques à chaque fournisseur, site, plateforme ou dataset.

---

## Ajout d’une nouvelle source

Cette architecture me permet d’ajouter une nouvelle source sans modifier l’ensemble du pipeline.

Pour intégrer une source supplémentaire, je dois principalement :

1. identifier la famille correspondante ;
2. ajouter sa configuration ;
3. créer son extracteur dans le dossier `source` ;
4. utiliser l’adaptateur de la famille ;
5. enregistrer l’extracteur dans le service d’exécution ;
6. vérifier que les articles produits respectent le schéma commun.

Les traitements déjà présents dans le moteur de la famille restent réutilisables.

---

## Conclusion

Cette organisation me permet de séparer la logique commune des traitements propres à chaque source.

Le dossier `core` gère le fonctionnement général des extracteurs, tandis que chaque famille fournit ses propres outils, moteurs et adaptateurs.

Les fichiers placés dans les dossiers `source` contiennent uniquement les particularités de chaque fournisseur.

Cette structure limite la duplication de code et facilite l’ajout de nouvelles sources de données dans le pipeline.