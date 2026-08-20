# Contribuer à ADM

Merci de contribuer à ADM. Ce guide décrit le chemin attendu entre une idée et son
intégration. Il complète les règles de qualité de
[`docs/CODING_GUIDELINES.md`](docs/CODING_GUIDELINES.md) et l'architecture décrite
dans [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Avant de commencer

1. Consultez le `README.md`, le backlog et les issues existantes.
2. Décrivez le besoin, le comportement attendu et les cas d'erreur.
3. Créez depuis `main` une branche courte dédiée, par exemple
   `feature/export-csv` ou `bugfix/score-incomplet`.
4. N'utilisez que des données fictives et anonymes.

Le projet suit le Trunk-Based Development : aucune modification n'est réalisée
directement sur `main`. Les déploiements hors DEV partent exclusivement d'un commit
de `main` portant un tag immuable.

## Préparer l'environnement

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Sous Windows, activez l'environnement avec `.venv\Scripts\Activate.ps1`. Pour une
démonstration prête à l'emploi, utilisez plutôt les scripts `setup_demo` documentés
dans le README.

## Règles d'implémentation

- Placez la logique métier et les validations réutilisables dans `src/ADM/` ; les
  routes ne doivent assurer que l'orchestration HTTP.
- Écrivez des fonctions courtes, nommées explicitement et entièrement annotées.
- Documentez les modules, les interfaces publiques et les décisions non évidentes.
  Un commentaire doit expliquer le *pourquoi* ; évitez de paraphraser le code.
- Validez les données aux frontières et interceptez uniquement les exceptions que la
  couche sait traiter. Ne masquez pas une erreur de typage avec `Any` ou un
  `# type: ignore` injustifié.
- N'introduisez ni secret, ni donnée personnelle, ni état global modifiable. Les
  secrets sont injectés par l'environnement ou un gestionnaire externe et ne sont
  jamais écrits dans les logs.
- Déclarez toute dépendance dans `pyproject.toml` et expliquez dans la Pull Request
  pourquoi la bibliothèque standard et les dépendances existantes ne suffisent pas.
- N'effectuez aucune connexion, écriture ou opération lourde lors de l'import d'un
  module, en particulier d'un éventuel DAG Airflow.

Respectez PEP 8 et la configuration Ruff du dépôt. Ne retirez pas une annotation de
type pour faire réussir mypy. Si une suppression mypy est indispensable, ciblez son
code d'erreur et ajoutez un commentaire expliquant la limite de la bibliothèque.

## Tests et contrôles

Toute évolution de comportement doit comporter un test reproduisant d'abord le cas
nominal et, lorsque pertinent, les entrées invalides et erreurs attendues. Les tests
ne doivent dépendre ni du réseau, ni d'un service partagé, ni de données réelles.

Depuis la racine du dépôt, exécutez :

```bash
ruff check .
ruff format --check .
mypy src main.py
pytest
```

Ne présentez jamais un contrôle comme réussi s'il n'a pas été exécuté. Si
l'environnement empêche un contrôle, indiquez précisément la commande, la limite et
les vérifications alternatives dans la Pull Request.

## Documentation et migrations

- Mettez à jour le README pour tout changement d'installation, de configuration ou
  d'utilisation, sans y placer de valeur sensible.
- Mettez à jour `docs/BUSINESS_RULES.md` lorsqu'un invariant métier évolue et
  `docs/ARCHITECTURE.md` lorsque les responsabilités ou dépendances changent.
- Après une modification de `static/questions.json` ou `static/info_texts.json`,
  régénérez et commitez `documentation.md` avec
  `python scripts/generate_md_doc.py`.
- Toute modification du modèle SQL doit inclure une révision Alembic. Vérifiez la
  montée de version et, si la révision le permet, son retour arrière sur une base de
  test vide.

## Commits et Pull Request

Créez des commits cohérents avec un message à l'impératif, par exemple
`Documente le parcours de contribution`. Une Pull Request reste limitée à un sujet,
décrit le problème et la solution, et mentionne les conséquences éventuelles sur les
données, la sécurité, le déploiement et la compatibilité.

Checklist avant de demander une revue :

- [ ] le changement et ses erreurs attendues sont documentés ;
- [ ] les tests utiles ont été ajoutés ou adaptés ;
- [ ] Ruff (lint et formatage), mypy et pytest ont été exécutés ;
- [ ] aucune donnée sensible ou personnelle n'est présente dans le diff ou les logs ;
- [ ] toute nouvelle dépendance est déclarée et justifiée ;
- [ ] toute évolution SQL possède une migration vérifiée ;
- [ ] l'impact sur les imports, exports et configurations existants est décrit ;
- [ ] l'artefact peut être construit une fois puis promu sans recompilation.

## Revue, fusion et livraison

La branche est fusionnée après revue et succès des contrôles. Une version livrée suit
Semantic Versioning (`MAJOR.MINOR.PATCH`) et porte un tag Git fixe. Le même artefact
validé en Qualification est promu en Recette puis en Production ; seule la
configuration change entre les environnements.
