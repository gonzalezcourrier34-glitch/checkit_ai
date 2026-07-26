# Choix techniques

## Objectif

Cette section présente les principaux choix techniques retenus pour le développement de **CheckIt.AI**.

L'objectif est de justifier les technologies utilisées pour concevoir une architecture modulaire, reproductible et évolutive, capable de collecter, transformer et stocker des données multimodales destinées à de futurs traitements d'intelligence artificielle.

Les choix présentés concernent aussi bien les bibliothèques Python que l'organisation logicielle du projet.

---

# Critères de sélection

Les technologies ont été choisies selon plusieurs critères :

- simplicité d'intégration ;
- compatibilité avec Python ;
- qualité de la documentation ;
- modularité ;
- facilité de maintenance ;
- reproductibilité des traitements ;
- compatibilité avec une future orchestration par Apache Airflow.

---

# Langage de développement

## Python

Le projet est entièrement développé en **Python**, langage de référence dans les domaines de la data science, du data engineering et de l'intelligence artificielle.

### Justification

- large écosystème scientifique ;
- nombreuses bibliothèques dédiées au traitement de données ;
- excellente compatibilité avec les APIs REST ;
- intégration native avec Apache Airflow ;
- forte adoption dans les projets d'intelligence artificielle.

---

# Architecture logicielle

Le projet est organisé selon une architecture modulaire où chaque composant possède une responsabilité unique.

| Module | Responsabilité |
|---------|----------------|
| **Extractors** | Collecte des données depuis les différentes sources. |
| **Cleaners** | Nettoyage et normalisation des contenus textuels. |
| **Transformers** | Harmonisation des données et génération des variables destinées aux modèles IA. |
| **Validators** | Vérification de la cohérence des données et des images. |
| **Services** | Orchestration des traitements spécialisés. |
| **Storage** | Gestion des écritures JSON et CSV. |
| **Pipelines** | Enchaînement des différentes étapes de traitement. |
| **Utils** | Fonctions communes réutilisées dans l'ensemble du projet. |

Cette organisation facilite les tests unitaires, la maintenance et l'ajout de nouvelles fonctionnalités.

---

# Bibliothèques utilisées

| Bibliothèque | Utilisation |
|--------------|-------------|
| **requests** | Communication avec les APIs REST et téléchargement des images. |
| **feedparser** | Lecture des flux RSS. |
| **BeautifulSoup** | Extraction d'informations depuis des pages HTML. |
| **Pandas** | Manipulation et export des données tabulaires. |
| **Pillow (PIL)** | Validation et lecture des métadonnées des images. |
| **Pathlib** | Manipulation portable des chemins et fichiers. |
| **Logging** | Journalisation des traitements. |
| **hashlib** | Génération d'identifiants uniques et déduplication. |

---

# Pipeline de transformation

Le pipeline est séparé en deux grandes étapes.

## Pipeline d'acquisition

Il collecte les données provenant des différentes sources puis les enregistre dans un format brut (RAW).

Les traitements comprennent notamment :

- extraction ;
- préparation ;
- validation ;
- téléchargement des images ;
- stockage des données brutes.

---

## Pipeline de transformation

Le second pipeline recharge les données brutes afin de produire un jeu de données homogène.

Les principales étapes sont :

- nettoyage ;
- normalisation métier ;
- génération des caractéristiques ;
- validation finale ;
- export des données transformées.

Cette séparation garantit la reproductibilité des traitements sans solliciter à nouveau les sources externes.

---

# Journalisation

Le projet utilise le module standard **logging**.

Chaque étape importante est journalisée :

- démarrage d'un pipeline ;
- nombre d'articles traités ;
- téléchargements d'images ;
- validations ;
- rejets ;
- erreurs éventuelles ;
- export des données.

Cette journalisation facilite le diagnostic et le suivi des traitements.

---

# Formats de stockage

Les données sont manipulées sous plusieurs formats.

| Format | Utilisation |
|---------|-------------|
| **JSON** | Stockage principal des données brutes et transformées. |
| **CSV** | Export des données pour les analyses exploratoires. |

Les images sont stockées séparément dans un répertoire dédié afin de conserver le lien entre les contenus textuels et visuels.

L'architecture reste compatible avec l'ajout futur d'autres formats tels que Parquet.

---

# Gestion des sources

Le pipeline privilégie systématiquement les modes d'accès officiels.

| Source | Méthode utilisée |
|----------|-----------------|
| Flux RSS | Feedparser |
| NewsData.io | API REST |
| GNews | API REST |
| GDELT | API REST |
| Reddit | API officielle |
| FakeNewsNet | Dataset |
| Fakeddit | Dataset |

Le scraping HTML est uniquement utilisé lorsqu'aucune API officielle ou flux RSS n'est disponible.

---

# Orchestration

## Apache Airflow

Le projet est conçu pour être orchestré par **Apache Airflow**.

À terme, deux DAGs seront mis en place :

- un DAG d'acquisition ;
- un DAG de transformation.

Cette architecture permettra :

- la planification automatique des traitements ;
- la reprise sur erreur ;
- le suivi des exécutions ;
- la production continue de nouveaux jeux de données.

---

# Conteneurisation

## Docker

Le développement s'appuie sur Docker afin de garantir un environnement d'exécution reproductible.

Les principaux avantages sont :

- environnement identique sur toutes les machines ;
- isolation des dépendances ;
- déploiement simplifié ;
- intégration facilitée avec Airflow.

---

# Documentation

## MkDocs

La documentation technique est générée avec **MkDocs Material**.

Cette solution permet :

- une documentation versionnée ;
- une navigation simple ;
- l'intégration de diagrammes Mermaid ;
- une génération automatique d'un site statique.

---

# Synthèse des choix techniques

| Élément | Choix retenu | Justification |
|----------|--------------|---------------|
| Langage | Python | Écosystème adapté au data engineering et à l'IA. |
| APIs | requests | Communication avec les services REST. |
| Flux RSS | feedparser | Lecture native des flux RSS. |
| HTML | BeautifulSoup | Extraction de contenu lorsque nécessaire. |
| Images | Pillow | Validation et lecture des images. |
| Traitement | Pandas | Manipulation et export des données. |
| Journalisation | logging | Suivi des traitements. |
| Documentation | MkDocs Material | Documentation technique. |
| Conteneurisation | Docker | Reproductibilité de l'environnement. |
| Orchestration | Apache Airflow | Automatisation des pipelines. |

---

# Conclusion

Les choix techniques retenus répondent aux besoins fonctionnels et techniques de **CheckIt.AI**.

L'architecture modulaire permet de séparer clairement les responsabilités entre les différents composants du projet, facilite la maintenance et prépare l'intégration d'une orchestration complète avec Apache Airflow.

Cette organisation garantit également la reproductibilité des traitements et la production de jeux de données homogènes destinés aux futurs modèles de traitement automatique du langage, de vision par ordinateur et de classification multimodale.