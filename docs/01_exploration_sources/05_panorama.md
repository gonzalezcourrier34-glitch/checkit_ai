# Panorama des sources étudiées

Au cours de cette étude, j'ai identifié plusieurs familles de sources susceptibles d'alimenter le pipeline d'acquisition de CheckIt.AI. Chacune présente des caractéristiques, des avantages et des contraintes spécifiques.

Ces sources peuvent être regroupées en cinq grandes catégories, résumées dans le tableau ci-dessous.

| Catégorie                    | Description                                                                                                                       | Intérêt principal                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Datasets académiques         | Jeux de données utilisés dans les travaux de recherche et contenant généralement des publications déjà annotées.                  | Constitution d'un corpus labellisé                 |
| APIs d'actualité             | Services web permettant d'accéder automatiquement à des articles d'actualité récents via une interface documentée.                | Collecte automatisée et actualisée                 |
| Flux RSS                     | Flux de syndication proposés par les médias pour diffuser leurs nouvelles publications.                                           | Veille continue et simplicité d'intégration        |
| Plateformes de fact-checking | Sites spécialisés dans la vérification d'informations publiant des analyses et des verdicts sur des affirmations ou des articles. | Acquisition de contenus vérifiés et de verdicts    |
| Réseaux sociaux              | Plateformes sur lesquelles les utilisateurs publient directement des contenus textuels et multimédias.                            | Collecte de contenus multimodaux récents et variés |

Aucune de ces catégories ne répond, à elle seule, à l'ensemble des besoins du projet. Certaines privilégient la disponibilité de labels de véracité, d'autres proposent une couverture de l'actualité en temps réel, tandis que les réseaux sociaux permettent d'accéder à des contenus multimodaux largement diffusés.

Les sections suivantes présentent chacune de ces catégories plus en détail afin d'en analyser les avantages, les limites et leur pertinence dans le cadre du développement du pipeline de collecte de CheckIt.AI.
