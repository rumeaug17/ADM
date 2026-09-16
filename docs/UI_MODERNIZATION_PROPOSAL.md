# US4.1 — Proposition de modernisation de l'interface (design)

Date : 2026-09-16. Document de cadrage produit avant tout développement, en
réponse à l'US4.1 du backlog (« Améliorer le design / Moderniser
l'affichage », Epic 4). Aucun code n'a été modifié à ce stade : ce document
sert de base à une future session d'implémentation, phase par phase.

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

**Phase 3 — Formulaires et pages secondaires (2 à 3 jours).** Étendre le
design system à `score.html` (en conservant impérativement la barre de
progression, le sommaire d'ancres et la validation des commentaires
obligatoires, uniquement réhabillés), `add.html`, `edit.html`, `login.html`,
`accounts.html`, `questions_settings.html`, `question_form.html`,
`settings.html`, `change_password.html`, `import_data.html` et
`error.html`. Labels flottants Bootstrap pour les formulaires courts,
popovers d'aide contextuelle conservés à l'identique fonctionnellement.

**Phase 4 — Interactivité progressive avec htmx et Alpine.js (3 à 5
jours).** Faire gagner en fluidité les actions qui rechargent aujourd'hui
toute la page, sans changer le contrat des routes existantes : suppression
et réinitialisation d'une application confirmées en modale puis appliquées
via une requête htmx qui ne rafraîchit que la ligne concernée ; filtres de
la synthèse (`?filter_score=...`, déjà gérés côté serveur) déclenchés en
htmx pour ne rafraîchir que le tableau et les KPI ; messages flash
remplacés par des toasts Bootstrap après une action htmx ; menu mobile et
bascule de thème gérés en Alpine.js. Concrètement, les routes concernées
apprennent à renvoyer un fragment de template quand la requête porte l'en-
tête htmx, et continuent de renvoyer la page complète sinon — une évolution
additive et rétrocompatible, pas une réécriture. C'est la phase la plus
proche d'un changement d'approche front évoqué en préambule, tout en
respectant strictement Flask/Python et le rendu par templates.

**Phase 5 — Mode sombre, accessibilité et finitions (1 à 2 jours).**
Finaliser la bascule de thème (persistée en `localStorage`, avec
`prefers-color-scheme` comme valeur par défaut), auditer les contrastes du
nouveau design, l'ordre de tabulation et les libellés ARIA, et corriger les
derniers écarts visuels entre pages.

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

## 13. Prochaine étape immédiate

Après revue et merge de la Phase 2, ouvrir la Phase 3 (formulaires et pages
secondaires : `score.html`, `add.html`, `edit.html`, `login.html`,
`accounts.html`, `questions_settings.html`, `question_form.html`,
`settings.html`, `change_password.html`, `import_data.html`, `error.html`)
comme prochain ticket de développement, en conservant impérativement la
barre de progression, le sommaire d'ancres et la validation des commentaires
obligatoires de `score.html`, uniquement réhabillés.
