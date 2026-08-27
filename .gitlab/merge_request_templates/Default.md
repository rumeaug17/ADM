## Résumé

<!-- Décrivez le besoin, le comportement attendu et la solution apportée.
     Limitez cette Merge Request à un seul sujet (voir CONTRIBUTING.md). -->

## Impact

<!-- Données, sécurité, déploiement, compatibilité : décrivez ce qui change,
     ou indiquez explicitement « Aucun impact ». -->

## Checklist

- [ ] Le comportement attendu et les erreurs gérées sont documentés.
- [ ] Les tests utiles ont été ajoutés ou adaptés (cas nominal, puis entrées
      invalides et erreurs attendues lorsque pertinent).
- [ ] `ruff check .`, `ruff format --check .`, `mypy src main.py` et `pytest`
      ont été exécutés avec succès localement (la CI les revérifie).
- [ ] Aucun secret ni donnée personnelle ou réelle n'apparaît dans le diff, les
      tests, la documentation ou les journaux applicatifs.
- [ ] Toute nouvelle dépendance est déclarée dans `pyproject.toml` et justifiée
      ci-dessus (bibliothèque standard ou dépendances existantes insuffisantes).
- [ ] Toute évolution du schéma SQL possède une révision Alembic vérifiée
      (montée de version et, si la révision le permet, retour arrière).
- [ ] La documentation concernée est à jour : `README.md`,
      `docs/BUSINESS_RULES.md` (invariants métier), `docs/ARCHITECTURE.md`
      (responsabilités ou dépendances), et `documentation.md` régénéré via
      `python scripts/generate_md_doc.py` si `static/questions.json` ou
      `static/info_texts.json` ont changé.
- [ ] L'impact sur les imports, exports et configurations existants est décrit.
- [ ] L'artefact peut être construit une seule fois puis promu sans
      recompilation de Qualification vers Recette puis Production.

<!-- Rappel : n'affirmez pas qu'un contrôle a réussi s'il n'a pas été exécuté.
     Si l'environnement empêche un contrôle, précisez la commande, la limite
     rencontrée et les vérifications alternatives réalisées. -->
