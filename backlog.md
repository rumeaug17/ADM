# Backlog du Projet - Gestion du Catalogue d'Applications

Ce document liste les fonctionnalités, user stories et tâches techniques à réaliser pour améliorer et étendre l'application.

Dernière relecture du code source (`src/ADM`) : les tâches déjà réalisées ont été retirées et de
nouvelles améliorations/évolutions ont été identifiées (marquées **[Nouveau]**).

---

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
- **[Nouveau] Tâche 3.7** : *Backend JSON : relecture et réécriture intégrales à chaque requête*  
  `JsonSession.__init__` (`ADM.database_json`) relit et reparse tout le fichier JSON (et reconstruit
  chaque `Application`/`Evaluation`) à l'ouverture de **chaque** session, et `commit()` réécrit
  l'intégralité du fichier à chaque validation — pas seulement pour le radar chart (déjà mis en
  cache par `ADM.services.RadarChartCache`), mais pour toute page qui touche le catalogue ou les
  comptes (`ADM.accounts_json` a la même structure). Sans impact avec un petit catalogue, ce coût
  croît linéairement avec le nombre d'enregistrements et devient sensible bien avant la pagination
  de la Tâche 3.6. À mesurer sur un catalogue représentatif ; pistes : cache de lecture invalidé sur
  le m-time du fichier, ou migration vers le backend SQLite pour les déploiements dont le catalogue
  grossit.
- **[Nouveau] Tâche 3.8** : *Backend JSON : écritures concurrentes non protégées*  
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
- **[Nouveau] Tâche 3.10** : *Couverture de tests non mesurée*  
  La suite de tests est déjà large et bien structurée, mais aucun rapport de couverture n'est
  produit ni suivi dans le temps (pas de `pytest-cov`, pas de seuil minimal en CI). Ajouter
  `--cov=ADM --cov-report=term-missing` (ou équivalent) au job `test`, avec un seuil initial fixé au
  niveau de couverture actuel pour éviter toute régression future.

## Epic 4 : Interface Utilisateur et Expérience (UI/UX)

### User Stories
- **US4.1** : *Améliorer le design*  
  Moderniser l'affichage. Pistes identifiées lors de la revue UX (voir les tâches ci-dessous) :
  - [ ] Harmoniser l'affichage des niveaux DICP/criticité (Tâche 4.4)
  - [ ] Unifier le composant d'aide contextuelle (Tâche 4.5)
  - [ ] Rendre le tableau du catalogue responsive (Tâche 4.6)
- **US4.3** : *Gestion des questions*  
  Ajouter une page de configuration des questions pour permettre des ajouts, des modifications, des suppressions.
  L'aide en ligne de chaque question doit également être modifiable par ce moyen.

### Tâches Techniques
- **[Nouveau] Tâche 4.4** : *Incohérence d'affichage des niveaux DICP et de criticité*  
  Les formulaires (`add.html`, `edit.html`) proposent des libellés humains (« Faible », « Moyenne »,
  « Élevée », « Critique ») pour la disponibilité/intégrité/confidentialité/pérennité, mais
  `index.html` et `resume.html` affichent ensuite les codes bruts (`D1`–`D4`, `I1`–`I4`, etc.) dans
  des badges colorés. L'utilisateur saisit un libellé et revoit un code qu'il doit réinterpréter. À
  harmoniser (libellé en infobulle du badge, ou libellé affiché directement).
- **[Nouveau] Tâche 4.5** : *Deux composants d'aide contextuelle différents*  
  Les boutons d'action de `index.html`/`resume.html` utilisent les tooltips Bootstrap natifs
  (`data-bs-toggle="tooltip"`), tandis que les icônes d'aide (`?`) de `score.html` et `add.html`
  réimplémentent en jQuery une infobulle positionnée en absolu, avec une largeur fixe différente
  selon la page (450px sur `score.html`, 1050px sur `add.html`) qui peut déborder sur petit écran.
  À unifier sur un seul composant (par exemple un popover Bootstrap natif), accessible au clavier et
  responsive.
- **[Nouveau] Tâche 4.6** : *Tableau du catalogue non responsive*  
  Le tableau de `/` (11 colonnes, `table-bordered` sans `table-responsive`) devient illisible sur
  mobile/tablette : pas de défilement horizontal contrôlé, colonnes tassées. Les actions
  (évaluer/réinitialiser/modifier/supprimer) ne sont représentées que par des émoji, sans libellé
  visible — seule une infobulle au survol les explicite, absente au toucher sur mobile. À envelopper
  dans `table-responsive` et à accompagner les boutons d'un libellé (visible ou `aria-label`).
- **[Nouveau] Tâche 4.7** : *Validation du formulaire d'évaluation via `alert()` natif*  
  `score.html` bloque la soumission par un `window.alert()` JavaScript lorsqu'un commentaire est
  vide, et surligne le champ en rose (`#ffc0cb`) directement en CSS inline. Ce message n'est pas
  cohérent avec les alertes Bootstrap utilisées partout ailleurs (flash messages) et interrompt le
  flux de façon abrupte. À remplacer par un retour inline (message sous le champ concerné,
  classe Bootstrap `is-invalid`/`invalid-feedback`).
- **[Nouveau] Tâche 4.8** : *Formulaire d'évaluation long sans repère de progression*  
  `score.html` empile toutes les catégories de questions verticalement, sans sommaire ni indicateur
  de progression (« X/Y questions répondues »), ni bouton « enregistrer » flottant pour un
  formulaire potentiellement très long. À étudier : sommaire d'ancres par catégorie, barre de
  progression, bouton de soumission persistant en bas d'écran.
- **[Nouveau] Tâche 4.9** : *Image du radar chart non responsive dans `resume.html`*  
  L'image du graphique radar est affichée avec la classe `img-fluid` dans `index.html` et
  `synthese.html`, mais pas dans `resume.html` : elle peut déborder de sa carte sur petit écran.
- **[Nouveau] Tâche 4.10** : *Grille des indicateurs de `/synthese` mal alignée*  
  Les cinq cartes de KPI utilisent chacune `col-md-3` dans une grille Bootstrap à 12 colonnes
  (5 × 3 = 15 > 12), ce qui provoque un retour à la ligne asymétrique de la dernière carte. Des
  balises `<p></p>`/`<p/>` isolées servent d'espacement à la place des classes utilitaires Bootstrap
  (`my-3`, `g-3`). À revoir avec une grille à 4 cartes par ligne (`col-md-3` × 4) ou `row-cols-*`,
  et des espacements via classes utilitaires.

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

### Tâches Techniques
- **[Nouveau] Tâche 6.5** : *Aucune longueur minimale imposée aux mots de passe*  
  `validate_account_creation_form`, `validate_password_reset_form` et
  `validate_password_change_form` (`ADM.validation`) refusent un mot de passe vide ou dépassant 255
  caractères, mais acceptent un mot de passe d'un seul caractère. Introduire une longueur minimale
  (par exemple 10-12 caractères) partagée par les trois formulaires, et documenter le choix dans
  `docs/BUSINESS_RULES.md`.
- **[Nouveau] Tâche 6.6** : *Absence d'en-têtes de sécurité HTTP*  
  Seuls les attributs du cookie de session (`HttpOnly`, `SameSite`, `Secure`) sont positionnés
  aujourd'hui (`ADM.app.create_app`). Aucune en-tête `Content-Security-Policy`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options` ni `Referrer-Policy` n'est ajoutée aux
  réponses. À ajouter via un `after_request` global dans `_register_web_components`.
---
