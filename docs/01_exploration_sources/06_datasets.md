# Datasets académiques

## Présentation

Les datasets académiques constituent une ressource importante pour le développement et l'évaluation des modèles de détection de désinformation. Contrairement aux API d'actualité ou aux flux RSS, ils proposent des données déjà structurées et annotées, généralement accompagnées de labels ou de verdicts de véracité. Ils facilitent ainsi l'entraînement supervisé, l'évaluation des performances et la comparaison des approches proposées dans la littérature scientifique.

Dans le cadre de **CheckIt.AI**, je n'utilise pas ces jeux de données pour alimenter quotidiennement le pipeline de collecte. Je les considère avant tout comme des corpus de référence permettant de développer, tester et évaluer les différents traitements mis en œuvre dans le pipeline multimodal.

Les datasets présentent néanmoins plusieurs limites. Ils sont généralement figés dans le temps, certaines ressources externes (articles ou images) peuvent ne plus être accessibles et ils ne permettent pas de collecter automatiquement de nouvelles informations. Ils constituent donc un excellent support pour le développement et l'évaluation des modèles, mais doivent être complétés par des sources dynamiques telles que les API d'actualité, les flux RSS, les plateformes de fact-checking ou les réseaux sociaux.

Les principaux jeux de données retenus pour cette étude sont présentés ci-dessous.

---

# FakeNewsNet

## Présentation

FakeNewsNet est l'un des jeux de données de référence dans le domaine de la détection automatique de désinformation. Construit à partir des verdicts publiés par les plateformes de fact-checking **PolitiFact** et **GossipCop**, il associe des articles d'actualité à des labels de véracité ainsi qu'à de nombreuses métadonnées.

Le projet original intègre également des informations issues des réseaux sociaux afin de permettre l'étude de la propagation des fake news. Une partie de ces données est toutefois devenue difficilement exploitable en raison de l'évolution des plateformes et de leurs politiques d'accès.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Dataset académique |
| Texte | ✅ |
| Images | ⚠️ Principalement référencées par URL |
| Labels | ✅ Labels de véracité |
| Format | JSON |
| Langue | Anglais |
| Extraction | Téléchargement |
| API | ❌ |
| RSS | ❌ |

## Avantages

- Référence largement utilisée dans la littérature scientifique.
- Présence de labels de véracité.
- Métadonnées riches.
- Adapté à l'entraînement et à l'évaluation de modèles supervisés.

## Limites

- Jeu de données statique.
- De nombreuses URL d'articles ou d'images ne sont plus accessibles.
- Corpus principalement anglophone.
- Une partie des informations issues des réseaux sociaux n'est plus directement exploitable.

## Analyse critique

FakeNewsNet constitue une référence académique largement utilisée pour entraîner et évaluer des modèles de détection de désinformation. Dans le cadre de **CheckIt.AI**, je prévois de l'utiliser principalement comme corpus de référence pour le développement et la validation des traitements. En revanche, son caractère statique ne permet pas d'alimenter un pipeline de collecte continue.

### Utilisation dans CheckIt.AI

- ✅ Développement
- ✅ Validation
- ✅ Entraînement des modèles
- ✅ Benchmark académique
- ❌ Collecte automatisée

### Sources

- Dépôt GitHub officiel : https://github.com/KaiDMML/FakeNewsNet
- Shu et al., *FakeNewsNet: A Data Repository with News Content, Social Context and Dynamic Information for Studying Fake News on Social Media* (2018)

---

# Fakeddit

## Présentation

Fakeddit est aujourd'hui l'un des principaux jeux de données multimodaux utilisés dans la recherche sur la détection de désinformation. Construit à partir de publications Reddit, il associe le contenu textuel des publications aux images lorsqu'elles sont disponibles et propose plusieurs niveaux de classification.

Grâce à cette richesse d'information, il constitue une référence pour les approches combinant traitement automatique du langage naturel et vision par ordinateur.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Dataset académique |
| Texte | ✅ |
| Images | ✅ |
| Labels | ✅ Plusieurs niveaux de classification |
| Format | TSV, CSV |
| Langue | Anglais |
| Extraction | Téléchargement |
| API | ❌ |
| RSS | ❌ |

## Avantages

- Dataset multimodal.
- Association directe entre le texte et l'image.
- Plusieurs niveaux de labels.
- Référence récente dans la littérature scientifique.

## Limites

