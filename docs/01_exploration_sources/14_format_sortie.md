# Format de sortie des données

## Présentation

Les données collectées par **CheckIt.AI** proviennent de sources très hétérogènes : datasets académiques, API d'actualité, flux RSS, plateformes de fact-checking et réseaux sociaux.

Chaque source possède son propre format, ses propres champs et ses propres conventions de nommage. Afin de simplifier les traitements réalisés par le pipeline, l'ensemble de ces données est converti vers un modèle unique.

Cette étape de normalisation constitue l'un des principes centraux de l'architecture du projet. Elle garantit que toutes les publications possèdent une structure cohérente, quel que soit leur mode d'acquisition.

Ce format commun facilite notamment :

* l'intégration de nouvelles sources ;
* la validation des données ;
* le nettoyage des informations collectées ;
* la suppression des doublons ;
* le téléchargement et la validation des images ;
* le stockage dans la base de données ;
* les traitements analytiques ;
* les futurs modèles d'intelligence artificielle.

---

# Modèle de données

Chaque publication est représentée sous la forme d'un dictionnaire Python respectant un schéma commun.

Les principaux champs utilisés dans **CheckIt.AI** sont les suivants.

| Champ                   | Type       | Description                               |
| :---------------------- | :--------- | :---------------------------------------- |
| `id`                    | Chaîne     | Identifiant unique de la publication      |
| `source`                | Chaîne     | Nom de la source                          |
| `title`                 | Texte      | Titre de la publication                   |
| `text`                  | Texte      | Contenu textuel principal                 |
| `image_url`             | URL        | URL de l'image lorsqu'elle est disponible |
| `image_path`            | Chemin     | Emplacement local de l'image téléchargée  |
| `image_download_status` | Texte      | Résultat du téléchargement de l'image     |
| `image_download_error`  | Texte      | Erreur éventuelle rencontrée              |
| `published_at`          | Date/Heure | Date de publication                       |
| `url`                   | URL        | Adresse de la publication                 |
| `author`                | Texte      | Auteur lorsqu'il est disponible           |
| `language`              | Texte      | Langue détectée ou fournie                |
| `category`              | Texte      | Catégorie de la publication               |
| `label`                 | Texte      | Label de véracité lorsque disponible      |
| `dataset_role`          | Texte      | Rôle fonctionnel de la source             |
| `extraction_date`       | Date/Heure | Date d'extraction                         |

Tous ces champs ne sont pas obligatoires. Leur présence dépend des informations réellement fournies par chaque source.

Par exemple :

* une API d'actualité fournit généralement une URL d'article et une URL d'image ;
* un flux RSS fournit principalement un titre, une URL et un résumé ;
* un dataset annoté fournit un texte et un label ;
* une plateforme de fact-checking fournit un verdict qui sera normalisé ;
* une publication sociale peut contenir du texte, des images ou aucun média.

---

# Construction du modèle commun

Quel que soit le mode d'extraction utilisé, chaque publication passe par les mêmes étapes :

1. récupération des données brutes ;
2. conversion vers le schéma commun ;
3. nettoyage des champs textuels ;
4. normalisation des dates ;
5. validation des URLs ;
6. application des règles propres au rôle de la source ;
7. suppression des doublons ;
8. préparation du téléchargement des images ;
9. transmission aux étapes suivantes du pipeline.

Cette organisation permet à tous les extracteurs de produire exactement le même type de données, même lorsque les sources utilisent des formats très différents.

---

# Validation des données

Avant leur enregistrement, les publications sont soumises à plusieurs étapes de validation.

Les contrôles réalisés comprennent notamment :

* validation des champs obligatoires ;
* normalisation des dates ;
* normalisation des langues ;
* validation des URLs ;
* nettoyage des textes ;
* suppression des espaces inutiles ;
* suppression des contenus supprimés ;
* suppression des doublons ;
* normalisation des labels ;
* contrôle des images lorsqu'elles existent.

Les règles appliquées dépendent du rôle attribué à la source.

Les principales politiques utilisées sont :

| Rôle                   | Contraintes principales                                                    |
| :--------------------- | :------------------------------------------------------------------------- |
| `acquisition`          | titre obligatoire, URL obligatoire, image facultative, label facultatif    |
| `labeled_reference`    | titre obligatoire, texte obligatoire, label obligatoire                    |
| `multimodal_reference` | titre obligatoire, texte obligatoire, image obligatoire, label obligatoire |

Cette distinction permet d'appliquer des règles adaptées à chaque famille de sources sans modifier les extracteurs.

---

# Gestion des images

Les images suivent également un traitement commun.

Lorsqu'une URL d'image est disponible :

