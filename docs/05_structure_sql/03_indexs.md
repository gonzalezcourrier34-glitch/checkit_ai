# Index

Des index ont été ajoutés sur les colonnes les plus utilisées.

Ils concernent notamment :

- les clés étrangères ;
- les dates ;
- les sources ;
- les statuts qualité ;
- les labels ;
- les noms et versions de modèles ;
- les noms et groupes de features ;
- les hashes ;
- les colonnes JSONB ;
- la recherche plein texte.

Exemple de recherche plein texte :

```sql
SELECT id, title
FROM checkit.articles
WHERE to_tsvector(
    'simple',
    title || ' ' || content
) @@ plainto_tsquery(
    'simple',
    'intelligence artificielle'
);
```