# Architecture du projet

## Présentation

Dans cette section, je présente l’architecture technique que j’ai retenue pour développer le pipeline d’acquisition de données multimodales de **CheckIt.AI**.

Je me suis appuyé sur les besoins identifiés pendant l’étude exploratoire afin d’organiser le projet de manière claire et progressive.

Mon objectif est de construire une solution capable de collecter, préparer, transformer et stocker des publications contenant du texte, des images et différentes métadonnées.

J’ai choisi une architecture modulaire afin de séparer les différentes responsabilités du projet. Cette organisation doit me permettre de mieux comprendre le rôle de chaque composant, de corriger plus facilement les erreurs et de faire évoluer le pipeline sans devoir modifier l’ensemble du code.

Cette architecture sert donc de base aux différentes étapes de développement présentées dans la suite du projet.

---

## Objectifs

Dans cette partie, je cherche à :

- présenter l’organisation générale de mon projet ;
- décrire les principaux composants du pipeline ;
- expliquer comment les données circulent entre les différentes étapes ;
- présenter les principes de conception que j’ai appliqués ;
- justifier les principaux choix techniques ;
- expliquer les mécanismes utilisés pour suivre les traitements et gérer les erreurs.

---

## Organisation de cette section

J’ai organisé cette partie autour de quatre chapitres :

1. **Architecture globale** : je présente l’organisation générale du projet, les principaux composants et les différents pipelines.
2. **Modèle de données** : je définis la structure des publications et les formats utilisés pour stocker les données.
3. **Choix techniques** : j’explique les technologies, bibliothèques et outils que j’ai sélectionnés pour développer et automatiser le pipeline.
4. **Gestion des erreurs** : je présente les mécanismes de validation, de journalisation et de reprise sur erreur mis en place dans le projet.

---

## Principes de conception

Pour construire le pipeline, je me suis appuyé sur plusieurs principes simples.

| Principe | Description |
|---|---|
| **Modularité** | J’ai séparé le projet en plusieurs composants afin que chaque partie réalise une tâche précise. |
| **Automatisation** | J’ai conçu les traitements pour qu’ils puissent être exécutés automatiquement, notamment avec Apache Airflow. |
| **Robustesse** | J’ai prévu des validations, des logs et des traitements d’erreur afin d’éviter qu’un problème isolé bloque tout le pipeline. |
| **Évolutivité** | L’architecture doit me permettre d’ajouter de nouvelles sources ou de nouvelles transformations sans reprendre tout le projet. |
| **Maintenabilité** | J’ai organisé le code pour qu’il reste lisible, réutilisable et plus simple à corriger. |
| **Reproductibilité** | Les transformations peuvent être rejouées à partir des données déjà extraites, sans devoir interroger une nouvelle fois les sources. |
| **Traçabilité** | Les différentes étapes produisent des logs, des statuts et des rapports afin que je puisse suivre les traitements réalisés. |

---

## Conclusion

Cette première partie me permet de présenter la logique générale retenue pour organiser **CheckIt.AI**.

Les chapitres suivants détaillent progressivement :

- l’organisation des composants ;
- la circulation des données ;
- la structure des publications ;
- les outils utilisés ;
- les mécanismes de validation et de gestion des erreurs.

Cette vue d’ensemble sert de point de départ avant de présenter plus précisément l’architecture globale du pipeline.