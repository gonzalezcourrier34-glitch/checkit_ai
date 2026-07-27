# Schéma du pipeline

## Présentation

Dans cette section, je regroupe les principaux schémas permettant de visualiser le fonctionnement général de **CheckIt.AI**.

Ces représentations complètent les chapitres précédents en illustrant la circulation des données entre les différents composants du projet.

---

# Vue d'ensemble

Le pipeline complet est organisé en plusieurs étapes successives.

```mermaid
flowchart LR
    A[Sources de données]
    --> B[Extraction]
    --> C[Préparation]
    --> D[Téléchargement des images]
    --> E[Transformation]
    --> F[Chargement PostgreSQL]
    --> G[Contrôle qualité]
    --> H[Dashboard]
```

Chaque étape produit les données nécessaires à la suivante.

---

# Organisation des extracteurs

Les publications sont collectées selon leur famille de sources.

```mermaid
flowchart TD

A[Sources]

A --> B[APIs]
A --> C[Flux RSS]
A --> D[Scrapers]
A --> E[Réseaux sociaux]
A --> F[Datasets]

B --> G[Schéma commun]
C --> G
D --> G
E --> G
F --> G
```

Toutes les données sont converties vers le même modèle d'article avant de poursuivre le pipeline.

---

# Préparation des articles

Les publications suivent plusieurs traitements avant leur transformation.

```mermaid
flowchart LR

A[Article brut]

A --> B[Normalisation]

B --> C[Nettoyage]

C --> D[Déduplication]

D --> E[Validation]

E --> F[Article préparé]
```

Cette étape garantit que les traitements suivants manipulent des données homogènes.

---

# Traitement des images

Lorsqu'une publication possède une image, celle-ci suit un pipeline spécifique.

```mermaid
flowchart LR

A[URL image]

A --> B[Téléchargement]

B --> C[Validation]

C --> D[Métadonnées]

D --> E[Association avec l'article]
```

Les informations obtenues sont ensuite ajoutées aux métadonnées de la publication.

---

# Pipeline de transformation

Les données préparées sont enrichies avant leur chargement.

```mermaid
flowchart LR

A[Articles préparés]

A --> B[Transformation métier]

B --> C[Génération des caractéristiques]

C --> D[Validation finale]

D --> E[Articles transformés]
```

Cette étape produit un jeu de données homogène destiné au stockage.

---

# Chargement des données

Les données transformées sont ensuite réparties dans les différentes tables PostgreSQL.

```mermaid
flowchart TD

A[Articles transformés]

A --> B[Articles]

A --> C[Images]

A --> D[Labels]

A --> E[Caractéristiques]

A --> F[Pipeline Runs]

A --> G[Sources]
```

Chaque table contient une partie des informations produites pendant le pipeline.

---

# Orchestration avec Apache Airflow

Les différentes étapes sont exécutées dans un ordre précis.

```mermaid
flowchart LR

A[Master DAG]

A --> B[Extract DAG]

B --> C[Transform DAG]

C --> D[Load DAG]

D --> E[Quality DAG]

```

Le DAG principal orchestre automatiquement les différentes phases du projet.

---

# Vue globale de l'architecture

L'ensemble du projet peut être résumé par le schéma suivant.

```mermaid
flowchart LR

A[Sources]

A --> B[Extracteurs]

B --> C[Articles RAW]

C --> D[Préparation]

D --> E[Transformation]

E --> F[Images]

F --> G[PostgreSQL]

G --> H[Dashboard]

G --> I[Rapports]

G --> J[Jeux de données IA]
```

Ce schéma met en évidence les principales étapes suivies par les données depuis leur collecte jusqu'à leur exploitation.

---

# Conclusion

Les différents schémas présentés dans cette section illustrent l'organisation générale du pipeline développé pour **CheckIt.AI**.

Ils montrent comment les données circulent entre les différents composants du projet, depuis leur acquisition jusqu'à leur stockage et leur exploitation.

Ces représentations complètent les descriptions détaillées des chapitres précédents et offrent une vision synthétique de l'architecture mise en œuvre.