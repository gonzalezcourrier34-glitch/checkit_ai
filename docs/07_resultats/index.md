# Résultats

## Objectif

Cette partie présente les résultats obtenus après le développement du pipeline **CheckIt.AI**.

L'objectif est de montrer que les différents choix techniques réalisés tout au long du projet permettent de constituer un pipeline d'acquisition multimodale complet, capable de collecter, transformer, stocker et contrôler automatiquement des données destinées au fact-checking et à la détection de désinformation.

Les résultats présentés s'appuient sur les différentes exécutions réalisées au cours du développement du projet.

---

## Organisation de cette partie

Cette section est organisée autour des principaux résultats obtenus.

1. **Exécution complète du pipeline** : présentation d'une exécution de bout en bout et des fichiers générés.
2. **Base PostgreSQL** : structure finale des données chargées et vérification des tables.
3. **Dashboard de supervision** : visualisation des informations du pipeline et des indicateurs.
4. **Limites du projet** : difficultés rencontrées et limites actuelles de la solution.
5. **Perspectives d'évolution** : améliorations envisageables pour les prochaines versions.

---

## Résultats attendus

À l'issue d'une exécution complète, le pipeline permet :

- d'acquérir automatiquement des données provenant de plusieurs familles de sources ;
- de télécharger et valider les images associées aux articles ;
- de transformer les données selon un modèle relationnel cohérent ;
- de charger les informations dans PostgreSQL ;
- de calculer automatiquement plusieurs indicateurs de qualité ;
- de produire des rapports détaillés à chaque étape du traitement.

L'ensemble de ces traitements est entièrement orchestré par Apache Airflow.

---

## Vérification du fonctionnement

Les différents chapitres de cette partie permettront de vérifier :

- que les DAGs s'exécutent dans le bon ordre ;
- que les données sont correctement transformées ;
- que les tables PostgreSQL sont correctement alimentées ;
- que les indicateurs de qualité sont calculés ;
- que le tableau de bord permet de superviser le pipeline.

Cette analyse permet d'évaluer le fonctionnement global de la solution développée ainsi que son adéquation avec les objectifs fixés au début du projet.

---

## Conclusion

Cette partie constitue la validation pratique du projet.

Elle montre que l'architecture présentée dans les chapitres précédents permet de construire un pipeline d'acquisition multimodale fonctionnel, reproductible et suffisamment robuste pour produire un jeu de données exploitable dans le cadre de futurs travaux de fact-checking et de détection de désinformation.