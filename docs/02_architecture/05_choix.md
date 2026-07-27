# Choix techniques

## Objectif

Dans cette section, je présente les principaux choix techniques que j’ai retenus pour développer **CheckIt.AI**.

L’objectif est d’expliquer pourquoi j’ai sélectionné certaines technologies, bibliothèques et méthodes d’organisation pour construire un pipeline capable de collecter, préparer, transformer, stocker et superviser des données multimodales.

J’ai cherché à obtenir une architecture :

- modulaire ;
- automatisée ;
- reproductible ;
- testable ;
- adaptée au traitement de volumes de données variables ;
- suffisamment évolutive pour accueillir de nouvelles sources.

Les choix présentés concernent le langage, les bibliothèques Python, le stockage, l’orchestration, la conteneurisation, la documentation et le tableau de bord.

---

## Critères de sélection

J’ai choisi les technologies du projet selon plusieurs critères :

- leur compatibilité avec Python ;
- leur simplicité d’intégration ;
- la qualité de leur documentation ;
- leur utilisation dans les domaines de la data et de l’intelligence artificielle ;
- leur capacité à être intégrées dans une architecture modulaire ;
- leur facilité de maintenance ;
- leur compatibilité avec Apache Airflow et Docker ;
- leur aptitude à produire des traitements reproductibles.

J’ai également privilégié les outils que je pouvais tester localement et intégrer progressivement dans le projet.

---

## Langage de développement

### Python

J’ai développé l’ensemble du pipeline en **Python**.

Ce langage est particulièrement adapté au projet, car il dispose de nombreuses bibliothèques pour :

- les requêtes HTTP ;
- la lecture de flux RSS ;
- le scraping HTML ;
- la manipulation de données ;
- le traitement des images ;
- la connexion à PostgreSQL ;
- l’orchestration avec Apache Airflow ;
- le développement d’interfaces avec Streamlit ;
- les futurs traitements d’intelligence artificielle.

Python me permet également de conserver le même langage pour les extracteurs, les transformations, les DAG Airflow, les tests et le tableau de bord.

---

## Organisation logicielle

J’ai organisé le projet en modules spécialisés afin que chaque partie possède une responsabilité précise.

| Module | Rôle dans le projet |
|---|---|
| `extractors` | Collecter les publications depuis les différentes sources. |
| `article` | Définir le schéma métier, préparer, nettoyer, dédupliquer, transformer et valider les articles. |
| `transformers` | Générer les caractéristiques calculées pendant la transformation. |
| `storage` | Lire et écrire les fichiers, télécharger les images et charger les données dans PostgreSQL. |
| `pipelines` | Enchaîner les différentes étapes métier. |
| `utils` | Regrouper les fonctions techniques communes. |
| `dags` | Orchestrer les pipelines avec Apache Airflow. |
| `dashboard` | Présenter les indicateurs et l’état du projet. |
| `config` | Centraliser les paramètres, les chemins et la configuration des sources. |
| `tests` | Vérifier le comportement des différents composants. |

Cette organisation me permet de limiter la duplication de code et de modifier un composant sans devoir reprendre l’ensemble du projet.

---

## Gestion des dépendances

Le projet utilise un fichier `pyproject.toml` pour déclarer les dépendances et les informations générales du projet.

J’utilise également **uv** pour gérer l’environnement Python et installer les bibliothèques nécessaires.

Ce choix me permet :

- de centraliser les dépendances ;
- de recréer plus facilement l’environnement ;
- de limiter les différences entre les installations ;
- de simplifier l’exécution des commandes Python ;
- de conserver une configuration versionnée avec le projet.

---

## Bibliothèques HTTP

### Requests

J’utilise `requests` pour plusieurs communications HTTP simples, notamment dans certains extracteurs et pour le téléchargement de ressources distantes.

Cette bibliothèque permet de gérer :

- les requêtes `GET` ;
- les en-têtes HTTP ;
- les paramètres d’URL ;
- les délais d’attente ;
- les codes de réponse ;
- les redirections ;
- le téléchargement en streaming.

