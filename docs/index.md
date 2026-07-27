# CheckIt.AI

## Pipeline d'acquisition multimodale pour la collecte et la préparation de données destinées à la détection de désinformation

# Présentation du projet

Dans le cadre de cette mission, **CheckIt.AI**, une start-up spécialisée dans le développement de solutions d'intelligence artificielle appliquées à la lutte contre la désinformation, souhaite mettre en place un pipeline complet d'acquisition de données multimodales.

L'objectif est de concevoir une solution capable de collecter automatiquement des publications d'actualité contenant à la fois du **texte** et des **images**, puis de les valider, les transformer, les enrichir et les stocker dans une base de données relationnelle.

Les données produites ont vocation à alimenter les futures étapes du moteur d'analyse développé par CheckIt.AI, notamment l'entraînement de modèles de détection automatique de désinformation.

---

# Contexte

La désinformation ne se limite plus à un simple texte. Les campagnes de manipulation utilisent aujourd'hui plusieurs modalités de données : photographies sorties de leur contexte, montages, captures d'écran, infographies trompeuses ou encore images générées par intelligence artificielle.

Afin d'entraîner des modèles capables d'identifier ces contenus, il est nécessaire de disposer d'un corpus fiable associant :

- un contenu textuel ;
- une ou plusieurs images ;
- des métadonnées (date, source, URL, auteur lorsque disponible) ;
- des informations permettant d'assurer la traçabilité des données.

La création d'un pipeline d'acquisition automatisé constitue ainsi une étape essentielle dans la construction d'une chaîne de traitement dédiée au fact-checking.

---

# Objectifs de la mission

Les principaux objectifs de ce projet sont les suivants :

- identifier les sources de données les plus pertinentes ;
- développer des extracteurs adaptés à chaque type de source ;
- normaliser les données collectées selon un modèle commun ;
- valider automatiquement les contenus et les images ;
- transformer les données afin de préparer leur stockage ;
- alimenter une base PostgreSQL ;
- contrôler la qualité des données produites ;
- superviser l'ensemble du pipeline grâce à Apache Airflow et un tableau de bord dédié.

---

# Périmètre du projet

Cette documentation couvre l'ensemble du développement du pipeline CheckIt.AI.

Elle présente notamment :

- l'étude des différentes sources de données ;
- les choix d'architecture retenus ;
- le fonctionnement du pipeline d'acquisition ;
- les schémas des principales structures de données ;
- la conception de la base PostgreSQL ;
- l'orchestration avec Apache Airflow ;
- les résultats obtenus après plusieurs exécutions.

---

# Technologies utilisées

Le projet repose principalement sur les technologies suivantes :

- **Python** pour le développement des extracteurs et des traitements ;
- **APIs REST**, **flux RSS**, **scraping HTML** et **datasets académiques** pour la collecte des données ;
- **PostgreSQL** pour le stockage relationnel ;
- **Apache Airflow** pour l'orchestration des traitements ;
- **Docker** pour la reproductibilité de l'environnement ;
- **Streamlit** pour le dashboard de supervision ;
- **MkDocs Material** pour la documentation technique.

---

# Organisation de la documentation

La documentation est organisée en sept chapitres.

1. **Exploration des sources de données**  
   Étude comparative des différentes sources utilisées pour constituer un corpus multimodal.

2. **Architecture du projet**  
   Présentation de l'architecture logicielle, des extracteurs et des principaux choix techniques.

3. **Pipeline d'acquisition**  
   Description du fonctionnement du pipeline, de son exécution et de sa reproductibilité.

4. **Schémas des données**  
   Présentation des principales structures de données utilisées par le pipeline.

5. **Structure de la base PostgreSQL**  
   Description du modèle relationnel, des tables, des index, des vues et des mécanismes de sécurité.

6. **Orchestration avec Apache Airflow**  
   Présentation des différents DAGs, de leur communication et de la gestion des traitements.

7. **Résultats**  
   Analyse des exécutions réalisées, du contenu de la base PostgreSQL, du dashboard de supervision ainsi que des limites et perspectives d'évolution du projet.

---

# Objectif de cette documentation

Cette documentation a pour objectif de présenter l'ensemble de la conception et de la réalisation du pipeline **CheckIt.AI**, depuis l'identification des sources de données jusqu'à la production d'un jeu de données multimodal validé, stocké et supervisé.

Elle constitue à la fois un document de conception, un support technique et une référence permettant de comprendre le fonctionnement global du projet.