# Méthodes d'extraction

## Présentation

Les sources intégrées à **CheckIt.AI** utilisent des modes de diffusion différents. Leur collecte nécessite donc plusieurs méthodes d'extraction adaptées à leur structure, à leur fréquence de mise à jour et à leurs conditions d'accès.

Le choix d'une méthode repose principalement sur plusieurs critères :

* l'existence d'une API officielle ;
* la disponibilité d'un flux RSS ;
* le format des fichiers proposés ;
* la structure du site web ;
* les conditions d'utilisation de la source ;
* la stabilité de la méthode d'accès ;
* la facilité de maintenance de l'extracteur.

Afin de garantir la robustesse et la pérennité du pipeline, je privilégie systématiquement les modes d'accès officiels avant de recourir à l'analyse directe de pages HTML.

---

# Comparaison des méthodes

| Méthode              | Principe                                    | Sources concernées dans CheckIt.AI                                                                                     |
| :------------------- | :------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------- |
| Lecture de fichiers  | Import et parcours d'un dataset local       | Fakeddit, FakeNewsNet, ISOT Fake News Dataset, CoAID                                                                   |
| API REST             | Requêtes HTTP vers une interface officielle | NewsData.io, GNews, NewsAPI, Currents News API, Mediastack, The Guardian Open Platform, GDELT, Google Fact Check Tools |
| Flux RSS             | Lecture et analyse de flux XML              | Le Monde, Le Monde - International, Franceinfo, BBC News, BBC Technology, The Guardian - World                         |
| Scraping HTML        | Extraction ciblée depuis des pages web      | Full Fact, Reuters Fact Check                                                                                          |
| API de réseau social | Collecte via les interfaces des plateformes | Reddit, Mastodon                                                                                                       |

---

# Méthodes retenues

## Lecture des datasets

Les datasets académiques sont stockés sous forme de fichiers locaux avant d'être traités par les extracteurs de **CheckIt.AI**.

Les formats utilisés varient selon les sources :

| Dataset                | Format configuré |
| :--------------------- | :--------------- |
| Fakeddit               | TSV              |
| FakeNewsNet            | JSON             |
| ISOT Fake News Dataset | CSV              |
| CoAID                  | CSV              |

Cette méthode présente plusieurs avantages :

* données structurées ;
* traitement reproductible ;
* absence de dépendance au réseau pendant l'extraction ;
* lecture rapide des fichiers locaux ;
* possibilité de traiter les fichiers volumineux par blocs.

Les extracteurs utilisent notamment une lecture par portions, ou *chunks*, afin d'éviter de charger entièrement les datasets les plus volumineux en mémoire.

Les datasets actuellement intégrés sont :

* Fakeddit ;
* FakeNewsNet ;
* ISOT Fake News Dataset ;
* CoAID.

Les données extraites sont ensuite converties vers le schéma commun de **CheckIt.AI**, puis filtrées selon leur rôle de référence annotée ou multimodale.

---

## API REST

Les API REST constituent le principal mécanisme d'acquisition de publications récentes.

Les extracteurs envoient des requêtes HTTP vers les différents fournisseurs afin de récupérer :

* les articles ou les affirmations ;
* leurs principales métadonnées ;
* les dates de publication ;
* les URLs d'origine ;
* les URLs des images lorsqu'elles sont disponibles ;
* les verdicts dans le cas de Google Fact Check Tools.

Les API actuellement intégrées sont :

* NewsData.io ;
* GNews ;
* NewsAPI ;
* Currents News API ;
* Mediastack ;
* The Guardian Open Platform ;
* GDELT ;
* Google Fact Check Tools.

Les appels sont réalisés en respectant :

* les mécanismes d'authentification ;
* les paramètres propres à chaque API ;
* les quotas d'utilisation ;
* la pagination ;
* les délais d'attente ;
* les tentatives supplémentaires sur certaines erreurs temporaires ;
* le nombre maximal d'articles configuré.

Les réponses JSON sont ensuite interprétées par des adaptateurs propres à chaque fournisseur. Ces adaptateurs convertissent les champs spécifiques de l'API vers le modèle d'article commun du projet.

---

## Pagination des API

La majorité des API utilisées limitent le nombre de résultats retournés par requête. Une gestion de la pagination est donc nécessaire pour récupérer plusieurs pages sans dépasser les limites définies.

La pagination peut reposer sur différents mécanismes :

* un numéro de page ;
* un décalage, ou *offset* ;
* un jeton transmis par la réponse précédente ;
* un nombre maximal de résultats par page.

Par exemple :

* NewsData.io utilise un paramètre de page ;
* GNews utilise un numéro de page et une taille maximale ;
* NewsAPI utilise `page` et `pageSize` ;
* Mediastack utilise `offset` et `limit` ;
* Google Fact Check Tools utilise un `pageToken`.

