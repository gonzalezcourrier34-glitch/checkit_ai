# APIs d'actualité

## Présentation

Les API d'actualité constituent l'une des principales sources de collecte de **CheckIt.AI**. Contrairement aux datasets académiques, elles permettent d'accéder à des articles publiés récemment par de nombreux médias et peuvent être interrogées régulièrement afin d'alimenter automatiquement le pipeline de collecte.

La plupart de ces API renvoient les données au format JSON et proposent des filtres permettant de cibler les résultats selon différents critères, tels que les mots-clés, la langue, le pays, la catégorie ou la période de publication.

En revanche, ces API ne fournissent généralement pas de labels de véracité. Leur objectif est de diffuser des articles d'actualité et non d'évaluer leur fiabilité. Les données collectées devront donc être complétées par des plateformes de fact-checking ou des jeux de données annotés lorsqu'elles seront utilisées pour entraîner ou évaluer des modèles de détection de désinformation.

Les principales API retenues pour le développement de **CheckIt.AI** sont présentées ci-dessous.

---

# NewsData.io

## Présentation

NewsData.io est une API REST spécialisée dans l'agrégation d'articles provenant de nombreux médias internationaux. Elle permet de rechercher des publications selon différents critères, notamment les mots-clés, la langue, le pays ou la catégorie.

Chaque résultat fournit les principales métadonnées de l'article ainsi qu'un lien vers l'image lorsqu'elle est disponible.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ✅ (URL) |
| Labels | ❌ |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- API simple à intégrer.
- Documentation claire.
- Grand nombre de sources.
- Recherche multicritère.
- Mise à jour régulière.

## Limites

- Absence de labels de véracité.
- Quotas sur l'offre gratuite.
- Les images sont fournies sous forme d'URL.

## Analyse critique

NewsData.io constitue l'une des principales sources utilisées dans **CheckIt.AI**. Sa simplicité d'intégration, la richesse de ses filtres et sa couverture internationale en font une API particulièrement adaptée à la collecte automatisée d'articles récents.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Pipeline de production
- ✅ Veille d'actualité
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://newsdata.io/documentation

---

# NewsAPI

## Présentation

NewsAPI est l'une des API d'actualité les plus connues. Elle agrège des articles provenant de nombreux médias internationaux et propose une interface REST permettant de rechercher les publications selon différents critères.

Les résultats retournés comprennent les principales métadonnées de chaque article ainsi qu'un lien vers l'image lorsqu'elle est disponible.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ✅ (URL) |
| Labels | ❌ |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- Documentation complète.
- API largement utilisée.
- Intégration simple.
- Nombreuses sources d'information.

## Limites

- Offre gratuite limitée.
- Certaines fonctionnalités nécessitent un abonnement.
- Les images sont disponibles uniquement via URL.

## Analyse critique

NewsAPI constitue une source complémentaire intéressante pour diversifier les articles collectés par **CheckIt.AI**. Son fonctionnement est proche de celui de NewsData.io, ce qui facilite son intégration au sein du pipeline.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Veille d'actualité
- ✅ Pipeline de production
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://newsapi.org/docs

---

# GNews

## Présentation

GNews est une API d'actualité permettant d'accéder à des articles provenant de nombreux médias internationaux. Elle propose des filtres par mots-clés, catégories, langues ou pays et fournit également les liens vers les images associées aux articles.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ✅ (URL) |
| Labels | ❌ |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- Interface simple.
- Résultats récents.
- Recherche multicritère.
- Documentation accessible.

## Limites

- Quotas sur la version gratuite.
- Images disponibles uniquement via URL.
- Absence de labels de véracité.

## Analyse critique

GNews complète efficacement les autres API utilisées dans **CheckIt.AI** en apportant des sources supplémentaires et une bonne couverture de l'actualité récente.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Veille d'actualité
- ✅ Pipeline de production
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://gnews.io/docs

---

# Currents API

## Présentation

Currents API permet d'accéder à des articles d'actualité récents provenant de différentes sources internationales. Elle propose plusieurs filtres de recherche ainsi qu'un accès aux principales métadonnées des articles.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ✅ (URL) |
| Labels | ❌ |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- API simple à utiliser.
- Données récentes.
- Plusieurs filtres disponibles.
- Réponses au format JSON.

## Limites

- Offre gratuite limitée.
- Couverture variable selon les langues.
- Aucun label de véracité.

## Analyse critique

Currents API constitue une source complémentaire permettant d'améliorer la diversité des contenus collectés par **CheckIt.AI**, notamment grâce à ses possibilités de filtrage.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Pipeline de production
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://currentsapi.services/

---

# MediaStack

## Présentation

MediaStack est une API commerciale donnant accès à des articles provenant de nombreux médias internationaux. Son fonctionnement est proche de celui de NewsAPI ou de NewsData.io.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ⚠️ Variables selon les sources |
| Labels | ❌ |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- API simple à utiliser.
- Documentation claire.
- Recherche multicritère.
- Couverture internationale.

## Limites

- Service principalement commercial.
- Quotas sur l'offre gratuite.
- Qualité des métadonnées variable selon les médias.

## Analyse critique

MediaStack constitue une source supplémentaire permettant de diversifier les contenus collectés. Son fonctionnement étant proche de celui des autres API étudiées, son intégration dans **CheckIt.AI** reste relativement simple.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Veille d'actualité
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://mediastack.com/documentation

---

# GDELT

## Présentation

GDELT (*Global Database of Events, Language and Tone*) est une plateforme mondiale consacrée à l'analyse de l'actualité. Elle agrège en continu des contenus provenant de milliers de médias internationaux et propose différents services d'accès, notamment via API et flux RSS.

