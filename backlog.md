# Backlog du Projet - Gestion du Catalogue d'Applications

Ce document liste les fonctionnalités, user stories et tâches techniques à réaliser pour améliorer et étendre l'application.
Les tâches réalisées sont retirées du fichier.

---

## Epic 1 : Fonctionnel

### User Stories
- **US1.3** : *Ajouter un score de dette global*  
  Ajouter un score de dette correspondant aux applications non évaluées. Par exemple 30 points par application non évaluées.
  Le nombre total d'application dans le SI est un paramètre de configuration (?)

## Epic 3 : Amélioration de la Qualité du Code, Tests et Exploitation

### Tâches Techniques
- **Tâche 3.6** : *Pagination des listes*  
  `applications.index` (`/`) et `accounts.list_accounts` (`/accounts`) chargent l'intégralité des
  enregistrements en mémoire et les rendent sans pagination ni recherche. Sans impact aujourd'hui,
  mais à traiter avant que le catalogue ou la liste des comptes ne grossisse significativement.
- **Tâche 3.7** : *Backend JSON : relecture et réécriture intégrales à chaque requête*  
  `JsonSession.__init__` (`ADM.database_json`) relit et reparse tout le fichier JSON (et reconstruit
  chaque `Application`/`Evaluation`) à l'ouverture de **chaque** session, et `commit()` réécrit
  l'intégralité du fichier à chaque validation — pas seulement pour le radar chart (déjà mis en
  cache par `ADM.services.RadarChartCache`), mais pour toute page qui touche le catalogue ou les
  comptes (`ADM.accounts_json` a la même structure). Sans impact avec un petit catalogue, ce coût
  croît linéairement avec le nombre d'enregistrements et devient sensible bien avant la pagination
  de la Tâche 3.6. À mesurer sur un catalogue représentatif ; pistes : cache de lecture invalidé sur
  le m-time du fichier, ou migration vers le backend SQLite pour les déploiements dont le catalogue
  grossit.
- **Tâche 3.8** : *Backend JSON : écritures concurrentes non protégées*  
  Ni `ADM.database_json.JsonSession` ni `ADM.accounts_json.AccountJsonSession` ne posent de verrou
  sur le fichier qu'elles lisent puis réécrivent. Deux requêtes concomitantes (plusieurs workers
  Gunicorn, ou simplement deux utilisateurs simultanés) peuvent lire le même état, le modifier
  chacune de leur côté, puis écrire à leur tour : la seconde écriture efface silencieusement la
  première (perte de mise à jour). Ce risque touche aussi des données sensibles à l'intégrité
  (compteur d'échecs de connexion, invariant du dernier admin actif, voir
  `docs/BUSINESS_RULES.md`), pas seulement le confort d'usage. À traiter par un verrou fichier
  (`fcntl`/`msvcrt` selon la plateforme, ou une dépendance telle que `filelock`), ou à défaut à
  documenter explicitement comme limite du backend JSON (déploiement mono-worker uniquement) dans
  `INSTALL.md`.

## Epic 4 : Interface Utilisateur et Expérience (UI/UX)

### User Stories
- **US4.1** : *Améliorer le design*  
  Moderniser l'affichage. Cadrage réalisé (`docs/UI_MODERNIZATION_PROPOSAL.md`) :
  plan en 7 phases, Bootstrap 5 modernisé + htmx/Alpine.js en complément
  progressif, sans changement de framework serveur ni de logique de gabarits
  Jinja2. Phase 0 (maquettes statiques, `mockups/`) validée le 2026-09-16 par
  Guillaume Rumeau, avec deux ajustements retenus pour la suite : couleur de
  marque en vert forêt légèrement foncé (`#0e6b5c` / `#0a4d42`, distincte du
  vert sémantique des badges DICP/criticité) plutôt que le bleu Bootstrap par
  défaut, et actions du catalogue regroupées dans un menu contextuel (`⋯`)
  plutôt qu'une rangée de boutons. Prochaine étape : Phase 1 (fondations du
  design system — `static/css/app.css` à partir de `mockups/assets/mockup.css`,
  vendoring Bootstrap/Bootstrap Icons, remplacement des émojis), à ouvrir
  comme prochain ticket de développement.

### Tâches Techniques
- **Tâche 4.9** : *Gestion des catégories de questions*  
  La page de configuration des questions (US4.3, livrée) ne permet d'ajouter, modifier et
  supprimer une question qu'au sein d'une catégorie déjà existante ; la création, le
  renommage et la suppression d'une catégorie restent réservés au fichier `questions.json`
  (portée volontairement réduite dans un premier temps). À traiter si le besoin se confirme.

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
  Ajouter un connecteur Active Directory (Azure AD)

### Tâches Techniques
- **Tâche 6.5** : *Aucune longueur minimale imposée aux mots de passe*  
  `validate_account_creation_form`, `validate_password_reset_form` et
  `validate_password_change_form` (`ADM.validation`) refusent un mot de passe vide ou dépassant 255
  caractères, mais acceptent un mot de passe d'un seul caractère. Introduire une longueur minimale
  (par exemple 10-12 caractères) partagée par les trois formulaires, et documenter le choix dans
  `docs/BUSINESS_RULES.md`.
- **Tâche 6.6** : *Absence d'en-têtes de sécurité HTTP*  
  Seuls les attributs du cookie de session (`HttpOnly`, `SameSite`, `Secure`) sont positionnés
  aujourd'hui (`ADM.app.create_app`). Aucune en-tête `Content-Security-Policy`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options` ni `Referrer-Policy` n'est ajoutée aux
  réponses. À ajouter via un `after_request` global dans `_register_web_components`.
---
