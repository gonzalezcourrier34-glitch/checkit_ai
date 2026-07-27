# Dashboard de supervision

## Objectif

En complément du pipeline d'acquisition, j'ai développé un tableau de bord permettant de superviser l'ensemble du fonctionnement de **CheckIt.AI**.

L'objectif de cette interface est de fournir une vision synthétique de l'état du pipeline, des données stockées dans PostgreSQL et des principales statistiques de fonctionnement.

Le dashboard constitue ainsi un outil d'aide au suivi et au diagnostic du pipeline.

---

## Présentation générale

Le dashboard est développé avec **Streamlit**.

Il communique directement avec PostgreSQL afin d'afficher les informations les plus récentes disponibles dans la base de données.

Les principales fonctionnalités sont regroupées dans plusieurs pages accessibles depuis une barre latérale de navigation.

Cette organisation permet de séparer les différentes vues tout en conservant une interface simple à utiliser.

---

## Informations affichées

Le tableau de bord permet notamment de consulter :

- l'état de la connexion PostgreSQL ;
- l'état d'Apache Airflow ;
- les dernières exécutions du pipeline ;
- les principaux indicateurs du projet ;
- les statistiques de la base de données.

Ces informations sont actualisées automatiquement afin de refléter l'état courant du pipeline.

---

## Suivi des exécutions

Le dashboard affiche les informations relatives aux derniers traitements réalisés.

Parmi les principaux éléments présentés :

- date de la dernière exécution ;
- statut du pipeline ;
- nombre d'articles traités ;
- nombre d'images téléchargées ;
- durée d'exécution ;
- indicateurs de qualité.

Cette vue permet de vérifier rapidement que le pipeline fonctionne correctement.

---

## Visualisation des données

Le tableau de bord offre également plusieurs vues facilitant l'exploration des données stockées dans PostgreSQL.

Selon les pages consultées, il est possible d'observer :

- les articles collectés ;
- les sources utilisées ;
- les images téléchargées ;
- les labels disponibles ;
- les caractéristiques calculées.

Cette visualisation simplifie le contrôle des données sans nécessiter de requêtes SQL.

---

## Indicateurs affichés

Le dashboard présente différents indicateurs permettant de suivre l'activité du pipeline.

Par exemple :

- nombre total d'articles ;
- nombre de sources ;
- nombre d'images ;
- nombre de labels ;
- nombre d'exécutions du pipeline.

Ces indicateurs offrent une vision synthétique de l'état du projet.

---

## Aide au diagnostic

En cas d'erreur, le dashboard facilite l'identification de l'origine du problème.

Les informations affichées permettent notamment de :

- vérifier que PostgreSQL est accessible ;
- vérifier que les DAGs se sont exécutés correctement ;
- consulter les derniers rapports produits ;
- contrôler les principaux indicateurs du pipeline.

Cette centralisation des informations simplifie les opérations de maintenance.

---

## Illustration

Cette section pourra être complétée par plusieurs captures d'écran présentant :

- la page d'accueil du dashboard ;
- les principaux indicateurs ;
- les statistiques de la base de données ;
- le suivi des exécutions du pipeline.

Ces illustrations permettront de visualiser concrètement l'interface développée.

---

## Conclusion

Le dashboard constitue un complément naturel du pipeline CheckIt.AI.

Il facilite la supervision des traitements, la consultation des données et le suivi des principaux indicateurs du projet.

Cette interface permet ainsi de disposer d'une vision globale du fonctionnement du pipeline sans avoir à consulter directement Apache Airflow ou PostgreSQL.