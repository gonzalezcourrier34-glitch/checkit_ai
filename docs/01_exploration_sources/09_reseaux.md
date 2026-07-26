# Réseaux sociaux

## Présentation

Les réseaux sociaux constituent aujourd'hui un vecteur important de diffusion de l'information, mais également de contenus trompeurs ou non vérifiés. Contrairement aux médias traditionnels, ils permettent aux utilisateurs de publier rapidement des contenus associant du texte, des images, des vidéos ou des liens vers des ressources externes.

Dans le cadre de **CheckIt.AI**, les réseaux sociaux constituent une source complémentaire aux API d'actualité, aux flux RSS, aux datasets académiques et aux plateformes de fact-checking. Ils permettent de collecter des publications produites directement par les utilisateurs et d'étudier la circulation de contenus sur des plateformes favorisant les interactions et le partage.

L'accès aux données varie fortement selon les plateformes. Certaines proposent une API officielle documentée, tandis que d'autres imposent des restrictions techniques, des quotas ou des conditions d'utilisation limitant les possibilités de collecte automatisée.

La version actuelle de **CheckIt.AI** prend en charge deux sources sociales :

* Reddit ;
* Mastodon.

Ces deux sources sont intégrées à l'architecture du projet, mais elles sont actuellement désactivées dans la configuration. Elles peuvent être activées lorsque les identifiants nécessaires sont disponibles et lorsque leurs conditions d'accès sont compatibles avec les besoins du projet.

---

# Reddit

## Présentation

Reddit est une plateforme communautaire organisée autour de communautés thématiques appelées *subreddits*. Les publications peuvent contenir du texte, des images, des vidéos ou des liens vers des ressources externes.

Une API officielle permet d'accéder aux publications publiques ainsi qu'à leurs principales métadonnées. Dans **CheckIt.AI**, l'extracteur Reddit est configuré pour récupérer les publications récentes de plusieurs communautés consacrées à l'actualité, aux sciences et aux technologies.

Les communautés actuellement configurées sont :

* `news` ;
* `worldnews` ;
* `technology` ;
* `science`.

L'extracteur consulte les nouvelles publications à l'aide du classement `new` et applique plusieurs règles de filtrage afin d'écarter certains contenus peu adaptés au corpus.

## Caractéristiques

| Critère           | Valeur                 |
| ----------------- | ---------------------- |
| Catégorie         | Réseau social          |
| Texte             | ✅                      |
| Images            | ✅ Selon la publication |
| Labels            | ❌                      |
| Format            | JSON                   |
| Langue configurée | Anglais                |
| Extraction        | API officielle         |
| Authentification  | OAuth                  |
| Statut actuel     | Désactivé              |

## Avantages

* API officielle documentée.
* Publications textuelles et multimodales.
* Métadonnées riches.
* Nombreuses communautés spécialisées.
* Collecte automatisable.
* Sélection possible des thématiques par subreddit.

## Limites

* Aucun label de véracité.
* Qualité des publications très variable.
* Présence possible de contenus bruités, supprimés ou peu informatifs.
* Authentification obligatoire.
* Politique d'accès susceptible d'évoluer.
* Les images ne sont pas présentes dans toutes les publications.

## Analyse critique

Reddit constitue une source intéressante pour enrichir **CheckIt.AI** avec des contenus publiés directement par les utilisateurs. La diversité de ses communautés permet de cibler plusieurs thématiques et d'obtenir des publications plus spontanées que celles provenant des médias traditionnels.

Je ne considère toutefois pas les publications Reddit comme des informations vérifiées. Elles sont utilisées comme des données sociales brutes et doivent être distinguées des contenus labellisés provenant des datasets académiques ou des organismes de fact-checking.

L'extracteur applique notamment les règles suivantes :

* récupération des nouvelles publications ;
* exclusion des contenus réservés aux adultes ;
* exclusion des publications épinglées ;
* conservation possible des publications contenant un avertissement de divulgâchage ;
* vérification d'une longueur textuelle minimale ;
* limitation du nombre de publications récupérées.

### Utilisation dans CheckIt.AI

* ✅ Source prise en charge
* ✅ Collecte automatisable
* ✅ Contenus multimodaux
* ✅ Veille thématique
* ✅ Étude de contenus sociaux
* ❌ Source actuellement activée
* ❌ Entraînement supervisé direct

### Sources

* Documentation officielle : https://developers.reddit.com/
* Documentation de l'API Reddit : https://www.reddit.com/dev/api/

---

# Mastodon

## Présentation

Mastodon est un réseau social décentralisé composé de nombreuses instances indépendantes. Chaque instance héberge ses propres utilisateurs et applique ses propres règles de modération, tout en restant capable de communiquer avec les autres instances du réseau.

Mastodon met à disposition une API permettant d'accéder aux publications publiques, appelées *statuts*, ainsi qu'à leurs métadonnées et à leurs éventuelles pièces jointes multimédias.

Dans **CheckIt.AI**, l'extracteur est configuré pour interroger la chronologie publique de l'instance `mastodon.social`. Il peut récupérer des publications locales ou distantes selon les paramètres choisis.

## Caractéristiques

