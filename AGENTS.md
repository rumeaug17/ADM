# Instructions pour les assistants IA

Ces instructions s'appliquent à l'ensemble du dépôt.

Avant toute modification, lire :

- `README.md` ;
- `docs/CODING_GUIDELINES.md` ;
- `pyproject.toml`.

## Règles obligatoires

- Respecter PEP 8 et la configuration Ruff.
- Ne pas introduire de variable globale modifiable.
- Utiliser des fonctions courtes, des noms explicites et des annotations de types.
- Conserver des annotations de types explicites et ne jamais les supprimer uniquement pour faire passer mypy.
- Ne pas introduire `Any` sans nécessité et éviter les `# type: ignore`.
- Si un `# type: ignore` est réellement nécessaire, préciser le code d'erreur mypy concerné et justifier son usage dans un commentaire.
- Valider les données d'entrée et gérer précisément les exceptions.
- Placer le métier dans `src/exemple_python_project_df/` et l'orchestration dans `dags/`.
- Ne jamais mettre de secret, notamment un mot de passe ou un jeton, dans le code ni dans un fichier de configuration versionné. Les secrets doivent être gérés par des variables d'environnement ou par un gestionnaire de secrets externe.
- Ne jamais écrire de secret ni de donnée personnelle dans les logs, les tests, la documentation ou les exemples.
- Déclarer toute dépendance dans `pyproject.toml` et justifier son ajout.
- Ajouter ou mettre à jour les tests pour toute évolution du comportement.
- Ne pas exécuter de traitement lourd lors de l'import d'un DAG Airflow.
- Ne pas recompiler un artefact entre Qualification, Recette et Production.
- Les déploiements hors DEV partent exclusivement de `main` et d'un tag fixe.

## Contrôles

Avant de proposer une modification, exécuter si possible :

```text
ruff check .
ruff format --check .
mypy src main.py
pytest
```

Ne jamais affirmer qu'un contrôle a réussi s'il n'a pas réellement été exécuté.