Chaque extracteur conserve les particularités de son API tout en appliquant les mêmes limites générales de collecte.

Cette approche permet d'éviter les boucles infinies, les volumes excessifs et le dépassement du nombre maximal d'articles attendu.

---

## GDELT

GDELT utilise également une API REST, mais son fonctionnement diffère des agrégateurs d'actualité classiques.

La plateforme indexe en continu un très grand nombre de publications provenant de médias internationaux et permet de lancer des recherches sur des périodes, des langues et des thématiques précises.

Dans **CheckIt.AI**, GDELT est configuré pour rechercher des contenus en français et en anglais sur plusieurs thèmes :

* politique ;
* santé ;
* sciences ;
* technologies ;
* environnement ;
* économie ;
* éducation ;
* criminalité.

L'extracteur interroge l'API documentaire de GDELT sur une période récente, puis normalise les résultats obtenus.

Cette source permet d'élargir la couverture géographique et thématique du projet, mais nécessite un filtrage important en raison du volume et de l'hétérogénéité des résultats.

---

## Flux RSS

Les flux RSS constituent une méthode simple et légère pour détecter les nouvelles publications de plusieurs médias.

Les flux sont analysés automatiquement afin de récupérer, lorsqu'elles sont disponibles :

* le titre ;
* l'URL ;
* la date de publication ;
* le résumé ;
* l'auteur ;
* la catégorie ;
* une éventuelle référence vers une image.

Les flux actuellement intégrés sont :

* Le Monde ;
* Le Monde - International ;
* Franceinfo ;
* BBC News ;
* BBC Technology ;
* The Guardian - World.

Un extracteur RSS commun prend en charge l'ensemble de ces sources. Il interprète les entrées XML, normalise les valeurs et applique les règles de validation définies pour les sources d'acquisition.

Les flux RSS complètent les API d'actualité tout en limitant la dépendance aux clés d'accès et aux quotas commerciaux.

Ils peuvent néanmoins présenter certaines difficultés :

* flux XML mal formé ;
* champs absents ;
* formats de date différents ;
* contenu HTML dans les résumés ;
* absence d'image ;
* texte intégral indisponible.

Ces variations sont traitées par les fonctions communes de nettoyage et de normalisation du projet.

---

## Scraping HTML

Lorsque certaines données ne sont disponibles ni via une API adaptée ni via un flux RSS exploitable, **CheckIt.AI** utilise un extracteur HTML.

Cette méthode est actuellement employée pour :

* Full Fact ;
* Reuters Fact Check.

Chaque source possède une configuration comprenant notamment :

* une ou plusieurs pages de départ ;
* un sélecteur pour les articles ;
* un sélecteur pour le titre ;
* un sélecteur pour le lien ;
* un sélecteur pour le texte ;
* un sélecteur pour l'image ;
* un sélecteur pour la date ;
* les paramètres de pagination.

L'extracteur générique récupère les pages, analyse leur structure HTML puis transmet chaque publication détectée à l'adaptateur de la source.

Les extracteurs appliquent plusieurs précautions :

* consultation du fichier `robots.txt` ;
* limitation de la fréquence des requêtes ;
* utilisation d'un `User-Agent` explicite ;
* gestion des erreurs réseau ;
* contrôle des redirections ;
* limitation du nombre de pages ;
* détection de certaines pages de blocage ;
* validation des données extraites.

Le scraping reste la méthode la plus sensible aux changements. Une modification de la structure HTML peut rendre certains sélecteurs obsolètes et nécessiter une mise à jour de la configuration ou de l'adaptateur.

---

## Réseaux sociaux

Les réseaux sociaux sont collectés à l'aide des interfaces proposées par les plateformes.

L'architecture actuelle prend en charge :

* Reddit ;
* Mastodon.

L'extracteur Reddit est configuré pour récupérer les nouvelles publications de plusieurs communautés :

* `news` ;
* `worldnews` ;
* `technology` ;
* `science`.

L'extracteur Mastodon interroge la chronologie publique de l'instance `mastodon.social`.

Ces extracteurs peuvent récupérer :

* le texte de la publication ;
* son URL ;
* sa date ;
* certaines informations sur son auteur ;
* les images ou médias associés ;
* différentes métadonnées sociales.

Reddit et Mastodon sont pris en charge par le projet, mais restent actuellement désactivés dans la configuration. Ils ne participent donc pas à l'exécution normale du pipeline.

---

# Normalisation commune

Quelle que soit la méthode d'extraction utilisée, les données collectées sont converties vers un schéma commun.

Cette normalisation permet notamment de conserver les champs suivants :

