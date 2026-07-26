# Comparaison des sources

## Objectif

Après avoir étudié les différentes catégories de sources, je réalise une comparaison globale afin d'identifier leur rôle respectif dans **CheckIt.AI** et de vérifier leur complémentarité.

Cette analyse repose sur plusieurs critères :

* la disponibilité de contenus textuels ;
* la présence éventuelle d'images ;
* la disponibilité de labels ou de verdicts de véracité ;
* l'actualisation des données ;
* la possibilité d'automatiser la collecte ;
* les contraintes d'authentification ;
* la facilité d'intégration ;
* le rôle de chaque source dans le pipeline.

Les sources intégrées au projet remplissent principalement deux fonctions :

* **l'acquisition continue de nouvelles publications** ;
* **la constitution d'un corpus de référence annoté**.

Certaines sources sociales sont également prises en charge par l'architecture, mais restent actuellement désactivées dans la configuration.

---

# Comparaison globale

| Source                     | Catégorie             | Texte |              Images              |    Labels ou verdicts   | Collecte continue |    Authentification    | Utilisation principale         |
| :------------------------- | :-------------------- | :---: | :------------------------------: | :---------------------: | :---------------: | :--------------------: | ------------------------------ |
| Fakeddit                   | Dataset académique    |   ✅   |                 ✅                |            ✅            |         ❌         |         Aucune         | Référence multimodale          |
| FakeNewsNet                | Dataset académique    |   ✅   | ⚠️ Selon les données disponibles |            ✅            |         ❌         |         Aucune         | Référence annotée              |
| ISOT Fake News Dataset     | Dataset académique    |   ✅   |                 ❌                |            ✅            |         ❌         |         Aucune         | Classification textuelle       |
| CoAID                      | Dataset académique    |   ✅   |            ⚠️ Partiel            |            ✅            |         ❌         |         Aucune         | Désinformation liée à la santé |
| NewsData.io                | API d'actualité       |   ✅   |      ⚠️ URL selon l'article      |            ❌            |         ✅         |         Clé API        | Collecte multilingue           |
| GNews                      | API d'actualité       |   ✅   |      ⚠️ URL selon l'article      |            ❌            |         ✅         |         Clé API        | Actualité générale             |
| NewsAPI                    | API d'actualité       |   ✅   |      ⚠️ URL selon l'article      |            ❌            |         ✅         |         Clé API        | Recherche thématique           |
| Currents News API          | API d'actualité       |   ✅   |      ⚠️ URL selon l'article      |            ❌            |         ✅         |         Clé API        | Acquisition complémentaire     |
| Mediastack                 | API d'actualité       |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Clé API        | Diversification des médias     |
| The Guardian Open Platform | API éditoriale        |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Clé API        | Actualité anglophone           |
| GDELT                      | Base mondiale / API   |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Veille internationale          |
| Google Fact Check Tools    | API de fact-checking  |   ✅   |            ⚠️ Variable           |        ✅ Verdicts       |         ✅         |         Clé API        | Références vérifiées           |
| Le Monde                   | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Actualité francophone          |
| Le Monde - International   | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Actualité internationale       |
| Franceinfo                 | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Actualité francophone          |
| BBC News                   | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Actualité internationale       |
| BBC Technology             | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Actualité technologique        |
| The Guardian - World       | Flux RSS              |   ✅   |            ⚠️ Variable           |            ❌            |         ✅         |         Aucune         | Veille internationale          |
| Full Fact                  | Site de fact-checking |   ✅   |            ⚠️ Variable           | ✅ Verdicts à normaliser |         ✅         |         Aucune         | Référence de fact-checking     |
| Reuters Fact Check         | Site de fact-checking |   ✅   |            ⚠️ Variable           | ✅ Verdicts à normaliser |         ✅         |         Aucune         | Référence de fact-checking     |
| Reddit                     | Réseau social         |   ✅   |      ⚠️ Selon la publication     |            ❌            |         ✅         |          OAuth         | Source sociale prise en charge |
| Mastodon                   | Réseau social         |   ✅   |      ⚠️ Selon la publication     |            ❌            |         ✅         | Jeton selon l'instance | Source sociale prise en charge |

> La présence d'une image dépend des informations réellement fournies par chaque source. Dans **CheckIt.AI**, l'image n'est obligatoire que pour les sources configurées comme références multimodales, notamment Fakeddit. Pour les sources d'acquisition, un article peut être conservé sans image.

---

# Analyse comparative

## Datasets académiques

Les datasets académiques constituent les principales sources de données annotées du projet. Ils fournissent des contenus accompagnés de labels permettant de distinguer les informations considérées comme fiables de celles considérées comme trompeuses.

Les quatre datasets intégrés à **CheckIt.AI** répondent à des besoins complémentaires :

