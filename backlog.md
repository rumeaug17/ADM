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
- ~~**Tâche 3.1** : Ajouter des tests unitaires pour les fonctions critiques (chargement/sauvegarde, calcul des scores, génération des graphiques).~~
- ~~**Tâche 3.2** : Documenter le projet (README, commentaires dans le code, guide de contribution).~~
- ~~**Tâche 3.3** : Rendre configurable les seuils de score et de risque dans les affichages~~
- ~~**Tâche 3.4** : Découper le fichier app.py. Au minimum séparer les fonctions utilitaires des fonctions de route~~

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

Les actions ci-dessous sont ordonnées pour rendre les changements relisibles :
chaque phase doit rester livrable indépendamment, avec ses tests et sans mélanger
refactorisation et évolution fonctionnelle.

### Phase 1 : Sécurisation et hygiène de base (faible risque)
- [x] Remplacer les secrets en clair par des variables d’environnement et documenter
  la configuration locale sans valeur sensible.
- [x] Ajouter une protection CSRF pour toutes les routes `POST`.
- [x] Centraliser la gestion des erreurs : messages génériques côté interface,
  exceptions précises et journaux sans donnée personnelle côté serveur.
- [x] Ajouter des validations d’entrée aux formulaires et aux imports JSON, avec
  un message distinct pour chaque champ invalide.
- [x] Remplacer les captures génériques de `Exception` par les exceptions attendues
  (`OSError`, `ValueError`, erreurs SQLAlchemy), puis tester chaque erreur gérée.

### Phase 2 : Robustesse et transactions
- [x] Introduire un gestionnaire de session DB (context manager) pour commit/rollback automatiques.
- [x] Rendre l’import JSON atomique (validation préalable + transaction unique).
- [x] Ajouter des tests unitaires pour les fonctions de calcul et d’import/export.

### Phase 3 : Découpage du monolithe `app.py`
- [x] Introduire une fabrique `create_app` pour supprimer l'initialisation de la base,
  la lecture des fichiers et la validation des variables d'environnement à l'import.
- [x] Créer des blueprints Flask (auth, applications, évaluations, export).
- [x] Extraire les services métier (scoring, risque, synthèse) dans des modules
  dédiés de `src/ADM/`, sans dépendance à Flask.
- [x] Injecter la fabrique de sessions dans les routes afin de supprimer l'état global
  et de faciliter les tests avec les deux backends.

### Phase 4 : Évolutivité du modèle et des validations
- [x] Définir des structures typées pour la configuration, les questions et les
  imports ; n'ajouter une bibliothèque de validation que si les types standards ne
  suffisent pas, et justifier alors la dépendance dans `pyproject.toml`.
- [x] Mettre en place Alembic pour les migrations.
- [x] Documenter les invariants métier (scoring, poids, règles).

### Phase 5 : Nettoyage et lisibilité
- [x] Réduire les routes longues en fonctions d'orchestration courtes et en
  sous-fonctions testables.
- [x] Remplacer progressivement les retours `Any` et les dictionnaires non paramétrés
  par des alias ou des structures typées explicites, sans masquer les erreurs mypy.
- [x] Harmoniser les noms français et anglais : choisir un vocabulaire par couche et
  documenter les termes historiques qui ne peuvent pas être renommés.
- [x] Documenter l’architecture dans `docs/` avec les responsabilités de chaque module,
  le sens des dépendances et le parcours d'une requête.
- [x] Déplacer les anciens scripts racine vers `scripts/` ou les supprimer après avoir
  documenté leur remplacement, afin d'avoir un seul point d'entrée par usage.

### Phase 6 : Contrôles automatisés et reproductibilité

- [ ] Exécuter `ruff check .`, `ruff format --check .`, `mypy src main.py` et `pytest`
  dans la CI sur la version minimale de Python supportée.
- [ ] Ajouter un test d'import garantissant que l'import de l'application ne crée ni
  fichier, ni connexion, ni traitement lourd.
- [ ] Tester les backends JSON et SQL avec le même contrat de persistance pour éviter
  les divergences de comportement.
- [ ] Choisir une seule source de vérité pour les dépendances : privilégier
  `pyproject.toml` et supprimer `requirements.txt` lorsque les outils historiques ont
  été migrés.
- [ ] Construire l'artefact une seule fois dans la CI, publier son empreinte et promouvoir
  exactement cet artefact de Qualification vers Recette puis Production depuis un tag
  fixe de `main`.
- [ ] Ajouter une checklist de Pull Request couvrant tests, typage, secrets,
  documentation, migrations et impact sur le déploiement.

## Critères de fin communs aux tâches techniques

Une tâche de ce plan n'est terminée que si :

1. son comportement attendu et ses erreurs sont documentés ;
2. les tests utiles ont été ajoutés ou mis à jour ;
3. les quatre contrôles du projet ont été exécutés, ou leur limitation
   d'environnement a été explicitement consignée ;
4. aucune donnée sensible ni dépendance non justifiée n'a été introduite ;
5. la modification reste compatible avec la promotion d'un artefact unique entre les
   environnements hors DEV.
