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
  plutôt qu'une rangée de boutons. Phase 1 (fondations du design system)
  réalisée le 2026-09-16 : `static/css/app.css` consolide tous les styles
  auparavant dupliqués par gabarit sous les noms de classes réels de
  l'application (avec la palette verte validée), Bootstrap 5.3.3 et
  Bootstrap Icons 1.11.3 sont vendorisés dans `static/vendor/` (fin du CDN
  `jsdelivr`), et les émojis ont été remplacés par des icônes Bootstrap
  Icons ; aucun changement de structure HTML ni de classe testée (voir
  section 10 de `docs/UI_MODERNIZATION_PROPOSAL.md` pour le détail complet
  et les écarts volontaires). `ruff`/`mypy --strict`/`pytest --cov=ADM`
  passent (275 tests, couverture 87,81 %, seuil 86 % maintenu), résultat
  identique à la mesure de référence avant modification. Phase 2 (refonte
  visuelle des pages principales) réalisée le 2026-09-16 : catalogue
  (`index.html`) avec recherche et tri instantanés en JavaScript pur côté
  client, actions regroupées dans un menu contextuel (`⋯`) à la place des
  quatre boutons, tableau conservant sa classe exacte testée ; fiche résumé
  (`resume.html`) aux sections aérées (icônes, espacements) ; synthèse
  (`synthese.html`) avec cartes KPI et tableaux redessinés (nouvelles
  couleurs sémantiques). Aucune route Flask modifiée, aucun test cassé
  (275 tests, 87,81 %, identique à la Phase 1 — détail et écarts volontaires
  en section 12 de `docs/UI_MODERNIZATION_PROPOSAL.md`). Phase 3 (formulaires
  et pages secondaires) réalisée le 2026-09-16 : labels flottants Bootstrap
  sur `login.html`/`change_password.html` (formulaires courts) et sur les
  trois champs courts d'`add.html`/`edit.html`, désormais regroupés en deux
  cartes thématiques ; `score.html` réhabillé sans toucher au sommaire
  d'ancres, à la barre de progression ni à la validation des commentaires
  obligatoires (Tâches 4.7/4.8, conservées) ; `accounts.html` aligné sur le
  patron `table-responsive` des autres pages de liste ; icônes ajoutées sur
  `questions_settings.html`/`settings.html` ; `import_data.html` et
  `error.html`, jamais retouchés depuis l'introduction du design system,
  passent au même gabarit que le reste de l'application ;
  `question_form.html` inchangé (déjà conforme). Aucune route Flask
  modifiée, aucun test cassé (275 tests, 87,81 %, identique aux Phases 1 et
  2 — détail et écarts volontaires en section 14 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Phase 4 (interactivité progressive
  avec htmx et Alpine.js) réalisée le 2026-09-16 : htmx 2.0.10 et
  Alpine.js 3.17.3 vendorisés dans `static/vendor/` ; suppression et
  réinitialisation d'une application depuis le catalogue confirmées en
  modale puis appliquées via htmx, qui ne rafraîchit que la ligne concernée
  (partiel `_application_row.html`, `id` de ligne stable propagé par
  `data-row-id`) au lieu de recharger toute la page ; filtres de la
  synthèse (`?filter_score=...`) rafraîchissant seulement le tableau
  (partiel `_synthese_results.html`, sans les cartes KPI, dont les valeurs
  ne dépendent volontairement pas du filtre côté serveur) ; messages de
  succès transmis en toasts Bootstrap via l'en-tête `HX-Trigger` plutôt
  qu'en `flash()` pour ces actions ; bascule de thème clair/sombre ajoutée
  et gérée en Alpine.js, avec script anti-FOUC dans `base.html` ; menu
  mobile conservé sur le `navbar-toggler` Bootstrap natif (déjà
  fonctionnel, non réécrit en Alpine). C'est la première phase qui modifie
  `ADM.routes` (branches conditionnelles sur l'en-tête `HX-Request`,
  additives, sans changer le comportement des requêtes non-htmx). Aucun
  test cassé (275 tests, couverture 87,55 %, seuil 86 % maintenu) hormis un
  test de présence de balisage statique adapté à son nouvel emplacement
  (détail et écarts volontaires en section 16 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Reste, côté utilisateur (session
  cloud sans accès `git` sur ce poste) : créer une branche, relire le diff,
  relancer les vérifications localement, tester manuellement les nouvelles
  interactions htmx/Alpine et commiter (détail dans le document). Phase 5
  (mode sombre, accessibilité et finitions) réalisée le 2026-09-16 : la
  bascule de thème et sa persistance `localStorage` étaient déjà livrées en
  Phase 4, cette phase a porté sur l'audit de contraste annoncé et ses
  corrections — badges de score/risque et badges DICP/criticité sur fond
  jaune/orange passés d'un texte blanc illisible (contraste ~1,6:1 et ~2,6:1)
  à un texte conforme WCAG AA (`text-bg-*` Bootstrap pour les premiers,
  nouveau jeton `--adm-badge-text-dark` pour les seconds, ~8,5:1 et ~5,4:1) ;
  aria-label ajouté aux deux liens d'action icône-seule de `resume.html` ;
  nom accessible corrigé sur le modal de réinitialisation de mot de passe
  d'`accounts.html` (`aria-labelledby`/`id` manquants) ; graphiques radar
  (toujours rendus en PNG blanc par matplotlib) encadrés d'une plaque
  blanche (`chart-surface`) pour rester lisibles en thème sombre ; aucun
  `tabindex` positif trouvé, ordre de tabulation déjà correct. Aucune route
  Flask modifiée. 282 tests passés (275 + 7 nouveaux dans
  `tests/test_phase5_accessibility.py`, dont un calcul programmatique du
  ratio de contraste WCAG), couverture 87,55 % maintenue (détail et écarts
  volontaires en section 18 de `docs/UI_MODERNIZATION_PROPOSAL.md`). Reste,
  côté utilisateur (session cloud sans accès `git` sur ce poste) : créer une
  branche, relire le diff, relancer les vérifications localement, vérifier
  visuellement (badges, thème sombre, lecteur d'écran/inspecteur
  d'accessibilité) et commiter (détail dans le document). Correctif du
  2026-09-16 (signalé par Guillaume Rumeau) : après une suppression ou une
  réinitialisation d'évaluation depuis le catalogue, le modal de
  confirmation restait ouvert alors que l'action était bien effectuée
  (toast affiché, ligne mise à jour/retirée) — la Phase 4 avait remplacé le
  rechargement de page qui fermait le modal de facto par une requête htmx,
  sans rien pour fermer le modal explicitement. Corrigé dans `base.html`
  (l'écouteur `htmx:afterRequest` existant referme désormais tout modal
  ancêtre de l'élément déclencheur après une requête réussie, correctif
  générique à tout formulaire htmx en modal, voir section 19 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). 285 tests passés (282 + 3 nouveaux),
  couverture 87,55 % maintenue. Correctif du 2026-09-16 (signalé par
  Guillaume Rumeau) : les messages informatifs s'affichaient tantôt en haut
  de page (messages flash Flask, alerte Bootstrap dupliquée dans 11
  gabarits), tantôt en bas à droite (toasts htmx de la Phase 4) — deux
  emplacements et deux formats pour la même notion de message après une
  action. Corrigé en centralisant le rendu des messages flash dans
  `base.html`, seul gabarit qui appelle encore `get_flashed_messages` : ils
  sont désormais rendus comme des toasts Bootstrap dans le même conteneur et
  avec le même balisage que les toasts htmx (`text-bg-<catégorie>`, bouton de
  fermeture adapté à la catégorie), et deux fonctions JavaScript partagées
  (`admActivateToast`, `admToastCloseButtonClass`) remplacent la logique
  auparavant dupliquée dans l'écouteur `htmx:afterRequest` (voir section 20
  de `docs/UI_MODERNIZATION_PROPOSAL.md`). 292 tests passés (285 + 7
  nouveaux dans `tests/test_flash_messages_as_toasts.py`), couverture
  87,55 % maintenue, aucune route Flask modifiée. Phase 6 optionnelle
  (graphiques interactifs) réalisée le 2026-09-16 : les radars matplotlib
  (résumé d'application, moyenne de la synthèse, radar d'une application
  choisie depuis la modale de la synthèse) sont désormais aussi affichés en
  graphique interactif Chart.js 4.5.1 (vendorisé, pas de CDN ; survol d'un
  axe pour lire sa valeur exacte), sans jamais supprimer le PNG existant :
  chaque page l'affiche par défaut et ne bascule sur le graphique interactif
  qu'une fois celui-ci rendu avec succès, avec retour automatique au PNG en
  cas d'échec (Chart.js non chargé, erreur réseau sur la modale) — jamais de
  régression possible par rapport au comportement d'avant cette phase.
  `ADM.services` gagne `radar_chart_data` (mêmes catégories/scores/échelle
  que le PNG, via un calcul interne désormais partagé,
  `_radar_chart_bounds`) et `ADM.routes` une route sœur JSON,
  `/radar/<name>/data`, à côté de `/radar/<name>` (PNG, strictement
  inchangée). 304 tests passés (292 + 12 nouveaux dans
  `tests/test_radar_interactive_chart.py`), couverture 87,65 % maintenue
  (détail et écarts volontaires en section 21 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du 2026-09-16 (signalé par
  Guillaume Rumeau) : deux bugs d'affichage des radars interactifs — le
  radar de `resume.html` s'affichait bien trop grand (Chart.js dimensionne
  le `<canvas>` d'après son parent direct, une carte pleine largeur, faute
  de conteneur dédié) et la modale « Radar » de la synthèse n'affichait
  qu'un point blanc (le graphique était construit sur l'évènement
  `show.bs.modal`, déclenché avant que Bootstrap ne rende le modal visible,
  donc sur un conteneur de largeur nulle). Corrigés respectivement par une
  nouvelle classe `.radar-chart-wrapper` (largeur plafonnée, `app.css`) et
  par le déplacement du rendu vers l'évènement `shown.bs.modal` (le modal
  réellement affiché). 310 tests passés (304 + 6 nouveaux), couverture
  87,65 % maintenue (détail en section 22 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du 2026-09-16 (demandé par
  Guillaume Rumeau) : le radar PNG (matplotlib, repli sans JavaScript et
  export/impression) restait tracé et rempli dans le bleu par défaut de
  matplotlib, seule couleur du radar que la Phase 6 n'avait pas alignée sur
  le vert de marque (`#0e6b5c`) déjà utilisé par le graphique interactif
  Chart.js. Corrigé via une nouvelle constante `_RADAR_CHART_COLOR` dans
  `ADM.services`, vérifiée par un test qui intercepte directement les appels
  matplotlib (`PolarAxes.plot`/`fill`) plutôt que par un échantillonnage de
  pixels du PNG, jugé trop fragile (marge trop faible entre bleu et vert une
  fois mélangés au fond blanc). 312 tests passés (310 + 2 nouveaux),
  couverture 87,65 % maintenue (détail en section 23 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du 2026-09-16 (signalé par
  Guillaume Rumeau) : à l'ouverture du radar d'une application depuis la
  synthèse, le graphique interactif Chart.js s'agrandissait progressivement
  depuis le centre (animation de création par défaut, ~1 seconde), perçu
  comme une seconde image se superposant au PNG plutôt qu'un simple
  remplacement. Corrigé en désactivant cette animation (`animation: false`)
  dans la configuration Chart.js commune aux trois radars interactifs de
  l'application (résumé, moyenne de la synthèse, modale « Radar »), qui
  s'affichent désormais instantanément dans leur état final. 313 tests
  passés (312 + 1 nouveau), couverture 87,65 % maintenue (détail en
  section 24 de `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du
  2026-09-16 (signalé par Guillaume Rumeau) : le blanc autour du radar de
  chaque application (page résumé, modale de la synthèse) était plus
  important qu'autour du radar moyenne de la synthèse — le radar est
  plafonné à 480px sur les trois emplacements, mais ses conteneurs (carte
  pleine largeur sur le résumé, modal `modal-lg` ~800px sur la synthèse)
  étaient bien plus larges que la carte `col-md-6` du radar moyenne. Corrigé
  en resserrant ces conteneurs à une largeur proche de celle du radar
  (`resume.html` : carte replacée dans une colonne `col-md-6` ; `synthese.
  html` : modale radar passée à la taille par défaut de Bootstrap, ~500px),
  sans toucher au radar lui-même. 315 tests passés (313 + 2 nouveaux),
  couverture 87,65 % maintenue (détail en section 25 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du 2026-09-16 (signalé par
  Guillaume Rumeau, captures à l'appui : le correctif précédent n'a pas
  suffi) : le radar interactif restait nettement plus petit, avec plus de
  blanc, que le radar moyenne en PNG — cause identifiée (hypothèse de
  Guillaume Rumeau, confirmée) : `.radar-chart-wrapper` plafonnait à 480px,
  une valeur fixée sans rapport avec la taille réelle du PNG, qui dépend des
  libellés de catégorie et mesure ~620-630px avec les 7 catégories
  réellement configurées (`static/questions.json`). Remonté à 640px
  (`app.css`), une limite qui n'est plus active dans les conteneurs actuels :
  le radar interactif utilise désormais toute la largeur disponible, comme
  le PNG. 316 tests passés (315 + 1 nouveau, qui mesure le PNG produit avec
  les vraies catégories et garde le plafond au moins aussi large), couverture
  87,65 % maintenue (détail en section 26 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Correctif du 2026-09-16 (signalé par
  Guillaume Rumeau, confirmé par une vidéo déposée dans « Claude outputs » et
  analysée image par image) : la modale « Radar » de la synthèse affichait
  le PNG dès l'ouverture puis le remplaçait, quelques centaines de
  millisecondes plus tard, par le graphique interactif — un remplacement net
  perçu comme un doublon. Ce PNG-puis-remplacement, hérité de la Phase 6, ne
  servait aucun usage sans JavaScript dans cette modale précise (elle
  n'existe que via le Modal Bootstrap, déjà dépendant de JavaScript).
  Corrigé en n'affichant plus qu'un indicateur de chargement neutre pendant
  la requête JSON, puis directement la représentation finale (graphique
  interactif, ou PNG seulement en cas d'échec) — un seul radar visible à la
  fois, jamais un premier remplacé par un second. Vérifié avec un navigateur
  piloté (Playwright), succès et échec simulés. 317 tests passés (316 + 1
  nouveau), couverture 87,65 % maintenue (détail en section 27 de
  `docs/UI_MODERNIZATION_PROPOSAL.md`). Prochaine étape de développement :
  Phase 7 (validation et non-régression, à formaliser en fin de projet).

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
