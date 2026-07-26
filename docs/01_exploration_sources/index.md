# Exploration des sources de données

## Objectif

Cette section présente l'étude que j'ai réalisée afin d'identifier les sources de données les plus pertinentes pour construire le pipeline d'acquisition multimodale de **CheckIt.AI**.

L'objectif est de comparer différentes solutions selon plusieurs critères :

* la richesse des données disponibles ;
* la présence de contenus textuels ;
* la disponibilité d'images ;
* la présence de labels ou de verdicts de véracité ;
* la fréquence d'actualisation ;
* la facilité d'extraction ;
* les contraintes techniques ;
* les conditions d'utilisation des sources.

Cette analyse permet de sélectionner des sources complémentaires répondant aux différents besoins du projet : acquisition continue de publications récentes, constitution de corpus annotés et récupération de contenus déjà vérifiés.

---

## Organisation de cette section

Cette partie est organisée selon les étapes suivantes :

1. **Contexte** : présentation du besoin métier et des enjeux associés à la collecte de données multimodales.

2. **Besoins fonctionnels** : définition des informations attendues pour chaque publication collectée.

3. **Cas typiques de fake news multimodales** : identification des principales formes de désinformation associant texte et image.

4. **Critères d'évaluation** : présentation de la méthode utilisée pour comparer les différentes sources.

5. **Panorama des sources** : description des principales catégories de sources étudiées dans le cadre du projet.

6. **Datasets académiques** : analyse des jeux de données annotés utilisés comme corpus de référence.

7. **API d'actualité** : étude des interfaces permettant de collecter automatiquement des publications récentes.

8. **Flux RSS** : analyse des flux officiels comme solution légère de veille et d'acquisition continue.

9. **Sources de fact-checking** : étude des API et plateformes spécialisées dans la vérification des faits.

10. **Réseaux sociaux** : présentation des plateformes prises en charge pour la collecte de contenus publiés par les utilisateurs.

11. **Comparaison des sources** : synthèse des avantages, des limites et du rôle de chaque catégorie dans **CheckIt.AI**.

12. **Recommandations** : justification des sources retenues et de leur complémentarité dans l'architecture du projet.

13. **Droits d'usage et aspects juridiques** : analyse des licences, des conditions d'utilisation et des bonnes pratiques de collecte.

14. **Méthodes d'extraction** : présentation des techniques retenues, notamment les API REST, les flux RSS, la lecture de datasets et le scraping HTML ciblé.

15. **Format de sortie des données** : définition du modèle commun utilisé pour normaliser les publications collectées.

Cette organisation suit progressivement le cheminement adopté dans **CheckIt.AI**, depuis l'identification du besoin jusqu'à la définition des sources, des méthodes d'acquisition et du format commun utilisé par le pipeline.
