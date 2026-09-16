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
et équivalents), pour ne plus redéfinir `#0d6efd` en dur à chaque page,
avec les mêmes teintes sémantiques que celles déjà choisies pour les badges
DICP et de criticité (vert/jaune/orange/rouge), mais déclarées une seule
fois. Une typographie web moderne (par exemple *Inter*), auto-hébergée dans
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

**Phase 0 — Cadrage visuel (0,5 à 1 jour, sans code).** Produire deux ou
trois maquettes statiques (catalogue, formulaire d'évaluation, synthèse) en
clair et en sombre, pour validation avant tout développement. Objectif :
éviter les allers-retours une fois le code entamé.

**Phase 1 — Fondations du design system (2 à 3 jours).** Créer
`src/ADM/resources/static/css/app.css` regroupant les tokens de couleur, les
styles de badges, cartes, tableaux, navigation et pied de page aujourd'hui
dupliqués ou inlinés. Supprimer les blocs `<style>` redondants de
`index.html`, `resume.html`, `synthese.html`, `score.html`, `add.html`,
`edit.html`, `accounts.html`, `questions_settings.html` et `settings.html`
au profit de classes communes. Auto-héberger (« vendoriser ») Bootstrap
CSS/JS et Bootstrap Icons dans `static/vendor/` à la place du CDN `jsdelivr`
actuel, en préparation de la CSP stricte de la Tâche 6.6 et pour un
fonctionnement sans dépendance réseau externe. Remplacer les émojis par des
icônes Bootstrap Icons. Fichiers impactés : `base.html` et l'ensemble des
gabarits cités, plus l'arborescence `static/`. Risque principal : les cinq
tests de présentation cités en section 2, à faire tourner en continu.

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

## 9. Prochaine étape immédiate

Valider ce document, puis produire les maquettes de la Phase 0 avant
d'ouvrir un premier ticket de développement pour la Phase 1.
