# Flux RSS

## Présentation

Les flux RSS (*Really Simple Syndication*) constituent un format standardisé permettant de diffuser automatiquement les dernières publications d'un site web. De nombreux médias proposent un ou plusieurs flux correspondant à leur page d'accueil, à une rubrique ou à une thématique particulière.

Dans le cadre de **CheckIt.AI**, les flux RSS représentent des sources d'acquisition complémentaires aux API d'actualité. Ils permettent de récupérer régulièrement les nouvelles publications sans utiliser de clé API et sans dépendre des quotas imposés par certains services commerciaux.

Les flux renvoient généralement le titre, l'URL, la date de publication et un résumé de l'article. Selon le média, ils peuvent également contenir le nom de l'auteur, une catégorie ou une référence vers une image. Ils ne fournissent toutefois pas systématiquement le texte intégral ni les données visuelles.

Leur accès technique est généralement ouvert, mais les contenus restent soumis aux conditions d'utilisation et aux droits de propriété intellectuelle de chaque éditeur.

Les flux RSS actuellement intégrés à **CheckIt.AI** sont les suivants :

- Le Monde - À la une
- Le Monde - International
- Franceinfo
- BBC News
- BBC Technology
- The Guardian - World

---

# Le Monde

## Présentation

Le Monde propose plusieurs flux RSS correspondant aux principales rubriques de son site. Deux flux sont actuellement utilisés dans **CheckIt.AI** :

- À la une
- International

Ils permettent de récupérer automatiquement les nouvelles publications ainsi que leurs principales métadonnées.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Flux RSS |
| Flux utilisés | À la une, International |
| Texte | ✅ Titre et résumé |
| Texte intégral | ❌ Non garanti |
| Images | ⚠️ Selon le flux |
| Labels | ❌ |
| Format | XML (RSS) |
| Langue | Français |
| Extraction | Lecture RSS |
| Authentification | Aucune |

## Avantages

- Média de référence.
- Deux flux complémentaires.
- Intégration simple.
- Pas de clé API.
- Mise à jour régulière.

## Limites

- Texte intégral non garanti.
- Images variables.
- Aucun label de véracité.
- Certaines publications peuvent être réservées aux abonnés.

## Analyse critique

Les flux RSS du Monde permettent d'alimenter **CheckIt.AI** avec des articles francophones récents. Ils servent principalement à détecter de nouvelles publications et à récupérer leurs métadonnées avant leur normalisation dans la pipeline.

**Utilisation dans CheckIt.AI**

- ✅ Collecte automatisée
- ✅ Actualité générale
- ✅ Actualité internationale
- ❌ Entraînement supervisé

---

# Franceinfo

## Présentation

Franceinfo met à disposition un flux RSS regroupant les principaux titres d'actualité. Ce flux complète les sources francophones intégrées au projet.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Flux RSS |
| Texte | ✅ |
| Texte intégral | ❌ Non garanti |
| Images | ⚠️ Variables |
| Labels | ❌ |
| Format | XML (RSS) |
| Langue | Français |
| Extraction | Lecture RSS |
| Authentification | Aucune |

## Avantages

- Source francophone généraliste.
- Gratuit.
- Mise à jour régulière.
- Intégration très simple.

## Limites

- Métadonnées limitées.
- Images non systématiques.
- Aucun label de véracité.

## Analyse critique

Franceinfo complète les autres médias français afin de diversifier les sources d'information collectées automatiquement.

**Utilisation dans CheckIt.AI**

- ✅ Collecte automatisée
- ✅ Veille
- ✅ Corpus francophone
- ❌ Entraînement supervisé

---

# BBC News

## Présentation

La BBC propose plusieurs flux RSS. Deux flux sont actuellement exploités :

- BBC News
- BBC Technology

