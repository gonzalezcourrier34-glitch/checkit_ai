# Cas typiques de fake news multimodales

## Présentation

La désinformation moderne ne repose plus uniquement sur un contenu textuel. Les campagnes de manipulation associent fréquemment plusieurs modalités de données, notamment du texte, des images, des vidéos ou des captures d'écran, afin de renforcer leur crédibilité et leur impact.

> [!IMPORTANT]
>
> ## Opinion controversée ou désinformation ?
>
> Dans le cadre de cette étude, il est essentiel de distinguer une **opinion controversée** d'un contenu relevant de la **désinformation**. Cette distinction est fondamentale pour constituer un corpus destiné au développement d'un modèle de détection de fake news.
>
> | Opinion controversée                                           | Désinformation                                                                                                   |
> | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
> | Repose sur un point de vue, une interprétation ou un jugement. | Repose sur une information objectivement fausse, trompeuse ou pouvant être contredite par des faits vérifiables. |
> | Peut être choquante, impopulaire ou contraire au consensus.    | Présente des informations incompatibles avec les faits établis ou déformant la réalité.                          |
> | Relève de la liberté d'expression.                             | Peut faire l'objet d'une vérification par des démarches de fact-checking.                                        |
> | N'est pas nécessairement fausse.                               | Repose sur des affirmations dont la véracité peut être évaluée objectivement.                                    |
>
> Le pipeline développé dans le cadre de CheckIt.AI aura pour objectif de collecter des publications multimodales, **sans conclure automatiquement qu'un contenu controversé constitue une fake news**. La véracité des informations devra être déterminée à partir de sources fiables, de plateformes de fact-checking ou de labels disponibles dans certains jeux de données.

---

Dans le cadre du projet CheckIt.AI, il est donc essentiel d'identifier les principales formes de désinformation multimodale afin de sélectionner les sources de données les plus adaptées à leur étude.

---

## Image sortie de son contexte

L'une des formes les plus courantes consiste à réutiliser une photographie authentique en lui associant un contexte erroné.

Par exemple, une image prise lors d'un événement ancien peut être présentée comme illustrant une catastrophe récente ou un conflit en cours.

### Difficultés pour la détection

* Le texte peut sembler cohérent avec l'image.
* L'image est authentique mais son contexte est faux.
* La vérification nécessite souvent des métadonnées, une recherche d'image inversée ou la consultation de sources fiables.

---

## Faux montage photographique

Certaines fake news utilisent des images modifiées afin de faire croire à un événement qui n'a jamais eu lieu.

Les retouches peuvent être réalisées à l'aide de logiciels de traitement d'image ou de techniques d'intelligence artificielle.

### Difficultés pour la détection

* Les modifications peuvent être très discrètes.
* Le texte renforce souvent la crédibilité du montage.
* Une analyse visuelle avancée peut être nécessaire.

---

## Texte trompeur associé à une image authentique

Dans ce cas, la photographie est réelle mais le texte qui l'accompagne contient une information fausse ou volontairement trompeuse.

L'image est utilisée pour renforcer la crédibilité du message.

### Difficultés pour la détection

* L'image ne présente aucune anomalie.
* La désinformation provient principalement du contenu textuel.
* Une analyse conjointe du texte et de l'image est nécessaire.

---

## Texte véridique associé à une image erronée

À l'inverse, une information correcte peut être illustrée par une image qui ne correspond pas au sujet traité.

Cette situation peut résulter d'une erreur de publication, d'une réutilisation hors contexte ou d'une volonté de renforcer l'impact émotionnel ou médiatique du contenu.

### Difficultés pour la détection

* Le texte est factuellement exact.
* L'incohérence provient uniquement du contenu visuel.
* La relation entre le texte et l'image doit être analysée.

---

## Images synthétiques générées par intelligence artificielle

Les progrès récents de l'intelligence artificielle générative permettent de produire des images très réalistes représentant des personnes, des objets ou des événements qui n'ont jamais existé.

Ces images peuvent être utilisées pour diffuser de fausses informations ou renforcer la crédibilité de contenus trompeurs.

### Difficultés pour la détection

* Les images peuvent paraître authentiques.
* Les indices visuels deviennent de plus en plus difficiles à identifier.
* Une analyse spécialisée est souvent nécessaire.

---

## Captures d'écran falsifiées

Certaines campagnes de désinformation utilisent de fausses captures d'écran de publications sur les réseaux sociaux, d'articles de presse ou de conversations.

Le contenu est modifié afin de faire croire qu'une personne, un média ou une organisation a réellement publié une information.

### Difficultés pour la détection

* La mise en page reproduit fidèlement les interfaces originales.
* Les modifications sont parfois difficiles à repérer.
* Une vérification de la publication ou de la source d'origine est indispensable.

---

## Réutilisation d'une image recadrée

Une photographie authentique peut être volontairement recadrée afin de masquer une partie importante de la scène ou d'en modifier l'interprétation.

Par exemple, un recadrage peut donner l'impression qu'une manifestation est beaucoup plus importante qu'elle ne l'est réellement ou masquer des éléments apportant un contexte différent.

### Difficultés pour la détection

* L'image est authentique.
* Le recadrage modifie la perception de la scène.
* La vérification nécessite souvent d'accéder à la photographie originale.

---

## Graphiques et visuels trompeurs

Certaines campagnes de désinformation diffusent de faux graphiques, tableaux ou statistiques afin de donner une apparence scientifique à des informations erronées.

Les manipulations peuvent porter sur les valeurs affichées, les échelles utilisées ou la présentation graphique.

### Difficultés pour la détection

* Les visuels paraissent crédibles.
* Les manipulations sont parfois difficiles à identifier.
* Une vérification des données d'origine est nécessaire.

---

## Synthèse

| Type de désinformation                         |    Texte   | Image | Difficulté principale                                        |
| ---------------------------------------------- | :--------: | :---: | ------------------------------------------------------------ |
| Image sortie de son contexte                   |      ✅     |   ✅   | Vérifier le contexte de l'image                              |
| Faux montage photographique                    |      ✅     |   ✅   | Détecter les modifications visuelles                         |
| Texte trompeur associé à une image authentique |      ✅     |   ✅   | Vérifier la cohérence entre le texte et l'image              |
| Texte véridique associé à une image erronée    |      ✅     |   ✅   | Identifier l'incohérence entre les modalités                 |
| Images synthétiques générées par IA            | Facultatif |   ✅   | Déterminer si le contenu visuel représente un événement réel |
| Captures d'écran falsifiées                    |      ✅     |   ✅   | Vérifier l'authenticité de la publication                    |
| Image recadrée                                 |      ✅     |   ✅   | Retrouver le contexte complet de la scène                    |
| Graphiques et visuels trompeurs                |      ✅     |   ✅   | Vérifier les données et leur représentation                  |

---

## Conclusion

Ces différents cas illustrent la diversité des formes de désinformation multimodale rencontrées aujourd'hui. Ils montrent qu'une analyse fondée uniquement sur le texte ou uniquement sur l'image est insuffisante.

Le pipeline développé dans le cadre de CheckIt.AI devra donc préserver l'association entre le texte, les images et les métadonnées de chaque publication afin de conserver l'intégrité des données collectées. Cette association constitue un prérequis indispensable pour le développement et l'évaluation de futurs modèles capables d'exploiter simultanément ces différentes modalités pour détecter des contenus potentiellement trompeurs.
