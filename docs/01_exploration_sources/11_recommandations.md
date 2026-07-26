# Recommandations

## Objectif

L'étude des différentes familles de sources montre qu'aucune ne répond, à elle seule, à l'ensemble des besoins de **CheckIt.AI**.

Certaines fournissent des données annotées indispensables au développement des futurs modèles, tandis que d'autres permettent de collecter automatiquement des publications récentes. D'autres encore apportent des contenus déjà vérifiés ou diversifient les médias couverts.

J'ai donc retenu une stratégie reposant sur plusieurs catégories de sources complémentaires, capables d'alimenter un pipeline robuste, évolutif et facilement maintenable.

---

# Sources retenues

## 1. Datasets académiques

Les datasets académiques constituent les principales sources de données annotées utilisées dans **CheckIt.AI**. Ils permettent de développer, d'entraîner et d'évaluer les futurs modèles de détection de désinformation.

Les datasets retenus sont les suivants :

| Dataset                    | Rôle principal                              |
| :------------------------- | :------------------------------------------ |
| **Fakeddit**               | Référence multimodale (texte, image, label) |
| **FakeNewsNet**            | Corpus annoté et métadonnées                |
| **ISOT Fake News Dataset** | Classification textuelle                    |
| **CoAID**                  | Désinformation liée à la santé              |

Dans la configuration actuelle du projet :

* **Fakeddit** possède le rôle `multimodal_reference` ;
* **FakeNewsNet**, **ISOT** et **CoAID** possèdent le rôle `labeled_reference`.

Ces jeux de données constituent les principaux corpus de référence. Leur caractère statique ne permet toutefois pas de suivre l'actualité ni de collecter automatiquement de nouvelles publications.

---

## 2. API d'actualité

Les API d'actualité constituent le principal mécanisme d'acquisition continue de publications récentes.

Afin de limiter la dépendance à un fournisseur unique, plusieurs services complémentaires sont intégrés à **CheckIt.AI**.

| API                            | Rôle principal             |
| :----------------------------- | :------------------------- |
| **NewsData.io**                | Collecte multilingue       |
| **GNews**                      | Actualité générale         |
| **NewsAPI**                    | Recherche thématique       |
| **Currents News API**          | Acquisition complémentaire |
| **Mediastack**                 | Diversification des médias |
| **The Guardian Open Platform** | Actualité anglophone       |
| **GDELT**                      | Veille internationale      |

Ces API permettent :

* de couvrir davantage de médias ;
* de diversifier les langues et les thématiques ;
* de réduire l'impact des quotas imposés par certains fournisseurs ;
* d'améliorer la disponibilité globale du pipeline.

Aucune de ces API ne fournit toutefois de labels de véracité. Les articles récupérés sont donc considérés comme des données d'acquisition non annotées.

---

## 3. Flux RSS

Les flux RSS complètent les API d'actualité en permettant une collecte simple, régulière et peu coûteuse des nouvelles publications.

Les flux actuellement intégrés sont :

* Le Monde ;
* Le Monde - International ;
* Franceinfo ;
* BBC News ;
* BBC Technology ;
* The Guardian - World.

Ils présentent plusieurs avantages :

* intégration simple ;
* absence de clé API ;
* faible coût technique ;
* mise à jour régulière ;
* complément des API d'actualité.

Ils permettent également de maintenir une collecte minimale lorsqu'une API devient temporairement indisponible ou atteint ses quotas.

---

## 4. Sources de fact-checking

Les organismes spécialisés dans la vérification des faits constituent une source importante de données de référence.

Les sources retenues sont :

| Source                      | Rôle principal                 |
| :-------------------------- | :----------------------------- |
| **Google Fact Check Tools** | API officielle de vérification |
| **Full Fact**               | Articles de fact-checking      |
| **Reuters Fact Check**      | Articles de fact-checking      |

Ces sources permettent de récupérer des affirmations déjà vérifiées ainsi que les verdicts publiés par les organismes spécialisés.

