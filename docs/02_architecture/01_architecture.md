# Architecture globale

## Objectif

Dans cette section, je présente l'organisation générale de **CheckIt.AI** ainsi que les principaux composants qui constituent le projet.

L'objectif est de construire un pipeline capable de collecter automatiquement des publications provenant de différentes sources, de les préparer dans un format commun, de les transformer puis de les stocker dans une base de données afin de constituer un jeu de données exploitable pour de futurs traitements d'intelligence artificielle.

Les données manipulées par le pipeline peuvent contenir :

- du texte ;
- des images ;
- des métadonnées ;
- des labels de véracité ;
- des caractéristiques générées pendant les différentes étapes de transformation.

Pour rendre le projet plus simple à développer et à maintenir, j'ai choisi de séparer le pipeline en plusieurs composants indépendants. Chaque composant possède un rôle bien défini et intervient à une étape précise du traitement.

Cette organisation me permet notamment de :

- limiter les dépendances entre les modules ;
- faciliter les tests et le débogage ;
- ajouter de nouvelles sources plus facilement ;
- rejouer certaines étapes du pipeline sans relancer l'ensemble des traitements ;
- automatiser l'exécution avec Apache Airflow ;
- suivre l'état du pipeline grâce au tableau de bord.

---

## Vue d'ensemble

Le traitement des données est organisé sous la forme d'une succession d'étapes.

Chaque étape reçoit les données produites par l'étape précédente, leur applique un traitement spécifique puis transmet le résultat à la suivante.

```mermaid
flowchart LR
    A[Sources de données] --> B[Extraction]
    B --> C[Préparation]
    C --> D[Transformation]
    D --> E[Chargement PostgreSQL]
    E --> F[Contrôle qualité]
    F --> G[Jeu de données exploitable]
```
Cette séparation permet de conserver une architecture lisible tout en facilitant la maintenance du projet. Lorsqu'une étape évolue, il est généralement possible de modifier uniquement le composant concerné sans impacter le reste du pipeline.

## Organisation du projet

Afin de respecter cette architecture, j'ai organisé le projet en plusieurs dossiers, chacun regroupant des composants ayant une responsabilité commune.

```text
checkit_ai/
│
├── config/
│   ├── sources/
│   ├── constants.py
│   ├── environment.py
│   ├── paths.py
│   └── settings.py
│
├── dags/
│   ├── checkit_master_pipeline.py
│   ├── checkit_extract_dag.py
│   ├── checkit_transform_dag.py
│   ├── checkit_load_dag.py
│   ├── checkit_quality_dag.py
│   └── checkit_cleanup_dag.py
│
├── dashboard/
│   ├── dashboard/
│   ├── services/
│   └── main.py
│
├── data/
│   ├── datasets/
│   ├── raw/
│   ├── processed/
│   └── images/
│
├── docs/
│
├── logs/
│
├── scripts/
│
├── secrets/ 
│
├── sql/
│
├── src/
│   ├── article/
│   │   ├── preparation/
│   │   ├── schema/
│   │   ├── validation/
│   │   ├── article_transformer.py
│   │   └── article_utils.py
│   │
│   ├── extractors/
│   │   ├── apis/
│   │   ├── datasets/
│   │   ├── rss/
│   │   ├── scrapers/
│   │   └── social/
│   │
│   ├── pipelines/
│   ├── storage/
│   │   ├── files/
│   │   └── postgres/
│   │
│   ├── transformers/
│   ├── utils/
│   └── logger.py
│
├── tests/
│
├── .env.example
├── docker-compose.yml
├── mkdocs.yml
├── pyproject.toml
└── README.md
```

J'ai choisi cette organisation afin de regrouper les fichiers ayant un même rôle. Cette séparation rend le projet plus lisible et facilite également les évolutions futures.

Par exemple, tous les extracteurs sont regroupés dans le même dossier, tandis que les traitements, le stockage ou encore les utilitaires sont isolés dans leurs propres modules.

La présence de dossiers dédiés à la documentation, aux tests, aux scripts SQL, aux secrets ou encore aux DAG Airflow permet également de mieux distinguer les différentes parties du projet.

## Conclusion

Cette architecture constitue la base de l'ensemble du projet CheckIt.AI.

Elle me permet de développer chaque composant indépendamment tout en conservant une organisation cohérente de l'ensemble du pipeline.

Les sections suivantes détaillent le rôle de chacun de ces composants ainsi que la manière dont les données circulent entre les différentes étapes du traitement.