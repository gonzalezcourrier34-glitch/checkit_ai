# Objectifs du monitoring

## Introduction

Le monitoring constitue un élément essentiel du fonctionnement d’un pipeline ETL. Il permet de suivre l’exécution des traitements, de mesurer leurs performances et de contrôler la qualité des données produites.

Dans le cadre de **CheckIt.AI**, l’objectif n’est pas uniquement de détecter les erreurs. Le dispositif de supervision doit également fournir une vision globale de l’activité du pipeline afin d’en faciliter l’exploitation, le diagnostic et la maintenance.

La supervision accompagne ainsi les différentes étapes du traitement, depuis l’extraction des données jusqu’au contrôle qualité final.

---

## Garantir le bon fonctionnement du pipeline

Le premier objectif du monitoring consiste à vérifier que les différentes étapes du pipeline s’exécutent correctement.

La supervision permet notamment de contrôler :

- le démarrage des traitements ;
- le bon enchaînement des DAGs ;
- la réussite ou l’échec des différentes étapes ;
- la durée des traitements ;
- le statut final de chaque exécution.

Ces informations permettent de détecter rapidement les anomalies susceptibles d’interrompre ou de dégrader le fonctionnement du pipeline.

---

## Contrôler la qualité des données

Le monitoring ne se limite pas au suivi technique des traitements. Il permet également de contrôler la qualité des données produites.

Les principaux indicateurs portent notamment sur :

- le nombre d’articles extraits ;
- le nombre d’articles validés ;
- le nombre d’articles rejetés ;
- les doublons détectés ;
- les images téléchargées ;
- les images invalides ;
- les champs obligatoires absents ;
- les taux de complétude des données.

Ces indicateurs permettent de vérifier que les données restent cohérentes, complètes et exploitables au fil des exécutions.

---

## Mesurer les performances

Le suivi des performances permet d’évaluer le comportement du pipeline au cours du temps.

Le monitoring fournit notamment des informations concernant :

- la durée de l’extraction ;
- la durée de la transformation ;
- la durée du chargement ;
- la durée du contrôle qualité ;
- la durée totale d’une exécution ;
- la durée des différentes tâches Airflow.

Ces mesures facilitent l’identification des ralentissements et permettent d’orienter les futures optimisations.

---

## Faciliter le diagnostic

En cas d’incident, le monitoring fournit les informations nécessaires pour identifier rapidement l’origine du problème.

Les différentes sources d’information disponibles sont complémentaires :

- les journaux d’exécution des tâches ;
- les états des DAGs et des DagRuns dans Apache Airflow ;
- les statistiques enregistrées dans PostgreSQL ;
- les rapports techniques produits par les différentes étapes du pipeline ;
- les messages d’erreur affichés dans le dashboard.

Le croisement de ces informations facilite les opérations de diagnostic et permet de distinguer une erreur d’extraction, de transformation, de chargement ou de qualité.

---

## Assurer la traçabilité

Chaque exécution du pipeline est enregistrée afin de conserver un historique des traitements réalisés.

Cette traçabilité permet notamment de :

- retrouver les paramètres d’une exécution ;
- consulter les statistiques produites ;
- analyser les résultats obtenus ;
- comparer plusieurs exécutions ;
- identifier les dernières erreurs ;
- suivre l’évolution du pipeline au cours du temps.

La conservation de ces informations facilite également les opérations d’audit, de maintenance et d’amélioration continue.

---

## Préparer une exploitation en production

Le monitoring constitue une étape importante avant le déploiement du pipeline dans un environnement de production.

Il permet de disposer des informations nécessaires pour :

- suivre l’état des traitements ;
- détecter rapidement les anomalies ;
- intervenir plus efficacement en cas d’incident ;
- surveiller la disponibilité des différents composants ;
- contrôler la qualité des données produites ;
- évaluer les performances du pipeline.

Cette approche contribue à rendre le pipeline plus robuste, plus observable et plus facilement exploitable.

---

## Conclusion

Le monitoring ne se limite pas à la détection des erreurs. Il constitue un véritable outil de pilotage permettant de suivre l’activité du pipeline, de contrôler la qualité des données, de mesurer les performances et de faciliter les opérations de diagnostic et de maintenance.

Les chapitres suivants présentent les différents composants mis en œuvre pour atteindre ces objectifs au sein du projet **CheckIt.AI**.