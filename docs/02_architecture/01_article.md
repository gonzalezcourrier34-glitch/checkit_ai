## Organisation du module `article`

Le domaine `article` est organisé par responsabilités afin de séparer clairement le schéma métier, la préparation, la validation et les traitements appliqués aux articles.

```text
src/
└── article/
    ├── __init__.py
    │
    ├── schema/
    │   ├── __init__.py
    │   ├── article_schema.py
    │   └── article_schema_normalizer.py
    │
    ├── preparation/
    │   ├── __init__.py
    │   ├── article_preparation.py
    │   ├── article_preparation_models.py
    │   └── article_preparation_profiles.py
    │
    ├── validation/
    │   ├── __init__.py
    │   ├── article_validator.py
    │   └── article_validation_policy.py
    │
    ├── article_cleaner.py
    ├── article_deduplicator.py
    ├── article_transformer.py
    └── article_utils.py
```

### Responsabilités des modules

| Module | Responsabilité |
|---------|----------------|
| `schema/article_schema.py` | Définit le schéma métier commun des articles (champs, alias, valeurs autorisées, constantes). |
| `schema/article_schema_normalizer.py` | Normalise les articles entrants afin qu'ils respectent le schéma standard CheckIt.AI. |
| `preparation/article_preparation.py` | Orchestre la préparation complète des articles : normalisation, nettoyage, déduplication et validation. |
| `preparation/article_preparation_models.py` | Contient les modèles (`ArticlePreparationReport`, `ArticlePreparationResult`) utilisés pendant la préparation. |
| `preparation/article_preparation_profiles.py` | Définit les profils de préparation (`acquisition`, `labeled_reference`, `multimodal_reference`). |
| `validation/article_validator.py` | Vérifie qu'un article respecte les règles métier et retourne les motifs de rejet. |
| `validation/article_validation_policy.py` | Construit les politiques de validation utilisées par le validateur. |
| `article_cleaner.py` | Nettoie le contenu textuel des articles (HTML, espaces, normalisation du texte). |
| `article_deduplicator.py` | Détecte et supprime les doublons d'articles. |
| `article_transformer.py` | Transforme les valeurs métier (langues, labels, catégories, rôles, etc.). |
| `article_utils.py` | Regroupe les fonctions utilitaires propres au domaine des articles (lecture des champs, helpers métier, etc.). |