# Objectifs du monitoring

# Introduction

Le monitoring constitue un élément essentiel du fonctionnement d'un pipeline ETL. Il permet de suivre l'exécution des traitements, de mesurer leurs performances et de vérifier en permanence la qualité des données produites.

Dans le cadre de **CheckIt.AI**, l'objectif n'est pas uniquement de détecter les erreurs, mais également de disposer d'une vision globale de l'activité du pipeline afin d'en faciliter l'exploitation et la maintenance.

Le dispositif de supervision accompagne ainsi l'ensemble des étapes, depuis l'extraction des données jusqu'au contrôle qualité final.

---

# Garantir le bon fonctionnement du pipeline

Le premier objectif du monitoring consiste à vérifier que les différentes étapes du pipeline s'exécutent correctement.

La supervision permet notamment de contrôler :

- le démarrage des traitements ;
- le bon enchaînement des DAGs ;
- la réussite ou l'échec des différentes étapes ;
- la durée des traitements ;
- le statut final de chaque exécution.

Ces informations permettent de détecter rapidement toute anomalie pouvant interrompre le pipeline.

---

# Contrôler la qualité des données

Le monitoring ne se limite pas au suivi technique du pipeline. Il permet également de contrôler la qualité des données produites.

Les principaux contrôles portent notamment sur :

- le nombre d'articles extraits ;
- le nombre d'articles validés ;
- les articles rejetés ;
- les doublons détectés ;
- les images téléchargées ;
- les images invalides ;
- les champs obligatoires absents.

Ces indicateurs permettent de vérifier que les données restent exploitables au fil des exécutions.

---

# Mesurer les performances

Le suivi des performances permet d'évaluer le comportement du pipeline au cours du temps.

Le monitoring fournit notamment des informations concernant :

- la durée d'extraction ;
- la durée de transformation ;
- la durée du chargement ;
- la durée du contrôle qualité ;
- le temps total d'exécution.

Ces mesures facilitent l'identification d'éventuels ralentissements et permettent d'orienter les optimisations futures.

---

# Faciliter le diagnostic

En cas d'incident, le monitoring fournit les informations nécessaires pour identifier rapidement l'origine du problème.

Les différentes sources d'information disponibles sont complémentaires :

- les journaux d'exécution ;
- les rapports JSON générés par chaque étape ;
- les informations enregistrées dans PostgreSQL ;
- les états d'exécution des DAGs dans Apache Airflow.

Le croisement de ces informations facilite considérablement les opérations de diagnostic.

---

# Assurer la traçabilité

Chaque exécution du pipeline est enregistrée afin de conserver un historique complet des traitements réalisés.

Cette traçabilité permet notamment de :

- retrouver les paramètres d'une exécution ;
- consulter les statistiques produites ;
- analyser les résultats obtenus ;
- comparer plusieurs exécutions ;
- suivre l'évolution du pipeline au cours du temps.

Cette conservation des informations facilite également les opérations d'audit et de maintenance.

---

# Préparer une exploitation en production

Le monitoring constitue une étape indispensable avant un déploiement dans un environnement de production.

Il permet de disposer des informations nécessaires pour :

- superviser automatiquement les traitements ;
- détecter rapidement les anomalies ;
- intervenir efficacement en cas d'incident ;
- garantir la disponibilité du pipeline ;
- assurer la qualité des données produites.

Cette approche contribue à rendre le pipeline plus robuste et plus facilement exploitable.

---

# Conclusion

Le monitoring ne se limite pas à la détection des erreurs. Il constitue un véritable outil de pilotage permettant de suivre l'activité du pipeline, de contrôler la qualité des données, de mesurer les performances et de faciliter les opérations de maintenance.

Les chapitres suivants présentent les différents composants mis en œuvre pour atteindre ces objectifs au sein du projet CheckIt.AI.