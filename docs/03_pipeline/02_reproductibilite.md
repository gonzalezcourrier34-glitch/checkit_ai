# Reproductibilité des traitements

## Présentation

Dans cette section, je présente les mécanismes que j'ai mis en place pour garantir la reproductibilité des traitements réalisés par **CheckIt.AI**.

L'objectif est de pouvoir exécuter plusieurs fois le pipeline sur un même lot de données tout en obtenant des résultats cohérents, sans devoir interroger une nouvelle fois les sources externes.

Cette approche est particulièrement importante dans un projet de data engineering, car elle facilite les tests, le débogage, les évolutions du pipeline et la comparaison des résultats entre plusieurs versions.

---

## Pourquoi garantir la reproductibilité ?

Les sources utilisées dans le projet évoluent en permanence.

Un article peut être modifié ou supprimé, une image peut disparaître, une API peut retourner des résultats différents ou un flux RSS peut être mis à jour.

Si le pipeline dépend uniquement des données disponibles au moment de son exécution, il devient difficile de reproduire exactement un traitement réalisé quelques jours auparavant.

J'ai donc choisi de séparer clairement l'acquisition des données de leur transformation.

Cette organisation me permet de conserver les données extraites et de rejouer uniquement les étapes de préparation, de transformation ou de chargement.

---

## Principe retenu

Le fonctionnement repose sur deux étapes distinctes.

```mermaid
flowchart LR
    A[Sources externes]
    --> B[Extraction]
    --> C[Lot RAW]

    C --> D[Transformation]

    D --> E[Lot PROCESSED]
```

Le lot RAW constitue une photographie des données au moment de leur collecte.

Toutes les transformations sont ensuite réalisées à partir de ce lot, sans contacter une nouvelle fois les sources distantes.

---

## Conservation des données extraites

À la fin du pipeline d'extraction, les publications sont enregistrées dans des fichiers JSON.

Ces fichiers deviennent l'entrée du pipeline de transformation.

Ils contiennent notamment :

- les informations extraites ;
- les métadonnées disponibles ;
- les chemins vers les images téléchargées ;
- les statuts associés aux images ;
- les informations nécessaires à la validation.

Le pipeline de transformation recharge directement ces fichiers.

Cette approche me permet de relancer les traitements autant de fois que nécessaire sans effectuer une nouvelle collecte.

---

## Séparation des responsabilités

J'ai volontairement séparé le projet en plusieurs pipelines indépendants.

| Pipeline | Rôle |
|---|---|
| Extraction | Collecter les publications et produire un lot RAW. |
| Transformation | Préparer, nettoyer et enrichir les données. |
| Chargement | Insérer les données dans PostgreSQL. |
| Contrôle qualité | Vérifier la cohérence des données chargées. |

Cette organisation me permet de relancer uniquement la partie concernée lorsqu'une erreur est corrigée.

Par exemple, une modification dans les règles de transformation ne nécessite pas une nouvelle extraction des données.

---

## Versionnement des traitements

Chaque exécution produit des informations permettant d'identifier précisément le traitement réalisé.

Les rapports de transformation enregistrent notamment :

- la date d'exécution ;
- la version du pipeline ;
- les statistiques produites ;
- les fichiers générés ;
- les éventuelles erreurs rencontrées.

Ces informations me permettent de comparer plusieurs exécutions et d'identifier plus facilement l'origine d'une différence de résultat.

---

## Génération des rapports

À la fin du pipeline de transformation, un rapport est automatiquement créé.

Il contient notamment :

- le nombre d'articles traités ;
- le nombre d'articles validés ;
- le nombre de doublons ;
- le nombre d'articles rejetés ;
- les motifs de rejet ;
- les fichiers exportés ;
- la durée d'exécution ;
- le statut final.

Ces rapports facilitent le suivi du pipeline et permettent de vérifier qu'une nouvelle exécution produit des résultats cohérents.

---

## Organisation des fichiers

Les différents fichiers produits par le pipeline sont conservés afin de pouvoir rejouer les traitements.

```text
data/
├── raw/
│
├── processed/
│   ├── transformed/
│   └── reports/
│
└── images/
```

Les données extraites, les données transformées, les rapports et les images restent disponibles après l'exécution du pipeline.

Cette organisation facilite les tests et le débogage.

---

## Reproductibilité avec PostgreSQL

Une fois les données transformées, elles sont chargées dans PostgreSQL.

Le pipeline conserve les informations relatives à chaque exécution afin de relier les données enregistrées au lot qui les a produites.

Cette traçabilité permet notamment :

- de retrouver les articles chargés ;
- d'associer les données à une exécution du pipeline ;
- de comparer plusieurs lots ;
- de produire les indicateurs affichés dans le tableau de bord.

---

## Reproductibilité avec Apache Airflow

Apache Airflow orchestre les différentes étapes du projet.

Chaque pipeline est exécuté indépendamment :

- extraction ;
- transformation ;
- chargement ;
- contrôle qualité.

Cette organisation me permet de relancer uniquement le DAG concerné lorsqu'une étape échoue.

Les données déjà produites sont alors réutilisées sans recommencer l'ensemble du traitement.

---

## Avantages de cette organisation

La séparation entre les différentes étapes du pipeline présente plusieurs avantages.

Elle me permet notamment de :

- limiter les appels aux sources externes ;
- conserver une copie des données extraites ;
- comparer plusieurs versions du pipeline ;
- tester de nouvelles transformations ;
- corriger un traitement sans refaire toute l'acquisition ;
- faciliter le débogage ;
- améliorer la traçabilité des traitements.

---

## Limites

La reproductibilité concerne principalement les traitements réalisés après l'extraction.

En revanche, une nouvelle acquisition peut produire des résultats différents lorsque :

- une API renvoie de nouvelles données ;
- un article est modifié ;
- une publication est supprimée ;
- une image devient inaccessible ;
- un quota limite la collecte.

La conservation des lots RAW permet justement de limiter l'impact de ces évolutions.

---

## Conclusion

J'ai construit **CheckIt.AI** de manière à séparer clairement la collecte des données de leur transformation.

Cette organisation me permet de conserver les données extraites, de rejouer les traitements autant de fois que nécessaire et de comparer facilement plusieurs exécutions du pipeline.

La production de rapports, la conservation des lots, le chargement dans PostgreSQL et l'orchestration avec Apache Airflow contribuent ensemble à garantir la reproductibilité et la traçabilité des traitements réalisés par le projet.