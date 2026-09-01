# ADM — Catalogue de dette applicative

ADM est une application web Flask destinée à inventorier les applications d'un
système d'information et à estimer leur dette technique à partir d'un questionnaire
pondéré. Elle fournit un score par application, conserve l'historique des évaluations
et présente une synthèse destinée à faciliter la priorisation des actions.

> ADM est un démonstrateur. Avant un usage réel, adaptez le questionnaire, les règles
> métier, l'authentification et les procédures d'exploitation à votre organisation.

## Fonctionnalités

- gestion d'un catalogue d'applications et de leurs caractéristiques de criticité ;
- questionnaire configurable selon le type d'application et son hébergement ;
- calcul du score de dette, des axes de risque et d'indicateurs de synthèse ;
- historique des évaluations et génération de graphiques radar ;
- import et export atomiques du catalogue au format JSON (réimportation totale
  réservée au rôle administrateur) ;
- persistance locale dans un fichier JSON ou SQLite, ou dans MySQL via SQLAlchemy ;
- validation des entrées, protection CSRF et limitation des imports à 5 Mio.

Les règles du questionnaire et du calcul sont détaillées dans
[`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md). La liste des questions par
défaut, générée depuis les fichiers de configuration, est disponible dans
[`documentation.md`](documentation.md).

## Prérequis

- Python 3.11 ou une version ultérieure ;
- Git, pour écrire la version affichée par l'application ;
- un serveur MySQL uniquement si le backend MySQL est utilisé ; SQLite ne nécessite
  aucun serveur supplémentaire.

## Démarrage rapide

### Démonstration autonome

Sous Linux ou macOS, les commandes suivantes créent l'environnement virtuel,
installent le projet, exécutent les contrôles et génèrent un catalogue fictif :

```bash
scripts/setup_demo.sh
scripts/run_demo.sh
```

Sous Windows PowerShell :

```powershell
.\scripts\setup_demo.ps1
.\scripts\run_demo.ps1
```

Par défaut, le serveur démarre avec le mode de débogage désactivé. Pour
choisir explicitement son état au lancement, utilisez `--debug-mode on|off` sous
Linux ou macOS, et `-DebugMode on|off` sous PowerShell :

```bash
scripts/run_demo.sh --debug-mode on
```

```powershell
.\scripts\run_demo.ps1 -DebugMode on
```

Le mode `on` est réservé au développement local. Il active notamment le
rechargement et le débogueur Flask ; ne l'utilisez pas sur un environnement exposé.

Le setup utilise le backend JSON et crée des identifiants aléatoires dans un fichier
local exclu de Git (`.adm-demo.env` ou `.adm-demo.json`). Ne publiez jamais ce fichier.
Le script PowerShell recherche automatiquement `py`, `python`, puis `python3`.
`PYTHON_BIN` (ou `-PythonBin` sous Windows) permet de choisir explicitement l'interpréteur et
`ADM_DEMO_VENV` (ou `-VenvPath`) l'emplacement de l'environnement virtuel.

### Installation manuelle

Les chemins `scripts/...` ci-dessous sont relatifs à la racine du dépôt. Placez-vous
d'abord dans le dossier ADM, quel que soit votre répertoire courant :

```bash
cd "$(git -C ~/ADM rev-parse --show-toplevel)"
```

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
git describe --tags --always > src/ADM/resources/static/version.txt
```

Définissez ensuite le secret dans l'environnement, créez le premier compte
administrateur, puis lancez le serveur :

```bash
export ADM_SECRET_KEY='valeur-locale-factice-a-remplacer'
python scripts/create_account.py --username admin --role admin
python main.py
```

`create_account.py` demande le mot de passe de façon interactive (jamais en
argument de ligne de commande, jamais journalisé). Sans compte créé au
préalable, aucune connexion à l'interface n'est possible. Le script charge
explicitement le paquet depuis le dossier `src` du checkout courant : il ne peut
donc pas utiliser par erreur une autre version déjà installée dans le profil
utilisateur ou dans l'environnement virtuel.

L'interface est alors accessible à l'adresse <http://127.0.0.1:5000/>.

## Configuration

`src/ADM/resources/config.json` contient uniquement les valeurs non sensibles par
défaut. Les secrets et paramètres propres à un environnement sont fournis par
variables d'environnement :

| Variable | Obligatoire | Description |
| --- | --- | --- |
| `ADM_SECRET_KEY` | Oui | Clé longue et aléatoire utilisée pour signer la session Flask. |
| `ADM_DB_BACKEND` | Non | `json` par défaut, `sqlite` ou `mysql`. |
| `ADM_DATABASE_URL` | Avec SQLite/MySQL | URL SQLAlchemy (ou chemin de fichier avec JSON). |
| `ADM_ACCOUNTS_URL` | Non | Chemin du fichier de comptes (backend JSON), remplace `accounts_connection_url`. |

Les seuils de couleur et de filtrage des affichages sont définis dans
`src/ADM/resources/config.json`, sous `display_thresholds`. Les valeurs `score` sont
des pourcentages et les valeurs `risk` utilisent l'unité du risque calculé. Pour chaque indicateur,
`warning` doit être positif ou nul et strictement inférieur à `critical`.

Ces seuils sont également modifiables depuis l'interface, à l'adresse `/settings`.

Avec le backend JSON, le chemin du fichier est défini par `json_connection_url` dans
`config.json` et peut être remplacé par `ADM_DATABASE_URL`.

Pour un déploiement local persistant mono-processus, SQLite stocke le catalogue,
les évaluations et les comptes dans un même fichier, sans serveur à installer :

```bash
export ADM_DB_BACKEND=sqlite
export ADM_DATABASE_URL='sqlite:////chemin/absolu/adm.db'
alembic upgrade head
python scripts/create_account.py --username admin --role admin
python main.py
```

Le répertoire contenant `adm.db` doit exister et être accessible en écriture par
le processus ADM. Sauvegardez le fichier lorsque l'application est arrêtée. Ce mode
n'est pas destiné à plusieurs processus applicatifs concurrents.

Avec MySQL, appliquez également les migrations avant le premier démarrage :

```bash
export ADM_DB_BACKEND=mysql
export ADM_DATABASE_URL='mysql+mysqlconnector://utilisateur:secret@hote/base'
alembic upgrade head
python main.py
```

Cette URL est un gabarit : ne copiez aucun secret réel dans un fichier versionné, une
commande enregistrée ou un journal. Une nouvelle migration se crée avec
`alembic revision --autogenerate -m "description"`.

## Utilisation

1. Connectez-vous avec un compte créé via `scripts/create_account.py` (voir
   Démarrage rapide et Configuration).
2. Ajoutez une application et renseignez ses caractéristiques.
3. Ouvrez son évaluation, répondez aux questions applicables, puis enregistrez-la.
4. Consultez la synthèse ou exportez le catalogue pour le sauvegarder.

Un import doit être un export ADM au format JSON. Cette opération, réservée aux
comptes administrateur, remplace le catalogue seulement après validation complète
du document ; conservez donc une sauvegarde avant l'opération.

## Organisation du dépôt

```text
src/ADM/       application, métier, validation et persistance
src/ADM/resources/templates/  vues Jinja
src/ADM/resources/static/     questionnaire, aides et ressources statiques
tests/         tests automatisés
migrations/    versions du schéma MySQL
scripts/       setup, génération de données, sauvegarde et documentation
docs/          architecture, règles métier et conventions
main.py        point d'entrée minimal du serveur de développement
```

La fabrique `ADM.app.create_app` charge la configuration et injecte la persistance
aux blueprints. Son import n'initialise ni fichier ni connexion. Le détail des couches,
de leurs dépendances et du parcours d'une requête se trouve dans
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Commandes utiles

Exécutez ces commandes depuis la racine du dépôt, et non depuis
`src/ADM/resources`. Pour retrouver cette racine depuis n'importe quel
sous-dossier du dépôt : `cd "$(git rev-parse --show-toplevel)"`.

```bash
# Régénérer la documentation fonctionnelle
python scripts/generate_md_doc.py

# Générer des données fictives pour le backend JSON
python scripts/generate_data_json.py

# Sauvegarder ou restaurer le catalogue (voir l'aide de la commande)
python scripts/backup_restore.py --help

# Créer un compte local, admin ou utilisateur (mot de passe demandé de façon interactive)
python scripts/create_account.py --username <nom> --role admin
```

## Développement et contribution

Installez les dépendances de développement avec `python -m pip install -e '.[dev]'`,
puis exécutez avant chaque Pull Request :

```bash
ruff check .
ruff format --check .
mypy src main.py
pytest
```

Le processus complet (branche, conventions, tests, migrations, documentation et
checklist de Pull Request) est décrit dans [`CONTRIBUTING.md`](CONTRIBUTING.md).
Les principes de style Python sont complétés par
[`docs/CODING_GUIDELINES.md`](docs/CODING_GUIDELINES.md).

## Licence

Ce projet est distribué selon les termes du fichier [`LICENSE`](LICENSE).

## Illustration

![Illustration ADM](image_adm_cow.jpg)
