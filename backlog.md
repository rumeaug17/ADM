# Backlog du Projet - Gestion du Catalogue d'Applications

Ce document liste les fonctionnalités, user stories et tâches techniques à réaliser pour améliorer et étendre l'application.

---

## Epic 0 : Correction des bugs 

## Epic 1 : Fonctionnel

### User Stories
- ~~**US1.1** : *Précision de l'estimation du score de dette*~~
  ~~Augmenter le nombre des questions à répondre et avoir des questions plus précises~~
- ~~**US1.2** : *Pondération des scores*~~  
  ~~Pondérer le poids des questions pour le calcul du score (toutes les dettes ne se valent pas)~~
- **US1.3** : *Ajouter un score de dette global*  
  Ajouter un score de dette correspondant aux applications non évaluées. Par exemple 30 points par application non évaluées.
  Le nombre total d'application dans le SI est un paramètre de configuration (?)

## Epic 2 : Sauvegarde et Historique des Données

### User Stories
- ~~**US2.3** : *Import / Export*~~  
  ~~Proposer un export global du catalogue, avec les évaluations et historique, puis un import global~~

## Epic 3 : Amélioration de la Qualité du Code et Tests

### Tâches Techniques
- **Tâche 3.1** : Ajouter des tests unitaires pour les fonctions critiques (chargement/sauvegarde, calcul des scores, génération des graphiques).
- **Tâche 3.2** : Documenter le projet (README, commentaires dans le code, guide de contribution).
- **Tâche 3.3** : Rendre configurable les seuils de score et de risque dans les affichages
- **Tâche 3.4** : Découper le fichier app.py. Au minimum séparer les fonctions utilitaires des fonctions de route

## Epic 4 : Interface Utilisateur et Expérience (UI/UX)

### User Stories
- **US4.1** : *Améliorer le design*  
  Moderniser l'affichage
- **US4.2** : *Configuration*  
  Ajouter une page de configuration pour pouvoir modifier la configuration de l'application à la volée
- **US4.3** : *Gestion des questions*  
  Ajouter une page de configuration des questions pour permettre des ajouts, des modifications, des suppressions.
  L'aide en ligne de chaque question doit également être modifiable par ce moyen.

## Epic 5 : Gestion des composants

### User Stories
- **US5.1** : *Liste des composants*  
  Ajouter et lister un ensemble de composants techniques (BDD, Langages, Frameworks, outillage, infrastructure, os)
  Chaque composant à un cycle de vie (états)
- **US5.2** : *Dépendance des composants*  
  Pour chaque application, lister les composants techniques associés
- **US5.3** : *Intégration des composants dans le score*  
  Utiliser l'état des composants dans le calcul de la dette
  
## Epic 6 : Habilitations et sécurité

### User Stories
- **US6.1** : *Habilitations*  
  Ajouter une habilitation multi-comptes avec un backend paramétrable
  
---

## Plan incrémental de refactorisation

### Phase 1 : Sécurisation et hygiène de base (faible risque)
- [ ] Remplacer les secrets en clair par des variables d’environnement et ajouter un exemple de configuration.  
- [ ] Ajouter une protection CSRF pour toutes les routes `POST`.  
- [ ] Centraliser la gestion des erreurs (messages génériques côté UI, logs détaillés côté serveur).  
- [ ] Ajouter des validations d’entrée (formulaires et upload JSON).  

### Phase 2 : Robustesse et transactions
- [ ] Introduire un gestionnaire de session DB (context manager) pour commit/rollback automatiques.  
- [ ] Rendre l’import JSON atomique (validation préalable + transaction unique).  
- [ ] Ajouter des tests unitaires pour les fonctions de calcul et d’import/export.  

### Phase 3 : Découpage du monolithe `app.py`
- [ ] Créer des blueprints Flask (auth, applications, évaluations, export).  
- [ ] Extraire les services métier (scoring, risk, synthèse) dans un module dédié.  
- [ ] Remplacer `from compute import *` par des imports explicites.  

### Phase 4 : Évolutivité du modèle et des validations
- [ ] Introduire des schémas de validation (Pydantic/Marshmallow) pour formulaires et imports.  
- [ ] Mettre en place Alembic pour les migrations.  
- [ ] Documenter les invariants métier (scoring, poids, règles).  

### Phase 5 : Nettoyage et lisibilité
- [ ] Réduire la taille des fonctions longues en sous-fonctions testables.  
- [ ] Harmoniser les conventions de nommage et ajouter des annotations de type.  
- [ ] Documenter l’architecture (README + diagramme de modules).  