| Critère             | Valeur                         |
| ------------------- | ------------------------------ |
| Catégorie           | Réseau social décentralisé     |
| Texte               | ✅                              |
| Images              | ✅ Selon la publication         |
| Labels              | ❌                              |
| Format              | JSON                           |
| Langue configurée   | Français                       |
| Extraction          | API REST                       |
| Authentification    | Jeton d'accès selon l'instance |
| Instance configurée | mastodon.social                |
| Statut actuel       | Désactivé                      |

## Avantages

* API documentée.
* Architecture ouverte et décentralisée.
* Publications textuelles et multimodales.
* Accès possible aux chronologies publiques.
* Intégration adaptée à une architecture modulaire.

## Limites

* Données réparties entre de nombreuses instances.
* Couverture dépendante de l'instance interrogée.
* Métadonnées et règles variables selon les serveurs.
* Aucun label de véracité.
* Présence possible de republications, de réponses ou de contenus peu informatifs.
* Un jeton d'accès peut être nécessaire selon l'instance et les opérations réalisées.

## Analyse critique

Mastodon constitue une source complémentaire intéressante pour **CheckIt.AI** grâce à son architecture ouverte et à son API accessible. Il permet d'étudier des publications provenant d'un environnement social décentralisé, différent du fonctionnement de Reddit ou des médias traditionnels.

La collecte doit néanmoins être encadrée avec attention. Une seule instance ne représente pas l'ensemble du réseau Mastodon et les publications disponibles peuvent varier fortement selon le serveur interrogé.

Dans la configuration actuelle, l'extracteur :

* interroge la chronologie publique de `mastodon.social` ;
* accepte les publications provenant d'autres instances ;
* ne limite pas la collecte aux publications contenant une image ;
* élimine les republications ;
* élimine les réponses ;
* applique une longueur textuelle minimale ;
* limite le nombre de publications récupérées.

### Utilisation dans CheckIt.AI

* ✅ Source prise en charge
* ✅ Collecte automatisable
* ✅ Contenus multimodaux
* ✅ Veille sociale
* ✅ Étude d'un réseau décentralisé
* ❌ Source actuellement activée
* ❌ Entraînement supervisé direct

### Sources

* Documentation officielle : https://docs.joinmastodon.org/
* Documentation de l'API : https://docs.joinmastodon.org/api/

---

# Comparaison des réseaux sociaux

| Plateforme | Texte |          Images         | API officielle |    Authentification    | Intégrée à CheckIt.AI | Activée |
| :--------- | :---: | :---------------------: | :------------: | :--------------------: | :-------------------: | :-----: |
| Reddit     |   ✅   | ⚠️ Selon la publication |        ✅       |          OAuth         |           ✅           |    ❌    |
| Mastodon   |   ✅   | ⚠️ Selon la publication |        ✅       | Jeton selon l'instance |           ✅           |    ❌    |

---

# Intégration dans CheckIt.AI

Les réseaux sociaux sont traités comme des sources d'acquisition de contenus produits directement par les utilisateurs.

Les publications récupérées sont normalisées selon le schéma commun de **CheckIt.AI** afin de conserver une structure homogène avec les données provenant des API, des flux RSS, des scrapers et des datasets académiques.

Les traitements communs comprennent notamment :

* la récupération des publications publiques ;
* la normalisation du texte et des métadonnées ;
* la récupération des URLs associées ;
* l'identification des images lorsqu'elles sont disponibles ;
* la suppression des contenus supprimés ou inutilisables ;
* la détection des doublons ;
* l'application des règles de filtrage définies pour chaque source ;
* la limitation du nombre de publications collectées.

Les extracteurs Reddit et Mastodon reposent sur la même architecture générale, mais conservent des paramètres propres à chaque plateforme. Cette organisation me permet de mutualiser les traitements communs sans supprimer les spécificités de chaque réseau social.

Les deux sources sont actuellement désactivées dans la configuration. Leur intégration technique est néanmoins prévue et elles peuvent être activées sans modifier le fonctionnement général du pipeline.

---

# Synthèse

Les réseaux sociaux apportent une dimension complémentaire aux autres sources utilisées dans **CheckIt.AI**. Ils permettent de collecter des contenus publiés directement par les utilisateurs et de disposer de données plus spontanées, multimodales et variées que celles proposées par les médias traditionnels.

Dans la version actuelle du projet, je prends en charge deux plateformes :

* **Reddit**, qui permet de cibler des communautés thématiques consacrées à l'actualité, aux sciences et aux technologies ;
* **Mastodon**, qui permet d'étudier des publications issues d'un réseau social ouvert et décentralisé.

Ces publications ne possèdent toutefois aucun label de véracité et leur qualité peut être très variable. Elles ne peuvent donc pas être considérées directement comme des exemples fiables ou trompeurs pour l'entraînement supervisé d'un modèle.

Je les utilise principalement comme sources sociales complémentaires, destinées à enrichir le corpus multimodal et à préparer de futures analyses sur la diffusion des contenus. Leur association avec des données issues du fact-checking ou avec des datasets annotés sera nécessaire pour leur attribuer éventuellement un niveau de véracité.

Enfin, bien que Reddit et Mastodon soient déjà pris en charge par l'architecture de **CheckIt.AI**, ils restent actuellement désactivés dans la configuration du pipeline.