* **Fakeddit** apporte un corpus multimodal associant texte, image et label ;
* **FakeNewsNet** fournit des contenus annotés issus notamment de domaines politiques et médiatiques ;
* **ISOT Fake News Dataset** propose un corpus principalement textuel destiné à la classification binaire ;
* **CoAID** est spécialisé dans les informations fiables et trompeuses liées à la santé et à la pandémie de COVID-19.

Dans la configuration du projet, Fakeddit possède le rôle `multimodal_reference`. Une image et un label sont donc requis pour conserver une publication issue de cette source.

FakeNewsNet, ISOT et CoAID possèdent le rôle `labeled_reference`. Pour ces datasets, le texte et le label sont obligatoires, tandis que l'image reste facultative.

Leur principale limite est leur caractère statique. Ils fournissent un corpus de référence reproductible, mais ne permettent pas de suivre automatiquement les nouvelles publications.

---

## API d'actualité

Les API d'actualité constituent l'un des principaux mécanismes d'acquisition continue de contenus récents.

Le projet utilise les API suivantes :

* NewsData.io ;
* GNews ;
* NewsAPI ;
* Currents News API ;
* Mediastack ;
* The Guardian Open Platform ;
* GDELT.

Ces sources permettent de diversifier les médias, les langues, les pays et les thématiques couverts. Elles proposent également différents mécanismes de recherche et de pagination permettant d'automatiser la collecte.

Dans la configuration actuelle, les requêtes ciblent notamment :

* la politique ;
* l'économie ;
* la santé ;
* les sciences ;
* les technologies ;
* l'environnement ;
* l'actualité générale et internationale.

La multiplication des fournisseurs limite la dépendance à une API unique et réduit l'impact d'une indisponibilité, d'un changement de quota ou d'une modification des conditions d'accès.

Ces API ne fournissent toutefois aucun label de véracité. Les articles collectés sont donc considérés comme des données d'acquisition non annotées.

Les images sont généralement fournies sous la forme d'une URL et leur présence dépend du média d'origine. Elles ne sont pas obligatoires pour conserver un article.

---

## Fact-checking

Les sources de fact-checking occupent une place intermédiaire entre les datasets académiques et les sources d'actualité.

Elles permettent de collecter des affirmations ou des publications ayant déjà fait l'objet d'une vérification. Elles apportent donc des informations exploitables pour constituer progressivement un corpus annoté.

Les sources de fact-checking prises en charge sont :

* Google Fact Check Tools ;
* Full Fact ;
* Reuters Fact Check.

Google Fact Check Tools est interrogé au moyen d'une API officielle. Il fournit des affirmations accompagnées d'une ou plusieurs évaluations publiées par des organismes de vérification.

Full Fact et Reuters Fact Check sont traités comme des sources HTML. Leurs publications sont récupérées dans le respect des règles définies par le projet, notamment la consultation du fichier `robots.txt` et l'application d'un délai entre les requêtes.

Ces sources ne proposent pas toutes un label binaire directement exploitable. Elles utilisent différents verdicts, formulations ou échelles d'évaluation. Une étape de normalisation est donc nécessaire pour convertir les verdicts récupérés vers les labels communs du projet :

* `fake` ;
* `real`.

Cette normalisation doit rester prudente afin de ne pas transformer abusivement un verdict nuancé en classification binaire.

---

## Flux RSS

Les flux RSS constituent une solution légère pour détecter automatiquement les nouvelles publications de plusieurs médias.

Les flux actuellement intégrés sont :

* Le Monde ;
* Le Monde - International ;
* Franceinfo ;
* BBC News ;
* BBC Technology ;
* The Guardian - World.

Ils fournissent généralement :

* le titre ;
* l'URL ;
* la date de publication ;
* un résumé ;
* parfois un auteur, une catégorie ou une image.

Le texte intégral et la présence d'une image ne sont cependant pas garantis.

Dans **CheckIt.AI**, les flux RSS possèdent un rôle d'acquisition. Ils sont donc utilisés pour détecter et intégrer de nouvelles publications, mais pas comme sources de données annotées.

Leur principal avantage réside dans leur simplicité d'accès. Ils ne nécessitent généralement aucune authentification et ne sont pas soumis aux mêmes quotas que les API commerciales.

---

## Réseaux sociaux

Les réseaux sociaux permettent de collecter directement des contenus publiés par les utilisateurs.

L'architecture actuelle de **CheckIt.AI** prend en charge deux plateformes :

* Reddit ;
* Mastodon.

Reddit est configuré pour récupérer les publications récentes de plusieurs communautés :

* `news` ;
* `worldnews` ;
* `technology` ;
* `science`.

Mastodon est configuré pour interroger la chronologie publique de l'instance `mastodon.social`.

Les deux extracteurs sont intégrés au projet, mais restent actuellement désactivés dans la configuration. Ils ne participent donc pas à l'exécution normale du pipeline tant que leur paramètre `enabled` reste positionné à `false`.

Ces sources permettent d'obtenir des contenus plus spontanés et hétérogènes que ceux provenant des médias traditionnels. Elles peuvent contenir du texte, des images ou des liens externes, mais ne fournissent aucun label de véracité.

