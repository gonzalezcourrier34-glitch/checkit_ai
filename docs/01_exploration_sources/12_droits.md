# Droits d'usage et aspects juridiques

## Présentation

La collecte automatisée de données sur Internet ne peut pas reposer uniquement sur des considérations techniques. Chaque source est soumise à des conditions d'utilisation, à des règles d'accès ainsi qu'aux législations applicables, notamment en matière de propriété intellectuelle, de droits sur les bases de données et de protection des données personnelles.

Dans le cadre de **CheckIt.AI**, je porte une attention particulière à ces contraintes afin de construire un pipeline d'acquisition conforme aux bonnes pratiques. Le projet privilégie les modes d'accès officiellement proposés par les fournisseurs et limite le recours au scraping aux situations dans lesquelles aucune API ou aucun flux adapté n'est disponible.

L'accessibilité publique d'une donnée ne signifie pas qu'elle peut être librement collectée, reproduite, stockée ou redistribuée. Sa réutilisation doit rester compatible avec la finalité du projet, les droits attachés au contenu et les conditions définies par sa source. Les recommandations de la CNIL rappellent également que les données personnelles accessibles publiquement restent protégées par le RGPD.

---

# Principes retenus

Les principes suivants guident la conception du pipeline d'acquisition :

* privilégier les API officielles lorsqu'elles existent ;
* utiliser les flux RSS publiés officiellement par les médias ;
* vérifier les licences des datasets académiques ;
* respecter les conditions d'utilisation de chaque fournisseur ;
* respecter les quotas et les limites imposés par les API ;
* limiter le scraping aux pages strictement nécessaires ;
* consulter le fichier `robots.txt` avant tout scraping ;
* identifier clairement la provenance des données collectées ;
* conserver uniquement les informations utiles au projet ;
* limiter la durée de conservation des données personnelles ;
* ne pas republier le contenu intégral des articles collectés.

Cette approche améliore la pérennité de la collecte et limite les risques liés à une évolution des plateformes, de leurs conditions contractuelles ou de leurs mécanismes d'accès.

Elle ne remplace toutefois pas une analyse juridique adaptée au contexte réel d'exploitation. **CheckIt.AI** est développé dans un cadre pédagogique et expérimental et n'a pas vocation, dans sa version actuelle, à redistribuer commercialement les contenus collectés.

---

# Analyse des principales sources

| Catégorie              | Mode d'accès privilégié | Principales contraintes                                                                        |
| :--------------------- | :---------------------- | :--------------------------------------------------------------------------------------------- |
| Datasets académiques   | Téléchargement officiel | Licence, attribution, droit de redistribution et conditions propres au dataset                 |
| API d'actualité        | API officielle          | Authentification, quotas, stockage, réutilisation et conditions contractuelles                 |
| API de fact-checking   | API officielle          | Authentification, quotas et conditions propres au service                                      |
| Flux RSS               | Flux officiel           | Droits d'auteur, conditions de l'éditeur et réutilisation limitée                              |
| Sites de fact-checking | Scraping ciblé          | Conditions d'utilisation, droits d'auteur, charge serveur et `robots.txt`                      |
| Réseaux sociaux        | API officielle          | Authentification, données personnelles, suppression des contenus et politique de la plateforme |

---

# Cas des datasets académiques

Les datasets académiques sont récupérés depuis les emplacements officiels ou les dépôts indiqués par leurs auteurs.

Avant leur intégration dans **CheckIt.AI**, plusieurs éléments doivent être vérifiés :

* la licence applicable ;
* les usages autorisés ;
* les obligations d'attribution ;
* les éventuelles restrictions commerciales ;
* l'autorisation de modifier ou de redistribuer les données ;
* les conditions applicables aux images et aux ressources externes.

La licence du dataset ne couvre pas nécessairement tous les contenus auxquels il fait référence. Par exemple, un jeu de données peut contenir une URL vers une image ou un article dont les droits restent détenus par l'éditeur d'origine.

Les datasets sont donc utilisés comme corpus de recherche et de référence. Leur intégration à **CheckIt.AI** ne signifie pas que leurs contenus peuvent être librement republiés.