Contrairement aux API classiques, GDELT met davantage l'accent sur l'analyse des événements et des tendances médiatiques à grande échelle.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Base mondiale d'actualité |
| Texte | ✅ |
| Images | ⚠️ Variables selon les articles |
| Labels | ❌ |
| Format | JSON, CSV |
| Langues | Multilingue |
| Extraction | API / RSS |
| Authentification | Variable selon le service |

## Avantages

- Couverture internationale.
- Très grand volume de données.
- Mise à jour continue.
- Disponible via API et RSS.

## Limites

- Plus complexe à exploiter.
- Nécessite un filtrage important.
- Les images ne sont pas systématiquement disponibles.
- Aucun label de véracité.

## Analyse critique

Grâce à sa couverture mondiale et au volume important de données disponibles, GDELT constitue une source particulièrement intéressante pour enrichir **CheckIt.AI** et réaliser des analyses à grande échelle. En revanche, sa richesse nécessite un travail de filtrage plus important que les autres API étudiées.

### Utilisation dans CheckIt.AI

- ✅ Veille internationale
- ✅ Collecte automatisée
- ✅ Pipeline de production
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://www.gdeltproject.org/

---

# Google Fact Check API

## Présentation

Google Fact Check API permet d'accéder aux vérifications publiées par de nombreux organismes de fact-checking à travers le monde. Elle ne fournit pas directement des articles d'actualité mais des affirmations (*claims*) accompagnées des verdicts publiés par les organismes ayant réalisé leur vérification.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API de fact-checking |
| Texte | ✅ |
| Images | ⚠️ Variables |
| Labels | ✅ Verdicts |
| Format | JSON |
| Langues | Multilingue |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- Données issues d'organismes de fact-checking reconnus.
- Présence de verdicts de véracité.
- Couverture internationale.
- Documentation officielle.

## Limites

- Ne fournit pas un flux d'actualité généraliste.
- Nombre de résultats dépendant des organismes partenaires.
- Images peu fréquentes.

## Analyse critique

Contrairement aux autres API étudiées, Google Fact Check API ne constitue pas une source destinée à alimenter le pipeline en articles d'actualité. Je l'utilise principalement afin de récupérer des verdicts de véracité et d'enrichir certaines informations collectées par d'autres sources.

### Utilisation dans CheckIt.AI

- ✅ Vérification des informations
- ✅ Enrichissement des données
- ✅ Fact-checking
- ❌ Collecte généraliste

### Sources

- Documentation officielle : https://developers.google.com/fact-check/tools/api

---

# The Guardian API

## Présentation

The Guardian met à disposition une API officielle permettant d'accéder aux articles publiés par le média. Elle offre plusieurs paramètres permettant de récupérer les métadonnées, le contenu des articles ainsi que certaines informations complémentaires.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | API d'actualité |
| Texte | ✅ |
| Images | ✅ |
| Labels | ❌ |
| Format | JSON |
| Langue | Anglais |
| Extraction | API REST |
| Authentification | Clé API |

## Avantages

- API officielle.
- Documentation complète.
- Métadonnées riches.
- Contenus de qualité.

## Limites

- Limité aux publications du Guardian.
- Principalement en anglais.
- Aucun label de véracité.

## Analyse critique

Bien que sa couverture soit limitée à un seul média, The Guardian API fournit des articles de qualité accompagnés de métadonnées détaillées. Elle permet ainsi de compléter efficacement les autres API utilisées dans **CheckIt.AI**.

### Utilisation dans CheckIt.AI

- ✅ Collecte automatisée
- ✅ Veille
- ✅ Pipeline de production
- ❌ Entraînement supervisé

### Sources

- Documentation officielle : https://open-platform.theguardian.com/

---

# Comparaison des API

| API | Texte | Images | Labels | Temps réel | Format | Authentification |
|:----|:-----:|:------:|:------:|:----------:|:------:|:----------------:|
| NewsData.io | ✅ | ✅ (URL) | ❌ | ✅ | JSON | Clé API |
| NewsAPI | ✅ | ✅ (URL) | ❌ | ✅ | JSON | Clé API |
| GNews | ✅ | ✅ (URL) | ❌ | ✅ | JSON | Clé API |
| Currents API | ✅ | ✅ (URL) | ❌ | ✅ | JSON | Clé API |
| MediaStack | ✅ | ⚠️ Variable | ❌ | ✅ | JSON | Clé API |
| GDELT | ✅ | ⚠️ Variable | ❌ | ✅ | JSON / CSV | Variable |
| Google Fact Check | ✅ | ⚠️ Variable | ✅ | ✅ | JSON | Clé API |
| The Guardian | ✅ | ✅ | ❌ | ✅ | JSON | Clé API |

---

# Synthèse

Les API constituent le principal mécanisme de collecte continue de **CheckIt.AI**. Elles permettent d'alimenter automatiquement le pipeline avec des articles récents provenant de nombreux médias internationaux.

Les différentes API retenues présentent des fonctionnalités complémentaires. **NewsData.io**, **NewsAPI**, **GNews**, **Currents API**, **MediaStack**, **GDELT** et **The Guardian API** contribuent à diversifier les sources d'information, tandis que **Google Fact Check API** apporte des verdicts de véracité permettant d'enrichir certaines données collectées.

Aucune de ces API ne fournit à elle seule l'ensemble des informations nécessaires au projet. J'ai donc choisi de combiner plusieurs services afin d'améliorer la couverture des médias, des langues et des thématiques tout en limitant la dépendance à une source unique. Cette approche permet de constituer un corpus plus riche et plus diversifié, qui sera ensuite complété par les flux RSS, les plateformes de fact-checking et les jeux de données académiques.