# Limites du projet

## Objectif

Comme tout projet d'ingénierie, **CheckIt.AI** présente certaines limites liées aux choix techniques réalisés, aux ressources disponibles et au périmètre retenu pour ce projet.

Cette section a pour objectif d'identifier ces limites afin de mieux comprendre les points pouvant être améliorés dans les versions futures du pipeline.

---

## Dépendance aux sources externes

Le pipeline repose principalement sur des sources de données externes :

- API d'actualité ;
- flux RSS ;
- sites de fact-checking ;
- jeux de données académiques.

Le fonctionnement du pipeline dépend donc directement de la disponibilité de ces différentes sources.

Une modification d'une API, un changement de structure d'un site web ou une interruption temporaire d'un service peut entraîner une diminution du nombre d'articles collectés.

---

## Qualité des données

La qualité des informations récupérées dépend directement des sources interrogées.

Certaines publications peuvent présenter :

- des métadonnées incomplètes ;
- des images absentes ;
- des contenus très courts ;
- des informations dupliquées ;
- des langues mal détectées.

Le pipeline met en œuvre plusieurs mécanismes de validation, mais il ne peut pas corriger toutes les imperfections présentes dans les données d'origine.

---

## Limitations des API

Plusieurs API utilisées dans le projet appliquent des restrictions d'utilisation.

Parmi les principales contraintes :

- quotas journaliers ;
- limitation du nombre de requêtes ;
- restrictions selon l'abonnement ;
- données historiques limitées.

Ces limitations peuvent réduire le volume de données collectées lors d'une exécution.

---

## Couverture des sources

Même si plusieurs familles de sources sont utilisées, le pipeline ne couvre pas l'ensemble des médias disponibles sur Internet.

Certaines plateformes ne proposent pas d'API publique ou imposent des restrictions empêchant une collecte automatisée.

Le corpus obtenu ne représente donc pas l'intégralité des informations publiées en ligne.

---

## Validation des images

Le pipeline vérifie la validité technique des images téléchargées.

En revanche, il n'analyse pas encore leur contenu.

Par exemple, il ne permet pas actuellement de :

- détecter une image manipulée ;
- reconnaître les objets présents ;
- identifier une image générée par intelligence artificielle ;
- comparer automatiquement deux images similaires.

Ces traitements pourront être ajoutés dans une version ultérieure.

---

## Performances

Les performances du pipeline dépendent notamment :

- du nombre de sources configurées ;
- de la vitesse des connexions réseau ;
- des performances du serveur PostgreSQL ;
- des temps de réponse des API.

Le temps d'exécution peut donc varier sensiblement d'un lancement à l'autre.

---

## Évolutivité

L'architecture modulaire facilite l'ajout de nouvelles sources de données.

Néanmoins, chaque nouvel extracteur nécessite :

- une configuration adaptée ;
- des tests spécifiques ;
- la gestion des éventuelles contraintes propres à la source.

L'intégration de nouvelles plateformes demande donc un travail de développement supplémentaire.

---

## Bilan

Malgré ces limites, le pipeline répond aux objectifs fixés au début du projet.

Il permet de collecter automatiquement des données issues de plusieurs familles de sources, de les préparer pour PostgreSQL et d'en contrôler la qualité avant leur exploitation.

Les limites identifiées constituent principalement des pistes d'amélioration pour les prochaines évolutions de CheckIt.AI.