# Perspectives d'évolution

# Introduction

Le dispositif de monitoring développé dans le cadre de CheckIt.AI répond aux besoins du projet en assurant le suivi des traitements, le contrôle de la qualité des données et la détection des principales anomalies.

Toutefois, dans un contexte de mise en production ou de montée en charge, plusieurs évolutions pourraient être envisagées afin d'améliorer encore les capacités de supervision du pipeline.

---

# Automatisation des alertes

Dans la version actuelle, la supervision repose principalement sur la consultation du dashboard, des rapports d'exécution et des journaux.

Une première évolution consisterait à automatiser l'envoi de notifications lorsqu'une anomalie est détectée.

Les événements pouvant déclencher une alerte sont par exemple :

- échec d'un DAG Airflow ;
- indisponibilité d'une API ;
- absence d'articles extraits ;
- dépassement d'un temps d'exécution maximal ;
- augmentation importante du taux de rejet.

Ces notifications permettraient une prise en charge plus rapide des incidents.

---

# Supervision en temps réel

Le monitoring actuel fournit principalement une vision de l'état des traitements après leur exécution.

Une évolution intéressante serait de mettre en place une supervision en temps réel permettant de suivre :

- la progression des traitements ;
- les ressources utilisées ;
- les performances du pipeline ;
- les erreurs dès leur apparition.

Cette approche faciliterait le suivi des traitements les plus longs.

---

# Historisation des indicateurs

Le stockage des indicateurs pourrait être enrichi afin de permettre une analyse sur de longues périodes.

Cette historisation offrirait plusieurs possibilités :

- suivre l'évolution du volume de données collectées ;
- mesurer les performances au fil du temps ;
- identifier des tendances ;
- détecter progressivement certaines anomalies.

Ces analyses permettraient d'anticiper les besoins d'optimisation du pipeline.

---

# Intégration d'outils spécialisés

Le dispositif de monitoring pourrait être complété par des solutions dédiées à la supervision des infrastructures.

Parmi les outils couramment utilisés, on peut citer :

- Prometheus pour la collecte des métriques ;
- Grafana pour la création de tableaux de bord interactifs ;
- Loki pour la centralisation des logs.

L'intégration de ces outils offrirait des fonctionnalités avancées de visualisation et d'analyse.

---

# Tableaux de bord enrichis

Le dashboard Streamlit pourrait également évoluer afin de proposer de nouvelles visualisations.

Par exemple :

- évolution des volumes de données ;
- performances par extracteur ;
- répartition des erreurs ;
- historique des exécutions ;
- évolution des indicateurs de qualité.

Ces représentations faciliteraient l'analyse du comportement du pipeline.

---

# Analyse prédictive

À plus long terme, il serait possible d'exploiter les données de monitoring afin de détecter automatiquement certains comportements inhabituels.

Une telle approche pourrait permettre :

- d'anticiper une dégradation des performances ;
- d'identifier des anomalies récurrentes ;
- de détecter un changement de comportement d'une source de données ;
- de prévoir certains incidents avant qu'ils ne perturbent le pipeline.

Cette évolution rapprocherait le dispositif de supervision des pratiques d'observabilité modernes.

---

# Vers une plateforme de production

Les améliorations précédentes permettraient de faire évoluer CheckIt.AI vers une solution plus adaptée à un environnement de production.

Le dispositif de monitoring gagnerait notamment en :

- automatisation ;
- réactivité ;
- capacité d'analyse ;
- traçabilité ;
- robustesse.

Ces évolutions contribueraient à améliorer la disponibilité du pipeline et à simplifier son exploitation au quotidien.

---

# Conclusion

Le monitoring développé dans le cadre de CheckIt.AI constitue une base solide pour la supervision du pipeline ETL.

Grâce à l'orchestration assurée par Apache Airflow, aux rapports d'exécution, aux journaux, au stockage des indicateurs dans PostgreSQL et au dashboard Streamlit, il est possible de suivre efficacement le fonctionnement de la plateforme et d'identifier rapidement les anomalies.

Les évolutions proposées dans ce chapitre ouvrent la voie à une supervision plus automatisée, plus réactive et davantage orientée vers les exigences d'un environnement de production.