Elles doivent donc être considérées comme des sources d'acquisition sociale et non comme des corpus directement utilisables pour l'entraînement supervisé.

---

# Forces et limites

| Catégorie            | Principaux avantages                                       | Principales limites                                         |
| :------------------- | :--------------------------------------------------------- | :---------------------------------------------------------- |
| Datasets académiques | Données annotées, reproductibilité, référence scientifique | Données statiques et couverture temporelle limitée          |
| API d'actualité      | Articles récents, automatisation, filtres et pagination    | Absence de labels et dépendance aux quotas                  |
| Fact-checking        | Informations vérifiées et verdicts exploitables            | Couverture limitée et verdicts hétérogènes                  |
| Flux RSS             | Simplicité, gratuité et faible coût technique              | Métadonnées limitées, texte intégral et images non garantis |
| Réseaux sociaux      | Contenus spontanés, multimodaux et thématiques             | Bruit important, absence de labels et contraintes d'accès   |

---

# Rôle des sources dans CheckIt.AI

Les différentes sources remplissent des fonctions complémentaires définies par leur rôle dans la configuration.

## Sources d'acquisition

Les API d'actualité, les flux RSS et les réseaux sociaux sont configurés avec le rôle `acquisition`.

Pour ces sources :

* le titre est obligatoire ;
* l'URL est obligatoire ;
* le texte complet est facultatif ;
* l'image est facultative ;
* aucun label n'est exigé ;
* les contenus supprimés sont écartés ;
* les doublons sont supprimés ;
* les URLs sont validées.

Ces règles permettent de conserver une publication même lorsque la source ne fournit qu'un titre, un résumé et une URL, à condition que la quantité totale de texte soit suffisante.

Les sources actuellement actives dans cette catégorie sont :

* NewsData.io ;
* GNews ;
* NewsAPI ;
* Currents News API ;
* Mediastack ;
* The Guardian Open Platform ;
* GDELT ;
* les six flux RSS configurés.

Reddit et Mastodon appartiennent également à cette catégorie, mais sont actuellement désactivés.

---

## Sources de référence annotée

Les datasets académiques, Google Fact Check Tools, Full Fact et Reuters Fact Check sont utilisés comme sources de référence annotée.

La majorité de ces sources possèdent le rôle `labeled_reference`.

Pour ces sources :

* le titre est obligatoire ;
* le texte est obligatoire ;
* le label est obligatoire ;
* l'image est facultative ;
* les URLs externes ne sont pas obligatoires ;
* les labels sont normalisés vers `fake` ou `real`.

Fakeddit possède un rôle particulier, `multimodal_reference`.

Pour cette source :

* le titre est obligatoire ;
* une quantité minimale de texte est requise ;
* l'image est obligatoire ;
* le label est obligatoire.

Cette distinction garantit que les publications issues de Fakeddit conservent bien leur caractère multimodal.

---

# Complémentarité des sources

Aucune catégorie de source ne répond seule à l'ensemble des besoins de **CheckIt.AI**.

Les datasets académiques apportent des données annotées indispensables à l'entraînement et à l'évaluation de futurs modèles.

Les API d'actualité assurent une collecte automatisée et régulière d'articles récents provenant de nombreux médias.

Les flux RSS permettent de compléter cette acquisition à faible coût technique, sans clé API et sans dépendre de quotas commerciaux.

Les sources de fact-checking permettent de récupérer des affirmations déjà évaluées et d'enrichir progressivement le corpus de référence.

Enfin, les réseaux sociaux permettent d'étendre le projet à des contenus publiés directement par les utilisateurs, même s'ils restent actuellement désactivés dans la configuration.

Cette complémentarité justifie l'utilisation de plusieurs mécanismes d'extraction et la mise en place d'un schéma de données commun.

---

# Synthèse

Aucune source ne fournit à elle seule des contenus récents, des images, des métadonnées riches et des labels de véracité fiables.

J'ai donc retenu une architecture combinant plusieurs catégories de sources.

Les datasets académiques fournissent les données annotées nécessaires au développement et à l'évaluation des modèles. Fakeddit joue un rôle particulier en garantissant la présence d'un texte, d'une image et d'un label.

Les API d'actualité et les flux RSS assurent la collecte continue de publications récentes provenant de médias français et internationaux. Ces données ne sont pas annotées, mais permettent de constituer un corpus actualisé.

Les sources de fact-checking apportent des affirmations et des verdicts déjà publiés par des organismes spécialisés. Elles nécessitent cependant une normalisation prudente avant leur intégration dans le corpus de référence.

Reddit et Mastodon complètent enfin l'architecture avec des sources sociales. Leurs extracteurs sont pris en charge par le projet, mais restent actuellement désactivés.

Cette organisation justifie l'architecture modulaire de **CheckIt.AI**. Chaque type de source conserve ses spécificités techniques, tandis que les données collectées sont normalisées vers un schéma commun avant leur validation, leur transformation et leur stockage.
