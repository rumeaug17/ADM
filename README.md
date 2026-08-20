# ADM
Gestion d'un catalogue d'application avec classification et score de dette

Il s'agit d'uner petite application toute simple (très primitive) servant à expliquer et démontrer l'intérêt d'une telle application pour la gestion de la dette applicative dans une DSI.

L'objectif d'une telle application est de calculer une estimation de la dette d'un SI application par application, afin d'avoir un état des lieux factuel, facilitant la prise de décision et permettant d'identifier là où un effort doit être prévu.

Les questions pour l'estimation du score de dette pour chaque application est configurable dans un fichier json. 

Les questions par défaut sont décrites ici : [Documentation.md](/documentation.md)

# Installation et exécution

Les dépendances, y compris celles de développement, sont déclarées dans
`pyproject.toml` :

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
git describe --tags --abbrev=0 > static/version.txt
```

Les secrets ne doivent pas être ajoutés à `config.json`. Pour une exécution
locale avec le backend JSON, fournissez-les uniquement via l'environnement :

```bash
export ADM_SECRET_KEY='valeur-locale-a-remplacer'
export ADM_USERNAME='utilisateur-local'
export ADM_PASSWORD='mot-de-passe-local-a-remplacer'
python main.py
```

L'application est alors disponible sur <http://127.0.0.1:5000/>. Pour MySQL,
définissez aussi `ADM_DB_BACKEND=mysql` et `ADM_DATABASE_URL` avec une URL de
connexion provenant du gestionnaire de secrets de l'environnement.

Tous les formulaires modifiant des données utilisent un jeton CSRF lié à la
session. Les formulaires incomplets ou contenant une valeur hors des choix proposés
sont refusés avec un message indiquant le champ concerné. Les imports sont limités
à 5 Mio, doivent contenir une liste JSON et chaque application est validée avant
le début de son enregistrement. Les détails techniques des erreurs restent dans les
journaux serveur ; l'interface n'affiche jamais le contenu d'une exception interne.

## Organisation du code Python

- `src/ADM/` contient le code installable, notamment l'application Flask, les calculs
  de score et les backends de persistance SQLAlchemy et JSON ;
- `main.py` reste le point d'entrée minimal de l'application web ;
- `scripts/` regroupe les utilitaires exécutés ponctuellement ;
- `tests/` contient les tests automatisés.

Les backends sont importés via `ADM.database` et `ADM.database_json`.

La Phase 3 organise désormais la couche web autour de la fabrique
`ADM.app.create_app` : l’import du module ne lit aucune configuration, ne valide
aucune variable d’environnement et n’initialise aucune persistance. La fabrique
charge explicitement la configuration, choisit le backend, puis injecte la fabrique
de sessions aux blueprints `auth`, `applications`, `evaluations` et `exports`. Les
calculs de risque, métriques et synthèse sont isolés dans `ADM.services` et restent
utilisables sans contexte Flask. Les erreurs de configuration (secret absent, backend
inconnu ou URL MySQL absente) sont levées au moment de l’appel à `create_app`.

Les utilitaires peuvent être lancés depuis n'importe quel répertoire. Par
exemple, la documentation fonctionnelle est régénérée avec :

```bash
python scripts/generate_md_doc.py
```

## Contrôles de qualité

```bash
ruff check .
ruff format --check .
mypy src main.py
pytest
```
# site de démo
https://rg17.pythonanywhere.com/
