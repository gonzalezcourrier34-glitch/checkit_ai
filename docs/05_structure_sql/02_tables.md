# Table `sources`

## Rôle

La table `sources` contient les informations décrivant les différentes origines des publications.

Une source peut correspondre à :

- un flux RSS ;
- une API ;
- un site web ;
- un réseau social ;
- un dataset académique.

## Principales colonnes

| Colonne | Type PostgreSQL | Description |
|---|---|---|
| `id` | `BIGINT` | Identifiant interne |
| `source_key` | `VARCHAR(100)` | Identifiant technique unique |
| `display_name` | `VARCHAR(150)` | Nom affiché |
| `source_type` | `VARCHAR(30)` | RSS, API, social, scraper ou dataset |
| `base_url` | `TEXT` | URL principale |
| `default_language` | `VARCHAR(10)` | Langue principale |
| `reliability_score` | `NUMERIC` | Score contextuel facultatif |
| `is_active` | `BOOLEAN` | État d’activation |
| `requires_api_key` | `BOOLEAN` | Présence d’une authentification |
| `refresh_interval_minutes` | `INTEGER` | Fréquence de collecte |
| `max_articles_per_run` | `INTEGER` | Nombre maximal d’articles |
| `configuration` | `JSONB` | Configuration complémentaire |
| `last_successful_run` | `TIMESTAMPTZ` | Dernière exécution réussie |
| `last_failed_run` | `TIMESTAMPTZ` | Dernière exécution en échec |
| `last_error` | `TEXT` | Dernière erreur connue |

## Contraintes principales

- `source_key` est unique ;
- `source_type` est limité aux valeurs autorisées ;
- `reliability_score` est compris entre 0 et 1 ;
- les paramètres numériques doivent être positifs.

---

# Table `pipeline_runs`

## Rôle

Cette table représente une exécution complète du pipeline ETL.

Elle permet de suivre :

- l’extraction ;
- la transformation ;
- le chargement ;
- les erreurs ;
- les durées ;
- les volumes traités ;
- les ressources utilisées.

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `id` | `UUID` | Identifiant de l’exécution |
| `dag_id` | `VARCHAR` | Nom du DAG Airflow |
| `airflow_run_id` | `VARCHAR` | Identifiant Airflow |
| `pipeline_name` | `VARCHAR` | Nom du pipeline |
| `pipeline_version` | `VARCHAR` | Version fonctionnelle |
| `code_version` | `VARCHAR` | Version du code |
| `airflow_version` | `VARCHAR` | Version d’Airflow |
| `status` | `VARCHAR` | running, success, partial ou failed |
| `started_at` | `TIMESTAMPTZ` | Début d’exécution |
| `finished_at` | `TIMESTAMPTZ` | Fin d’exécution |
| `duration_seconds` | `NUMERIC` | Durée totale |
| `extracted_count` | `INTEGER` | Articles extraits |
| `transformed_count` | `INTEGER` | Articles transformés |
| `valid_count` | `INTEGER` | Articles valides |
| `rejected_count` | `INTEGER` | Articles rejetés |
| `loaded_count` | `INTEGER` | Articles chargés |
| `images_downloaded_count` | `INTEGER` | Images téléchargées |
| `images_valid_count` | `INTEGER` | Images valides |
| `images_invalid_count` | `INTEGER` | Images invalides |
| `peak_memory_mb` | `NUMERIC` | Pic mémoire |
| `average_cpu_percent` | `NUMERIC` | Utilisation CPU moyenne |
| `error_message` | `TEXT` | Erreur globale |
| `run_metadata` | `JSONB` | Métadonnées complémentaires |

---

# Table `articles`

## Rôle

La table `articles` constitue la table centrale du projet.

Elle conserve uniquement les données observées et normalisées.

```text
articles
├── texte
├── métadonnées
├── URLs
└── qualité
```

