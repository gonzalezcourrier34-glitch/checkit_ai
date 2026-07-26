# Sécurité

La base utilise plusieurs rôles PostgreSQL.

| Rôle | Accès |
|---|---|
| `checkit_et1` | Lecture et écriture pour le pipeline ETL |
| `checkit_reader` | Lecture seule |
| `checkit_dashboard` | Lecture limitée aux vues KPI |

Les secrets ne sont pas stockés dans les scripts SQL.

Ils sont gérés via :

- les variables d’environnement ;
- les connexions Airflow ;
- un fichier `.env` non versionné ;
- éventuellement un backend de secrets.