### HTTPX

Le projet utilise également `httpx` dans les composants nécessitant une gestion HTTP plus structurée.

Cette bibliothèque permet notamment de réutiliser une session HTTP et de mieux organiser les requêtes envoyées aux sources distantes.

### Tenacity

J’utilise `tenacity` pour encadrer les nouvelles tentatives lorsqu’une erreur temporaire se produit.

Les nouvelles tentatives sont réservées aux situations où elles peuvent être utiles, par exemple :

- erreur serveur temporaire ;
- délai d’attente dépassé ;
- problème réseau ponctuel ;
- limitation momentanée d’une source.

Je ne relance pas automatiquement les requêtes lorsque l’erreur est définitive, comme une authentification invalide ou une mauvaise configuration.

---

## Extraction des flux RSS

### Feedparser

J’utilise `feedparser` pour lire et analyser les flux RSS.

Cette bibliothèque permet d’accéder aux principales informations d’une publication :

- titre ;
- lien ;
- résumé ;
- date ;
- auteur ;
- médias associés.

Les données produites par `feedparser` sont ensuite adaptées vers le schéma commun de CheckIt.AI par les composants du module `rss`.

J’ai retenu cette solution car elle prend en charge les différences courantes entre les flux RSS et Atom.

---

## Extraction HTML

### Beautiful Soup

J’utilise **Beautiful Soup** pour analyser le contenu HTML des sites qui ne proposent pas d’API ou de flux directement exploitable.

Cette bibliothèque me permet notamment de :

- sélectionner les blocs correspondant aux publications ;
- lire un titre ;
- récupérer un lien ;
- extraire un texte ;
- rechercher une date ;
- lire un auteur ;
- récupérer certaines métadonnées HTML.

Les sélecteurs restent propres à chaque site, tandis que les fonctions communes sont regroupées dans le module `scrapers`.

Le scraping est utilisé de manière limitée, principalement pour les sources de fact-checking qui ne fournissent pas d’accès officiel adapté aux besoins du projet.

---

## Manipulation des données

### Pandas

J’utilise `pandas` pour manipuler les données tabulaires et produire les exports CSV.

Cette bibliothèque intervient notamment pour :

- la lecture de certains datasets ;
- le traitement de fichiers volumineux par blocs ;
- la construction de tableaux de données ;
- l’harmonisation des colonnes ;
- l’export des articles transformés au format CSV.

Le traitement par blocs permet de ne pas charger inutilement l’intégralité d’un dataset volumineux en mémoire.

---

## Traitement des images

### Pillow

J’utilise **Pillow** pour inspecter et valider les images téléchargées.

La bibliothèque permet de récupérer plusieurs informations techniques :

- format réel ;
- largeur ;
- hauteur ;
- mode de couleur ;
- présence d’une animation ;
- nombre d’images ;
- taille du fichier ;
- intégrité générale.

Elle permet également de détecter certaines images corrompues, tronquées ou anormalement volumineuses.

Les images ne sont pas chargées entièrement en mémoire lorsque cela n’est pas nécessaire. Le pipeline commence par contrôler les en-têtes, la taille du fichier et les métadonnées disponibles.

---

## Gestion des chemins

### Pathlib

J’utilise `pathlib` pour construire et manipuler les chemins du projet.

Ce choix me permet :

- d’éviter les chemins écrits manuellement sous forme de chaînes ;
- de conserver une meilleure compatibilité entre Windows et Linux ;
- de créer les dossiers nécessaires ;
- de vérifier l’existence des fichiers ;
- de construire les chemins vers les lots, les images et les rapports.

Les chemins principaux sont centralisés dans `config/paths.py`.

---

## Fichiers de configuration

### YAML

Les sources de données sont configurées dans plusieurs fichiers YAML.

Cette organisation me permet de séparer la configuration du code Python.

```text
config/
└── sources.yaml
```