Les variables calculées sont stockées séparément dans `article_features`.

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `id` | `VARCHAR(64)` | Identifiant CheckIt.AI |
| `source_id` | `BIGINT` | Référence vers la source |
| `pipeline_run_id` | `UUID` | Exécution ayant traité l’article |
| `external_id` | `TEXT` | Identifiant fourni par la source |
| `title` | `TEXT` | Titre |
| `content` | `TEXT` | Contenu textuel |
| `original_url` | `TEXT` | URL initiale |
| `canonical_url` | `TEXT` | URL normalisée |
| `author` | `TEXT` | Auteur |
| `language` | `VARCHAR(10)` | Langue |
| `category` | `TEXT` | Catégorie |
| `published_at` | `TIMESTAMPTZ` | Date de publication |
| `extracted_at` | `TIMESTAMPTZ` | Date d’extraction |
| `transformed_at` | `TIMESTAMPTZ` | Date de transformation |
| `dataset_role` | `VARCHAR(50)` | Rôle dans le corpus |
| `data_quality_status` | `VARCHAR(30)` | Statut qualité |
| `rejection_reason` | `TEXT` | Motif de rejet |
| `transformation_version` | `VARCHAR(30)` | Version du pipeline |
| `title_hash` | `VARCHAR(64)` | Empreinte du titre |
| `content_hash` | `VARCHAR(64)` | Empreinte du contenu |
| `canonical_url_hash` | `VARCHAR(64)` | Empreinte de l’URL |
| `raw_payload` | `JSONB` | Données techniques non mappées |

## Relations

- `source_id` référence `sources.id` ;
- `pipeline_run_id` référence `pipeline_runs.id`.

---

# Table `images`

## Rôle

La table `images` stocke les métadonnées techniques et visuelles des images associées aux articles.

Les fichiers restent sur disque dans le dossier :

```text
data/images/
```

La base conserve uniquement leur chemin et leurs caractéristiques.

## Structure fonctionnelle

```text
images
├── caractéristiques techniques
├── caractéristiques visuelles
└── validation
```

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `id` | `BIGINT` | Identifiant image |
| `article_id` | `VARCHAR(64)` | Article associé |
| `remote_url` | `TEXT` | URL distante |
| `local_path` | `TEXT` | Chemin local |
| `file_name` | `TEXT` | Nom du fichier |
| `file_format` | `VARCHAR` | JPEG, PNG, WebP... |
| `mime_type` | `VARCHAR` | Type MIME |
| `width` | `INTEGER` | Largeur |
| `height` | `INTEGER` | Hauteur |
| `aspect_ratio` | `NUMERIC` | Ratio largeur/hauteur |
| `size_bytes` | `BIGINT` | Taille du fichier |
| `file_hash` | `VARCHAR` | Empreinte technique |
| `perceptual_hash` | `VARCHAR` | Empreinte perceptuelle |
| `blur_score` | `NUMERIC` | Score de flou |
| `brightness_score` | `NUMERIC` | Luminosité |
| `entropy_score` | `NUMERIC` | Entropie visuelle |
| `download_duration_ms` | `INTEGER` | Durée de téléchargement |
| `is_primary` | `BOOLEAN` | Image principale |
| `is_valid` | `BOOLEAN` | Résultat de validation |
| `validation_status` | `VARCHAR` | Statut de validation |
| `validation_error` | `TEXT` | Erreur éventuelle |
| `association_status` | `VARCHAR` | Cohérence texte-image |
| `association_score` | `NUMERIC` | Score de cohérence |
| `association_method` | `VARCHAR` | Méthode de validation |

---

# Table `article_labels`

## Rôle

La table `article_labels` stocke les labels de référence associés à un article.

Elle ne contient pas les prédictions des modèles.

