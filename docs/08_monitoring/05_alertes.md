# Gestion des alertes

# Introduction

Le monitoring ne consiste pas uniquement à observer le fonctionnement du pipeline. Il doit également permettre de détecter rapidement les situations anormales nécessitant une intervention.

Dans CheckIt.AI, les alertes reposent principalement sur l'analyse des états d'exécution, des indicateurs de qualité et des journaux produits par les différentes étapes du pipeline.

L'objectif est d'identifier les anomalies le plus tôt possible afin de limiter leur impact sur la qualité des données produites.

---

# Détection des anomalies

Plusieurs types d'événements peuvent révéler un dysfonctionnement du pipeline.

Les principales situations surveillées concernent :

- l'échec d'une exécution Airflow ;
- une erreur lors de l'extraction ;
- une erreur pendant la transformation ;
- un échec du chargement dans PostgreSQL ;
- un contrôle qualité non conforme ;
- une baisse importante du nombre d'articles collectés ;
- une augmentation anormale des erreurs ou des rejets.

La surveillance de ces événements permet d'intervenir rapidement avant que les anomalies ne se propagent aux traitements suivants.

---

# Exemples de situations surveillées

Les indicateurs produits par le pipeline permettent de mettre en évidence différents types d'anomalies.

| Situation observée | Conséquence possible |
|--------------------|----------------------|
| DAG en échec | Arrêt du pipeline |
| Aucun article extrait | Source indisponible ou erreur de configuration |
| Forte baisse du nombre d'articles | Changement de structure d'une source ou limitation d'une API |
| Nombre important d'articles rejetés | Données incomplètes ou invalides |
| Nombre élevé d'images invalides | Problème de téléchargement ou de validation |
| Temps d'exécution anormalement long | Dégradation des performances ou ralentissement d'un service |
| Erreurs répétées dans les logs | Dysfonctionnement nécessitant une analyse |

Ces situations ne signifient pas systématiquement qu'une erreur critique est présente, mais elles doivent attirer l'attention de l'exploitant.

---

# Seuils de surveillance

Tous les indicateurs n'ont pas la même importance.

Certains événements nécessitent une intervention immédiate, tandis que d'autres peuvent simplement faire l'objet d'une surveillance renforcée.

| Niveau | Exemple |
|---------|----------|
| Information | Exécution plus longue que d'habitude |
| Avertissement | Baisse du nombre d'articles collectés |
| Critique | Échec d'un DAG ou interruption du pipeline |

Cette hiérarchisation permet de concentrer les efforts de maintenance sur les événements les plus importants.

---

# Sources d'information

Les alertes peuvent être détectées grâce à plusieurs composants du projet.

| Composant | Informations fournies |
|------------|-----------------------|
| Apache Airflow | État des DAGs et historique des exécutions |
| Dashboard Streamlit | Vue synthétique des principaux indicateurs |
| Rapports JSON | Statistiques détaillées de chaque étape |
| PostgreSQL | Historique des traitements et indicateurs |
| Logs | Messages d'erreur et informations de diagnostic |

La combinaison de ces différentes sources permet d'obtenir une vision complète de l'état du pipeline.

---

# Réaction face à une alerte

Lorsqu'une anomalie est détectée, plusieurs vérifications peuvent être réalisées.

Par exemple :

1. vérifier le statut de l'exécution dans Apache Airflow ;
2. consulter les journaux d'exécution ;
3. analyser le rapport JSON correspondant ;
4. vérifier les indicateurs enregistrés dans PostgreSQL ;
5. identifier la cause du problème ;
6. corriger l'anomalie ;
7. relancer le pipeline si nécessaire.

Cette démarche permet de limiter le temps nécessaire au diagnostic.

---

# Évolutions possibles

Dans sa version actuelle, CheckIt.AI repose principalement sur une supervision manuelle réalisée à l'aide du dashboard, des rapports et des logs.

Dans une version destinée à la production, plusieurs améliorations pourraient être mises en place :

- envoi automatique d'un e-mail lors d'un échec ;
- notifications Microsoft Teams ou Slack ;
- alertes basées sur des seuils configurables ;
- supervision temps réel ;
- intégration avec des outils spécialisés tels que Prometheus ou Grafana.

Ces évolutions permettraient d'automatiser davantage la surveillance du pipeline.

---

# Conclusion

La gestion des alertes constitue un élément essentiel du dispositif de monitoring. Elle permet de détecter rapidement les anomalies, de limiter les interruptions de service et de garantir la fiabilité du pipeline.

Le chapitre suivant présente la procédure de gestion des incidents et les différentes étapes permettant de diagnostiquer puis de résoudre un dysfonctionnement.