Ils permettent d'intégrer des contenus anglophones couvrant l'actualité internationale et les nouvelles technologies.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Flux RSS |
| Flux utilisés | News, Technology |
| Texte | ✅ |
| Texte intégral | ❌ Non garanti |
| Images | ⚠️ Variables |
| Labels | ❌ |
| Format | XML (RSS) |
| Langue | Anglais |
| Extraction | Lecture RSS |
| Authentification | Aucune |

## Avantages

- Média reconnu.
- Deux thématiques complémentaires.
- Intégration simple.
- Actualisation fréquente.

## Limites

- Texte intégral non garanti.
- Images variables.
- Aucun label de véracité.

## Analyse critique

Les flux RSS de la BBC renforcent la diversité linguistique et thématique du corpus collecté par **CheckIt.AI**, notamment dans le domaine technologique.

**Utilisation dans CheckIt.AI**

- ✅ Collecte automatisée
- ✅ Veille internationale
- ✅ Actualité technologique
- ❌ Entraînement supervisé

---

# The Guardian

## Présentation

The Guardian propose des flux RSS pour chacune de ses principales rubriques. **CheckIt.AI** utilise le flux **World**, consacré à l'actualité internationale.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Flux RSS |
| Flux utilisé | World |
| Texte | ✅ |
| Texte intégral | ❌ Non garanti |
| Images | ⚠️ Variables |
| Labels | ❌ |
| Format | XML (RSS) |
| Langue | Anglais |
| Extraction | Lecture RSS |
| Authentification | Aucune |

## Avantages

- Bonne couverture internationale.
- Intégration simple.
- Mise à jour régulière.
- Complément des flux BBC.

## Limites

- Aucun label de véracité.
- Images variables.
- Texte intégral non garanti.

## Analyse critique

Le flux **World** du Guardian permet de compléter la couverture internationale de **CheckIt.AI** en diversifiant les sources anglophones.

**Utilisation dans CheckIt.AI**

- ✅ Collecte automatisée
- ✅ Actualité internationale
- ✅ Veille
- ❌ Entraînement supervisé

---

# Comparaison des flux RSS

| Source | Langue | Texte | Texte intégral | Images | Labels | Format |
|:--------|:------:|:------:|:--------------:|:------:|:------:|:------:|
| Le Monde | FR | ✅ | ❌ | ⚠️ Variable | ❌ | XML |
| Franceinfo | FR | ✅ | ❌ | ⚠️ Variable | ❌ | XML |
| BBC News | EN | ✅ | ❌ | ⚠️ Variable | ❌ | XML |
| BBC Technology | EN | ✅ | ❌ | ⚠️ Variable | ❌ | XML |
| The Guardian World | EN | ✅ | ❌ | ⚠️ Variable | ❌ | XML |

---

# Intégration dans CheckIt.AI

Les flux RSS sont traités comme des sources d'acquisition de nouvelles publications.

L'extracteur RSS commun du projet :

- récupère les nouvelles entrées des flux ;
- normalise les métadonnées selon le schéma commun de **CheckIt.AI** ;
- valide les URLs ;
- élimine les doublons ;
- accepte les articles même en l'absence d'image ou de texte complet.

Cette approche permet d'utiliser un même pipeline de traitement pour les flux RSS et les autres sources de données.

---

# Synthèse

Les flux RSS constituent une solution simple, légère et fiable pour compléter les API d'actualité utilisées dans **CheckIt.AI**. Ils permettent de suivre automatiquement plusieurs médias français et internationaux sans dépendre de quotas d'utilisation.

Les flux actuellement intégrés couvrent des domaines complémentaires :

- **Le Monde** et **Franceinfo** renforcent le corpus francophone ;
- **BBC News** et **The Guardian** apportent une couverture internationale ;
- **BBC Technology** enrichit les contenus liés aux technologies.

Bien que les flux RSS fournissent généralement moins de métadonnées que les API d'actualité et ne garantissent ni le texte intégral ni la présence d'images, ils constituent une source efficace pour détecter rapidement de nouvelles publications et alimenter la pipeline de collecte automatisée de **CheckIt.AI**.