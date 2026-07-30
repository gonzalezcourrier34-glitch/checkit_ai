# Gestion des alertes

## Introduction

Le monitoring ne consiste pas uniquement à observer le fonctionnement du pipeline. Il doit également permettre de détecter rapidement les situations anormales nécessitant une intervention.

Dans **CheckIt.AI**, les alertes reposent principalement sur l'analyse des états d'exécution, des indicateurs de qualité, des KPI de supervision et des journaux produits par les différentes étapes du pipeline.

L'objectif est d'identifier les anomalies le plus tôt possible afin de limiter leur impact sur la qualité des données produites et sur le bon déroulement des traitements.

---

## Détection des anomalies

Plusieurs types d'événements peuvent révéler un dysfonctionnement du pipeline.

Les principales situations surveillées concernent notamment :

- l'échec d'une exécution Airflow ;
- une erreur lors de l'extraction ;
- une erreur pendant la transformation ;
- un échec du chargement dans PostgreSQL ;
- un contrôle qualité non conforme ;
- une baisse importante du nombre d'articles collectés ;
- une augmentation anormale des erreurs ou des rejets ;
- une dégradation des performances du pipeline.

La surveillance de ces événements permet d'identifier rapidement les anomalies avant qu'elles n'affectent les traitements suivants ou les données stockées.

---

## Exemples de situations surveillées

Les indicateurs produits par le pipeline permettent de mettre en évidence différents types d'anomalies.

| Situation observée | Conséquence possible |
|--------------------|----------------------|
| DAG en échec | Arrêt du pipeline |
| Aucun article extrait | Source indisponible ou erreur de configuration |
| Forte baisse du nombre d'articles | Changement de structure d'une source ou limitation d'une API |
| Nombre important d'articles rejetés | Données incomplètes ou invalides |
| Nombre élevé d'images invalides | Problème de téléchargement ou de validation |
| Faible taux de complétude | Métadonnées ou contenus manquants |
| Temps d'exécution anormalement long | Dégradation des performances ou ralentissement d'un service |
| Erreurs répétées dans les logs | Dysfonctionnement nécessitant une analyse |

Ces situations ne traduisent pas systématiquement une erreur critique, mais elles constituent des signaux qui méritent une analyse.

---

## Niveaux de surveillance

Tous les événements ne présentent pas le même niveau de gravité.

Selon leur impact, ils peuvent être classés en plusieurs niveaux de surveillance.

| Niveau | Exemple |
|---------|----------|
| Information | Exécution plus longue que d'habitude |
| Avertissement | Baisse du nombre d'articles collectés ou augmentation des rejets |
| Critique | Échec d'un DAG, interruption du pipeline ou impossibilité de charger les données |

Cette hiérarchisation permet de prioriser les opérations de diagnostic et de concentrer les efforts sur les incidents les plus importants.

---

## Sources d'information

Les alertes peuvent être détectées grâce à plusieurs composants du projet.

| Composant | Informations fournies |
|------------|-----------------------|
| Apache Airflow | État des DAGs, des tâches et historique des exécutions |
| Dashboard Streamlit | Vue synthétique des principaux indicateurs et KPI |
| Rapports JSON | Statistiques détaillées de chaque étape |
| PostgreSQL | Historique des traitements et données utilisées pour les indicateurs |
| Logs | Messages d'erreur, avertissements et informations de diagnostic |

Le croisement de ces différentes sources permet d'obtenir une vision complète de l'état du pipeline et de faciliter l'identification de l'origine d'un incident.

---

## Réaction face à une alerte

Lorsqu'une anomalie est détectée, plusieurs vérifications peuvent être réalisées afin d'identifier rapidement son origine.

Une démarche typique consiste à :

1. vérifier le statut de l'exécution dans Apache Airflow ;
2. consulter les journaux d'exécution ;
3. analyser le rapport JSON correspondant ;
4. vérifier les indicateurs enregistrés dans PostgreSQL ;
5. identifier la cause du dysfonctionnement ;
6. corriger l'anomalie ;
7. relancer le pipeline si nécessaire.

Cette méthode permet de réduire le temps nécessaire au diagnostic et de limiter l'impact des incidents sur les traitements suivants.

---

## Limites du dispositif actuel

Dans sa version actuelle, **CheckIt.AI** repose principalement sur une supervision manuelle réalisée à l'aide du dashboard, des rapports d'exécution et des journaux.

Le projet ne met pas en œuvre de mécanisme automatique d'envoi d'alertes ou de notifications. L'identification des anomalies repose donc sur la consultation des différents outils de supervision.

Cette approche reste adaptée au contexte pédagogique du projet tout en offrant une bonne visibilité sur le fonctionnement du pipeline.

---

## Évolutions possibles

Dans une version destinée à un environnement de production, plusieurs améliorations pourraient être mises en place :

- envoi automatique d'un courrier électronique lors d'un échec ;
- notifications Microsoft Teams ou Slack ;
- alertes basées sur des seuils configurables ;
- supervision continue des traitements ;
- intégration avec des outils spécialisés tels que Prometheus ou Grafana ;
- tableaux de bord historiques et alertes prédictives.

Ces évolutions permettraient d'automatiser davantage la surveillance du pipeline et de réduire les délais d'intervention.

---

## Conclusion

La gestion des alertes constitue un élément essentiel du dispositif de monitoring de **CheckIt.AI**.

Elle permet de détecter rapidement les anomalies, de faciliter leur diagnostic et de limiter leur impact sur le fonctionnement du pipeline et sur la qualité des données produites.

Même si la supervision repose aujourd'hui principalement sur une analyse manuelle des différents indicateurs, l'architecture mise en place constitue une base solide pouvant évoluer vers un système d'alertes automatisé dans un contexte de production.