* identifiant ;
* source ;
* titre ;
* texte ;
* URL de l'article ;
* URL de l'image ;
* chemin local de l'image ;
* date de publication ;
* auteur ;
* langue ;
* catégorie ;
* label ;
* rôle du dataset ;
* date d'extraction.

Les valeurs sont ensuite nettoyées et validées selon les règles associées au rôle de la source.

Cette étape permet de traiter de manière homogène des données provenant de fichiers CSV, de réponses JSON, de flux XML, de pages HTML ou de publications sociales.

---

# Comparaison des méthodes

| Méthode              | Fiabilité | Facilité de maintenance | Volume potentiel | Dépendance externe |
| :------------------- | :-------: | :---------------------: | :--------------: | :----------------: |
| Lecture de fichiers  |   ⭐⭐⭐⭐⭐   |          ⭐⭐⭐⭐⭐          |       ⭐⭐⭐⭐⭐      |       Faible       |
| API REST             |   ⭐⭐⭐⭐⭐   |          ⭐⭐⭐⭐☆          |       ⭐⭐⭐⭐☆      |   Moyenne à forte  |
| Flux RSS             |   ⭐⭐⭐⭐☆   |          ⭐⭐⭐⭐☆          |       ⭐⭐⭐☆☆      |  Faible à moyenne  |
| Scraping HTML        |   ⭐⭐⭐☆☆   |          ⭐⭐☆☆☆          |       ⭐⭐⭐☆☆      |        Forte       |
| API de réseau social |   ⭐⭐⭐⭐☆   |          ⭐⭐⭐☆☆          |       ⭐⭐⭐⭐☆      |        Forte       |

Cette évaluation reste indicative. La fiabilité d'une méthode dépend également de la disponibilité du fournisseur, de la qualité des données et de l'évolution de ses conditions d'accès.

---

# Stratégie retenue

Afin d'obtenir un pipeline robuste et facilement maintenable, **CheckIt.AI** applique la hiérarchie suivante :

1. utiliser une API officielle lorsqu'elle est disponible ;
2. utiliser un flux RSS officiel lorsqu'il répond au besoin ;
3. lire les datasets depuis des fichiers locaux pour constituer les corpus de référence ;
4. utiliser les API officielles des réseaux sociaux lorsqu'elles sont activées ;
5. recourir au scraping ciblé uniquement lorsqu'aucune solution plus stable n'est disponible.

Cette hiérarchie ne dépend pas uniquement de la facilité technique. Elle prend également en compte :

* la stabilité de l'accès ;
* les conditions d'utilisation ;
* les quotas ;
* la qualité des métadonnées ;
* la facilité de maintenance ;
* la reproductibilité des traitements.

---

# Gestion des erreurs

Chaque méthode d'extraction peut produire des erreurs différentes.

Le pipeline doit notamment gérer :

* les fichiers absents ou invalides ;
* les erreurs de décodage ;
* les réponses HTTP en erreur ;
* les délais d'attente ;
* les quotas dépassés ;
* les clés API absentes ;
* les réponses JSON incomplètes ;
* les flux XML mal formés ;
* les changements de structure HTML ;
* les publications supprimées ;
* les URLs invalides ;
* les données obligatoires manquantes.

Les erreurs d'un extracteur sont isolées afin qu'une source défaillante ne provoque pas automatiquement l'arrêt de l'ensemble de la collecte.

Chaque exécution produit également un statut et des statistiques permettant de distinguer :

* une extraction réussie ;
* une réussite partielle ;
* une source vide ;
* une source désactivée ;
* un échec.

---

# Conclusion

Les méthodes d'extraction utilisées dans **CheckIt.AI** répondent à des besoins complémentaires.

La lecture de fichiers locaux permet d'exploiter les datasets académiques comme corpus de référence. Les API REST assurent la collecte automatisée de publications récentes et d'affirmations vérifiées. Les flux RSS complètent cette veille avec un coût technique réduit, tandis que les extracteurs HTML permettent d'accéder à certaines plateformes de fact-checking ne proposant pas d'interface directement exploitable.

Reddit et Mastodon complètent l'architecture avec des méthodes dédiées aux réseaux sociaux, même si ces deux sources restent actuellement désactivées.

En combinant ces approches au sein d'une architecture commune, **CheckIt.AI** peut traiter des sources hétérogènes tout en conservant un fonctionnement cohérent. Les adaptateurs propres à chaque source prennent en charge leurs particularités, tandis que les fonctions communes assurent la normalisation, la validation, la déduplication et la gestion des erreurs.

Cette organisation rend le pipeline modulaire, évolutif et plus facile à maintenir lorsque les sources ou leurs interfaces évoluent.