---

# Cas des API

Les API constituent le mode d'accès privilégié dans **CheckIt.AI**.

Elles présentent plusieurs avantages :

* une interface documentée ;
* des formats de données standardisés ;
* des mécanismes d'authentification ;
* un contrôle du volume de requêtes ;
* des règles d'utilisation identifiables.

Le projet utilise notamment les API suivantes :

* NewsData.io ;
* NewsAPI ;
* GNews ;
* Currents News API ;
* Mediastack ;
* The Guardian Open Platform ;
* GDELT ;
* Google Fact Check Tools.

Chaque appel doit respecter les mécanismes d'authentification, les quotas et les conditions imposées par le fournisseur. L'utilisation d'une clé API ne donne pas automatiquement le droit de reproduire ou de redistribuer les articles récupérés.

Google précise notamment que l'utilisation de Fact Check Tools API reste soumise à ses conditions d'utilisation applicables aux API.

Les clés et jetons d'accès sont stockés dans des variables d'environnement et ne doivent pas apparaître dans le code source, les journaux d'exécution ou les fichiers publiés sur un dépôt Git.

---

# Cas des flux RSS

Les flux RSS représentent une solution simple, officiellement proposée par de nombreux médias pour diffuser leurs dernières publications.

Ils permettent de récupérer certaines informations sans analyser directement les pages HTML :

* le titre ;
* l'URL ;
* la date de publication ;
* un résumé ;
* parfois un auteur, une catégorie ou une image.

Les flux intégrés dans **CheckIt.AI** proviennent directement des médias concernés :

* Le Monde ;
* Franceinfo ;
* BBC ;
* The Guardian.

Même lorsqu'un flux RSS est publiquement accessible, les contenus restent soumis aux droits de leur éditeur. La présence d'un flux ne signifie donc pas que les articles, résumés ou images peuvent être librement reproduits ou redistribués.

Dans **CheckIt.AI**, les flux sont principalement utilisés pour détecter de nouvelles publications, conserver leurs métadonnées et enregistrer un lien vers la ressource d'origine.

---

# Cas du scraping

Le scraping constitue une solution de dernier recours lorsqu'aucune API officielle ni aucun flux RSS adapté ne permet d'accéder aux informations recherchées.

Dans **CheckIt.AI**, cette approche est principalement utilisée pour certaines plateformes de fact-checking :

* Full Fact ;
* Reuters Fact Check.

Les extracteurs concernés appliquent plusieurs règles :

* consultation préalable du fichier `robots.txt` ;
* refus de la collecte lorsque la politique définie ne peut pas être vérifiée ;
* respect des délais d'exploration indiqués lorsqu'ils sont disponibles ;
* limitation de la fréquence des requêtes ;
* utilisation d'un en-tête `User-Agent` explicite ;
* téléchargement uniquement des pages nécessaires ;
* limitation du nombre de pages analysées ;
* gestion des erreurs, des délais d'attente et des redirections.

Le fichier `robots.txt` fournit des instructions destinées aux robots d'exploration, mais il ne constitue ni une licence ni une autorisation juridique générale. Une page autorisée par `robots.txt` peut toujours rester protégée par le droit d'auteur, les droits sur les bases de données ou les conditions d'utilisation du site.

La fouille et l'extraction de contenus peuvent également mettre en jeu le droit d'auteur ou le droit propre aux bases de données. Lorsqu'aucune exception ou autorisation ne s'applique, l'accord du titulaire des droits peut être nécessaire.

---

# Propriété intellectuelle

Les articles, photographies, illustrations et autres contenus éditoriaux peuvent être protégés par le droit d'auteur.

Pour limiter les risques, **CheckIt.AI** applique les principes suivants :

* conserver la source et l'URL d'origine ;
* éviter la republication publique des articles complets ;
* limiter les extraits aux besoins du traitement ;
* ne pas présenter les contenus collectés comme appartenant au projet ;
* conserver les informations d'attribution lorsqu'elles sont disponibles ;
* vérifier séparément les droits applicables aux images.

