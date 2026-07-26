# Critères d'évaluation des sources

## Méthode d'évaluation

Afin d'identifier les sources les plus adaptées aux besoins de CheckIt.AI, j'ai analysé l'ensemble des solutions potentielles à l'aide d'une grille d'évaluation commune. Cette approche permet de comparer des sources de nature très différente selon des critères homogènes.

L'objectif est de sélectionner des sources capables d'alimenter un pipeline de collecte multimodale produisant des données exploitables pour l'entraînement, l'évaluation et l'amélioration de futurs modèles de détection de désinformation.

L'analyse porte aussi bien sur les jeux de données académiques que sur les API d'actualité, les flux RSS, les réseaux sociaux, les plateformes de fact-checking et, lorsque cela est autorisé, les sites web accessibles par scraping.

---

## Critères retenus

| Critère                       | Description                                                                                                      | Importance |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- | :--------: |
| **Texte**                     | Disponibilité du contenu textuel complet de l'article ou de la publication.                                      |     ⭐⭐⭐    |
| **Images**                    | Présence d'une ou plusieurs images associées au contenu.                                                         |     ⭐⭐⭐    |
| **Labels / verdicts**         | Disponibilité d'un label ou d'un verdict permettant d'évaluer la véracité du contenu.                            |     ⭐⭐⭐    |
| **Qualité des métadonnées**   | Auteur, date, langue, catégorie, URL, source et autres informations descriptives.                                |     ⭐⭐     |
| **API officielle**            | Existence d'une API documentée facilitant l'automatisation de la collecte.                                       |     ⭐⭐     |
| **Flux RSS**                  | Disponibilité d'un flux RSS exploitable.                                                                         |      ⭐     |
| **Langues**                   | Diversité des langues proposées.                                                                                 |     ⭐⭐     |
| **Méthode d'extraction**      | API, RSS, téléchargement, scraping autorisé ou combinaison de plusieurs méthodes.                                |     ⭐⭐⭐    |
| **Format des données**        | JSON, CSV, TSV, XML ou tout autre format facilement exploitable.                                                 |     ⭐⭐     |
| **Fréquence de mise à jour**  | Régularité de l'actualisation des contenus.                                                                      |     ⭐⭐⭐    |
| **Documentation**             | Qualité de la documentation technique et facilité d'intégration.                                                 |     ⭐⭐     |
| **Contraintes d'utilisation** | Clés API, quotas, licence, conditions d'utilisation, restrictions techniques et respect du fichier *robots.txt*. |     ⭐⭐⭐    |

Les critères les plus déterminants sont la disponibilité simultanée du texte et des images, la présence éventuelle d'un label ou d'un verdict de véracité, ainsi que la possibilité d'automatiser la collecte tout en respectant les conditions d'utilisation des différentes sources.

---

# Aperçu des principales sources étudiées

| Source             |         Catégorie         | Texte |       Images      | Labels / Verdicts | API | RSS |   Langues   |   Extraction   |
| :----------------- | :-----------------------: | :---: | :---------------: | :---------------: | :-: | :-: | :---------: | :------------: |
| FakeNewsNet        |     Dataset académique    |   ✅   |         ✅         |         ✅         |  ❌  |  ❌  |      EN     | Téléchargement |
| Fakeddit           |     Dataset académique    |   ✅   |         ✅         |         ✅         |  ❌  |  ❌  |      EN     | Téléchargement |
| CoAID              |     Dataset académique    |   ✅   |     ⚠️ Partiel    |         ✅         |  ❌  |  ❌  |      EN     | Téléchargement |
| LIAR               |     Dataset académique    |   ✅   |         ❌         |         ✅         |  ❌  |  ❌  |      EN     | Téléchargement |
| NewsAPI            |      API d'actualité      |   ✅   |      ✅ (URL)      |         ❌         |  ✅  |  ❌  | Multilingue |    API REST    |
| NewsData.io        |      API d'actualité      |   ✅   |      ✅ (URL)      |         ❌         |  ✅  |  ❌  | Multilingue |    API REST    |
| GNews              |      API d'actualité      |   ✅   |      ✅ (URL)      |         ❌         |  ✅  |  ❌  | Multilingue |    API REST    |
| Currents API       |      API d'actualité      |   ✅   |      ✅ (URL)      |         ❌         |  ✅  |  ❌  | Multilingue |    API REST    |
| Mediastack         |      API d'actualité      |   ✅   |    ⚠️ Variable    |         ❌         |  ✅  |  ❌  | Multilingue |    API REST    |
| GDELT              | Base mondiale d'actualité |   ✅   |    ⚠️ Variable    |         ❌         |  ✅  |  ✅  | Multilingue |    API / RSS   |
| The Guardian       |           Média           |   ✅   |         ✅         |         ❌         |  ✅  |  ✅  |      EN     |    API / RSS   |
| Google Fact Check  |       Fact-checking       |   ✅   |    ⚠️ Variable    |    ✅ (verdicts)   |  ✅  |  ❌  | Multilingue |       API      |
| AFP Factuel        |       Fact-checking       |   ✅   |         ✅         |   ✅ (déductible)  |  ❌  |  ✅  |      FR     | RSS / Scraping |
| Reuters Fact Check |       Fact-checking       |   ✅   |         ✅         |   ✅ (déductible)  |  ❌  |  ✅  |      EN     | RSS / Scraping |
| Full Fact          |       Fact-checking       |   ✅   |         ✅         |   ✅ (déductible)  |  ❌  |  ✅  |      EN     | RSS / Scraping |
| PolitiFact         |       Fact-checking       |   ✅   |         ✅         |   ✅ (déductible)  |  ❌  |  ✅  |      EN     |       RSS      |
| Reddit             |       Réseau social       |   ✅   |         ✅         |         ❌         |  ✅  |  ❌  | Multilingue |       API      |
| Flux RSS de presse |    Médias généralistes    |   ✅   | ⚠️ Selon le média |         ❌         |  ❌  |  ✅  |   Variable  |       RSS      |

---

Ce tableau met en évidence la complémentarité des différentes familles de sources étudiées.

Les jeux de données académiques constituent une ressource précieuse pour disposer de contenus déjà annotés, indispensables à l'entraînement ou à l'évaluation de modèles supervisés. Les API d'actualité, les flux RSS et les réseaux sociaux permettent quant à eux d'alimenter en continu le pipeline avec des publications récentes et variées. Enfin, les plateformes de fact-checking apportent des analyses et des verdicts qui peuvent être utilisés pour enrichir ou valider certaines informations collectées.

Aucune source ne répond à elle seule à l'ensemble des besoins du projet. J'ai donc choisi de m'appuyer sur plusieurs familles de sources complémentaires afin de construire un corpus aussi diversifié, récent et exploitable que possible. Cette approche permet de tirer parti des avantages de chaque solution tout en limitant leurs contraintes respectives, notamment en matière de disponibilité des images, de présence de labels, de couverture linguistique ou de conditions d'accès aux données.
