# Pipeline de traitement

## Présentation

Dans cette section, je présente le pipeline de traitement développé pour le projet **CheckIt.AI**.

Le projet repose sur plusieurs étapes complémentaires permettant de collecter des publications, de les préparer, de les transformer puis de les charger dans un format exploitable.

Les données peuvent provenir de plusieurs types de sources :

- flux RSS ;
- API ;
- réseaux sociaux ;
- sites de fact-checking ;
- datasets académiques.

Le pipeline transforme progressivement ces données afin d’obtenir un jeu homogène, traçable et réutilisable pour de futurs traitements d’intelligence artificielle.

---

## Objectifs

Cette partie a pour objectif de :

- présenter le fonctionnement général du pipeline ;
- expliquer la circulation des données entre les différentes étapes ;
- montrer comment les traitements peuvent être rejoués ;
- décrire les modalités d’exécution du pipeline ;
- présenter les entrées, les sorties et les principaux fichiers produits.

---

## Vue d’ensemble

Le traitement complet suit plusieurs étapes successives.

```mermaid
flowchart LR
    A[Sources de données] --> B[Extraction]
    B --> C[Données extraites]
    C --> D[Transformation]
    D --> E[Données transformées]
    E --> F[Chargement PostgreSQL]
    F --> G[Contrôle qualité]
    G --> H[Jeu de données exploitable]