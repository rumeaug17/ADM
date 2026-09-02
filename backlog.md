# Backlog du Projet - Gestion du Catalogue d'Applications

Ce document liste les fonctionnalités, user stories et tâches techniques à réaliser pour améliorer et étendre l'application.

Dernière relecture du code source (`src/ADM`) : les tâches déjà réalisées ont été retirées et de
nouvelles améliorations/évolutions ont été identifiées (marquées **[Nouveau]**).

---

## Epic 0 : Correction des bugs et dette technique

### Tâches Techniques
- **[Nouveau] Tâche 0.2** : *Export CSV sans BOM UTF-8*  
  `exports.export_csv` écrit le CSV en UTF-8 simple ; Excel (notamment sous Windows, cas d'usage
  probable de cet export) mal-interprète alors les caractères accentués à l'ouverture directe du
  fichier. Écrire le flux en `utf-8-sig` (BOM) pour une ouverture correcte sans étape d'import manuel.
## Epic 1 : Fonctionnel

### User Stories
- **US1.3** : *Ajouter un score de dette global*  
  Ajouter un score de dette correspondant aux applications non évaluées. Par exemple 30 points par application non évaluées.
  Le nombre total d'application dans le SI est un paramètre de configuration (?)

## Epic 3 : Amélioration de la Qualité du Code, Tests et Exploitation

### Tâches Techniques
- **[Nouveau] Tâche 3.6** : *Pagination des listes*  
  `applications.index` (`/`) et `accounts.list_accounts` (`/accounts`) chargent l'intégralité des
  enregistrements en mémoire et les rendent sans pagination ni recherche. Sans impact aujourd'hui,
  mais à traiter avant que le catalogue ou la liste des comptes ne grossisse significativement.
- **[Nouveau] Tâche 3.7** : *Génération du radar chart non mise en cache*  
  `generate_radar_chart` (matplotlib) est recalculée à chaque affichage de `/synthese` et de
  `/resume/<name>`, y compris lorsque les données n'ont pas changé depuis le dernier rendu. À évaluer
  si cela devient un point de lenteur perçu.

## Epic 4 : Interface Utilisateur et Expérience (UI/UX)

### User Stories
- **US4.1** : *Améliorer le design*  
  Moderniser l'affichage
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
  Ajouter une habilitation multi-comptes avec un backend paramétrable.
  Voir l'invariant du dernier admin actif et le rôle requis pour `/settings`
  dans [`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md).
  - [ ] Étendre la protection par rôle à la gestion des questions (US4.3)

- **[Nouveau] US6.3** : *Renforcement de la sécurité des sessions et de l'authentification*  
  - [ ] Limiter les tentatives de connexion (compteur d'échecs / délai progressif / verrouillage
    temporaire) : `auth.login` n'a aujourd'hui aucune protection contre le brute-force
  - [ ] Configurer explicitement les attributs des cookies de session (`SESSION_COOKIE_SECURE`,
    `SESSION_COOKIE_SAMESITE`, durée de vie) dans `create_app`, plutôt que de s'appuyer sur les
    valeurs par défaut de Flask
  - [ ] Journal d'audit des actions sensibles (création/suppression de compte, changement de rôle,
    activation/désactivation, réimport total du catalogue) : aujourd'hui seuls les échecs techniques
    sont journalisés (`current_app.logger.warning`), pas les actions métier réussies

---
