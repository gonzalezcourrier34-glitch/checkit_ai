# Contexte

Dans le cadre du développement de CheckIt.AI, je souhaite mettre en place un pipeline capable de collecter automatiquement des publications d’actualité pouvant contenir du texte, des images et différentes métadonnées.

Ces données seront ensuite utilisées pour alimenter un moteur de détection de désinformation. Il est donc important que le texte, l’image et les métadonnées d’une même publication restent correctement associés tout au long du processus de collecte et de traitement.

Avant de développer ce pipeline, je dois identifier les sources de données les plus pertinentes. Cette phase d’exploration consiste à comparer plusieurs solutions selon des critères techniques, fonctionnels et juridiques afin de sélectionner celles qui répondent le mieux aux besoins du projet.

Les sources étudiées comprennent notamment :

* des datasets académiques ;
* des API d’actualité ;
* des flux RSS ;
* des réseaux sociaux ;
* des sites spécialisés dans le fact-checking ;
* des sites web accessibles par scraping, lorsque leurs conditions d’utilisation et leur fichier `robots.txt` l’autorisent.

Toutes ces sources ne proposent pas nécessairement les mêmes informations. Certaines fournissent uniquement du texte et des métadonnées, tandis que d’autres contiennent également des images ou des labels indiquant si une publication est considérée comme fiable, trompeuse ou fausse. L’étude doit donc permettre de déterminer précisément les données disponibles pour chaque source.

## Objectifs

À travers cette étude, je cherche à :

* identifier les sources proposant des publications contenant à la fois du texte, des images et des métadonnées exploitables ;
* vérifier que les différents éléments d’une publication restent correctement associés lors de leur récupération ;
* déterminer si les images sont directement fournies par la source ou si elles doivent être récupérées depuis les pages des articles ;
* évaluer la présence éventuelle de labels permettant de distinguer les contenus fiables des contenus relevant de la désinformation ;
* analyser les méthodes d’extraction automatisée proposées par chaque source ;
* vérifier les contraintes techniques, les quotas et les conditions d’utilisation associés à chaque solution ;
* évaluer la qualité, la quantité, la diversité et la fréquence de mise à jour des données disponibles ;
* comparer les avantages et les limites de chaque source ;
* recommander les sources les plus adaptées au développement du pipeline CheckIt.AI.

Cette analyse doit finalement me permettre de sélectionner un ensemble complémentaire de sources. Les sources d’actualité pourront fournir des publications récentes et variées, tandis que les datasets académiques et les plateformes de fact-checking pourront apporter des données déjà annotées, utiles pour l’évaluation ou l’entraînement futur d’un modèle de détection de désinformation.