Les différents verdicts étant exprimés selon des formulations variées, une étape de normalisation est appliquée afin de les convertir vers les labels utilisés dans **CheckIt.AI**.

---

## 5. Réseaux sociaux

L'architecture actuelle du projet prend en charge deux réseaux sociaux :

| Plateforme   |           Statut           |
| :----------- | :------------------------: |
| **Reddit**   | Pris en charge (désactivé) |
| **Mastodon** | Pris en charge (désactivé) |

Les extracteurs correspondants sont déjà développés mais ne participent pas actuellement à l'exécution normale du pipeline, leur paramètre `enabled` étant positionné à `false`.

Cette organisation permet de les activer ultérieurement sans modifier l'architecture générale du projet.

---

# Architecture recommandée

L'analyse réalisée conduit à retenir une architecture reposant sur plusieurs catégories de sources complémentaires.

| Catégorie            | Rôle dans CheckIt.AI                                 |
| :------------------- | :--------------------------------------------------- |
| Datasets académiques | Corpus annotés de référence                          |
| API d'actualité      | Collecte automatisée de publications récentes        |
| Flux RSS             | Veille continue et diversification des médias        |
| Fact-checking        | Constitution d'un corpus vérifié                     |
| Réseaux sociaux      | Acquisition de contenus publiés par les utilisateurs |

Toutes les données collectées sont converties vers un schéma commun avant leur validation, leur transformation puis leur stockage.

Cette architecture permet :

* d'uniformiser le traitement de sources très différentes ;
* de mutualiser les traitements de validation ;
* de faciliter l'ajout de nouveaux extracteurs ;
* de limiter les modifications nécessaires lors de l'évolution du projet.

---

# Limites

Chaque catégorie de source présente des contraintes spécifiques qu'il est nécessaire de prendre en compte.

## Datasets académiques

* données statiques ;
* disponibilité parfois limitée ;
* couverture temporelle figée ;
* mises à jour peu fréquentes.

## API d'actualité

* quotas d'utilisation ;
* évolution des offres commerciales ;
* dépendance aux clés API ;
* absence de labels de véracité.

## Flux RSS

* métadonnées parfois limitées ;
* texte intégral non garanti ;
* images non systématiques ;
* structure variable selon les médias.

## Fact-checking

* couverture limitée selon les sujets ;
* formulations différentes des verdicts ;
* normalisation nécessaire avant exploitation.

## Réseaux sociaux

* accès dépendant des politiques des plateformes ;
* qualité des publications très variable ;
* absence de labels de véracité ;
* nécessité d'une modération et d'un filtrage importants.

Ces contraintes sont prises en compte dans **CheckIt.AI** grâce à plusieurs mécanismes :

* validation des données ;
* normalisation des métadonnées ;
* suppression des doublons ;
* filtrage des contenus ;
* gestion des erreurs ;
* architecture modulaire des extracteurs.

---

# Conclusion

L'étude des différentes familles de sources montre qu'aucune ne répond seule à l'ensemble des besoins du projet.

J'ai donc retenu une stratégie reposant sur la complémentarité de plusieurs catégories de sources.

Les datasets académiques fournissent les données annotées indispensables au développement et à l'évaluation des futurs modèles. Les API d'actualité assurent la collecte automatisée de publications récentes provenant de nombreux médias. Les flux RSS complètent cette collecte grâce à une veille continue simple à mettre en œuvre. Les plateformes de fact-checking permettent d'enrichir progressivement le corpus avec des affirmations déjà vérifiées.

Enfin, Reddit et Mastodon sont déjà pris en charge par l'architecture du projet. Bien qu'ils soient actuellement désactivés dans la configuration, leur intégration technique est opérationnelle et leur activation pourra être réalisée ultérieurement afin d'enrichir le corpus avec des contenus publiés directement par les utilisateurs.

Cette stratégie est cohérente avec l'architecture modulaire de **CheckIt.AI**. En normalisant l'ensemble des données vers un modèle commun, le projet peut intégrer des sources très différentes tout en conservant un pipeline homogène, évolutif et facilement maintenable.