* le téléchargement est effectué séparément ;
* le type réel du fichier est vérifié ;
* les dimensions sont contrôlées ;
* la taille maximale autorisée est vérifiée ;
* les fichiers invalides sont rejetés ;
* le chemin local est enregistré.

Plusieurs informations sont alors ajoutées à la publication :

* `image_url` ;
* `image_path` ;
* `image_download_status` ;
* `image_download_error`.

Cette séparation permet de distinguer les erreurs d'extraction des erreurs liées aux images.

---

# Formats utilisés dans le pipeline

Plusieurs formats sont utilisés dans **CheckIt.AI** selon les différentes étapes du traitement.

| Format   | Utilisation                               |
| :------- | :---------------------------------------- |
| JSON     | Échange entre les étapes du pipeline      |
| CSV      | Datasets académiques et exports           |
| TSV      | Certains datasets (Fakeddit)              |
| XML      | Flux RSS                                  |
| JSON API | Réponses des API                          |
| HTML     | Scraping des plateformes de fact-checking |

Le format **JSON** constitue le format de travail principal.

Les résultats de chaque étape du pipeline sont enregistrés dans des fichiers JSON, ce qui permet de conserver l'ensemble des métadonnées associées à une publication.

Les autres formats sont uniquement utilisés lors de l'extraction avant d'être convertis vers le modèle commun.

---

# Exemple d'enregistrement

```json
{
  "id": "7b45ef12",
  "source": "NewsData.io",
  "title": "Example title",
  "text": "Example article...",
  "image_url": "https://example.com/image.jpg",
  "image_path": "images/7b45ef12.jpg",
  "image_download_status": "success",
  "image_download_error": null,
  "published_at": "2026-07-09T08:30:00Z",
  "url": "https://example.com/article",
  "author": "John Doe",
  "language": "en",
  "category": "politics",
  "label": null,
  "dataset_role": "acquisition",
  "extraction_date": "2026-07-09T10:15:00Z"
}
```

Cet exemple illustre une publication provenant d'une API d'actualité.

Les champs `label`, `author`, `category` ou les informations relatives aux images peuvent être absents ou renseignés différemment selon la source.

---

# Normalisation des différentes sources

Les différentes familles de sources ne fournissent pas les mêmes informations.

Le pipeline transforme automatiquement ces données afin d'obtenir un schéma commun.

| Type de source              | Données principalement disponibles     |
| :-------------------------- | :------------------------------------- |
| Dataset académique          | Texte, label, parfois image            |
| API d'actualité             | Titre, texte, métadonnées, URL d'image |
| Flux RSS                    | Titre, URL, résumé, date               |
| Plateforme de fact-checking | Texte, verdict, métadonnées            |
| Réseau social               | Texte, médias, métadonnées             |

Les adaptateurs propres à chaque source convertissent ensuite ces données vers les mêmes champs normalisés.

Les traitements suivants peuvent ainsi fonctionner sans connaître l'origine de la publication.

---

# Avantages du format retenu

L'utilisation d'un modèle de données unique présente plusieurs avantages.

Elle permet notamment :

* d'intégrer facilement de nouvelles sources ;
* de limiter le code spécifique à chaque extracteur ;
* de mutualiser les traitements de validation ;
* de faciliter le téléchargement des images ;
* d'appliquer les mêmes règles de nettoyage ;
* de produire un stockage homogène ;
* de simplifier les traitements analytiques ;
* de préparer directement les données destinées aux modèles d'intelligence artificielle.

Cette organisation améliore également la maintenabilité du projet en séparant clairement :

* l'acquisition ;
* la normalisation ;
* la validation ;
* le traitement des images ;
* le stockage.

---

# Traçabilité

Chaque publication conserve plusieurs informations permettant de retrouver son origine.

Le modèle commun enregistre notamment :

* la source d'origine ;
* son rôle dans le projet ;
* son URL lorsqu'elle existe ;
* la date de publication ;
* la date d'extraction.

Cette traçabilité permet :

* d'identifier rapidement une publication ;
* de retrouver sa source ;
* de distinguer les contenus annotés des contenus d'acquisition ;
* de faciliter les mises à jour ;
* d'améliorer les opérations de contrôle qualité.

---

# Conclusion

Le choix d'un format de données commun constitue un élément central de l'architecture de **CheckIt.AI**.

La normalisation permet d'intégrer des sources très différentes tout en conservant une structure homogène pour l'ensemble du pipeline.

Grâce à cette organisation, les étapes de validation, de déduplication, de téléchargement des images, de stockage et de transformation utilisent les mêmes structures de données, indépendamment de l'origine des publications.

Cette approche facilite l'ajout de nouveaux extracteurs, limite le code spécifique à chaque source et fournit une base robuste pour les traitements analytiques ainsi que pour les futurs modèles de détection de désinformation.
