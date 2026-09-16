# US4.1 — Proposition de modernisation de l'interface (design)

Date : 2026-09-16. Document de cadrage produit avant tout développement, en
réponse à l'US4.1 du backlog (« Améliorer le design / Moderniser
l'affichage », Epic 4). Aucun code n'a été modifié à ce stade : ce document
sert de base à une future session d'implémentation, phase par phase.

> **Statut (2026-09-16) : US4.1 terminée.** Les 7 phases décrites ci-dessous
> ont toutes été réalisées et validées (Phase 7, section 28 : revue des
> trois rôles sur desktop et mobile, aucune régression). US4.1 a été retirée
> de `backlog.md`, conformément à la convention de ce fichier (les tâches
> réalisées y sont retirées, pas seulement cochées) ; ce document reste
> l'historique complet du chantier (cadrage, 7 phases, correctifs) et n'est
> donc plus mis à jour au fil de nouvelles phases.

## 1. Objectif et périmètre

Moderniser l'apparence de l'application (catalogue d'applications, fiche
résumé, évaluation par questionnaire, synthèse globale, gestion des comptes,
gestion des questions, configuration des seuils, import/export,
authentification) sans rien retirer de l'existant fonctionnel, en gardant
Flask et Python côté serveur, et en gardant le rendu par templates Jinja2 :
les routes continuent de produire du HTML (ou des fragments HTML, voir Phase
4) exactement comme aujourd'hui, sans passer par une API JSON consommée par
un front séparé.

## 2. État des lieux

L'interface actuelle repose sur Bootstrap 5.3.0 chargé depuis le CDN
`jsdelivr` dans `base.html`, sans aucune feuille de style statique dédiée :
le dossier `static/` ne contient que `info_tooltip.js`, `logo.svg` et des
fichiers de données JSON. Chaque gabarit redéfinit son propre bloc
`{% block extra_head %}<style>...</style>{% endblock %}`, ce qui provoque une
duplication réelle : les couleurs des badges DICP (`badge-d1`, `badge-i2`,
etc.) et de criticité sont recopiées à l'identique dans `index.html`,
`resume.html` et implicitement dans `synthese.html` ; l'ombre de carte
`box-shadow: 0 4px 8px rgba(0,0,0,0.1)` apparaît dans au moins six gabarits.
Les icônes sont des émojis (📋 ➕ 📊 📥 ✅ ✏️ ❌ ♻️ 👤 🔑 ⚙️ ❓ 📈), dont le rendu
varie selon le système d'exploitation et le navigateur — peu adapté à un
outil de gouvernance interne. Il n'existe pas de mode sombre. Le graphique
radar (résumé d'application et synthèse) est généré côté serveur avec
`matplotlib` et injecté en image PNG encodée en base64 : simple et robuste,
mais statique (pas de survol, pas de zoom).

Il faut aussi noter que du travail de qualité a déjà été livré et qu'il ne
faut pas régresser dessus : tableaux responsives (`table-responsive`),
grille de KPI en `row-cols-*` (Tâche 4.10), popovers d'aide accessibles au
clavier via déclenchement `focus` (Tâche 4.5), barre de progression et
sommaire d'ancres sur le formulaire d'évaluation (Tâche 4.8), validation
inline des commentaires obligatoires (Tâche 4.7). Plusieurs tests
(`test_catalogue_table_responsive.py`, `test_resume_radar_responsive.py`,
`test_score_progress_indicator.py`, `test_synthese_kpi_grid.py`,
`test_help_widget.py`) vérifient très probablement des détails de structure
ou de classes CSS : toute refonte visuelle devra les faire évoluer au même
rythme que le HTML, jamais après coup, sous peine de régression silencieuse.

Enfin, le projet est aujourd'hui un pur projet Python : aucun `package.json`,
aucun outillage Node/npm/webpack, tout est chargé depuis un CDN externe. Le
backlog prévoit par ailleurs (Tâche 6.6) l'ajout d'en-têtes de sécurité HTTP,
dont une `Content-Security-Policy` — une dépendance à un CDN externe pour le
JavaScript/CSS compliquera cette tâche si elle n'est pas anticipée.

## 3. Contraintes retenues

Flask et Python restent le seul serveur d'application ; Jinja2 continue de
produire le rendu final (pages complètes aujourd'hui, éventuellement des
fragments HTML en Phase 4, jamais du JSON consommé par un front séparé) ;
aucune fonctionnalité actuelle n'est supprimée ni masquée, y compris les cas
liés aux rôles (`admin`, `readonly`) déjà gérés côté serveur ; le résultat
doit rester compatible avec le déploiement conteneurisé documenté
(Docker/Kubernetes) et faciliter, plutôt que compliquer, la Tâche 6.6 du
backlog (en-têtes de sécurité).

## 4. Choix d'architecture front proposés

**Option recommandée — Bootstrap 5 modernisé, auto-hébergé, complété par
htmx et Alpine.js.** Bootstrap est déjà utilisé intensivement (navigation,
modales de confirmation, popovers, formulaires) ; une bascule vers un autre
framework CSS obligerait à réécrire la totalité des gabarits et à
réimplémenter des comportements aujourd'hui gratuits (modales, popovers,
tooltips), avec un risque de régression élevé sur des points d'accessibilité
et de responsive déjà réglés avec soin. Bootstrap 5.3 apporte nativement des
variables CSS et un mode sombre (`data-bs-theme`), ce qui permet une
modernisation visible à moindre coût. `htmx` permet de rendre certaines
actions plus fluides (suppression, filtres, pagination future) sans jamais
quitter le rendu serveur par templates Jinja : c'est la définition même du
« garder la logique de template » — le serveur continue de renvoyer du HTML,
seulement un fragment plutôt que la page entière. `Alpine.js` (quelques Ko,
sans étape de build) suffit pour les petites interactions purement
visuelles (menu mobile, bascule de thème). Ni l'un ni l'autre n'exige
d'outillage Node : les deux se chargent comme de simples fichiers statiques,
au même titre que Bootstrap.

**Alternative envisagée — migration vers Tailwind CSS** (éventuellement
complété par des composants type DaisyUI). Avantages : liberté de design
totale, esthétique très contemporaine, CSS finement optimisé après purge.
Inconvénients, à mettre en balance : réécriture des classes de tous les
gabarits sans exception, perte des widgets JavaScript fournis gratuitement
par Bootstrap (modales, popovers, tooltips — à réimplémenter avec Alpine.js
ou une autre librairie), et nécessité d'un pipeline de build (Tailwind CLI
ou PostCSS, donc une dépendance Node ajoutée à un projet aujourd'hui 100 %
Python) puisque le CDN « Play » de Tailwind est explicitement déconseillé en
production (pas de purge, temps de génération à chaque page, empreinte trop
lourde). Cette option est gardée en réserve : à réévaluer après la Phase 1
si l'ambition visuelle du Bootstrap modernisé s'avère insuffisante, mais ce
n'est pas le chemin recommandé pour un premier incrément, compte tenu du
rapport effort/risque.

**Option écartée — réécriture en SPA (React/Vue) consommant une API JSON.**
Contredit directement la contrainte « garder la logique de template » (Jinja
ne produirait plus la page) et démultiplierait l'effort : API à construire,
authentification par session à repenser, chaîne de build front complète à
introduire dans un projet qui n'a aujourd'hui aucune dépendance JavaScript
significative.

## 5. Design system proposé

Une palette de couleurs formalisée en variables CSS Bootstrap (`--bs-primary`
et équivalents), pour ne plus redéfinir la couleur de marque en dur à chaque
page. Couleur de marque validée en Phase 0 (voir section 9) : un vert forêt
légèrement foncé (`#0e6b5c`, variante appuyée `#0a4d42`) à la place du bleu
Bootstrap par défaut, volontairement distinct du vert sémantique des badges
DICP et de criticité (`#198754`, plus vif) pour ne jamais confondre couleur
de marque et code couleur fonctionnel. Les teintes sémantiques elles-mêmes
restent celles déjà choisies pour les badges DICP et de criticité
(vert/jaune/orange/rouge), mais déclarées une seule fois. Une typographie
web moderne (par exemple *Inter*), auto-hébergée dans
`static/` plutôt qu'appelée depuis Google Fonts, pour rester cohérente avec
la future CSP et fonctionner en environnement fermé. Une iconographie
Bootstrap Icons en remplacement des émojis partout où ils servent d'action
ou de statut (`<i class="bi bi-plus-lg">` plutôt que `➕`), les libellés
textuels et attributs `aria-label` déjà présents étant conservés à
l'identique pour ne rien perdre côté accessibilité. Un espacement, des
rayons de bordure et des ombres unifiés dans une seule feuille
`static/css/app.css`, qui remplace les blocs `<style>` dupliqués. Un mode
sombre natif Bootstrap 5.3, activable et mémorisé côté client sans aller-
retour serveur. Et un réexamen visuel — pas fonctionnel — des composants
clés : en-tête de navigation (plus compact, sticky), tableau du catalogue
(badges harmonisés, actions regroupées), formulaire d'évaluation (la
progression et le sommaire d'ancres, déjà solides, sont conservés et
seulement habillés), cartes de synthèse et KPI, graphiques radar (rendu
matplotlib conservé comme référence pour ce premier incrément — voir Phase 6
optionnelle pour une version interactive).

## 6. Plan d'action détaillé

