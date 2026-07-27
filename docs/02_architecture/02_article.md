## Organisation du module `article`

Le domaine `article` regroupe l'ensemble des traitements appliqués aux publications tout au long du pipeline.

J'ai organisé ce module en plusieurs sous-modules afin de séparer les différentes responsabilités. Cette organisation me permet de distinguer le schéma des articles, leur préparation, leur validation ainsi que les différents traitements métier qui leur sont appliqués.

```text
src/
└── article/
    ├── preparation/
    │   ├── article_preparation.py
    │   ├── article_preparation_models.py
    │   └── article_preparation_profiles.py
    │
    ├── processing/
    │   ├── article_deduplicator.py
    │   └── article_transformer.py
    │
    ├── schema/
    │   ├── article_schema.py
    │   └── article_schema_normalizer.py
    │
    ├── validation/
    │   ├── article_validation_policy.py
    │   └── article_validator.py
    │
    ├── article_cleaner.py
    ├── article_deduplicator.py
    ├── article_transformer.py
    ├── article_utils.py
    └── fact_check_labels.py
```

Chaque module intervient à une étape précise du traitement des articles et peut être réutilisé par différents pipelines.

### Responsabilités des modules

| Module | Rôle dans le projet |
|---------|---------------------|
| `schema/article_schema.py` | Définit le schéma commun utilisé par les articles ainsi que les principaux champs et constantes associés. |
| `schema/article_schema_normalizer.py` | Normalise les données provenant des différentes sources afin qu'elles respectent le schéma standard du projet. |
| `preparation/article_preparation.py` | Orchestre la préparation complète des articles avant leur transformation. |
| `preparation/article_preparation_models.py` | Regroupe les modèles représentant les résultats et les rapports de préparation. |
| `preparation/article_preparation_profiles.py` | Définit les profils de préparation appliqués selon le rôle des articles (`acquisition`, `labeled_reference` et `multimodal_reference`). |
| `processing/article_deduplicator.py` | Réalise les traitements de déduplication utilisés pendant les traitements métier. |
| `processing/article_transformer.py` | Applique les transformations métier aux articles avant leur enrichissement. |
| `validation/article_validator.py` | Vérifie qu'un article respecte les règles de validation définies par le projet et retourne les éventuels motifs de rejet. |
| `validation/article_validation_policy.py` | Construit les politiques de validation utilisées par le pipeline. |
| `article_cleaner.py` | Nettoie et homogénéise le contenu des articles avant les différentes étapes de traitement. |
| `article_deduplicator.py` | Fournit les fonctions communes de détection des doublons utilisées dans le projet. |
| `article_transformer.py` | Contient les fonctions de transformation générales appliquées aux articles. |
| `article_utils.py` | Regroupe les fonctions utilitaires communes utilisées dans le domaine `article`. |
| `fact_check_labels.py` | Centralise les correspondances et la normalisation des labels de fact-checking provenant des différentes sources. |

Cette organisation me permet de conserver une séparation claire entre les différentes étapes du traitement tout en facilitant la maintenance du code. Les composants spécialisés peuvent évoluer indépendamment sans modifier le fonctionnement global du pipeline.