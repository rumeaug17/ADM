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

## Contrôles de qualité

```bash
ruff check .
ruff format --check .
mypy src main.py
pytest
```
# site de démo
https://rg17.pythonanywhere.com/
