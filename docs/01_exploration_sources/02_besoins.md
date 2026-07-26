# Besoins fonctionnels

Afin de répondre aux objectifs de CheckIt.AI, je souhaite concevoir un pipeline d'acquisition capable de récupérer automatiquement des publications multimodales contenant les informations nécessaires à leur exploitation par le moteur d'analyse.

Dans la mesure du possible, chaque publication devra regrouper le contenu principal ainsi que les métadonnées permettant d'identifier son origine, son contexte de publication et les ressources qui lui sont associées.

Les informations recherchées sont résumées dans le tableau ci-dessous.

| Élément                     | Description                                                                                 |   Priorité  |
| --------------------------- | ------------------------------------------------------------------------------------------- | :---------: |
| Texte                       | Contenu principal de la publication ou de l'article                                         | Essentielle |
| Image                       | Image ou ensemble d'images associées à la publication, lorsque la source en fournit         | Essentielle |
| Date de publication         | Date et heure de publication                                                                |    Élevée   |
| URL                         | Lien vers la publication d'origine                                                          |    Élevée   |
| Source de publication       | Média, organisme, plateforme ou réseau social ayant publié le contenu                       |    Élevée   |
| Auteur                      | Auteur, journaliste ou compte ayant publié le contenu, lorsqu'il est disponible             |   Moyenne   |
| Langue                      | Langue principale de la publication                                                         |   Moyenne   |
| Métadonnées complémentaires | Catégorie, mots-clés, tags, pays ou autres informations descriptives fournies par la source |   Moyenne   |
| Label de véracité           | Indication de véracité (« vrai », « faux » ou équivalent), lorsqu'elle est disponible       |    Élevée   |

Ces informations constituent le jeu de données cible que je cherche à obtenir pour alimenter le pipeline de CheckIt.AI. Toutefois, toutes les sources ne fournissent pas nécessairement l'ensemble de ces informations. Certaines peuvent ne proposer que le texte et quelques métadonnées, tandis que d'autres offrent également des images ou des labels de véracité.

Cette variabilité sera prise en compte lors de l'étude comparative afin d'évaluer la capacité de chaque source à répondre aux besoins du projet et d'identifier les solutions les plus adaptées au développement du pipeline.