**Phase 0 — Cadrage visuel (0,5 à 1 jour, sans code). Réalisée et validée le
2026-09-16 par Guillaume Rumeau.** Quatre pages HTML statiques (sommaire,
catalogue, formulaire d'évaluation, synthèse), clair et sombre, dans
`mockups/` (voir section 9 pour le détail et les deux ajustements retenus
avant de passer en Phase 1).

**Phase 1 — Fondations du design system (2 à 3 jours). Réalisée le
2026-09-16 ; en attente de revue/merge côté utilisateur (voir section 10).**
Créé `src/ADM/resources/static/css/app.css` regroupant les tokens de
couleur, les styles de badges, cartes, tableaux, navigation et pied de page
auparavant dupliqués ou inlinés. Supprimé les blocs `<style>` redondants de
`base.html`, `index.html`, `resume.html`, `synthese.html`, `score.html`,
`add.html`, `edit.html`, `accounts.html`, `questions_settings.html`,
`settings.html` et `question_form.html` au profit de classes communes.
Auto-hébergé (« vendorisé ») Bootstrap 5.3.3 CSS/JS et Bootstrap Icons 1.11.3
dans `static/vendor/` à la place du CDN `jsdelivr` précédent, en préparation
de la CSP stricte de la Tâche 6.6 et pour un fonctionnement sans dépendance
réseau externe. Remplacé les émojis par des icônes Bootstrap Icons partout où
ils servaient d'action ou de statut. Fichiers impactés : `base.html` et
l'ensemble des gabarits cités, plus l'arborescence `static/`. Détail complet
en section 10.

**Phase 2 — Refonte visuelle des pages principales (3 à 4 jours).**
Appliquer le nouveau design system aux pages les plus consultées :
`index.html` (navigation resserrée, badges harmonisés, actions regroupées
dans un menu contextuel plutôt que quatre boutons côte à côte, tri/recherche
instantanés en JavaScript pur côté client sur les données déjà rendues par
Jinja, sans toucher aux routes), `resume.html` (sections plus aérées) et
`synthese.html` (cartes KPI et tableau redessinés avec les nouvelles
couleurs sémantiques).

**Phase 3 — Formulaires et pages secondaires (2 à 3 jours). Réalisée le
2026-09-16 (voir section 14).** Étendre le design system à `score.html` (en
conservant impérativement la barre de progression, le sommaire d'ancres et
la validation des commentaires obligatoires, uniquement réhabillés),
`add.html`, `edit.html`, `login.html`, `accounts.html`,
`questions_settings.html`, `question_form.html`, `settings.html`,
`change_password.html`, `import_data.html` et `error.html`. Labels flottants
Bootstrap pour les formulaires courts, popovers d'aide contextuelle
conservés à l'identique fonctionnellement.

**Phase 4 — Interactivité progressive avec htmx et Alpine.js (3 à 5
jours). Réalisée le 2026-09-16 (voir section 16).** Faire gagner en fluidité
les actions qui rechargent aujourd'hui toute la page, sans changer le
contrat des routes existantes : suppression et réinitialisation d'une
application confirmées en modale puis appliquées via une requête htmx qui
ne rafraîchit que la ligne concernée ; filtres de la synthèse
(`?filter_score=...`, déjà gérés côté serveur) déclenchés en htmx pour ne
rafraîchir que le tableau et les KPI ; messages flash remplacés par des
toasts Bootstrap après une action htmx ; menu mobile et bascule de thème
gérés en Alpine.js. Concrètement, les routes concernées apprennent à
renvoyer un fragment de template quand la requête porte l'en-tête htmx, et
continuent de renvoyer la page complète sinon — une évolution additive et
rétrocompatible, pas une réécriture. C'est la phase la plus proche d'un
changement d'approche front évoqué en préambule, tout en respectant
strictement Flask/Python et le rendu par templates.

**Phase 5 — Mode sombre, accessibilité et finitions (1 à 2 jours). Réalisée
le 2026-09-16 (voir section 18).** Finaliser la bascule de thème (persistée
en `localStorage`, avec `prefers-color-scheme` comme valeur par défaut),
auditer les contrastes du nouveau design, l'ordre de tabulation et les
libellés ARIA, et corriger les derniers écarts visuels entre pages.

**Phase 6 — Graphiques interactifs (optionnelle, 2 à 3 jours, à arbitrer
séparément).** Remplacer les images radar statiques par un graphique
interactif (Chart.js, vendorisé, sans CDN) affichant les mêmes données.
Cette phase est isolée des précédentes car elle touche `ADM.services` et les
routes concernées pour exposer les scores en JSON en plus du PNG actuel :
c'est une évolution plus proche du fonctionnel que du seul habillage, à ne
lancer qu'après validation des phases 1 à 5.

**Phase 7 — Validation et non-régression (en continu, 1 jour dédié en fin
de projet).** `pytest --cov=ADM` (seuil 86 % à maintenir), `ruff check`,
`ruff format --check` et `mypy --strict` après chaque phase, pas seulement à
la fin. Revue manuelle de chaque rôle (`admin`, `readonly`, utilisateur
standard) sur desktop et mobile, avec captures d'écran avant/après comme
preuve de non-régression fonctionnelle.

## 7. Estimation globale

Environ 14 à 21 jours-homme selon que la Phase 6 optionnelle est retenue.
Chaque phase est livrable et testable indépendamment : un déploiement
progressif est possible, sans « big bang ».

## 8. Lien avec le backlog existant

US4.1 (Epic 4) est directement couverte par ce plan. La Tâche 4.9 (gestion
des catégories de questions) reste indépendante et peut être traitée avant,
pendant ou après cette refonte sans conflit de fichiers majeur. La Tâche 6.6
(en-têtes de sécurité HTTP, CSP) est facilitée par le vendoring des assets
prévu en Phase 1 : une CSP stricte devient réalisable sans exception pour un
CDN externe. La Tâche 3.6 (pagination des listes) gagnerait à être
développée en même temps que la Phase 4 (htmx), les deux se combinant
naturellement.

## 9. Suivi — Phase 0 validée

Document validé par Guillaume Rumeau le 2026-09-16. Les maquettes de la
Phase 0 sont dans `mockups/` (`index.html` en sommaire, `catalogue.html`,
`evaluation.html`, `synthese.html`, `README.md`, `assets/mockup.css`) et
n'ont entraîné aucune modification du code de l'application. Deux
ajustements y ont été décidés par rapport à la proposition initiale, à
reprendre tels quels en Phase 1 :

- **Couleur de marque** : vert forêt légèrement foncé (`#0e6b5c`, variante
  appuyée `#0a4d42`, variante claire `#3ddbb4` pour le mode sombre et les
  accents type barre de progression) à la place du bleu Bootstrap par
  défaut évoqué en section 5 de la version initiale de ce document. Choisi
  volontairement distinct du vert sémantique des badges DICP/criticité
  (`#198754`) pour ne pas mélanger couleur de marque et code couleur
  fonctionnel. `mockups/assets/mockup.css` implémente ce retint par-dessus
  Bootstrap (variables `--bs-primary`/`--bs-link-color` côté racine,
  surcharge explicite de `.btn-primary`/`.btn-outline-primary` qui ne sont
  pas pilotés par ces variables dans Bootstrap 5.3) : cette approche, pas
  seulement les valeurs de couleur, est directement réutilisable pour
  `static/css/app.css` en Phase 1.
- **Actions du catalogue** : les quatre boutons d'action par ligne
  (Évaluer/Modifier/Réinitialiser/Supprimer) sont regroupés dans un menu
  contextuel unique (icône « ⋯ »), comme déjà envisagé en section 6 (Phase
  2) mais avancé dès la maquette après un premier essai en boutons empilés
  jugé peu lisible.

Aucune autre remarque sur les pages ou le contenu : la direction visuelle
(cartes, tableaux, badges, mode sombre, typographie, iconographie Bootstrap
Icons) est validée telle quelle.

## 10. Suivi — Phase 1 réalisée

Implémentée le 2026-09-16 depuis une session cloud liée au poste de
Guillaume Rumeau (pas d'accès `git`/shell sur ce poste depuis cette session :
voir « Ce qui reste à faire côté utilisateur » ci-dessous).

**Ce qui a été fait.** `src/ADM/resources/static/css/app.css` regroupe
désormais : les tokens de couleur (`--adm-*`) et le retint des variables
Bootstrap natives (`--bs-primary` et équivalents) repris tels quels de
`mockups/assets/mockup.css`, avec la même palette validée en Phase 0 ; la
surcharge explicite de `.btn-primary`/`.btn-outline-primary`/`:focus` (non
pilotés par `--bs-primary` dans Bootstrap 5.3) ; et tous les styles
auparavant dupliqués par gabarit (badges DICP/criticité, cartes, tableaux,
flèches de tendance, formulaire d'évaluation, ligne d'option du formulaire de
question, aide contextuelle/popover, mise en page globale de `base.html`) —
**sous les noms de classes réels de l'application** (`badge-d1`, `.info-icon`,
`.eval-actions`, etc.), et non ceux, renommés, de la maquette
(`.badge-dicp-1`, `.info-icon-adm`…), pour ne rien casser côté gabarits ou
tests. Bootstrap 5.3.3 et Bootstrap Icons 1.11.3 sont vendorisés dans
`static/vendor/` (CSS/JS minifiés + police d'icônes) et remplacent le CDN
`jsdelivr` dans `base.html`. Les émojis ont été remplacés par des icônes
Bootstrap Icons (`<i class="bi bi-...">`, `aria-hidden="true"`) dans tous les
gabarits qui en contenaient encore.

**Écarts volontaires par rapport à une reprise à l'identique de la
maquette**, documentés ici pour la revue :
- La refonte visuelle des gabarits (nouvelles classes `.card-adm`,
  `.table-adm`, `.kpi-card`, menu d'actions `⋯` du catalogue, etc.) n'a
  **pas** été reprise : elle est explicitement prévue en Phase 2. Cette
  Phase 1 ne change ni la structure HTML des pages ni les classes testées,
  seulement l'origine et la couleur du CSS, conformément à son objectif
  (« fondations », pas « refonte »).
- La règle `h3 { background-color: ...; }` de `score.html` (bannière bleue
  appliquée à tout `<h3>` de la page) a été reprise sous la forme scopée
  `.card h3`, pour ne pas déteindre globalement sur les `<h3>` d'autres pages
  qui n'avaient jamais cette bannière (`synthese.html`, notamment). Elle
  s'applique par ailleurs, en plus, au titre de catégorie de
  `_evaluation_readonly.html` (inclus dans la modale de comparaison de
  `resume.html`), qui vit lui aussi dans une `.card` : c'est un gain de
  cohérence visuelle, pas une régression.
- La règle `button { margin-top: 15px; }` de `score.html`, générique et non
  scopée, n'a **pas** été reprise telle quelle : appliquée globalement via
  `app.css`, elle aurait décalé tout bouton de toutes les pages (y compris le
  bouton « afficher/masquer » du menu de navigation de `base.html`). Les
  boutons concernés disposent déjà d'un espacement suffisant via les
  utilitaires Bootstrap (`mt-2`, `w-100`, `gap-2`) présents dans le HTML.
- `.card { margin-bottom: 1rem; }` a été rendu global (auparavant présent
  uniquement dans le `<style>` de `resume.html`) : cela ajoute un espacement
  vertical cohérent aux cartes des autres pages, qui n'avaient cette marge
  qu'à cause d'une incohérence préexistante entre gabarits.
- Deux tests qui vérifiaient jusqu'ici le texte brut d'un bloc `<style>`
  déplacé vers `app.css` ont été adaptés pour lire ce nouveau fichier
  (`tests/test_help_widget.py` : largeur du `.popover` ; et
  `tests/test_score_progress_indicator.py` : `position: sticky` de
  `.eval-actions`, nouvelle constante `STATIC`). Dans les deux cas, la même
  garantie comportementale est vérifiée, seulement à son nouvel
  emplacement — aucune assertion n'a été affaiblie ou supprimée.
- `pyproject.toml` (`[tool.setuptools.package-data]`) est passé de
  `resources/static/*` (non récursif) à `resources/static/**`, pour inclure
  les nouveaux sous-répertoires `static/css/` et `static/vendor/` dans le
  paquet distribué.

**Vérifications effectuées** (environnement cloud isolé, dépôt complet
copié) : `ruff check`, `ruff format --check` et `mypy --strict` (`src`,
`main.py`) sans erreur ; `pytest --cov=ADM` : 275 tests passés, couverture
87,81 % (seuil 86 % maintenu), pour un résultat rigoureusement identique à
la mesure de référence avant modification. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) sont un problème de
fins de ligne CRLF propre au checkout Windows de ce poste, préexistant et
sans rapport avec cette Phase 1 — non traités ici, hors périmètre.

**Ce qui reste à faire côté utilisateur.** Cette session cloud n'a pas accès
à `git`/un shell sur ce poste : les fichiers ont été déposés directement dans
l'arborescence locale (`C:\usr\ADM`) via la liaison au poste, mais aucune
branche ni commit n'a été créé. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase1-design-system`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés.
2. Relire le diff, en particulier les gabarits (suppression des `<style>`,
   remplacement des émojis) et `static/css/app.css`.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) sur quelques
   pages clés (catalogue, évaluation, synthèse, comptes) pour un contrôle
   visuel rapide — cette Phase 1 ne change pas la mise en page, seulement les
   couleurs et l'origine du CSS/des icônes.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 12. Suivi — Phase 2 réalisée

Implémentée le 2026-09-16, depuis la même session cloud liée au poste de
Guillaume Rumeau (toujours pas d'accès `git`/shell sur ce poste depuis cette
session : voir « Ce qui reste à faire côté utilisateur » ci-dessous).

**Ce qui a été fait.** `index.html` : en-tête de page restructuré en ligne
flex (titre + sous-titre avec le nombre d'applications), ajout d'un champ de
recherche instantanée (`#catalogueSearch`) et de colonnes triables
(`data-sort-col`/`data-sort-type`, icône `bi-arrow-down-up`), le tout géré en
JavaScript pur côté client sur les lignes déjà rendues par Jinja (aucune
route modifiée) ; tableau enveloppé dans une carte (`<div class="card p-2
p-md-3">`) ; les quatre boutons d'action par ligne (Évaluer/Réinitialiser/
Modifier/Supprimer) remplacés par un menu contextuel Bootstrap unique
(icône « ⋯ »), conformément à l'ajustement retenu en Phase 0 (section 9).
`resume.html` : en-tête restructuré en ligne flex, icônes ajoutées aux
titres de carte, espacements aérés (`g-4`, `mb-4`, `h-100 mb-0`) entre les
sections évaluation courante/précédente et scores par dimension.
`synthese.html` : les 5 cartes KPI reconstruites avec les nouvelles classes
`.kpi-card`/`.kpi-icon`/`.kpi-label` (dégradés sémantiques), radar et tableau
« pires scores par catégorie » enveloppés dans des cartes symétriques, et le
tableau principal des applications enveloppé dans `table-responsive` (il ne
l'était pas jusqu'ici). `base.html` : boutons de la barre de navigation
passés en taille `btn-sm`, icônes ajoutées à « Retour à l'index » et
« Déconnexion ». `static/css/app.css` complété avec les nouvelles règles
associées (bandeau de navigation sticky en dégradé, cartes KPI, en-tête de
colonne triable, badges arrondis, polish des `.card-header`/`.card-body`).

