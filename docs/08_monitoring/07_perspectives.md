# Perspectives d'évolution

## Introduction

Le dispositif de monitoring développé dans le cadre de **CheckIt.AI** répond aux besoins du projet en assurant le suivi des traitements, le contrôle de la qualité des données et la détection des principales anomalies.

Toutefois, dans un contexte de montée en charge ou de déploiement en production, plusieurs évolutions pourraient être envisagées afin d'améliorer les capacités de supervision, d'automatiser davantage les opérations de surveillance et de renforcer l'observabilité du pipeline.

---

## Automatisation des alertes

Dans sa version actuelle, la supervision repose principalement sur la consultation du dashboard, des rapports d'exécution et des journaux.

Une première évolution consisterait à automatiser l'envoi de notifications lorsqu'une anomalie est détectée.

Les événements susceptibles de déclencher une alerte pourraient notamment être :

- l'échec d'un DAG Airflow ;
- l'indisponibilité d'une API ;
- l'absence d'articles extraits ;
- le dépassement d'un temps d'exécution maximal ;
- une augmentation importante du taux de rejet ;
- une dégradation du taux de complétude des données.

Ces notifications permettraient une prise en charge plus rapide des incidents et réduiraient le temps de réaction des équipes d'exploitation.

---

## Supervision en continu

Le monitoring actuel fournit principalement une vision de l'état des traitements lors ou après leur exécution.

Une évolution intéressante consisterait à mettre en place une supervision en continu permettant de suivre :

- la progression des traitements ;
- l'état des différentes tâches ;
- les ressources utilisées ;
- les performances du pipeline ;
- les erreurs dès leur apparition.

Cette approche améliorerait la visibilité sur les traitements les plus longs et faciliterait la détection précoce des anomalies.

---

## Historisation des indicateurs

Le stockage des indicateurs pourrait être enrichi afin de permettre une analyse sur de longues périodes.

Cette historisation offrirait plusieurs possibilités :

- suivre l'évolution du volume de données collectées ;
- mesurer les performances au fil du temps ;
- comparer plusieurs exécutions ;
- identifier des tendances ;
- détecter progressivement certaines anomalies.

Ces analyses faciliteraient l'identification des évolutions du pipeline et permettraient d'anticiper les besoins d'optimisation.

---

## Intégration d'outils spécialisés

Le dispositif de monitoring pourrait être complété par des solutions dédiées à la supervision des infrastructures et des applications.

Parmi les outils couramment utilisés, on peut notamment citer :

- Prometheus pour la collecte des métriques ;
- Grafana pour la création de tableaux de bord interactifs ;
- Loki pour la centralisation des journaux ;
- ELK (Elasticsearch, Logstash, Kibana) pour l'analyse des logs.

L'intégration de ces outils offrirait des fonctionnalités avancées de visualisation, de corrélation des événements et d'analyse des performances.

---

## Tableaux de bord enrichis

Le dashboard Streamlit pourrait également évoluer afin de proposer des visualisations plus complètes.

Par exemple :

- évolution des volumes de données ;
- performances par extracteur ;
- répartition des erreurs ;
- historique des exécutions ;
- évolution des indicateurs de qualité ;
- évolution des taux de complétude ;
- comparaisons entre plusieurs exécutions.

Ces représentations faciliteraient l'analyse du comportement du pipeline et le suivi de son évolution dans le temps.

---

## Analyse prédictive

À plus long terme, les données issues du monitoring pourraient être exploitées afin de détecter automatiquement certains comportements inhabituels.

Une telle approche pourrait permettre :

- d'anticiper une dégradation des performances ;
- d'identifier des anomalies récurrentes ;
- de détecter un changement de comportement d'une source de données ;
- d'estimer le risque d'échec d'un traitement ;
- de prévoir certains incidents avant qu'ils ne perturbent le pipeline.

Cette évolution rapprocherait progressivement le dispositif de supervision des pratiques modernes d'observabilité et de maintenance prédictive.

---

## Renforcement de la résilience

Une autre évolution consisterait à améliorer la capacité du pipeline à faire face automatiquement à certains incidents.

Par exemple :

- relance automatique de traitements temporaires en échec ;
- reprise après interruption ;
- mécanismes de bascule vers une source alternative ;
- seuils de surveillance configurables ;
- contrôle automatique de la disponibilité des services.

Ces améliorations contribueraient à accroître la robustesse du pipeline et à limiter les interventions manuelles.

---

## Vers une plateforme de production

Les améliorations précédentes permettraient de faire évoluer **CheckIt.AI** vers une solution davantage adaptée à un environnement de production.

Le dispositif de monitoring gagnerait notamment en :

- automatisation ;
- réactivité ;
- observabilité ;
- capacité d'analyse ;
- traçabilité ;
- robustesse.

Ces évolutions contribueraient à simplifier l'exploitation quotidienne du pipeline tout en améliorant la fiabilité des traitements et la qualité des données produites.

---

## Conclusion

Le monitoring développé dans le cadre de **CheckIt.AI** constitue une base solide pour la supervision du pipeline ETL.

Grâce à l'orchestration assurée par Apache Airflow, aux rapports d'exécution, aux journaux, au stockage des données dans PostgreSQL et au dashboard Streamlit, il est possible de suivre efficacement le fonctionnement de la plateforme, d'évaluer la qualité des données produites et d'identifier rapidement les anomalies.

Les perspectives présentées dans ce chapitre montrent que cette architecture peut évoluer progressivement vers un dispositif de supervision plus automatisé, plus réactif et davantage orienté vers les exigences d'un environnement de production et d'observabilité moderne.