```text
article_labels
├── vérité terrain
├── labels humains
└── labels datasets
```

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `id` | `BIGINT` | Identifiant du label |
| `article_id` | `VARCHAR(64)` | Article concerné |
| `label` | `VARCHAR(50)` | fake, real, misleading... |
| `label_type` | `VARCHAR(30)` | dataset, manual ou fact_check |
| `label_source` | `VARCHAR(150)` | Origine |
| `annotator` | `VARCHAR(150)` | Annotateur |
| `annotation_method` | `VARCHAR(50)` | Méthode d’annotation |
| `confidence` | `NUMERIC` | Niveau de confiance |
| `is_ground_truth` | `BOOLEAN` | Vérité terrain |
| `is_active` | `BOOLEAN` | Label actif |
| `notes` | `TEXT` | Justification |
| `label_metadata` | `JSONB` | Métadonnées complémentaires |

---

# Table `article_features`

## Rôle

La table `article_features` stocke les variables calculées par les traitements Python ou les modèles d’extraction de caractéristiques.

```text
article_features
├── NLP
├── Vision
├── Multimodal
├── Embeddings
└── Features IA
```

## Exemples de features

- longueur du titre ;
- nombre de mots ;
- sentiment ;
- score de clickbait ;
- entités nommées ;
- score de cohérence texte-image ;
- chemin d’un embedding ;
- dimension d’un embedding.

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `article_id` | `VARCHAR(64)` | Article concerné |
| `image_id` | `BIGINT` | Image concernée |
| `pipeline_run_id` | `UUID` | Exécution productrice |
| `feature_group` | `VARCHAR` | NLP, vision, multimodal... |
| `feature_name` | `VARCHAR` | Nom de la feature |
| `feature_type` | `VARCHAR` | numeric, text, json... |
| `feature_version` | `VARCHAR` | Version fonctionnelle |
| `producer_name` | `VARCHAR` | Algorithme ou modèle |
| `producer_version` | `VARCHAR` | Version du producteur |
| `numeric_value` | `NUMERIC` | Valeur numérique |
| `text_value` | `TEXT` | Valeur textuelle |
| `boolean_value` | `BOOLEAN` | Valeur booléenne |
| `json_value` | `JSONB` | Valeur structurée |
| `vector_path` | `TEXT` | Chemin vers un embedding |
| `vector_dimension` | `INTEGER` | Dimension du vecteur |
| `confidence` | `NUMERIC` | Confiance éventuelle |

---

# Table `model_predictions`

## Rôle

La table `model_predictions` conserve les décisions produites par les modèles.

```text
model_predictions
├── modèle
├── version
├── probabilités
└── décision
```

## Principales colonnes

| Colonne | Type | Description |
|---|---|---|
| `article_id` | `VARCHAR(64)` | Article analysé |
| `image_id` | `BIGINT` | Image éventuelle |
| `pipeline_run_id` | `UUID` | Exécution productrice |
| `model_name` | `VARCHAR` | Nom du modèle |
| `model_version` | `VARCHAR` | Version |
| `task_type` | `VARCHAR` | Type de tâche |
| `feature_set_version` | `VARCHAR` | Version des features |
| `predicted_label` | `VARCHAR` | Label prédit |
| `confidence` | `NUMERIC` | Confiance |
| `decision_threshold` | `NUMERIC` | Seuil |
| `probabilities` | `JSONB` | Probabilités par classe |
| `explanation` | `JSONB` | Éléments explicatifs |
| `prediction_status` | `VARCHAR` | success, failed ou skipped |
| `error_message` | `TEXT` | Erreur éventuelle |

---

# Tables de monitoring

## `pipeline_metrics`

Elle stocke les métriques détaillées associées à une exécution.

Exemples :

- durée d’extraction ;
- taux de données valides ;
- nombre d’images téléchargées ;
- consommation mémoire ;
- taux de chargement.

## `etl_logs`

Elle conserve les logs structurés :

- niveau ;
- composant ;
- message ;
- type d’erreur ;
- métadonnées.

## `dataset_versions`

Elle décrit les différentes versions des datasets produits :

- nom de version ;
- nombre d’articles ;
- nombre d’images ;
- nombre de labels ;
- chemin ;
- checksum.

## `pipeline_configuration`

Elle contient les paramètres fonctionnels du pipeline :

- nombre maximal d’articles ;
- langues autorisées ;
- timeout ;
- activation du téléchargement d’images.

