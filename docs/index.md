# CheckIt.AI

## Pipeline d'acquisition de données multimodales pour la détection de désinformation

## Présentation du projet

Dans le cadre de cette mission, **CheckIt.AI**, une start-up spécialisée dans le développement de solutions d'intelligence artificielle pour la lutte contre la désinformation, souhaite enrichir son moteur d'analyse en créant un pipeline d'acquisition de données multimodales.

L'objectif est de concevoir un système capable de collecter automatiquement des publications d'actualité contenant à la fois du **texte** et des **images**, à partir de sources accessibles telles que des APIs, des flux RSS ou des sites web lorsque le scraping est autorisé.

Les données collectées ont vocation à alimenter les futures étapes du moteur d'analyse développé par CheckIt.AI.

---

## Contexte

La désinformation ne se limite plus à un simple texte. Les campagnes de manipulation s'appuient désormais sur plusieurs modalités de données : photographies sorties de leur contexte, montages, captures d'écran, infographies trompeuses ou encore images générées par intelligence artificielle (Multimodal Fake News Detection: A Survey).

Pour entraîner des modèles capables d'identifier ces contenus, il est indispensable de disposer de jeux de données où chaque publication associe correctement :

* un contenu textuel ;
* une ou plusieurs images ;
* des métadonnées (date, source, URL, auteur lorsque disponible).

Cette première étape consiste donc à identifier les meilleures sources de données et à évaluer leur pertinence avant de développer le pipeline d'acquisition.

---

## Objectifs de la mission

Les objectifs de ce projet sont les suivants :

* identifier plusieurs sources de données multimodales pertinentes pour la détection de désinformation ;
* comparer ces sources selon des critères techniques et fonctionnels ;
* sélectionner les sources les plus adaptées aux besoins de CheckIt.AI ;
* définir une stratégie d'extraction automatisée adaptée à chaque source (API REST, téléchargement de datasets, flux RSS ou scraping lorsque cela est autorisé) ;
* proposer un format de données standardisé facilitant les traitements ultérieurs.

---

## Périmètre de l'étude

Cette documentation couvre l'ensemble de la phase d'exploration précédant le développement du pipeline.

Les travaux portent notamment sur :

* l'analyse des datasets académiques ;
* l'étude des APIs d'actualité ;
* l'exploration des flux RSS ;
* l'identification de sources ouvertes permettant de récupérer simultanément du texte et des images ;
* l'évaluation de la qualité des labels disponibles (vrai/faux, fiable/non fiable, absence de labels) ;
* les contraintes techniques et juridiques liées à l'extraction des données.

---

## Technologies envisagées

Le pipeline sera développé autour des technologies suivantes :

* **Python** pour le développement des extracteurs ;
* **APIs REST** pour la collecte automatisée des données ;
* **Flux RSS** pour la récupération continue des publications ;
* **Scraping web** lorsque celui-ci est autorisé par les conditions d'utilisation des sites concernés ;
* **Airflow** pour l'orchestration des tâches ;
* **Docker** pour garantir la reproductibilité de l'environnement d'exécution ;
* **MkDocs** pour la documentation technique du projet.

---

## Organisation de la documentation

La documentation est structurée en plusieurs chapitres correspondant aux différentes phases du projet :

1. **Exploration des sources** : analyse comparative des sources de données multimodales.
2. **Architecture** : conception du pipeline d'acquisition et choix techniques.
3. **Pipeline** : développement des modules d'extraction, de validation et de stockage.
4. **Schemas des structures** : développement des modules d'extraction, de validation et de stockage.
5. **Résultats** : évaluation du pipeline, statistiques de collecte et perspectives d'amélioration.
