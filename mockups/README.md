# Maquettes — Phase 0 de US4.1 (modernisation de l'interface)

**Statut : validées par Guillaume Rumeau le 2026-09-16.** Deux ajustements
ont été apportés par rapport à la première version de ces maquettes, avant
validation finale : la couleur de marque est passée du bleu Bootstrap par
défaut à un vert forêt légèrement foncé (`#0e6b5c` / `#0a4d42`, distinct du
vert sémantique des badges), et les quatre boutons d'action du catalogue ont
été regroupés dans un menu contextuel unique (« ⋯ ») plutôt qu'affichés côte
à côte. Le détail est consigné dans `docs/UI_MODERNIZATION_PROPOSAL.md`
(section 9). La Phase 1 (fondations du design system dans l'application) est
prête à être ouverte.

Ces fichiers sont le livrable de la **Phase 0** décrite dans
`docs/UI_MODERNIZATION_PROPOSAL.md` : des maquettes statiques destinées à
valider une direction visuelle avant tout développement.

## Ce que c'est

Trois écrans clés, réhabillés selon le design system proposé (palette et
ombres unifiées, icônes Bootstrap Icons à la place des émojis, mode sombre
natif Bootstrap 5.3, cartes et tableaux modernisés) :

- `index.html` — sommaire, à ouvrir en premier ;
- `catalogue.html` — reprise de `templates/index.html` (liste des
  applications) ;
- `evaluation.html` — reprise de `templates/score.html` (formulaire
  d'évaluation, avec sa progression et son sommaire d'ancres) ;
- `synthese.html` — reprise de `templates/synthese.html` (KPI, radar,
  tableau des scores).

Le bouton en haut à droite de chaque page bascule entre thème clair et
sombre (réglage mémorisé dans le navigateur).

## Ce que ce n'est pas

Ce sont de simples fichiers HTML statiques, avec des données fictives,
**non connectés à Flask ni à Jinja2**. Aucune route, aucun gabarit, aucun
fichier Python de l'application n'a été modifié. Bootstrap, Bootstrap Icons
et la police Inter sont chargés depuis des CDN uniquement pour cette
maquette ; l'implémentation réelle (Phase 1 du plan) les auto-hébergera dans
`static/vendor/` comme prévu dans le document de cadrage, notamment pour
préparer la CSP de la Tâche 6.6 du backlog.

## Comment les consulter

Ouvrir `index.html` dans un navigateur (double-clic, ou glisser le fichier
dans une fenêtre de navigateur). Aucun serveur, aucune installation n'est
nécessaire.

## Réutilisation en Phase 1

`assets/mockup.css` regroupe déjà les tokens de couleur, les styles de
cartes/tableaux/badges (`.card-adm`, `.table-adm`, `.badge-crit-*`,
`.badge-dicp-*`, `.kpi-card`, `.eval-progress-card`, etc.) : ce fichier peut
servir de point de départ pour le futur `src/ADM/resources/static/css/app.css`
plutôt que d'être réécrit de zéro.

## Suite

Direction validée. La Phase 1 (fondations du design system dans
l'application elle-même) est le prochain ticket de développement — voir
`docs/UI_MODERNIZATION_PROPOSAL.md` section 10 et `backlog.md` (US4.1,
Epic 4).
