# CheckIt.AI

> **Pipeline d'acquisition multimodale pour la collecte, la validation et le stockage d'articles de presse destinés au fact-checking et à la détection de la désinformation.**

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Airflow](https://img.shields.io/badge/Airflow-3.x-red.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)

---

# Présentation

CheckIt.AI est une plateforme d'acquisition et de préparation de données développée dans le cadre de la formation **Ingénieur IA - OpenClassrooms**.

Son objectif est de constituer automatiquement une base d'articles de presse exploitable pour des projets de :

- fact-checking ;
- détection de la désinformation ;
- veille informationnelle ;
- entraînement de modèles d'intelligence artificielle.

Le pipeline centralise des contenus provenant de sources hétérogènes (RSS, APIs, sites web, réseaux sociaux et jeux de données académiques), puis applique une série de traitements afin d'obtenir des données homogènes, fiables et exploitables avant leur stockage dans PostgreSQL.

Contrairement à un simple scraper, CheckIt.AI réalise également :

- la normalisation des articles ;
- la validation des métadonnées ;
- la suppression des doublons ;
- la validation des URLs et des dates ;
- le téléchargement et le contrôle des images ;
- la gestion des erreurs d'extraction ;
- la génération d'indicateurs de qualité.

L'ensemble du processus est orchestré par **Apache Airflow**, permettant d'automatiser le pipeline et de relancer indépendamment chaque étape.

---

# Pipeline

```text
RSS       ─┐
API       ─┼──► Extraction
Web       ─┤
Social    ─┤
Datasets  ─┘
                │
                ▼
         Validation
                │
                ▼
  Téléchargement des images
                │
                ▼
       Transformation
                │
                ▼
         PostgreSQL
                │
                ▼
      Contrôle qualité
```

---

# Fonctionnalités

## Acquisition

- Flux RSS
- APIs d'actualité
- Scraping HTML
- Réseaux sociaux
- Jeux de données académiques

## Préparation des données

- Normalisation des articles
- Déduplication
- Validation des champs
- Nettoyage des contenus
- Validation des dates et des URLs

## Gestion des images

- Téléchargement automatique
- Validation du format
- Contrôle des dimensions
- Détection des images invalides

## Orchestration

- Pipeline Apache Airflow
- Journalisation complète
- Configuration YAML
- Stockage PostgreSQL

---

# Sources supportées

| Catégorie | Sources |
|-----------|----------|
| **RSS** | Le Monde, France Info, BBC, The Guardian, AFP Factuel, Reuters Fact Check, Full Fact |
| **APIs** | NewsAPI, NewsData, GNews, Guardian API, Currents, Mediastack, GDELT, Google Fact Check |
| **Réseaux sociaux** | Reddit, Mastodon |
| **Datasets** | FakeNewsNet, Fakeddit, COAID, ISOT |

---

# Architecture

Le projet est construit autour de quatre **moteurs d'extraction génériques** :

- Global RSS Extractor
- Global API Extractor
- Global Scraper Extractor
- Global Dataset Extractor

Chaque moteur implémente la logique commune à une famille de sources tandis que les particularités de chaque fournisseur sont décrites dans un adaptateur spécifique ainsi que dans des fichiers YAML.

Cette architecture permet :

- de limiter le code dupliqué ;
- d'ajouter facilement de nouvelles sources ;
- de simplifier la maintenance ;
- de garantir un comportement homogène entre les extracteurs.

---

# Technologies

- Python 3.12+
- Apache Airflow
- Docker
- PostgreSQL
- Requests
- HTTPX
- BeautifulSoup
- Feedparser
- Pandas
- Pillow
- PyYAML
- Tenacity

---

# Installation

## Prérequis

- Git
- Docker Desktop
- Docker Compose

Le projet a été développé et testé avec **Python 3.12**.

---

## 1. Cloner le dépôt

```bash
git clone https://github.com/<utilisateur>/checkit-ai.git
cd checkit-ai
```

---

## 2. Configurer le projet

Les paramètres des extracteurs sont regroupés dans :

```text
config/
└── sources.yaml
```

### Clés API

Les clés API ne sont **jamais** stockées dans le dépôt GitHub.

Les fichiers YAML référencent uniquement le nom d'un secret via le champ :

```yaml
api_key_secret_name
```

Les valeurs réelles doivent être créées dans le dossier :

```text
secrets/
├── guardian_api_key
├── newsapi_api_key
├── gnews_api_key
├── newsdata_api_key
├── currents_api_key
├── mediastack_api_key
└── google_fact_check_api_key
```

Chaque fichier doit contenir uniquement la valeur de la clé API, sans guillemets.

Exemple :

```text
secrets/
└── guardian_api_key
```

Contenu :

```text
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Les clés API ne sont pas fournies avec ce projet.

> Les extracteurs nécessitant une clé API seront automatiquement ignorés si le secret correspondant est absent.

---

## 3. Datasets requis

Les jeux de données académiques ne sont pas inclus dans le dépôt GitHub en raison de leur taille et de leurs conditions de diffusion.

Les datasets suivants doivent être téléchargés séparément :

- Fakeddit
- FakeNewsNet
- ISOT Fake News Dataset
- COAID

Ils doivent ensuite être placés dans les emplacements définis dans la configuration du projet (`config/sources.yaml`).

> Les flux RSS restent utilisables sans téléchargement supplémentaire.

---

## 4. Construire les images Docker

```bash
docker compose build
```

Cette étape est nécessaire uniquement lors du premier lancement ou après une modification des images Docker.

---

## 5. Initialiser Airflow

```bash
docker compose up airflow-init
```

Cette commande initialise la base de données Airflow lors de la première exécution.

---

## 6. Démarrer l'application

```bash
docker compose up -d
```

Les principaux services démarrés sont :

- PostgreSQL
- Airflow Scheduler
- Airflow Worker
- Airflow Webserver

L'interface Airflow est accessible à l'adresse :

```text
http://localhost:8080
```

---

## 7. Lancer le tableau de bord

Depuis le répertoire du projet :

```bash
streamlit run dashboard/app.py
```

Le tableau de bord est accessible à l'adresse :

```text
http://localhost:8501
```

> Adapter le chemin si le point d'entrée Streamlit est différent.

---

## 8. Lancer la documentation

Depuis le répertoire du projet :

```bash
mkdocs serve
```

La documentation est accessible à l'adresse :

```text
http://localhost:8000
```

---

# Utilisation

Le pipeline est piloté depuis l'interface Airflow.

Le DAG principal :

```text
checkit_master_pipeline
```

enchaîne automatiquement les étapes suivantes :

1. Extraction
2. Validation
3. Téléchargement des images
4. Transformation
5. Chargement PostgreSQL
6. Contrôle qualité

---

# Structure du projet

```text
checkit_ai/
├── config/
├── dashboard/
├── dags/
├── docs/
├── src/
│   ├── extractors/
│   ├── services/
│   ├── storage/
│   ├── transformers/
│   ├── validators/
│   └── utils/
├── tests/
├── logs/
└── secrets/
```

---

# Qualité des données

Le pipeline réalise automatiquement :

- la validation des articles ;
- la suppression des doublons ;
- la validation des URLs ;
- le contrôle des dates ;
- la validation des images ;
- la journalisation des erreurs ;
- la génération d'indicateurs de qualité.

---

# Perspectives

- Ajout de nouvelles sources
- Enrichissement NLP
- Génération d'embeddings
- Classification automatique
- Détection multimodale texte/image
- Tableau de bord de supervision enrichi

---

# Auteur

Projet réalisé par **Stéphane Moa** dans le cadre de la formation **Ingénieur IA** d'OpenClassrooms.

---

# Licence

Ce projet est distribué sous licence **MIT**.