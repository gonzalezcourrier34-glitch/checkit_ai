# Indicateurs de suivi (KPI)

# Introduction

Afin de mesurer le bon fonctionnement du pipeline, plusieurs indicateurs clés de performance (Key Performance Indicators ou KPI) sont calculés au cours des différentes étapes de traitement.

Ces indicateurs permettent de suivre l'activité du pipeline, d'évaluer la qualité des données produites et de détecter rapidement d'éventuelles anomalies.

Ils sont enregistrés au fil des exécutions et peuvent être consultés depuis le dashboard de supervision.

---

# Indicateurs d'exécution

Les premiers indicateurs concernent le déroulement général du pipeline.

Ils permettent de vérifier que les différentes étapes se sont correctement exécutées.

| Indicateur | Description |
|------------|-------------|
| Nombre d'exécutions | Nombre total de pipelines exécutés |
| Statut de l'exécution | Succès ou échec du pipeline |
| Date de début | Heure de lancement |
| Date de fin | Heure de fin |
| Durée totale | Temps nécessaire pour exécuter le pipeline |

Ces informations permettent d'obtenir une vision globale de l'activité du système.

---

# Indicateurs d'extraction

Les indicateurs d'extraction permettent de suivre la collecte des données.

Ils renseignent notamment sur :

- le nombre de sources interrogées ;
- le nombre d'articles analysés ;
- le nombre d'articles extraits ;
- le nombre d'articles rejetés ;
- les erreurs rencontrées lors de la collecte.

Ces mesures permettent de détecter rapidement une source devenue indisponible ou une baisse anormale du volume de données collectées.

---

# Indicateurs de transformation

La phase de transformation produit également plusieurs indicateurs.

Ils permettent de mesurer :

- le nombre d'articles transformés ;
- le nombre de doublons supprimés ;
- le nombre de labels générés ;
- le nombre de caractéristiques calculées ;
- les éventuels rejets liés aux validations.

Ces informations permettent de vérifier que les données sont correctement préparées avant leur chargement dans la base.

---

# Indicateurs de chargement

Le chargement dans PostgreSQL est suivi afin de garantir l'intégrité des données.

Les principaux indicateurs sont :

- le nombre d'articles enregistrés ;
- le nombre d'images enregistrées ;
- le nombre de labels enregistrés ;
- le nombre de caractéristiques enregistrées ;
- les éventuelles erreurs d'insertion.

Ces indicateurs permettent de vérifier que les données produites sont correctement stockées.

---

# Indicateurs de qualité

Le contrôle qualité calcule plusieurs mesures destinées à évaluer la qualité des données produites.

Les principaux indicateurs sont notamment :

- nombre d'articles valides ;
- nombre d'articles invalides ;
- taux de validation ;
- taux de rejet ;
- qualité globale du lot.

Ces indicateurs permettent de vérifier que les données répondent aux critères définis avant leur exploitation.

---

# Indicateurs liés aux images

Les images constituent une composante importante du pipeline multimodal.

Le monitoring suit notamment :

- le nombre d'images téléchargées ;
- le nombre d'images valides ;
- le nombre d'images invalides ;
- les téléchargements en échec ;
- les images absentes.

Ces indicateurs permettent d'évaluer la qualité du corpus multimodal.

---

# Indicateurs de performance

Les performances du pipeline sont également surveillées.

Les principales mesures concernent :

- la durée de l'extraction ;
- la durée de la transformation ;
- la durée du chargement ;
- la durée du contrôle qualité ;
- la durée totale du pipeline.

Le suivi de ces valeurs facilite l'identification d'éventuels ralentissements.

---

# Exploitation des KPI

Les indicateurs calculés sont utilisés à plusieurs niveaux.

Ils permettent notamment de :

- suivre l'évolution du pipeline ;
- détecter les anomalies ;
- comparer plusieurs exécutions ;
- alimenter le dashboard de supervision ;
- faciliter les opérations de maintenance.

Ils constituent ainsi un outil d'aide à la décision pour l'exploitation quotidienne du pipeline.

---

# Conclusion

Les KPI jouent un rôle central dans le dispositif de monitoring de CheckIt.AI.

Ils permettent de mesurer objectivement le fonctionnement du pipeline, d'évaluer la qualité des données produites et de disposer d'informations fiables pour le diagnostic et l'amélioration continue de la plateforme.