- Données limitées à Reddit.
- Certaines images peuvent devenir indisponibles avec le temps.
- Présence de contenu parfois bruité ou peu informatif.

## Analyse critique

Parmi les datasets étudiés, Fakeddit apparaît comme celui qui répond le mieux aux objectifs multimodaux de **CheckIt.AI**. L'association entre les contenus textuels et visuels, ainsi que la richesse de ses annotations, en font un excellent corpus de référence pour le développement de traitements multimodaux.

### Utilisation dans CheckIt.AI

- ✅ Développement multimodal
- ✅ Validation
- ✅ Entraînement
- ✅ Benchmark académique
- ❌ Collecte automatisée

### Sources

- Dépôt GitHub officiel : https://github.com/entitize/Fakeddit
- Nakamura et al., *Fakeddit: A New Multimodal Benchmark Dataset for Fine-grained Fake News Detection*

---

# CoAID

## Présentation

CoAID est un jeu de données consacré à la désinformation liée à la pandémie de COVID-19. Il rassemble des articles d'actualité, des affirmations (*claims*), des publications issues des réseaux sociaux ainsi que leurs labels de véracité.

Il a été conçu afin d'étudier la propagation des fausses informations dans le domaine de la santé et constitue aujourd'hui une référence pour les travaux portant sur la désinformation médicale.

## Caractéristiques

| Critère | Valeur |
|----------|--------|
| Catégorie | Dataset académique |
| Texte | ✅ |
| Images | ⚠️ Partiellement |
| Labels | ✅ Labels de véracité |
| Format | CSV, JSON |
| Langue | Anglais |
| Extraction | Téléchargement |
| API | ❌ |
| RSS | ❌ |

## Avantages

- Présence de labels de véracité.
- Métadonnées disponibles.
- Combine articles, publications sur les réseaux sociaux et affirmations.
- Corpus spécialisé dans la désinformation médicale.

## Limites

- Domaine limité à la COVID-19.
- Peu représentatif des autres formes de désinformation.
- Peu adapté à une utilisation généraliste.

## Analyse critique

CoAID constitue un corpus spécialisé particulièrement intéressant pour évaluer les traitements de **CheckIt.AI** dans le domaine de la désinformation médicale. En revanche, son champ d'application reste limité et il ne peut pas constituer à lui seul un corpus généraliste.

### Utilisation dans CheckIt.AI

- ✅ Cas d'étude spécialisé
- ✅ Validation
- ❌ Corpus principal
- ❌ Collecte automatisée

### Sources

- Dépôt GitHub officiel : https://github.com/cuilimeng/CoAID
- Cui et al., *CoAID: COVID-19 Healthcare Misinformation Dataset*

---

# Comparaison des datasets

| Dataset | Texte | Images | Labels | Multimodal | Temps réel | Intérêt principal |
|:---------|:-----:|:------:|:------:|:----------:|:----------:|-------------------|
| FakeNewsNet | ✅ | ⚠️ Principalement via URL | ✅ | Partiel | ❌ | Benchmark académique |
| Fakeddit | ✅ | ✅ | ✅ | Oui | ❌ | Référence multimodale |
| CoAID | ✅ | ⚠️ Partiel | ✅ | Partiel | ❌ | Désinformation médicale |

---

# Synthèse

Les trois datasets retenus présentent des caractéristiques complémentaires répondant à différents besoins du projet **CheckIt.AI**.

- **FakeNewsNet** constitue une référence académique grâce à ses labels de véracité et à la richesse de ses métadonnées.
- **Fakeddit** apparaît comme le dataset le plus pertinent pour une approche multimodale en associant directement les contenus textuels et visuels.
- **CoAID** apporte un corpus spécialisé permettant d'étudier la désinformation dans le domaine de la santé.

Aucun de ces jeux de données ne permet, à lui seul, d'alimenter un pipeline de collecte continue. Leur principal intérêt réside dans leur utilisation comme corpus de référence pour le développement, l'entraînement et l'évaluation des futurs modèles de détection de désinformation.

J'ai donc choisi de les intégrer en complément de sources dynamiques telles que les API d'actualité, les flux RSS, les plateformes de fact-checking et les réseaux sociaux. Cette combinaison permet de bénéficier à la fois de données annotées, indispensables au développement des modèles, et de publications récentes nécessaires à l'alimentation continue du pipeline de **CheckIt.AI**.