Le téléchargement technique d'une image ne transfère aucun droit de propriété sur celle-ci. Les images collectées sont utilisées uniquement pour les traitements internes nécessaires à l'étude multimodale et ne doivent pas être redistribuées sans autorisation adaptée.

---

# Protection des données personnelles

Les sources intégrées à **CheckIt.AI** concernent principalement des contenus publiquement accessibles. Certaines peuvent néanmoins contenir des données permettant d'identifier une personne, par exemple :

* un nom d'auteur ;
* un pseudonyme ;
* une photographie ;
* un identifiant de compte ;
* le contenu d'une publication sociale ;
* une URL de profil.

Le fait que ces informations soient publiques ne les exclut pas du champ de la protection des données personnelles. Leur traitement doit conserver une finalité déterminée, rester proportionné et être limité aux informations nécessaires au projet.

Le projet applique donc plusieurs précautions :

* ne pas rechercher volontairement de données sensibles ;
* limiter la collecte aux champs nécessaires ;
* éviter la constitution de profils individuels ;
* ne pas collecter de messages privés ;
* protéger l'accès aux données stockées ;
* prévoir une durée de conservation adaptée ;
* pouvoir supprimer les données devenues inutiles ;
* ne pas republier les informations personnelles collectées.

Les données personnelles ne doivent pas être conservées indéfiniment. Une durée doit être définie en fonction de la finalité poursuivie.

---

# Cas des réseaux sociaux

Reddit et Mastodon sont pris en charge par l'architecture de **CheckIt.AI**, mais restent actuellement désactivés dans la configuration.

Lorsqu'ils seront activés, seules les publications accessibles au moyen des API autorisées seront collectées. L'utilisation de Reddit doit notamment respecter les conditions destinées aux développeurs et les conditions spécifiques de son API de données.

Une attention particulière devra être portée :

* aux pseudonymes et identifiants des utilisateurs ;
* aux contenus supprimés après leur collecte ;
* aux durées de conservation ;
* aux conditions de stockage des publications ;
* aux restrictions relatives à l'entraînement de modèles ;
* aux obligations de suppression éventuellement imposées par la plateforme.

Les contenus sociaux ne seront pas utilisés pour surveiller individuellement les utilisateurs ni pour établir des profils personnels.

---

# Traçabilité des données

Chaque article normalisé dans **CheckIt.AI** conserve plusieurs informations permettant d'identifier son origine, notamment :

* le nom de la source ;
* le type de source ;
* l'URL d'origine lorsqu'elle est disponible ;
* la date de publication ;
* la date d'extraction ;
* l'auteur lorsqu'il est fourni par la source ;
* le rôle du contenu dans le projet.

Cette traçabilité permet :

* de retrouver la provenance d'une donnée ;
* de distinguer les contenus d'acquisition des références annotées ;
* de faciliter les opérations de suppression ;
* d'appliquer les contraintes propres à chaque fournisseur ;
* de documenter la constitution du corpus.

---

# Synthèse

La stratégie retenue dans **CheckIt.AI** repose sur une hiérarchie claire des modes d'acquisition :

1. utiliser une API officielle lorsqu'elle est disponible ;
2. utiliser un flux RSS officiel lorsque cela est possible ;
3. recourir au scraping ciblé uniquement en l'absence d'une alternative adaptée.

Cette hiérarchie ne suffit toutefois pas à garantir la conformité juridique. Pour chaque source, il reste nécessaire de vérifier :

* sa licence ;
* ses conditions d'utilisation ;
* les droits attachés aux contenus ;
* les règles relatives aux données personnelles ;
* les possibilités de stockage et de redistribution.

Le projet applique également des principes de minimisation, de traçabilité, de limitation de la conservation et de protection des accès.

Cette approche permet de construire un pipeline plus robuste, plus pérenne et plus facilement maintenable, tout en réduisant les risques associés à la collecte automatisée. Les aspects juridiques sont ainsi intégrés à l'architecture de **CheckIt.AI** au même titre que la validation, la normalisation, la déduplication et le stockage des données.