**Écarts volontaires par rapport à la maquette, documentés ici pour la
revue** :
- Le tableau du catalogue **conserve exactement** la classe
  `<table class="table table-bordered text-center">` (sans `id` ni classe
  supplémentaire sur la balise elle-même), car `tests/
  test_catalogue_table_responsive.py` vérifie cette sous-chaîne littérale.
  La maquette utilisait `.table-adm` : ce renommage n'a **pas** été repris,
  au profit d'un habillage par sélecteur de classe existant
  (`.table.table-bordered`) dans `app.css`, et le script de tri/recherche
  sélectionne la table via `document.querySelector('table.table-bordered
  .text-center')` plutôt que par un `id`, pour la même raison.
- Le menu d'actions du catalogue conserve à l'identique les quatre
  `aria-label` requis par les tests (« Évaluer l'application », etc.) ainsi
  que les attributs `data-bs-target`/`data-appname` utilisés par le script
  (non modifié) qui alimente la modale de confirmation : seule leur
  présentation change (dropdown au lieu de boutons côte à côte).
- La carte KPI « Applications > seuil critique % » de `synthese.html`
  n'utilise plus la classe `.bg-score-high` (remplacée par `.kpi-danger`) :
  vérifié par recherche dans `tests/` qu'aucun test ne dépend de cette
  classe.
- Les trois libellés KPI requis par `tests/test_synthese_kpi_grid.py`
  (« Nombre total d'applications », « Score moyen », « Risque global »), la
  structure en 5 `<div class="col">` et les classes de grille
  `row-cols-1 row-cols-sm-2 row-cols-lg-5 g-3 my-4 text-center` sont
  strictement inchangées.
- La ligne `<img src="data:image/png;base64,{{ radar_chart }}" alt="Radar
  Chart" class="img-fluid">` de `resume.html`, requise à l'identique par
  `tests/test_resume_radar_responsive.py`, n'a subi aucune modification
  (vérifié par relecture directe après édition).
- Le bouton « Radar » de `synthese.html` est passé en `btn-outline-primary`
  avec icône et libellé « Radar » (texte auparavant différent) : aucun test
  ne dépend de ce texte, vérifié par recherche.

**Vérifications effectuées** (même environnement cloud isolé qu'en Phase 1,
dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur — ces trois vérifications
sont d'ailleurs sans effet réel ici puisque cette phase ne touche aucun
fichier Python, seulement des gabarits et du CSS. `pytest --cov=ADM` : 275
tests passés, couverture 87,81 % (seuil 86 % maintenu), résultat strictement
identique à la Phase 1 — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec cette Phase 2.

**Ce qui reste à faire côté utilisateur.** Comme en Phase 1, cette session
cloud n'a pas accès à `git`/un shell sur ce poste : les 5 fichiers modifiés
(`static/css/app.css`, `templates/base.html`, `templates/index.html`,
`templates/resume.html`, `templates/synthese.html`) ont été déposés
directement dans `C:\usr\ADM` via la liaison au poste, sans branche ni
commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase2-refonte-pages`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés
   (les 5 ci-dessus, aucun autre).
2. Relire le diff, en particulier le nouveau menu d'actions du catalogue et
   le script de tri/recherche dans `index.html`.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) sur le
   catalogue, une fiche résumé et la synthèse, avec un test manuel du tri et
   de la recherche instantanée sur le catalogue.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 14. Suivi — Phase 3 réalisée

Implémentée le 2026-09-16, depuis la même session cloud liée au poste de
Guillaume Rumeau (toujours pas d'accès `git`/shell sur ce poste depuis cette
session : voir « Ce qui reste à faire côté utilisateur » ci-dessous).

**Ce qui a été fait.** `login.html` et `change_password.html` (formulaires
courts par excellence) passent en labels flottants Bootstrap
(`form-floating`) pour tous leurs champs, dans une carte centrée. `add.html`
et `edit.html` sont réorganisés en deux cartes thématiques (« Informations
générales » et « Classification de sécurité ») disposées en grille
responsive (`row g-3`), avec labels flottants sur les trois champs courts
(nom, RDA, date de première possession) ; les listes déroulantes et les
boutons d'aide contextuelle (`?`) restent des `<select>`/`<button>` Bootstrap
classiques, inchangés fonctionnellement. `score.html` reçoit un traitement
plus mesuré, conformément à la consigne de ne pas toucher au sommaire
d'ancres, à la barre de progression ni à la validation des commentaires
obligatoires : les puces du sommaire passent en pastilles arrondies
(`rounded-pill`), chaque carte de catégorie reçoit une icône dans son
bandeau de titre, et le libellé « Commentaire : » gagne un style discret
(`text-muted small`, nouvelle règle `.comment` dans `app.css`) pour mieux se
distinguer visuellement de la question elle-même. `accounts.html` voit son
tableau enveloppé dans une carte `table-responsive`, comme les autres pages
de liste depuis la Phase 2. `questions_settings.html` et `settings.html`
reçoivent des icônes Bootstrap Icons sur leurs titres de section, pour
rester cohérents avec le reste de l'application. `import_data.html` et
`error.html`, qui n'avaient jamais été touchés depuis l'introduction du
design system, passent au même gabarit que les autres pages : titre avec
icône, formulaire/contenu dans une `.card`, bloc de messages flash ajouté
sur `import_data.html` par cohérence avec le reste de l'application (ce
chemin n'est actuellement jamais emprunté par la route, qui redirige
toujours vers le catalogue en cas d'erreur, mais le bloc reste sans effet
tant que ce comportement ne change pas). `question_form.html` n'a pas été
modifié : sa structure (labels Bootstrap classiques, `textarea`, cases à
cocher `form-check-inline`) était déjà conforme au design system depuis son
introduction, sans nécessiter de réhabillage supplémentaire.

**Écarts volontaires par rapport au plan initial, documentés ici pour la
revue** :
- Le bouton d'aide contextuelle conserve strictement le préfixe
  `<button type="button" class="info-icon"` sur `add.html`, `edit.html` et
  `score.html`, requis à l'identique par
  `tests/test_help_widget.py::test_help_icons_render_as_accessible_popover_buttons` :
  aucun attribut n'a été inséré entre `type="button"` et `class="info-icon"`.
- Le sommaire d'ancres, la barre de progression (`id="evaluationProgressBar"`,
  `role="progressbar"`) et l'indicateur « X/Y questions répondues » de
  `score.html` sont strictement inchangés, de même que l'attribut littéral
  `id="category-{{ loop.index }}"` requis par
  `tests/test_score_progress_indicator.py` ; seule la classe
  `rounded-pill` (utilitaire Bootstrap natif, pas une nouvelle règle CSS) a
  été ajoutée aux liens du sommaire.
- Le formulaire de suppression de compte (`accounts.html`) conserve
  exactement `onsubmit="return confirm('Supprimer définitivement ce compte
  ?');"`, vérifié par
  `tests/test_routes_accounts.py` (le message de confirmation n'interpole
  jamais le nom du compte, donc le test qui vérifie l'absence du nom
  d'utilisateur dans cet attribut continue de passer).
- Les attributs `name="..."` de tous les champs de formulaire (`category`,
  `key`, `option_value`, `score_warning`, etc., vérifiés par
  `tests/test_routes_questions.py` et `tests/test_routes_settings.py`) et le
  marqueur `name="csrf_token" value="` (utilisé par l'extracteur de jeton CSRF
  de `tests/test_routes_auth.py`) sont strictement inchangés ; seule leur
  présentation (regroupement en cartes, labels flottants) a changé.

**Vérifications effectuées** (même environnement cloud isolé qu'aux Phases 1
et 2, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 275
tests passés, couverture 87,81 % (seuil 86 % maintenu), résultat strictement
identique aux Phases 1 et 2 — aucune régression introduite. Les 7 échecs
restants (`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le
même problème de fins de ligne CRLF préexistant, sans rapport avec cette
Phase 3.

**Ce qui reste à faire côté utilisateur.** Comme aux Phases 1 et 2, cette
session cloud n'a pas accès à `git`/un shell sur ce poste : les 11 fichiers
modifiés (`static/css/app.css`, `templates/login.html`,
`templates/change_password.html`, `templates/add.html`,
`templates/edit.html`, `templates/accounts.html`,
`templates/questions_settings.html`, `templates/settings.html`,
`templates/import_data.html`, `templates/error.html`, `templates/score.html`)
ont été déposés directement dans `C:\usr\ADM` via la liaison au poste, sans
branche ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase3-formulaires`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés
   (les 11 ci-dessus, aucun autre — `question_form.html` n'a pas été
   modifié).
2. Relire le diff, en particulier `add.html`/`edit.html` (réorganisation en
   deux cartes) et les nouveaux labels flottants.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) sur la
   connexion, l'ajout/modification d'une application, l'évaluation, les
   comptes, la configuration et l'import de données.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 16. Suivi — Phase 4 réalisée

Implémentée le 2026-09-16, depuis la même session cloud liée au poste de
Guillaume Rumeau (toujours pas d'accès `git`/shell sur ce poste depuis cette
session : voir « Ce qui reste à faire côté utilisateur » ci-dessous). C'est
la première phase qui modifie `ADM.routes` lui-même, et non plus seulement
les gabarits/CSS.

**Ce qui a été fait.** htmx 2.0.10 et Alpine.js 3.17.3 sont vendorisés dans
`static/vendor/htmx/htmx.min.js` et `static/vendor/alpinejs/alpine.min.js`
(builds `dist/htmx.min.js` et `dist/cdn.min.js`, choisis pour rester sur des
scripts globaux sans étape de build, dans le même esprit que Bootstrap en
Phase 1 — htmx 4.x, ESM uniquement, et le build modulaire d'Alpine,
qui exige un appel manuel à `Alpine.start()`, ont été volontairement
écartés). Le tableau du catalogue (`index.html`) voit sa ligne factorisée
dans un nouveau partiel `_application_row.html`, réutilisé à la fois par la
boucle complète et par la réponse fragment de `/reset/<name>` : chaque ligne
reçoit un identifiant stable `app-row-{{ loop.index }}`, porté aussi par les
boutons de suppression/réinitialisation du menu d'actions (`data-row-id`).
Comme les modales de confirmation Bootstrap sont uniques et partagées (hors
du tableau), le JavaScript de `index.html` lit ce `data-row-id` à
l'ouverture de la modale (`show.bs.modal`) pour poser dynamiquement
`hx-post`/`hx-target`/`hx-swap` sur le formulaire de confirmation puis
appeler `htmx.process(form)` (nécessaire car ces attributs n'existent pas au
chargement initial de la page). Pour la réinitialisation, le `row_id`
courant est en plus recopié dans un champ caché du formulaire afin que le
serveur puisse le renvoyer tel quel dans l'`id` du fragment produit, et que
htmx retrouve la bonne ligne même après plusieurs réinitialisations
successives. Côté serveur, `ADM.routes` gagne deux petits utilitaires
(`is_htmx_request`, qui teste l'en-tête `HX-Request`, et
`hx_trigger_toast_header`, qui construit l'en-tête `HX-Trigger` au format
JSON attendu par le script d'écoute côté client) : `delete_application`
renvoie, pour une requête htmx, un corps vide avec cet en-tête (la ligne est
alors retirée du tableau par `hx-swap="outerHTML"` sur une réponse vide) ;
`reset_evaluation` renvoie le fragment `_application_row.html` de la ligne
mise à jour, sans appeler `flash()` dans cette branche (pour éviter qu'un
message Flask reste en attente et s'affiche à tort lors d'une navigation
complète ultérieure) ; les deux routes conservent strictement leur
comportement `redirect()`/`flash()` d'origine pour toute requête non-htmx
(vérifié explicitement, voir Vérifications ci-dessous). La synthèse
(`synthese.html`) voit son bloc filtres + tableau factorisé dans
`_synthese_results.html`, encapsulé dans `<div id="syntheseResults">` :
cliquer sur un filtre (`?filter_score=...`) déclenche un `hx-get` qui ne
remplace que ce bloc (`hx-push-url="true"` conserve une URL
partageable/rechargeable), sans régénérer le graphique radar. Un toast
Bootstrap générique est ajouté dans `base.html` : un script écoute
l'évènement `htmx:afterRequest`, relit lui-même l'en-tête `HX-Trigger` de la
réponse (plutôt que de s'appuyer sur le déclenchement d'évènement intégré de
htmx, pour rester indépendant de ses détails de version) et affiche un
`bootstrap.Toast` dont le texte est posé via `textContent` (jamais
`innerHTML`, le nom d'application inclus dans le message venant de données
utilisateur). Enfin, `base.html` reçoit un bouton de bascule de thème géré en
Alpine.js (`x-data`/`x-on:click`/`:class`, avec persistance dans
`localStorage`), précédé d'un script synchrone dans `<head>` qui applique le
thème choisi (ou `prefers-color-scheme` à défaut) avant le premier rendu
pour éviter tout flash de thème incorrect (FOUC) — ce script est
indépendant d'Alpine.js, chargé plus tard avec `defer`, et ne gère que
l'application initiale du thème, pas sa bascule interactive.

**Écarts volontaires par rapport au plan initial, documentés ici pour la
revue** :
- Les 5 cartes KPI de `synthese.html` ne sont volontairement **pas**
  intégrées au fragment `_synthese_results.html` rafraîchi par htmx, alors
  que le plan initial (section 6) mentionnait de rafraîchir « le tableau et
  les KPI ». En y regardant de plus près, `ADM.routes.synthese()` calcule ces
  5 valeurs (`summarize_catalogue`) à partir de la liste complète des
  applications, pas de la liste filtrée `scored_apps` : elles ne dépendent
  donc jamais de `filter_score`, et les inclure dans le fragment échangé
  n'aurait fait que retransmettre le même HTML à chaque clic de filtre, sans
  bénéfice pour l'utilisateur. Cette exclusion évite aussi de casser
  `tests/test_synthese_kpi_grid.py`, qui compte 5 occurrences littérales de
  `<div class="col">` dans `synthese.html`.
- `test_catalogue_action_buttons_have_accessible_labels`
  (`tests/test_catalogue_table_responsive.py`) a été adapté pour lire
  `_application_row.html` au lieu d'`index.html`, puisque le balisage des
  boutons d'action (et leurs `aria-label`) a été déplacé dans ce nouveau
  partiel ; les assertions elles-mêmes (mêmes 4 libellés) sont inchangées.
  Même précédent que l'adaptation de `test_help_widget.py` et
  `test_score_progress_indicator.py` en Phase 1.
- Le menu de navigation mobile (`navbar-toggler`/`collapse` Bootstrap natif)
  n'a volontairement **pas** été réécrit en Alpine.js : il fonctionnait déjà
  correctement et n'était couvert par aucun test spécifique, donc le
  réimplémenter en Alpine n'aurait fait qu'ajouter un risque de régression
  visuelle sans bénéfice fonctionnel. Seule la bascule de thème, qui
  n'existait pas encore, a été confiée à Alpine.js.
- `app.css` gagne une courte section « Interactivité htmx (Phase 4) » : des
  styles de transition (opacité pendant l'échange, fond transitoire après
  l'échange) sur les classes `htmx-swapping`/`htmx-settling`, posées
  automatiquement par htmx pendant le remplacement d'une ligne, pour un
  retour visuel discret sans JavaScript supplémentaire.

**Vérifications effectuées** (même environnement cloud isolé qu'aux Phases 1
à 3, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 275
tests passés, couverture 87,55 % (seuil 86 % maintenu), résultat conforme
aux phases précédentes — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec cette Phase 4.
En complément de la suite automatisée, un script manuel a exercé les trois
nouvelles branches `HX-Request` (`/reset/<name>`, `/delete/<name>`,
`/synthese?filter_score=...`) avec et sans l'en-tête htmx : les réponses
htmx renvoient bien un fragment/corps vide avec l'en-tête `HX-Trigger`
attendu, tandis que les requêtes sans cet en-tête conservent exactement le
`redirect()`/page complète d'origine (notamment `reset_evaluation`, dont le
comportement non-htmx est aussi couvert par
`tests/test_routes_applications.py::test_reset_receives_the_name_parameter`).

**Ce qui reste à faire côté utilisateur.** Comme aux phases précédentes,
cette session cloud n'a pas accès à `git`/un shell sur ce poste : les 10
fichiers modifiés ou créés (`src/ADM/routes.py`,
`static/css/app.css`, `templates/base.html`, `templates/index.html`,
`templates/synthese.html`, `templates/_application_row.html` (nouveau),
`templates/_synthese_results.html` (nouveau),
`static/vendor/htmx/htmx.min.js` (nouveau),
`static/vendor/alpinejs/alpine.min.js` (nouveau),
`tests/test_catalogue_table_responsive.py`) ont été déposés directement dans
`C:\usr\ADM` via la liaison au poste, sans branche ni commit créés. Reste
donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase4-htmx-alpine`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés/
   créés (les 10 ci-dessus, aucun autre).
2. Relire le diff, en particulier `ADM/routes.py` (nouvelles branches
   `HX-Request` dans `delete_application`, `reset_evaluation` et
   `synthese`) et les nouveaux partiels de gabarits.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) et vérifier à
   la souris : suppression et réinitialisation d'une application depuis le
   catalogue (la ligne doit disparaître/se mettre à jour sans rechargement
   de page, avec un toast de confirmation), changement de filtre sur la page
   de synthèse (le tableau se met à jour sans rechargement, l'URL change),
   bascule du thème clair/sombre (persistée après rafraîchissement de la
   page), et menu mobile sur un écran étroit.
5. Vérifier qu'aucun message d'erreur JavaScript n'apparaît dans la console
   du navigateur pendant ces actions.
6. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 18. Suivi — Phase 5 réalisée

Implémentée le 2026-09-16, depuis la même session cloud liée au poste de
Guillaume Rumeau (toujours pas d'accès `git`/shell sur ce poste depuis cette
session : voir « Ce qui reste à faire côté utilisateur » ci-dessous).

**Ce qui a été fait.** La bascule de thème clair/sombre elle-même (script
anti-FOUC, bouton Alpine.js, persistance `localStorage` avec
`prefers-color-scheme` en valeur par défaut) avait déjà été construite en
Phase 4 : cette phase a porté sur l'audit annoncé (contrastes, tabulation,
libellés ARIA) et sur les écarts qu'il a révélés.

*Audit de contraste.* Les badges affichés sur fond jaune (`--adm-warning`)
ou orange (`--adm-orange`) — badges DICP/criticité personnalisés
(`.badge-d2`, `.badge-criticite2`, etc., définis dans `app.css`) et badges de
score/risque calculés à l'exécution (`_application_row.html`,
`_synthese_results.html`, `resume.html`, `synthese.html`) — utilisaient tous
le texte blanc par défaut de `.badge` (Bootstrap), avec un contraste mesuré
d'environ 1,6:1 (jaune) et 2,6:1 (orange), très en-dessous du minimum WCAG AA
de 4,5:1 (les badges sur fond vert/rouge, eux, passaient de justesse, environ
4,5:1). Corrigé de deux façons complémentaires : les badges de score/risque,
qui utilisaient les utilitaires Bootstrap `bg-danger`/`bg-warning`/
`bg-success` (lesquels ne fixent pas de couleur de texte), sont passés aux
utilitaires `text-bg-*` équivalents, qui pairent automatiquement la bonne
couleur de texte (noir pour `text-bg-warning`, déjà blanc et donc inchangé
pour `text-bg-danger`/`text-bg-success`) ; les badges DICP/criticité
personnalisés reçoivent un nouveau jeton `--adm-badge-text-dark` (`#3a2a00`,
la même teinte que le texte déjà utilisé sur la carte KPI jaune) comme
couleur de texte explicite sur fond jaune/orange, portant le contraste à
environ 8,5:1 et 5,4:1 respectivement. Par cohérence, les badges `bg-success`/
`bg-secondary` sans problème de contraste (`accounts.html`,
`questions_settings.html`) sont eux aussi passés à `text-bg-*` (aucun
changement visuel, juste le bon idiome Bootstrap).

*Libellés accessibles.* Les deux boutons d'action de `resume.html`
(modifier/évaluer) n'étaient identifiés que par un `title` (infobulle
Bootstrap) : un `aria-label` reprenant le même texte a été ajouté, à
l'identique des libellés déjà utilisés pour les mêmes actions dans
`_application_row.html`. Le modal de réinitialisation de mot de passe
d'`accounts.html` (un par compte, `id="resetPasswordModal-{{ loop.index }}"`)
n'avait pas d'`aria-labelledby` ni d'`id` sur son titre, contrairement à tous
les autres modaux de l'application : corrigé à l'identique du patron déjà en
place ailleurs (`id="resetPasswordModalLabel-{{ loop.index }}"` posé sur le
titre et référencé par le modal).

*Tabulation.* Aucun `tabindex` positif n'a été trouvé dans l'application (les
seuls `tabindex` présents sont les `tabindex="-1"` standards des modaux
Bootstrap) : l'ordre de tabulation suit l'ordre du DOM partout, aucune
correction n'était nécessaire sur ce point.

*Finition visuelle liée au mode sombre.* Les graphiques radar
(`resume.html`, `synthese.html`) sont des images PNG rendues côté serveur
par matplotlib, toujours sur fond blanc (rendu conservé tel quel, voir Phase
6 optionnelle pour une version interactive) : en thème sombre, sans
traitement, elles flottaient en rectangle blanc brut sur la carte sombre qui
les contient. Une nouvelle classe `.chart-surface` les encadre d'une plaque
blanche avec un léger espacement, pour que ce contraste paraisse voulu
plutôt que subi, en clair comme en sombre.

**Écarts volontaires par rapport au plan initial, documentés ici pour la
revue** :
- La bascule de thème et sa persistance, prévues dans le libellé de cette
  phase, avaient déjà été livrées en Phase 4 (section 16) : cette phase n'a
  donc pas eu à les reconstruire, seulement à les auditer et à corriger ce
  que l'audit a trouvé.
- `.badge-d1`/`.badge-i1`/`.badge-c1`/`.badge-p1`/`.badge-criticite4` (fond
  vert) et `.badge-d4`/`.badge-i4`/`.badge-c4`/`.badge-p4`/`.badge-criticite1`
  (fond rouge), ainsi que `.bg-score-high`, sont restés en texte blanc : leur
  contraste mesuré (~4,5:1) passe le seuil WCAG AA, de justesse mais sans
  ambiguïté ; les retoucher n'aurait apporté aucun bénéfice d'accessibilité.
- L'audit n'a pas cherché à revoir la hiérarchie des titres (`<h2>`/`<h3>`/
  `<h5>`) page par page : `.card h3` sert de bandeau visuel coloré depuis la
  Phase 1 (pas nécessairement un vrai niveau 3 de plan de page), un chantier
  de restructuration sémantique plus large que le périmètre annoncé de
  cette phase (contrastes, tabulation, libellés ARIA, finitions), à
  reconsidérer séparément si besoin.

**Vérifications effectuées** (même environnement cloud isolé qu'aux Phases 1
à 4, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 282
tests passés (275 + 7 nouveaux, `tests/test_phase5_accessibility.py`),
couverture 87,55 % (seuil 86 % maintenu), résultat conforme aux phases
précédentes — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec cette Phase 5.
Les nouveaux tests vérifient, de façon programmatique (calcul du ratio de
contraste selon la formule WCAG officielle, pas une simple présence de
règle CSS), que le texte des badges jaune/orange atteint bien 4,5:1, que les
gabarits de score/risque utilisent `text-bg-*` et non plus `bg-*` seul, que
les deux liens d'action de `resume.html` portent leur `aria-label`, et que
le modal de réinitialisation de mot de passe expose un nom accessible
correctement apparié pour chaque compte. Un test préexistant
(`test_resume_radar_responsive.py`) a été mis à jour pour refléter l'ajout
de `chart-surface` à la classe de l'image radar (même précédent que les
adaptations de tests des phases précédentes).

**Ce qui reste à faire côté utilisateur.** Comme aux phases précédentes,
cette session cloud n'a pas accès à `git`/un shell sur ce poste : les 9
fichiers modifiés ou créés (`static/css/app.css`,
`templates/_application_row.html`, `templates/_synthese_results.html`,
`templates/resume.html`, `templates/synthese.html`,
`templates/accounts.html`, `templates/questions_settings.html`,
`tests/test_resume_radar_responsive.py`,
`tests/test_phase5_accessibility.py` (nouveau)) ont été déposés directement
dans `C:\usr\ADM` via la liaison au poste, sans branche ni commit créés.
Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase5-accessibilite`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés/
   créés (les 9 ci-dessus, aucun autre).
2. Relire le diff, en particulier les nouvelles classes `text-bg-*` et
   `chart-surface`, et le nouveau fichier de tests.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) et vérifier à
   l'œil : lisibilité des badges de score/risque et de criticité sur fond
   jaune/orange, apparence des graphiques radar en thème sombre (plaque
   blanche discrète plutôt que rectangle brut), annonce du nom du modal de
   réinitialisation de mot de passe par un lecteur d'écran ou l'inspecteur
   d'accessibilité du navigateur.
5. Idéalement, passer un outil d'audit automatisé (Lighthouse, axe
   DevTools) sur les pages principales pour confirmer qu'aucune régression
   d'accessibilité n'a été introduite ailleurs.
6. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 19. Correctif — modal de confirmation resté ouvert après une action htmx

Signalé le 2026-09-16 par Guillaume Rumeau après la Phase 5, en testant les
interactions htmx introduites en Phase 4 : après confirmation d'une
suppression ou d'une réinitialisation d'évaluation depuis le catalogue, la
ligne concernée était bien mise à jour et un toast confirmait l'action, mais
le modal de confirmation restait affiché à l'écran au lieu de se refermer.

**Cause.** Avant la Phase 4, la soumission de ces formulaires provoquait un
rechargement complet de la page (`redirect()`) : le modal, absent du nouveau
DOM, disparaissait de fait, sans qu'aucun code n'ait jamais eu besoin de le
fermer explicitement. La Phase 4 a remplacé ce rechargement par une requête
htmx qui ne touche que la ligne concernée (voir section 16) : la page ne se
recharge plus, et rien ne demandait plus à Bootstrap de fermer le modal —
l'oubli n'était pas visible en revue de code, seulement à l'usage.

**Correctif.** L'écouteur `htmx:afterRequest` de `base.html` (déjà en place
pour afficher le toast à partir de l'en-tête `HX-Trigger`, voir section 16)
recherche désormais, pour toute requête htmx réussie
(`event.detail.successful`), un modal Bootstrap ancêtre de l'élément
déclencheur (`event.detail.elt.closest('.modal')`) et le referme via
l'instance `bootstrap.Modal` déjà créée par son ouverture
(`bootstrap.Modal.getInstance(modalEl).hide()`). Ce correctif est générique :
il s'applique à tout formulaire htmx placé dans un modal, actuel ou futur,
sans coder en dur les ids `confirmDeleteModal`/`confirmResetModal`, et
s'exécute avant tout `return` anticipé du traitement du toast (donc y
compris pour la suppression, dont la réponse n'a pas de corps et peut ne pas
porter de toast si l'en-tête venait à manquer).

**Vérifications effectuées** : `ruff check`, `ruff format --check` et
`mypy --strict` sans erreur ; `pytest --cov=ADM` : 285 tests passés (282 + 3
nouveaux, `tests/test_htmx_modal_dismissal.py`), couverture 87,55 % (seuil
86 % maintenu). Les nouveaux tests vérifient, sur le gabarit réellement
servi, que le correctif est bien dans l'écouteur `htmx:afterRequest`
existant (pas un second écouteur séparé, plus facile à perdre), qu'il
s'exécute avant tout retour anticipé, et que les deux formulaires concernés
sont bien des descendants d'un `.modal` (condition nécessaire à
`closest('.modal')`) — ils ne peuvent pas exécuter de JavaScript ni piloter
un vrai navigateur, donc ne remplacent pas un test manuel à l'œil.

**Ce qui reste à faire côté utilisateur.** Le seul fichier modifié
(`templates/base.html`) et le nouveau fichier de tests
(`tests/test_htmx_modal_dismissal.py`) ont été déposés dans `C:\usr\ADM` via
la liaison au poste. Vérifier à l'œil, en clair comme en sombre : supprimer
une application depuis le catalogue (modal fermé, ligne retirée, toast
affiché) et réinitialiser une évaluation (modal fermé, ligne mise à jour,
toast affiché), puis inclure ce correctif dans la même branche/revue que la
Phase 5 (ou une branche dédiée si la Phase 5 est déjà mergée).

## 20. Correctif — homogénéisation des messages informatifs

Signalé le 2026-09-16 par Guillaume Rumeau après la Phase 5 : « Il faut
homogénéiser les messages informatifs. Parfois en haut de l'écran parfois en
bas à droite. Il faut que ce soit toujours au même endroit et avec le même
format. »

**Cause.** L'application affichait ses messages informatifs de deux façons
différentes selon leur origine, un décalage hérité de la Phase 4. Les
messages flash Flask (connexion, erreurs de formulaire, actions terminées
par un rechargement complet de page) apparaissaient en haut de la page, dans
une alerte Bootstrap (`alert alert-{{ category }}`) — un bloc identique
dupliqué dans 11 gabarits (`index.html`, `add.html`, `edit.html`,
`score.html`, `login.html`, `change_password.html`, `accounts.html`,
`questions_settings.html`, `settings.html`, `import_data.html`,
`question_form.html`). Les actions déclenchées en htmx (suppression/
réinitialisation d'une application, voir section 16), elles, affichaient
depuis la Phase 4 un toast Bootstrap en bas à droite. Deux emplacements,
deux formats, pour la même notion de message informatif après une action —
la Phase 4 avait introduit le second mécanisme sans unifier le premier.

**Correctif.** Le rendu des messages flash est désormais centralisé dans
`base.html`, seul gabarit qui appelle encore `get_flashed_messages` : ils
sont rendus directement comme des toasts Bootstrap, dans le même conteneur
que les toasts htmx (`#admToastContainer`, en bas à droite) et avec
exactement le même balisage (`toast align-items-center
text-bg-<catégorie> border-0`, bouton de fermeture dont la couleur s'adapte
à la catégorie — sombre sur fond clair pour `warning`/`info`/`light`, blanc
sinon). Les 11 gabarits cités ci-dessus ont perdu leur bloc `{% with
messages = get_flashed_messages(...) %}` dupliqué (retiré via un script
Python plutôt que l'outil d'édition habituel, par prudence : plusieurs de
ces gabarits utilisent des fins de ligne CRLF, un script en octets garantit
qu'aucune n'est corrompue au passage). Deux fonctions JavaScript partagées
(`admToastCloseButtonClass`, qui choisit la couleur du bouton de fermeture
selon la catégorie, et `admActivateToast`, qui affiche le toast avec le même
délai de 5 s et le retire du DOM à sa fermeture) remplacent la logique
auparavant écrite en dur dans l'écouteur `htmx:afterRequest` : ce dernier les
appelle désormais lui aussi, pour garantir un comportement strictement
identique quelle que soit l'origine du message (rendu serveur au chargement
de la page, ou toast construit dynamiquement après une action htmx).

**Écarts volontaires par rapport à une suppression pure et simple, documentés
ici pour la revue** :
- `login.html` a reçu un petit ajustement cosmétique en plus du retrait du
  bloc de messages flash : une ligne vide a été restaurée entre le titre et
  la carte de connexion (l'ancien bloc, bien que vide la plupart du temps,
  servait aussi de séparateur visuel dans le gabarit), pour rester cohérent
  avec la mise en page des autres pages courtes.
- Les catégories de message utilisées dans `ADM.routes` restent uniquement
  `"success"`, `"danger"` et `"info"` (vérifié par recherche) : le nouveau
  rendu gère néanmoins aussi `warning`/`primary`/`secondary`/`light`/`dark`
  par cohérence avec l'ensemble des couleurs sémantiques Bootstrap
  disponibles, et retombe sur `secondary` pour toute catégorie inconnue,
  plutôt que de laisser passer une classe CSS invalide.
- Le conteneur de toasts (`#admToastContainer`) existait déjà depuis la
  Phase 4 (section 16) : cette correction ne crée ni nouveau conteneur ni
  nouvel emplacement à l'écran, elle fait converger les messages flash vers
  celui qui existait déjà pour les toasts htmx.

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 292
tests passés (285 + 7 nouveaux, `tests/test_flash_messages_as_toasts.py`),
couverture 87,55 % (seuil 86 % maintenu), résultat conforme aux phases
précédentes — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec ce correctif.
Les nouveaux tests vérifient : qu'aucun des 11 gabarits ne contient plus
d'appel à `get_flashed_messages` ni le patron `alert-{{ category }}` (garde-
fou anti-régression, sur l'ensemble des gabarits) ; qu'une erreur de
connexion s'affiche bien comme un toast (`text-bg-danger`) et non plus comme
une alerte en haut de page ; que le message de déconnexion (`text-bg-info`,
fond clair) garde un bouton de fermeture sombre tandis qu'une connexion
réussie (`text-bg-success`, fond foncé) garde un bouton blanc ; et que les
deux fonctions JavaScript partagées sont bien définies une seule fois et
appelées à la fois par la boucle d'activation des toasts flash et par
l'écouteur `htmx:afterRequest`.

**Ce qui reste à faire côté utilisateur.** Les 13 fichiers modifiés ou créés
(`templates/base.html`, `templates/accounts.html`,
`templates/questions_settings.html`, `templates/index.html`,
`templates/score.html`, `templates/import_data.html`,
`templates/settings.html`, `templates/edit.html`, `templates/add.html`,
`templates/change_password.html`, `templates/login.html`,
`templates/question_form.html`, `tests/test_flash_messages_as_toasts.py`
(nouveau)) ont été déposés directement dans `C:\usr\ADM` via la liaison au
poste, sans branche ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex.
   `fix/us4-1-homogeneisation-messages-informatifs`) et vérifier le statut
   `git` pour confirmer la liste des fichiers modifiés/créés (les 13
   ci-dessus, aucun autre).
2. Relire le diff, en particulier `base.html` (nouveau rendu des toasts
   flash et fonctions JS partagées) et les 11 gabarits dont un bloc a été
   retiré (vérifier qu'aucun contenu utile n'a disparu au passage, en
   particulier sur les fichiers CRLF).
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) et vérifier à
   l'œil que tous les messages qui apparaissaient auparavant en haut de page
   (erreur de connexion, validation de formulaire, déconnexion, changement de
   mot de passe, ajout/modification/suppression d'une question ou d'un
   compte, import de données) s'affichent désormais en bas à droite, avec le
   même format que les toasts de suppression/réinitialisation d'application
   déjà en place depuis la Phase 4.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 21. Suivi — Phase 6 réalisée (optionnelle)

Implémentée le 2026-09-16, depuis la même session cloud liée au poste de
Guillaume Rumeau (toujours pas d'accès `git`/shell sur ce poste depuis cette
session : voir « Ce qui reste à faire côté utilisateur » ci-dessous). Cette
phase optionnelle (section 6) a été retenue par Guillaume Rumeau plutôt que
la Phase 7.

**Ce qui a été fait.** Chart.js 4.5.1 est vendorisé (`static/vendor/chartjs/
chart.umd.min.js`, build UMD complet, auto-enregistré — pas de CDN, dans le
même esprit que Bootstrap/htmx/Alpine.js) : les radars matplotlib (résumé
d'une application, moyenne de la synthèse, radar d'une application choisie
depuis la modale de la synthèse) sont désormais aussi affichés sous forme de
graphique interactif (survol d'un axe pour lire sa valeur exacte), sans
supprimer le PNG existant. Conformément au plan initial (section 6),
`ADM.services` gagne une fonction `radar_chart_data`, qui produit exactement
les mêmes catégories/scores/échelle que `generate_radar_chart` (les deux
s'appuient désormais sur un même calcul interne, `_radar_chart_bounds`, pour
ne jamais pouvoir diverger), au format attendu par Chart.js
(`{labels, scores, max}`) plutôt qu'en PNG. `ADM.routes` gagne une route
`/radar/<name>/data`, sœur JSON de `/radar/<name>` (PNG, strictement
inchangée), qui alimente la modale de la synthèse ; `resume()` et
`synthese()` transmettent en plus cette même donnée à leur template
(`radar_chart_json`), puisqu'ils calculent déjà les scores d'axes pour leur
propre rendu — sans aller-retour réseau supplémentaire. Une nouvelle fonction
JavaScript partagée (`static/radar_charts.js` : `admRadarChartConfig`,
`admRenderRadarChart`, `admRenderRadarChartFromElement`,
`admShowRadarChart`) construit et affiche le graphique, avec la couleur de
marque validée en Phase 0 (`#0e6b5c`).

**Le PNG n'est jamais supprimé, conformément au plan** (« exposer les scores
en JSON... en plus du PNG actuel ») : `resume.html` et `synthese.html`
affichent le PNG par défaut et le remplacent par le canvas Chart.js
seulement une fois celui-ci rendu avec succès (`admShowRadarChart` rend
d'abord le `<canvas>` visible et masque l'image, puis tente le rendu ; en cas
d'échec — Chart.js non chargé, donnée invalide — il revient au PNG plutôt que
de laisser un graphique vide à l'écran). La modale de la synthèse suit le
même principe côté réseau : le PNG (`/radar/<name>`) est posé en premier, de
façon synchrone, puis remplacé par le graphique interactif dès que
`/radar/<name>/data` répond ; si ce second appel échoue, le PNG déjà affiché
reste en place. Dans les trois cas, le comportement ne peut donc jamais être
pire qu'avant cette phase, seulement meilleur quand Chart.js se charge
correctement.

**Écarts volontaires par rapport au plan initial, documentés ici pour la
revue** :
- Le plan (section 6) ne précisait pas si le PNG resterait affiché par
  défaut ou serait un simple repli caché : l'option retenue (PNG visible par
  défaut, canvas affiché seulement après un rendu Chart.js réussi) a été
  préférée à un `<noscript>` pur, qui n'aurait protégé que contre
  l'absence de JavaScript, pas contre un échec silencieux de Chart.js
  lui-même (script bloqué, erreur de rendu) — un risque jugé plus probable
  en pratique qu'un navigateur sans JavaScript sur cette application interne.
- Pour le résumé d'application et la moyenne de la synthèse, les données
  radar sont intégrées directement au rendu de la page (``<script
  type="application/json">``) plutôt qu'exposées via une route JSON dédiée :
  ces deux pages calculent déjà ces scores pour leur propre rendu (PNG), et
  une route séparée n'aurait fait qu'ajouter un aller-retour réseau évitable.
  Seule la modale de la synthèse (radar d'une application choisie
  dynamiquement, dont le nom n'est connu que côté client au moment du clic)
  utilise la nouvelle route `/radar/<name>/data`.
- Le cache de PNG (`RadarChartCache`, Tâche 3.7) n'a pas d'équivalent pour la
  donnée JSON : contrairement au rendu matplotlib, construire
  `{labels, scores, max}` est une opération triviale (aucun calcul
  matplotlib), sans coût à amortir.
- Les cinq cartes KPI de la synthèse ne sont toujours pas concernées par
  cette phase (déjà exclues du rafraîchissement htmx en Phase 4 pour la même
  raison : elles ne dépendent pas du filtre ni du radar).

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 304
tests passés (292 + 12 nouveaux, `tests/test_radar_interactive_chart.py`),
couverture 87,65 % (seuil 86 % maintenu), résultat conforme aux phases
précédentes — aucune régression introduite, notamment sur
`tests/test_routes_applications.py` (route PNG `/radar/<name>` strictement
inchangée) et `tests/test_resume_radar_responsive.py` (l'image PNG de
`resume.html`, avec sa classe `img-fluid chart-surface`, reste exactement la
même chaîne littérale qu'avant cette phase). Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec cette Phase 6.
Ces tests ne pouvant pas exécuter de JavaScript ni piloter un vrai
navigateur, ils vérifient la donnée exposée côté serveur et la
présence/structure du balisage et des scripts attendus, pas le rendu visuel
du graphique lui-même (survol, redimensionnement) : un contrôle manuel dans
un navigateur reste nécessaire pour ça, voir ci-dessous.

**Ce qui reste à faire côté utilisateur.** Les 7 fichiers modifiés ou créés
(`src/ADM/services.py`, `src/ADM/routes.py`, `templates/resume.html`,
`templates/synthese.html`, `static/radar_charts.js` (nouveau),
`static/vendor/chartjs/chart.umd.min.js` (nouveau),
`tests/test_radar_interactive_chart.py` (nouveau)) ont été déposés
directement dans `C:\usr\ADM` via la liaison au poste, sans branche ni commit
créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `feature/us4-1-phase6-radar-interactif`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés/
   créés (les 7 ci-dessus, aucun autre).
2. Relire le diff, en particulier la nouvelle route `/radar/<name>/data`
   dans `ADM.routes` et la factorisation `_radar_chart_bounds` dans
   `ADM.services`.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur (clair et sombre) et vérifier à
   l'œil, sur la fiche résumé d'une application évaluée et sur la synthèse :
   que le radar s'affiche bien sous forme de graphique interactif (et non
   plus l'image statique), que le survol d'un axe affiche une infobulle avec
   sa valeur exacte, que le graphique reste lisible en thème sombre (plaque
   blanche `chart-surface`, comme le PNG avant lui), et que cliquer sur
   « Radar » dans le tableau de la synthèse affiche bien le graphique
   interactif de l'application choisie dans la modale.
5. Vérifier qu'aucun message d'erreur JavaScript n'apparaît dans la console
   du navigateur pendant ces actions, et que la page reste utilisable si
   Chart.js est bloqué (couper temporairement `static/vendor/chartjs/` ou
   simuler une erreur réseau dans les outils de développement du navigateur :
   le PNG doit rester affiché).
6. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 22. Correctif — affichage des graphiques radar interactifs

Signalé le 2026-09-16 par Guillaume Rumeau après la Phase 6, deux bugs
d'affichage : (1) sur `resume.html`, le radar interactif s'affichait bien
trop grand ; (2) sur la modale de la synthèse (bouton « Radar » d'une
application), la popup s'ouvrait mais sans radar visible, seulement « un
point blanc ».

**Cause du bug 1 (radar trop grand).** Chart.js, en mode `responsive`,
dimensionne le `<canvas>` d'après la largeur de son **parent direct**, pas
d'après une éventuelle règle `max-width` posée sur le canvas lui-même
(`.chart-surface` n'y suffisait donc pas). Sur `resume.html`, ce parent est
une carte pleine largeur (contrairement à `synthese.html`, où le radar tient
dans une colonne `col-md-6` ~ deux fois plus étroite) : le graphique
s'agrandissait démesurément par rapport au PNG qu'il remplace (~600×530px,
voir `ADM.services.generate_radar_chart`).

**Cause du bug 2 (radar invisible dans la modale).** L'évènement Bootstrap
`show.bs.modal`, utilisé jusqu'ici pour déclencher le rendu Chart.js, se
déclenche **avant** que Bootstrap ne rende le modal visible à l'écran (le
fondu d'ouverture ne démarre qu'ensuite, dans `_showElement`, appelé après
`show.bs.modal`). Créer le graphique à ce moment-là revient à le dimensionner
d'après un conteneur dont la largeur affichée est nulle : Chart.js produit
alors un canvas quasi invisible, dont seul le contour blanc de
`.chart-surface` (fond blanc, léger padding) reste perceptible — exactement
le « point blanc » signalé.

**Correctifs.**
- Une nouvelle classe `.radar-chart-wrapper` (`static/css/app.css`, `max-
  width: 480px; margin: 0 auto;`) enveloppe chaque `<canvas>` de radar
  (`resume.html`, radar moyen et modale de `synthese.html`) : Chart.js mesure
  désormais ce conteneur dédié et de largeur plafonnée, plutôt que la carte
  ou le modal qui l'englobe. La configuration Chart.js (`static/
  radar_charts.js`) fixe en plus explicitement `aspectRatio: 1` (carré),
  plutôt que de dépendre du ratio par défaut de la librairie.
- Le rendu du graphique de la modale (`synthese.html`) est déplacé de
  l'écouteur `show.bs.modal` vers un nouvel écouteur `shown.bs.modal`,
  déclenché une fois le modal réellement affiché (dimensions non nulles). La
  requête réseau (`/radar/<name>/data`) démarre toujours dès `show.bs.modal`
  (pas besoin d'attendre pour l'envoyer), mais son résultat n'est exploité —
  et le graphique construit — qu'après `shown.bs.modal`, via une promesse
  intermédiaire (`pendingRadarData`).

**Écarts volontaires par rapport à une correction minimale, documentés ici
pour la revue** :
- `.radar-chart-wrapper` a été appliqué aux trois emplacements (résumé,
  radar moyen de la synthèse, modale), alors que seuls le premier et le
  troisième étaient explicitement signalés en bug : le radar moyen de la
  synthèse tient dans une colonne `col-md-6` qui reste raisonnable sur un
  écran standard, mais deviendrait lui aussi surdimensionné sur un très
  large écran — corrigé par cohérence et par prudence plutôt que d'attendre
  un troisième signalement.
- Le PNG (image, repli) n'est pas concerné par ces deux bugs ni par ces
  correctifs : il conserve sa taille intrinsèque via `img-fluid`, inchangée
  depuis la Phase 5.

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 310
tests passés (304 + 6 nouveaux dans `tests/test_radar_interactive_chart.py`),
couverture 87,65 % (seuil 86 % maintenu), résultat conforme aux phases
précédentes — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec ce correctif.
Les nouveaux tests vérifient : que `.radar-chart-wrapper` plafonne bien la
largeur (`max-width`) et enveloppe directement chacun des trois `<canvas>`
de radar ; que `aspectRatio: 1` est bien configuré ; et — pour le bug 2 —
que `admRenderRadarChart` n'est appelé que dans le gestionnaire
`shown.bs.modal`, jamais directement dans `show.bs.modal`, tandis que la
requête réseau, elle, démarre bien dès ce dernier. Comme pour la Phase 6,
ces tests ne peuvent pas exécuter de JavaScript ni piloter un vrai
navigateur : un contrôle manuel reste nécessaire pour confirmer le rendu
visuel effectif.

**Ce qui reste à faire côté utilisateur.** Les 5 fichiers modifiés
(`static/css/app.css`, `static/radar_charts.js`, `templates/resume.html`,
`templates/synthese.html`, `tests/test_radar_interactive_chart.py`) ont été
déposés directement dans `C:\usr\ADM` via la liaison au poste, sans branche
ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radars-interactifs-affichage`)
   et vérifier le statut `git` pour confirmer la liste des fichiers modifiés
   (les 5 ci-dessus, aucun autre).
2. Relire le diff, en particulier le passage de `show.bs.modal` à
   `shown.bs.modal` dans `synthese.html`.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur et vérifier à l'œil : le radar de
   `resume.html` s'affiche à une taille raisonnable (comparable au PNG
   précédent, pas plus large que la carte) ; le clic sur « Radar » d'une
   application dans la synthèse affiche bien le graphique dans la modale
   (plus de point blanc), avec un léger délai le temps du fondu d'ouverture
   du modal.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 23. Correctif — couleur du radar PNG alignée sur la couleur de marque

Demandé le 2026-09-16 par Guillaume Rumeau : « Change la couleur de
l'intérieur des radars, pour avoir un vert homogène avec le reste de
l'application. »

**Cause.** La Phase 6 avait introduit le graphique radar interactif Chart.js
en reprenant déjà la couleur de marque (vert forêt `#0e6b5c`, jeton
`--adm-primary`/`--bs-primary` validé en Phase 0, voir `ADM_RADAR_COLOR` dans
`static/radar_charts.js`), mais n'avait pas touché au PNG matplotlib
(`ADM.services.generate_radar_chart`, conservé comme repli sans JavaScript et
pour l'impression/l'export) : celui-ci restait tracé et rempli dans le bleu
par défaut de matplotlib (`color="blue"`), seule couleur du radar que la
Phase 6 n'avait pas alignée sur le reste de l'application.

**Correctif.** Une nouvelle constante `_RADAR_CHART_COLOR = "#0e6b5c"`
(`src/ADM/services.py`, juste après `MAX_OPTION_SCORE`) remplace `"blue"`
dans les deux appels matplotlib de `generate_radar_chart` (`axis.plot` et
`axis.fill`). Cette valeur est dupliquée à dessein entre Python (constante),
CSS (`--adm-primary`) et JavaScript (`ADM_RADAR_COLOR`), faute de pouvoir
partager une variable entre ces trois langages ; un nouveau test
(`tests/test_radar_interactive_chart.py`) garde les trois en phase.

**Vérification de la couleur réellement produite.** Un test par
échantillonnage de pixels du PNG a été exploré puis écarté : une fois
mélangée au fond blanc (`alpha=0.25`), la marge entre le bleu par défaut et
le vert de marque est trop faible sur les canaux RGB pour un seuil fiable et
non fragile. Le nouveau test intercepte à la place directement les appels
`PolarAxes.plot`/`PolarAxes.fill` (via `monkeypatch`) et vérifie l'argument
`color` réellement transmis à matplotlib (`"#0e6b5c"`, jamais `"blue"`) —
une vérification du comportement d'exécution, pas seulement du texte source.

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 312
tests passés (310 + 2 nouveaux dans `tests/test_radar_interactive_chart.py`),
couverture 87,65 % (seuil 86 % maintenu), résultat conforme aux phases
précédentes — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec ce correctif.

**Ce qui reste à faire côté utilisateur.** Les 2 fichiers modifiés
(`src/ADM/services.py`, `tests/test_radar_interactive_chart.py`) ont été
déposés directement dans `C:\usr\ADM` via la liaison au poste, sans branche
ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radar-couleur-verte`) et vérifier
   le statut `git` pour confirmer la liste des fichiers modifiés (les 2
   ci-dessus, aucun autre).
2. Relire le diff.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur et vérifier à l'œil que le radar
   s'affiche désormais dans un vert homogène avec le reste de l'application,
   y compris en repli PNG (par exemple en désactivant JavaScript, ou en
   observant la modale de la synthèse juste après son ouverture, avant que
   le graphique interactif ne prenne le relais).
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 24. Correctif — suppression de l'animation d'apparition du radar interactif

Signalé le 2026-09-16 par Guillaume Rumeau : sur la page synthèse, à
l'ouverture du radar d'une application (modale), « il y a une première
image, puis une seconde qui se rajoute par-dessus avec un effet de
transition (le radar s'agrandit progressivement) », jugé désagréable
visuellement — demande de ne plus afficher qu'une seule couche d'image du
radar.

**Cause.** Sans configuration explicite, Chart.js anime la création de tout
graphique (par défaut ~1 seconde, easing `easeOutQuart`) ; pour un radar,
cela se traduit par l'échelle radiale qui grandit progressivement depuis le
centre jusqu'à sa taille finale. Le PNG et le canvas ne se chevauchent
jamais réellement (l'un est masqué par `d-none` avant que l'autre ne
devienne visible, voir `admShowRadarChart`/le correctif de la section 22),
mais l'enchaînement — PNG statique affiché, puis canvas qui apparaît et dont
le contenu grandit sur une seconde — est perçu comme une seconde image qui
se superpose à la première avec un effet de zoom, plutôt que comme un simple
remplacement.

**Correctif.** Ajout de `animation: false` à la configuration Chart.js
commune (`admRadarChartConfig`, `static/radar_charts.js`), utilisée par les
trois radars interactifs de l'application (résumé, moyenne de la synthèse,
modale « Radar » d'une application). Le graphique s'affiche désormais
instantanément, dans son état final, sans transition : une seule couche
visible à la fois, comme pour le PNG qu'il remplace.

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 313
tests passés (312 + 1 nouveau dans `tests/test_radar_interactive_chart.py`,
qui vérifie la présence de `animation: false` dans `admRadarChartConfig`),
couverture 87,65 % (seuil 86 % maintenu), résultat conforme aux correctifs
précédents — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec ce correctif.
Comme pour les correctifs précédents, ce test ne peut pas exécuter de
JavaScript ni piloter un vrai navigateur : un contrôle manuel reste
nécessaire pour confirmer que l'effet visuel a bien disparu.

**Ce qui reste à faire côté utilisateur.** Les 2 fichiers modifiés
(`static/radar_charts.js`, `tests/test_radar_interactive_chart.py`) ont été
déposés directement dans `C:\usr\ADM` via la liaison au poste, sans branche
ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radar-sans-animation`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés
   (les 2 ci-dessus, aucun autre).
2. Relire le diff.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur et vérifier à l'œil, sur les
   trois emplacements (résumé d'application, moyenne de la synthèse, modale
   « Radar » d'une application depuis la synthèse), que le graphique
   interactif apparaît instantanément dans sa forme finale, sans effet de
   grossissement progressif.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 25. Correctif — réduction du blanc autour des radars par application

Signalé le 2026-09-16 par Guillaume Rumeau : sur les radars de chaque
application (page résumé, et modale « Radar » de la synthèse), « le blanc
autour du radar est plus important que sur le radar moyenne globale » —
demande d'aligner ce rendu sur celui du radar moyenne.

**Cause.** Le radar lui-même (PNG ou graphique interactif Chart.js) est
plafonné à 480px par `.radar-chart-wrapper` sur les trois emplacements
(résumé, moyenne de la synthèse, modale), voir le correctif de la
section 22. Mais le conteneur qui l'entoure diffère fortement en largeur
selon l'emplacement :
- le radar moyenne (`synthese.html`) est dans une carte `col-md-6`, une
  colonne dont la largeur (~450-560px selon la taille d'écran) est déjà
  proche des 480px du radar : peu de blanc résiduel ;
- le radar de la page résumé (`resume.html`) était dans une carte **pleine
  largeur** (`<div class="card mb-4">`, sans colonne), potentiellement bien
  plus large que 480px sur un écran large : l'écart se traduisait par un
  bandeau blanc de carte nettement plus visible autour du radar ;
- la modale « Radar » de la synthèse (`synthese.html`) utilisait
  `modal-lg` (~800px), pour la même raison en plus prononcé.

**Correctif.** Aucun changement sur `.radar-chart-wrapper` ni sur le radar
lui-même (déjà correctement dimensionné) : seuls les conteneurs qui
l'entourent sont resserrés pour se rapprocher de sa largeur, comme sur la
synthèse.
- `resume.html` : la carte « Graphique Radar » est désormais placée dans une
  colonne `col-md-6` centrée (`row g-4 mb-4 justify-content-center`), au
  lieu d'une carte pleine largeur — structure identique à celle du radar
  moyenne de la synthèse.
- `synthese.html` : la modale radar (`#radarModal`) passe de `modal-lg` à la
  taille par défaut de Bootstrap (~500px, sans classe de taille), déjà très
  proche des 480px du radar.

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 315
tests passés (313 + 2 nouveaux dans `tests/test_radar_interactive_chart.py`,
qui vérifient que la carte du radar de `resume.html` est bien dans une
colonne `col-md-6` et que la modale radar de la synthèse n'utilise plus
`modal-lg`/`modal-xl`), couverture 87,65 % (seuil 86 % maintenu), résultat
conforme aux correctifs précédents — aucune régression introduite. Les 7
échecs restants (`test_container_entrypoint.py`, `test_demo_scripts.py`)
restent le même problème de fins de ligne CRLF préexistant, sans rapport
avec ce correctif. Comme pour les correctifs précédents, ces tests
vérifient le balisage servi, pas le rendu visuel lui-même : un contrôle
manuel reste nécessaire pour confirmer que le blanc autour des trois radars
est désormais visuellement comparable.

**Ce qui reste à faire côté utilisateur.** Les 3 fichiers modifiés
(`templates/resume.html`, `templates/synthese.html`,
`tests/test_radar_interactive_chart.py`) ont été déposés directement dans
`C:\usr\ADM` via la liaison au poste, sans branche ni commit créés. Reste
donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radar-espacement`) et vérifier
   le statut `git` pour confirmer la liste des fichiers modifiés (les 3
   ci-dessus, aucun autre).
2. Relire le diff.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur et vérifier à l'œil que le blanc
   autour du radar de la page résumé et de la modale de la synthèse est
   désormais comparable à celui du radar moyenne de la synthèse.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 26. Correctif — le radar interactif restait trop petit face au PNG (limite sous-dimensionnée)

Signalé le 2026-09-16 par Guillaume Rumeau, captures d'écran à l'appui : le
correctif de la section 25 (colonnes/modal resserrés) n'a pas suffi — « il y
a trop de blanc et le radar lui-même est trop petit ». En comparant avec le
radar moyenne (affiché en PNG sur la capture), l'écart de taille était
flagrant ; hypothèse avancée, confirmée par investigation : « c'est
probablement lié aux libellés ».

**Cause, plus précise que celle de la section 25.** `.radar-chart-wrapper`
plafonnait le radar interactif à 480px — une valeur choisie lors du
correctif de la section 22 sans tenir compte de la taille réelle du PNG
qu'elle est censée égaler. Or cette taille dépend directement des libellés
de catégorie (l'hypothèse du signalement, confirmée) : avec les 7 catégories
réellement configurées dans cette instance (`static/questions.json` :
« Architecture & Intégration », « Documentation & Gouvernance », etc.), le
PNG recadré par matplotlib (`bbox_inches="tight"`) mesure environ 620-630px
de large — nettement plus que les 480px du plafond. Résultat : même une fois
les conteneurs resserrés (section 25), le radar interactif restait
visiblement plus petit que le PNG (radar moyenne), avec un excédent de blanc
correspondant à l'écart entre 480px et sa taille réelle.

**Correctif.** `.radar-chart-wrapper` passe de 480px à 640px (`app.css`) —
une valeur qui n'est plus une limite active dans les conteneurs actuels
(colonne `col-md-6`, modal de taille par défaut, tous deux plus étroits que
640px dans la quasi-totalité des résolutions d'écran) : le radar interactif
utilise désormais toute la largeur disponible de son conteneur, exactement
comme le fait déjà le PNG (`img-fluid`, qui n'a jamais eu de plafond propre).

**Vérifications effectuées** (même environnement cloud isolé qu'aux phases
précédentes, dépôt complet copié) : `ruff check`, `ruff format --check` et
`mypy --strict` (`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 316
tests passés (315 + 1 nouveau dans `tests/test_radar_interactive_chart.py`),
couverture 87,65 % (seuil 86 % maintenu), résultat conforme aux correctifs
précédents — aucune régression introduite. Les 7 échecs restants
(`test_container_entrypoint.py`, `test_demo_scripts.py`) restent le même
problème de fins de ligne CRLF préexistant, sans rapport avec ce correctif.
Le nouveau test génère le PNG avec les catégories réellement définies dans
`static/questions.json`, mesure sa largeur (Pillow) et vérifie que le
plafond de `.radar-chart-wrapper` lui reste au moins égal — garde-fou
directement dérivé du signalement, qui empêche cette régression précise (un
plafond redevenu plus petit que le PNG réel) de se reproduire silencieusement
si les catégories ou leurs libellés changent. Comme pour les correctifs
précédents, un contrôle manuel reste nécessaire pour confirmer le rendu
visuel effectif.

**Ce qui reste à faire côté utilisateur.** Les 3 fichiers modifiés
(`static/css/app.css`, `templates/resume.html`, `templates/synthese.html`,
`tests/test_radar_interactive_chart.py` — 4 au total) ont été déposés
directement dans `C:\usr\ADM` via la liaison au poste, sans branche ni
commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radar-taille`) et vérifier le
   statut `git` pour confirmer la liste des fichiers modifiés (les 4
   ci-dessus, aucun autre).
2. Relire le diff.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. Ouvrir l'application dans un navigateur et vérifier à l'œil que le radar
   de la page résumé et celui de la modale de la synthèse sont désormais
   visuellement comparables en taille (et en blanc environnant) au radar
   moyenne de la synthèse.
5. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 27. Correctif — doublon d'affichage du radar dans la modale de la synthèse

Signalé le 2026-09-16 par Guillaume Rumeau, avec deux niveaux de vérification
successifs. D'abord un doute (« il y a toujours un double affichage du
radar sur la modale ») : une instance temporaire de l'application a été
montée dans l'environnement cloud isolé et pilotée par un vrai navigateur
(Playwright/Chromium), avec inspection de l'état calculé (`display`,
dimensions) du PNG et du canvas à chaque dizaine de millisecondes après un
clic sur « Radar », y compris en rouvrant rapidement la modale pour une
autre application sur un réseau ralenti — aucune coexistence simultanée
trouvée : le code, tel qu'issu du correctif de la section 22, alternait
strictement entre les deux, jamais les deux affichés en même temps. Ce
constat a été communiqué à l'utilisateur avec l'hypothèse la plus probable
(gabarits ou fichiers statiques non rechargés par le serveur applicatif).

Après redémarrage du serveur et vidage du cache navigateur, confirmation que
le problème persistait, avec une vidéo déposée dans le dossier « Claude
outputs » du dépôt. L'analyse image par image de cette vidéo (`ffmpeg`, 30
images/seconde autour du clic) a permis de RECTIFIER le diagnostic : il n'y
a jamais eu de coexistence simultanée des deux représentations (le code
alternait bien strictement entre les deux, comme confirmé plus haut), mais
un remplacement visible et net d'un radar par un autre, quelques centaines
de millisecondes après l'ouverture — le PNG matplotlib (sans marqueurs de
points, graduations tous les 0,5) apparaissant d'abord, puis cédant
instantanément la place au graphique Chart.js (marqueurs de points ronds,
graduations entières). Visuellement, ce remplacement se lit comme
l'apparition d'un second radar par-dessus le premier, d'où le terme
« doublon » employé par l'utilisateur — une lecture légitime du
comportement, même sans bug de coexistence au sens strict.

**Cause de fond.** Ce PNG-puis-remplacement était le comportement voulu
depuis la Phase 6, pensé comme une amélioration progressive pour les pages
qui fonctionnent sans JavaScript (`resume.html`, radar moyenne de
`synthese.html`) : le PNG y sert de repli réel, utile sans JavaScript. Mais
la modale radar de la synthèse, elle, ne s'ouvre que via le composant Modal
de Bootstrap, qui exige déjà JavaScript pour fonctionner — y poser le PNG
avant même de savoir si le graphique interactif va réussir à se charger ne
sert donc aucun usage réel sans JavaScript : ce n'était qu'un habillage sans
justification fonctionnelle, qui produisait ce remplacement visible.

**Correctif.** La modale n'affiche plus le PNG dès l'ouverture. Elle affiche
seulement un indicateur de chargement neutre (`spinner-border` Bootstrap,
dans la couleur de marque) le temps de la requête JSON
(`/radar/<name>/data`), puis directement la représentation finale : le
graphique interactif en cas de succès, ou le PNG (`/radar/<name>`, route
inchangée) seulement si ce dernier échoue pour une raison quelconque
(réseau, réponse invalide, Chart.js indisponible) — un seul radar visible à
la fois, sans jamais passer par un premier radar provisoire. Le repli PNG
reste entièrement fonctionnel, simplement affiché seulement quand il est
réellement nécessaire plutôt que systématiquement en amont.

**Vérifications effectuées.** Après correction, la même instance de test a
été revérifiée avec Playwright : l'indicateur de chargement s'affiche seul
pendant la requête, puis le graphique interactif s'affiche seul, sans jamais
passer par le PNG (captures et relevés d'état à l'appui) ; un test
supplémentaire a simulé l'échec de la requête JSON (route interceptée et
annulée) pour confirmer que le repli PNG s'affiche alors correctement, seul
également. Côté suite automatisée (même environnement cloud isolé, dépôt
complet copié) : `ruff check`, `ruff format --check` et `mypy --strict`
(`src`, `main.py`) sans erreur ; `pytest --cov=ADM` : 317 tests passés
(316 + 1 nouveau dans `tests/test_radar_interactive_chart.py`, qui vérifie
que le gestionnaire `show.bs.modal` ne pose plus le PNG et que celui-ci
reste masqué par défaut dans le balisage), couverture 87,65 % (seuil 86 %
maintenu), résultat conforme aux correctifs précédents — aucune régression
introduite. Les 7 échecs restants (`test_container_entrypoint.py`,
`test_demo_scripts.py`) restent le même problème de fins de ligne CRLF
préexistant, sans rapport avec ce correctif.

**Ce qui reste à faire côté utilisateur.** Les 2 fichiers modifiés
(`templates/synthese.html`, `tests/test_radar_interactive_chart.py`) ont été
déposés directement dans `C:\usr\ADM` via la liaison au poste, sans branche
ni commit créés. Reste donc à faire, localement :
1. Créer une branche dédiée (ex. `fix/us4-1-radar-modale-doublon`) et
   vérifier le statut `git` pour confirmer la liste des fichiers modifiés
   (les 2 ci-dessus, aucun autre).
2. Relire le diff.
3. Relancer localement `ruff check`, `ruff format --check`, `mypy --strict`
   et `pytest --cov=ADM` pour confirmer le résultat obtenu côté cloud.
4. **Redémarrer le serveur applicatif** (les gabarits Jinja2 restent en
   mémoire tant que le processus tourne, sans rechargement automatique hors
   mode `--debug`) et vider le cache du navigateur avant de tester.
5. Ouvrir la modale « Radar » d'une application depuis la synthèse et
   vérifier à l'œil qu'un seul radar s'affiche, sans remplacement visible
   (un bref indicateur de chargement peut apparaître selon la vitesse du
   réseau, ce qui est attendu).
6. Commiter et ouvrir la revue habituelle.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 28. Suivi — Phase 7 réalisée (2026-09-16)

**Demande.** Phase 7 du plan : « Validation et non-régression (en continu,
1 jour dédié en fin de projet). `pytest --cov=ADM` (seuil 86 % à
maintenir), `ruff check`, `ruff format --check` et `mypy --strict` après
chaque phase, pas seulement à la fin. Revue manuelle de chaque rôle
(`admin`, `readonly`, utilisateur standard) sur desktop et mobile, avec
captures d'écran avant/après comme preuve de non-régression fonctionnelle. »

**Portique qualité automatisé — confirmation finale.** Le portique complet a
déjà été exécuté et a réussi après chacune des Phases 1 à 6 et de chacun des
9 correctifs livrés depuis (couleur, animation, espacement ×2, doublon
modale, homogénéisation des messages, etc.) — la partie « en continu, après
chaque phase » de la Phase 7 est donc déjà satisfaite de facto tout au long
du projet, et non reportée à cette seule étape finale. Cette section en
donne la confirmation consolidée de fin de projet, exécutée une dernière
fois sur l'état actuel du dépôt : `ruff check` (« All checks passed! »),
`ruff format --check` (69 fichiers déjà au format), `mypy --strict src
main.py` (« Success: no issues found in 21 source files ») et `pytest
--cov=ADM --cov-report=term-missing` : 317 tests passés, couverture 87,65 %
(seuil 86 % maintenu), résultat identique à celui obtenu après le dernier
correctif (section 27) — aucune régression entre-temps.

7 échecs préexistants et sans rapport avec la modernisation UI ont été
observés dans cette même exécution (`tests/test_container_entrypoint.py` et
`tests/test_demo_scripts.py`) : ils échouent avec l'erreur bash `set:
pipefail: invalid option name`, provoquée par des fins de ligne CRLF
présentes sur l'ensemble de la copie du dépôt dans cet environnement cloud
isolé (constaté y compris sur des fichiers `.py` jamais touchés par ce
projet — `services.py`, `routes.py` — donc une caractéristique de la copie,
pas du contenu réellement suivi par git). Aucun fichier concerné par la
modernisation UI (Phases 1 à 6, tous les correctifs) n'est en cause : ces
échecs sont antérieurs et extérieurs à ce chantier. Le seuil de couverture
(86 %) reste atteint (87,65 %) malgré ces 7 échecs, qui ne portent donc pas
à conséquence pour la Phase 7. Il est recommandé de vérifier cette suite
localement (`git bash`/WSL sur poste Windows), où les fins de ligne du dépôt
suivi par git sont normalement correctes.

**Revue manuelle par rôle, desktop et mobile.** Une instance de test
temporaire (données JSON réalistes, catégories/questions réelles de
`static/questions.json`, 3 applications dont une non évaluée) a été créée
avec un compte par rôle (`admin-test`, `user-test`, `readonly-test`), et
parcourue avec un navigateur piloté (Playwright/Chromium) sur deux
viewports : desktop (1600×1000) et mobile (390×844, format iPhone). Pour
chacun des 3 rôles × 2 viewports (6 parcours), les pages suivantes ont été
visitées avec capture d'écran à l'appui : catalogue (`/`), synthèse
(`/synthese`) y compris l'ouverture de la modale radar d'une application,
fiche résumé (`/resume/<app>`), page d'évaluation (`/score/<app>`), et pour
le rôle `admin` uniquement, gestion des comptes (`/accounts`) et
configuration (`/settings`).

Résultats :
- **Aucune erreur console JavaScript inattendue** sur l'ensemble des 6
  parcours (les seuls messages « Failed to load resource » relevés
  correspondent exactement aux 6 tentatives volontaires d'accès à
  `/accounts` par les rôles `user`/`readonly`, qui reçoivent bien un 403 —
  comportement attendu, pas une anomalie).
- **Cloisonnement des rôles conforme** : `admin` accède à `/accounts` et
  `/settings` ; `user` et `readonly` en sont exclus (403, page d'erreur
  générique affichée, aucune fuite d'information). `readonly` reçoit
  également un 403 sur `/score/<app>` (le formulaire d'évaluation lui est
  entièrement fermé, y compris en lecture, conformément à
  `write_access_required` — comportement déjà en vigueur, non lié à la
  modernisation UI, confirmé sans régression).
- **Rendu radar (Phases 1, 4, 6 et correctifs associés) confirmé sur les 6
  parcours** : un seul radar visible dans la modale de synthèse (plus de
  doublon), couleur verte de marque homogène, pas d'espace blanc excessif,
  taille cohérente avec le radar moyenne — sur desktop comme sur mobile.
  Sur mobile, le radar de la fiche résumé occupe correctement la largeur de
  sa carte (Phase/correctif d'espacement toujours valide à cette largeur de
  viewport).
- **Formulaire d'évaluation** (`/score/<app>`) pleinement fonctionnel et
  éditable pour `admin`/`user` (32/32 questions, sommaire d'ancres, barre de
  progression, validation des commentaires obligatoires — Tâches 4.7/4.8
  intactes), inaccessible pour `readonly` comme attendu.
- **Point technique noté en cours de revue (pas une anomalie applicative)**
  : une capture d'écran « pleine page » (`full_page=True`) de Playwright
  rend la modale Bootstrap (en position CSS fixe) vide/désalignée dans
  l'image recomposée, car cette méthode de capture réassemble la page en la
  faisant défiler — artefact connu de l'outillage de capture, pas un bug du
  rendu réel (confirmé par une capture du seul viewport visible, qui montre
  la modale correctement affichée). Documenté ici pour éviter toute fausse
  alerte lors d'une revue future utilisant la même méthode.
- **Observation hors périmètre, pour un futur ticket** : sur mobile
  (390 px), le tableau de gestion des comptes (`/accounts`, jamais modifié
  par ce chantier) laisse entrevoir un liseré de la colonne d'actions au
  bord droit de sa carte — défilement horizontal intentionnel du tableau
  (`table-responsive`, même patron que les autres pages de liste, aucun
  débordement de la page elle-même constaté : 0 px de dépassement horizontal
  mesuré). Comportement pré-existant et fonctionnel, sans lien avec la
  modernisation UI ; à améliorer visuellement si souhaité dans un ticket
  dédié, hors US4.1.

**Conclusion.** Aucune régression fonctionnelle détectée sur les trois
rôles, desktop et mobile, à l'issue des 6 phases de modernisation et des
correctifs associés. Le portique qualité automatisé (hors les 7 échecs
préexistants et sans rapport, détaillés ci-dessus) confirme le même
résultat. La Phase 7 étant la dernière du plan, le chantier de modernisation
UI (US4.1) est fonctionnellement complet, sous réserve de la revue et du
merge locaux de l'ensemble des correctifs listés dans ce document.

**Ce qui reste à faire côté utilisateur.** Cette phase n'a modifié aucun
fichier de l'application (revue de validation uniquement) ; seul ce document
et `backlog.md` sont mis à jour. Reste donc à faire, localement :
1. Vérifier que tous les correctifs des sections précédentes (Phases 1 à 6
   et correctifs associés) sont bien mergés.
2. Relancer localement la suite complète (`ruff check`, `ruff format
   --check`, `mypy --strict`, `pytest --cov=ADM`) pour confirmer l'absence
   des 7 échecs liés aux fins de ligne CRLF observés dans cet environnement
   cloud (ils ne devraient pas apparaître sur un dépôt Windows/git normal).
3. Effectuer, si souhaité, une dernière vérification visuelle manuelle en
   conditions réelles (poste de travail, compte de chaque rôle) avant
   fermeture du chantier US4.1.

`backlog.md` a été mis à jour en conséquence sous US4.1 (Epic 4).

## 29. Clôture du chantier (2026-09-16)

Les 7 phases du plan de modernisation UI (US4.1) sont désormais toutes
réalisées et validées (Phase 7). US4.1 est en conséquence retirée de
`backlog.md`, conformément à la convention du fichier (« Les tâches
réalisées sont retirées du fichier. ») — ce document en reste l'historique
complet et détaillé (cadrage, 7 phases, tous les correctifs livrés en cours
de route) et n'a plus vocation à être complété par de nouvelles phases.

Les fichiers déposés dans le dossier `Claude outputs` du poste (`C:\usr\ADM
\Claude outputs`, captures d'écran de maquettes et de revue produites au fil
des différentes phases de cette session) sont devenus obsolètes maintenant
que le chantier est clos et doivent être supprimés par l'utilisateur ; cette
session cloud n'a pas les droits nécessaires pour les supprimer elle-même
(liaison au poste en lecture/écriture de fichiers uniquement, sans exécution
de commandes ni suppression sur ce poste).

Les seuls points restants identifiés lors de ce chantier sont hors périmètre
de cette user story et restent au backlog séparément : l'observation sur le
tableau des comptes en mobile (section 28, à traiter dans un ticket dédié si
souhaité — jamais formalisée en tâche technique numérotée) et la Tâche
technique 4.9 (gestion des catégories de questions, portée volontairement
réduite, toujours au backlog sous Epic 4).
