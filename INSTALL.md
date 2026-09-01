# Guide d'installation d'ADM

Ce guide décrit une installation **standard, persistante et prête à l'emploi**
d'ADM avec MySQL. La procédure vise PythonAnywhere, mais les mêmes principes
s'appliquent à tout hébergeur Python proposant une application WSGI et une base
MySQL.

> ADM est un démonstrateur. Avant de l'exposer à des données réelles, adaptez
> l'authentification, le questionnaire, les règles métier, la sauvegarde et la
> supervision aux exigences de votre organisation.

## 1. Architecture et chemins utilisés

L'installation sépare le code, l'environnement Python, la configuration sensible
et les données :

| Élément | PythonAnywhere (exemple) | Serveur Linux classique (exemple) |
| --- | --- | --- |
| Code source | `/home/<utilisateur>/ADM` | `/opt/adm/app` |
| Environnement virtuel | `/home/<utilisateur>/.virtualenvs/adm` | `/opt/adm/venv` |
| Données Python persistantes | MySQL ; aucun fichier métier local | MySQL ; aucun fichier métier local |
| Secrets/configuration d'exécution | Variables du processus WSGI, hors Git | `/etc/adm/adm.env`, mode `600` |
| Fichiers statiques | `/home/<utilisateur>/ADM/src/ADM/resources/static` | `/opt/adm/app/src/ADM/resources/static` |

Dans les commandes ci-dessous, remplacez les valeurs entre chevrons. Ne copiez
jamais un mot de passe, une clé de session ou une URL contenant un mot de passe
dans le dépôt, un ticket, un journal ou l'historique du shell.

## 2. Prérequis

- Python 3.11 ou plus récent ;
- Git ;
- une base MySQL accessible depuis le serveur web ;
- un compte MySQL limité à la base ADM ;
- un accès HTTPS au site final ;
- un shell permettant de créer un environnement virtuel et d'exécuter Alembic.

Pour figer un déploiement hors DEV, partez de `main` et d'un tag immuable. Construisez
une seule fois un wheel depuis ce tag dans la chaîne de livraison, publiez-le avec sa
somme SHA-256 dans un dépôt d'artefacts, puis installez **ce même fichier** en
Qualification, Recette et Production. Ne reconstruisez jamais le wheel à partir du
checkout propre à chaque environnement.

## 3. Préparer MySQL

### 3.1 PythonAnywhere

Dans l'onglet **Databases**, créez une base MySQL et notez sans les publier :

- le nom de la base (souvent `<utilisateur>$adm`) ;
- le nom d'utilisateur MySQL ;
- le nom d'hôte MySQL indiqué par le tableau de bord ;
- le mot de passe MySQL.

Ne supposez pas que l'hôte est `localhost` : utilisez exactement celui affiché
par l'hébergeur. Les tables seront créées par Alembic à l'étape 7.

### 3.2 Serveur MySQL administré par vos soins

Connectez-vous avec un compte d'administration MySQL, puis créez une base UTF-8
et un compte dédié. Les valeurs ci-dessous sont des **gabarits**, pas des secrets
réels :

```sql
CREATE DATABASE adm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'adm_app'@'<hote-web>' IDENTIFIED BY '<mot-de-passe-a-generer>';
GRANT ALL PRIVILEGES ON adm.* TO 'adm_app'@'<hote-web>';
FLUSH PRIVILEGES;
```

En production, réduisez les privilèges après les migrations si votre procédure
d'exploitation le prévoit et chiffrez la connexion MySQL lorsque le réseau n'est
pas strictement privé.

## 4. Installer le code et l'environnement Python

Un virtualenv est recommandé pour isoler les dépendances et rendre le déploiement
reproductible, mais il n'est pas obligatoire. La section 4.3 décrit une
installation dans le compte utilisateur lorsque l'hébergeur fournit déjà Python.

Avant le premier déploiement hors DEV, la chaîne de livraison construit le livrable
une seule fois depuis un tag appartenant à `main` :

```bash
git checkout <tag-de-version>
python3.11 -m pip install build
git describe --tags --always > src/ADM/resources/static/version.txt
python3.11 -m build --wheel
(python3.11 -m zipfile -l dist/<nom-exact-du-wheel>.whl | grep -E \
  'ADM/resources/(config.json|static/questions.json|templates/base.html)')
(cd dist && sha256sum <nom-exact-du-wheel>.whl > <nom-exact-du-wheel>.whl.sha256)
```

La vérification du contenu doit afficher les trois ressources indiquées. Si l'une
d'elles manque, ne publiez pas le wheel : il ne pourra pas démarrer une fois installé.
Le fichier de version est généré **avant** la construction afin qu'il appartienne au
même artefact immuable que le code et les autres ressources.

Publiez le wheel et le fichier `.sha256` dans un dépôt d'artefacts immuable. Dans
chacun des environnements promus, récupérez ces deux fichiers dans un répertoire
`<repertoire-artefacts>`, vérifiez la somme avec la commande suivante et conservez le
nom exact du fichier dans toutes les commandes d'installation :

```bash
cd <repertoire-artefacts>
sha256sum --check <nom-exact-du-wheel>.whl.sha256
```

Les commandes ci-dessous supposent que ce contrôle a réussi. Le checkout du même tag
reste nécessaire pour les migrations, les scripts et les fichiers statiques, mais il
ne sert pas à reconstruire le paquet Python.

### 4.1 PythonAnywhere

Ouvrez une console Bash :

```bash
cd /home/<utilisateur>
git clone <url-du-depot> ADM
cd /home/<utilisateur>/ADM
git switch main
git pull --ff-only
git checkout <tag-de-version>
python3.11 -m venv /home/<utilisateur>/.virtualenvs/adm
source /home/<utilisateur>/.virtualenvs/adm/bin/activate
python -m pip install --upgrade pip
python -m pip install <repertoire-artefacts>/<nom-exact-du-wheel>.whl
```

Si l'offre ne fournit pas exactement la commande `python3.11`, sélectionnez dans
l'onglet Web une version disponible **au moins égale à 3.11**, puis utilisez la
même version pour créer le virtualenv.

### 4.2 Serveur Linux équivalent

```bash
sudo install -d -o adm -g adm /opt/adm
sudo -u adm git clone <url-du-depot> /opt/adm/app
cd /opt/adm/app
sudo -u adm git checkout <tag-de-version>
sudo -u adm python3.11 -m venv /opt/adm/venv
sudo -u adm /opt/adm/venv/bin/python -m pip install --upgrade pip
sudo -u adm /opt/adm/venv/bin/python -m pip install <repertoire-artefacts>/<nom-exact-du-wheel>.whl
```

L'installation standard n'utilise pas `applications.json` ni `accounts.json` :
le catalogue, les évaluations **et les comptes** sont stockés dans la même base
MySQL. Le dossier `src/` contient les paquets Python ; l'installation du wheel les
installe dans l'environnement Python choisi. Il ne faut donc ni déplacer `src/ADM`,
ni ajouter un dossier de données Python arbitraire au `PYTHONPATH`.

### 4.3 Installation sans virtualenv

Sur PythonAnywhere, ou sur un serveur où ADM s'exécute sous un compte dédié,
installez le projet dans le répertoire utilisateur de ce compte. Si ce n'est pas
déjà fait, clonez d'abord le dépôt et positionnez-vous sur le tag à déployer
comme au début de la section 4.1 (`git clone`, `git checkout <tag-de-version>`),
mais **sans créer le virtualenv ni y installer le wheel** : ces commandes sont
remplacées par les suivantes.

```bash
cd /home/<utilisateur>/ADM
python3.11 -m pip install --user <repertoire-artefacts>/<nom-exact-du-wheel>.whl
python3.11 -c "import ADM; print(ADM.__file__)"
```

Utilisez ensuite exactement cette version de Python pour les migrations, le
diagnostic et le processus WSGI. Sur PythonAnywhere, choisissez aussi cette
version dans l'onglet Web et ne renseignez pas de virtualenv. L'installation
`--user` doit être réalisée avec le même compte que celui qui exécute
l'application, car un autre compte ne verra pas ces paquets.

N'utilisez pas `sudo pip install` dans le Python système. Certaines distributions
Linux interdisent par ailleurs `pip install --user` dans leur Python administré ;
dans ce cas, utilisez le virtualenv de la section 4.2 ou construisez un paquet selon
la procédure de votre distribution.

## 5. Configurer les variables d'environnement

ADM reconnaît les variables suivantes :

| Variable | Installation MySQL | Rôle |
| --- | --- | --- |
| `ADM_SECRET_KEY` | obligatoire | Signe les sessions Flask ; valeur longue, aléatoire et stable. |
| `ADM_DB_BACKEND` | obligatoire (`mysql`) | Sélectionne la persistance MySQL. |
| `ADM_DATABASE_URL` | obligatoire | URL SQLAlchemy de la base. |
| `ADM_ACCOUNTS_URL` | non utilisée | Réservée au chemin du fichier de comptes avec le backend JSON. |
| `ADM_CONFIG_PATH` | recommandée | Chemin persistant de `config.json` (seuils d'affichage, modifiables depuis `/settings`). Voir l'avertissement ci-dessous. |

`config.json` n'est pas une ressource figée : les seuils d'affichage y sont
réécrits à chaud lorsqu'un administrateur les modifie depuis `/settings`. Sans
`ADM_CONFIG_PATH`, ce fichier reste à son emplacement par défaut **à l'intérieur
du paquet installé** (le wheel, dans le virtualenv ou l'installation `--user`) :
toute mise à jour du wheel (section 12) le remplace intégralement et efface donc
silencieusement les seuils personnalisés. Définissez `ADM_CONFIG_PATH` vers un
chemin persistant, hors de l'arborescence du code (par exemple à côté de
`ADM_DATABASE_URL` en JSON/SQLite, ou dans un répertoire de données dédié pour
MySQL) : le fichier y est créé automatiquement à partir du gabarit empaqueté au
premier démarrage si nécessaire.

Générez la clé de session sans l'afficher ni la copier dans l'historique du shell,
par exemple directement dans le gestionnaire de secrets de l'hébergeur. Elle doit
rester identique entre deux redémarrages, faute de quoi toutes les sessions seront
invalidées.

La forme de l'URL est :

```text
mysql+mysqlconnector://<utilisateur>:<mot-de-passe-encode>@<hote>/<base>
```

Les caractères réservés du nom d'utilisateur, du mot de passe et du nom de base
doivent être encodés pour une URL (`@` devient `%40`, par exemple). Pour construire
l'URL sans exposer le mot de passe dans une commande, utilisez l'interface du
gestionnaire de secrets ou un outil local sûr, puis effacez toute copie temporaire.

### PythonAnywhere

Déclarez ces variables dans la configuration d'environnement du processus
Web si votre offre le permet. Sinon, définissez-les au tout début du fichier WSGI
privé fourni par l'onglet Web, avant l'import d'ADM :

```python
import os

os.environ["ADM_DB_BACKEND"] = "mysql"
os.environ["ADM_DATABASE_URL"] = "<url-sqlalchemy-fournie-comme-secret>"
os.environ["ADM_SECRET_KEY"] = "<cle-aleatoire-fournie-comme-secret>"
os.environ["ADM_CONFIG_PATH"] = "/home/<utilisateur>/adm-data/config.json"
```

Ce fichier est une configuration sensible : ne le placez pas dans Git, limitez-en
les droits d'accès et ne recopiez jamais son contenu dans des journaux ou captures.
Si un gestionnaire de secrets est disponible, préférez son injection automatique.

### Serveur Linux avec fichier d'environnement

Créez `/etc/adm/adm.env` avec le compte d'exploitation ou votre gestionnaire de
secrets, sans le versionner :

```text
ADM_DB_BACKEND=mysql
ADM_DATABASE_URL=mysql+mysqlconnector://<utilisateur>:<mot-de-passe-encode>@<hote>/<base>
ADM_SECRET_KEY=<cle-de-session-longue-et-aleatoire>
ADM_CONFIG_PATH=/var/lib/adm/config.json
```

```bash
sudo chown root:adm /etc/adm/adm.env
sudo chmod 640 /etc/adm/adm.env
```

Le gestionnaire du service WSGI doit charger ce fichier dans l'environnement du
processus, par exemple avec `EnvironmentFile=/etc/adm/adm.env` dans systemd.

`config.json` ne contient que les réglages non sensibles (seuils d'affichage et
valeurs par défaut). N'y ajoutez pas les secrets.

## 6. Vérifier la connexion sans révéler les secrets

Dans la console de déploiement, injectez les mêmes variables par le mécanisme sûr
de l'hébergeur. Vérifiez uniquement leur présence, jamais leur valeur :

```bash
test "$ADM_DB_BACKEND" = mysql
test -n "$ADM_DATABASE_URL"
test -n "$ADM_SECRET_KEY"
```

Sur PythonAnywhere, une console Bash et l'application Web n'ont pas forcément le
même environnement. Définissez donc aussi temporairement ces variables (ainsi que
`ADM_CONFIG_PATH` si vous l'utilisez, faute de quoi les commandes exécutées dans
cette console -- création de compte à l'étape 8, diagnostic -- retomberaient sur
le `config.json` empaqueté par défaut, distinct de celui utilisé par le processus
Web) dans la console qui exécutera les migrations, sans les enregistrer dans
l'historique.

## 7. Créer ou mettre à jour le schéma

Depuis la racine du dépôt, avec le virtualenv actif si vous en utilisez un :

```bash
cd /home/<utilisateur>/ADM
source /home/<utilisateur>/.virtualenvs/adm/bin/activate
alembic upgrade head
alembic current
```

Sur un serveur classique, adaptez les deux chemins à `/opt/adm/app` et
`/opt/adm/venv`. `alembic upgrade head` est la procédure de référence ; n'importez
pas manuellement `sql/create-db-mysql.sql`, qui ne remplace pas l'historique des
migrations. Sans virtualenv, exécutez `python3.11 -m alembic upgrade head`, puis
`python3.11 -m alembic current`, afin d'utiliser les modules installés à l'étape
4.3 même si `~/.local/bin` n'est pas dans `PATH`.

Pour un diagnostic sans afficher l'URL, utilisez le même interpréteur que lors de
l'installation. Avec le virtualenv recommandé :

```bash
/home/<utilisateur>/.virtualenvs/adm/bin/python -c "from ADM.app import create_app; create_app(); print('Initialisation ADM réussie')"
```

Sans virtualenv :

```bash
python3.11 -c "from ADM.app import create_app; create_app(); print('Initialisation ADM réussie')"
```

Une erreur `ModuleNotFoundError: No module named 'ADM'` à cette étape ne signale
pas un problème de chemin courant. Le projet utilise une arborescence `src/` : le
paquet devient importable après son installation dans l'environnement Python,
réalisée à l'étape 4. Vérifiez l'interpréteur et l'installation sans modifier
`PYTHONPATH`. Avec un virtualenv :

```bash
command -v python
/home/<utilisateur>/.virtualenvs/adm/bin/python -m pip show adm-catalogue
/home/<utilisateur>/.virtualenvs/adm/bin/python -c "import ADM; print(ADM.__file__)"
```

La première commande doit désigner
`/home/<utilisateur>/.virtualenvs/adm/bin/python` après activation. Si
`pip show` ne trouve pas le paquet, reprenez l'installation du wheel déjà vérifié
avec le même interpréteur :

```bash
/home/<utilisateur>/.virtualenvs/adm/bin/python -m pip install <repertoire-artefacts>/<nom-exact-du-wheel>.whl
```

Sans virtualenv, effectuez les mêmes contrôles avec `python3.11 -m pip show
adm-catalogue` et réinstallez si nécessaire avec `python3.11 -m pip install --user
<repertoire-artefacts>/<nom-exact-du-wheel>.whl`.

Contrôlez également le chemin de configuration calculé par le code effectivement
installé. Cette commande ne lit ni n'affiche aucun secret :

```bash
python3.11 -c "from ADM.app import PACKAGE_RESOURCES; print(PACKAGE_RESOURCES); print((PACKAGE_RESOURCES / 'config.json').is_file())"
```

Sans virtualenv, le premier résultat doit se terminer par
`.local/lib/python3.13/site-packages/ADM/resources` (en adaptant `python3.13` à la
version sélectionnée) et le second doit être `True`. Un chemin qui se termine
directement par `.local/lib/python3.13` identifie sans ambiguïté une ancienne
version défectueuse du paquet ; créer manuellement un `config.json` à cet endroit
masquerait le défaut de déploiement et n'est pas une correction.

Une version corrigée démarre désormais avec les valeurs non sensibles par défaut
si cette ressource est absente. Cette tolérance évite l'indisponibilité du site,
mais ne dispense pas de remplacer le wheel incomplet : les autres ressources du
paquet doivent également être présentes et la configuration doit rester
reproductible.

Si l’initialisation signale un `FileNotFoundError` sur un `config.json` situé à la
racine du virtualenv (par exemple `.virtualenvs/adm/lib/python3.13/config.json`),
le wheel installé est défectueux : il cherche les ressources relativement à
l'interpréteur au lieu de les charger depuis `ADM/resources`. C'est notamment le
cas de l'artefact construit depuis le tag `v1.4.0`. Le fait de changer de tag dans
le checkout ne remplace pas le paquet déjà installé dans le virtualenv.

Construisez et publiez depuis un tag corrigé un **nouvel** artefact avec la
procédure de l'étape 4, contrôlez sa somme et son contenu, puis forcez la
réinstallation de ce wheel précis. Ne réinstallez pas directement le checkout :
cela reconstruirait un artefact différent dans l'environnement cible.

```bash
# Avec virtualenv
/home/<utilisateur>/.virtualenvs/adm/bin/python -m pip install --no-cache-dir --force-reinstall <repertoire-artefacts>/<nouveau-wheel-corrige>.whl
/home/<utilisateur>/.virtualenvs/adm/bin/python -c "from ADM.app import create_app; create_app(); print('Initialisation ADM réussie')"

# Sans virtualenv
python3.11 -m pip install --user --no-cache-dir --force-reinstall <repertoire-artefacts>/<nouveau-wheel-corrige>.whl
python3.11 -c "from ADM.app import create_app; create_app(); print('Initialisation ADM réussie')"
```

Dans les deux modes, `create_app` utilise les ressources incluses à côté du module
`ADM` qui a réellement été importé. Il ne doit donc pas être nécessaire de copier
manuellement `config.json`, `static/` ou `templates/` à la racine du virtualenv ou
sous `~/.local/lib/python3.13`.

## 8. Créer le premier administrateur

Toujours dans le même environnement configuré :

```bash
# Les chemins scripts/... sont relatifs à la racine du dépôt.
cd /home/<utilisateur>/ADM

# Avec virtualenv actif
python scripts/create_account.py --username <nom-administrateur> --role admin

# Sans virtualenv
python3.11 scripts/create_account.py --username <nom-administrateur> --role admin
```

Le programme demande deux fois le mot de passe de manière interactive. Ne le
fournissez jamais en argument. Sans ce compte, il est impossible de se connecter.
Les comptes suivants pourront être administrés depuis l'interface par un
administrateur. Si le terminal se trouve dans un sous-dossier tel que
`src/ADM/resources`, revenez d'abord à la racine avec
`cd "$(git rev-parse --show-toplevel)"` : sinon Python cherchera à tort un dossier
`scripts` dans le répertoire courant.

## 9. Configurer l'application WSGI sur PythonAnywhere

Dans l'onglet **Web** :

1. créez une application Web en configuration manuelle (pas l'assistant Django) ;
2. choisissez la même version Python que celle utilisée pour installer ADM ;
3. indiquez `/home/<utilisateur>/.virtualenvs/adm` comme virtualenv, ou laissez ce
   champ vide si vous avez suivi l'installation `--user` de la section 4.3 ;
4. éditez le fichier de configuration WSGI et conservez l'injection des variables
   décrite à l'étape 5 ;
5. ajoutez ensuite le code suivant ;
6. configurez le mapping statique `/static/` vers
   `/home/<utilisateur>/ADM/src/ADM/resources/static` ;
7. rechargez l'application depuis l'onglet Web.

```python
from ADM.app import create_app

application = create_app()
```

Aucune manipulation de `sys.path` n'est nécessaire ni souhaitable ici : ADM est
importable directement dès lors que le wheel a été installé à l'étape 4 (dans le
virtualenv déclaré à l'étape 3, ou via `site-packages` utilisateur pour
l'installation `--user` de la section 4.3). Le paquet vit sous `src/ADM` dans le
dépôt : insérer `/home/<utilisateur>/ADM` dans `sys.path` n'apporterait donc rien
(ce n'est pas là que se trouve `ADM`) et va à l'encontre du principe de la
section 4.2. Si l'import échoue, la cause est toujours à chercher du côté de
l'installation du paquet, jamais d'un ajustement de `sys.path`.

Le nom `application` est celui attendu par le serveur WSGI. N'utilisez pas
`python main.py` en production : ce point d'entrée lance le serveur de
développement Flask, pas un serveur WSGI de production.

Si l'import `ADM` échoue, contrôlez en priorité la version Python, l'environnement
configuré dans l'onglet Web et le résultat de la commande correspondant à votre
mode d'installation :

```bash
# Avec virtualenv
/home/<utilisateur>/.virtualenvs/adm/bin/python -c "import ADM; print(ADM.__file__)"

# Sans virtualenv
python3.11 -c "import ADM; print(ADM.__file__)"
```

## 10. Validation fonctionnelle après déploiement

1. Ouvrez l'URL **HTTPS** du site et vérifiez que la page de connexion s'affiche.
2. Connectez-vous avec le compte administrateur initial.
3. Créez une application factice ne contenant aucune donnée personnelle.
4. Complétez une évaluation et vérifiez la synthèse et l'historique.
5. Déconnectez-vous, puis reconnectez-vous.
6. Supprimez la donnée factice si elle n'est plus utile.
7. Consultez les journaux du serveur en vérifiant qu'ils ne contiennent ni secret
   ni donnée personnelle.

Une erreur au chargement est souvent due à une variable absente, une URL MySQL mal
encodée, un hôte MySQL incorrect, une migration non appliquée ou une version Python
différente entre le virtualenv et l'application Web.

## 11. Sauvegarde et restauration

Avant l'ouverture du service, activez les sauvegardes MySQL de l'hébergeur et
testez une restauration sur une base isolée. Le dépôt fournit aussi :

```bash
# Avec virtualenv actif
python scripts/backup_restore.py backup
python scripts/backup_restore.py restore --file <fichier-de-sauvegarde>.sql

# Sans virtualenv
python3.11 scripts/backup_restore.py backup
```

Cette commande nécessite les clients `mysqldump`/`mysql`, installés séparément
sur la machine qui l'exécute (ils ne sont pas fournis par les dépendances Python
d'ADM). Elle réutilise directement `ADM_DATABASE_URL` : la base sauvegardée ou
restaurée est donc toujours celle réellement configurée pour l'application, sans
variable ni fichier de configuration supplémentaire à renseigner. Si le mot de
passe n'est pas inclus dans `ADM_DATABASE_URL`, définissez `ADM_DATABASE_PASSWORD`
en complément. Ne placez jamais un mot de passe dans la ligne de
commande ou le fichier exporté. Protégez les sauvegardes, chiffrez-les et appliquez
une politique de rétention. Un export fonctionnel depuis l'interface ne remplace
pas une sauvegarde complète et testée de MySQL.

## 12. Mises à jour et retour arrière

Avant toute mise à jour : sauvegardez MySQL, lisez les migrations et testez le tag
sur un environnement distinct. Construisez le nouveau wheel une seule fois avec la
procédure de la section 4, publiez-le, puis vérifiez et installez exactement ce même
artefact dans chaque environnement promu.

Avec le virtualenv :

```bash
cd /home/<utilisateur>/ADM
git fetch --tags
git checkout <nouveau-tag>
source /home/<utilisateur>/.virtualenvs/adm/bin/activate
cd <repertoire-artefacts>
sha256sum --check <nom-exact-du-wheel>.whl.sha256
python -m pip install <repertoire-artefacts>/<nom-exact-du-wheel>.whl
cd /home/<utilisateur>/ADM
python -m alembic upgrade head
```

Sans virtualenv, conservez explicitement l'interpréteur sélectionné à la section
4.3 pour l'installation et la migration :

```bash
cd /home/<utilisateur>/ADM
git fetch --tags
git checkout <nouveau-tag>
cd <repertoire-artefacts>
sha256sum --check <nom-exact-du-wheel>.whl.sha256
python3.11 -m pip install --user <repertoire-artefacts>/<nom-exact-du-wheel>.whl
cd /home/<utilisateur>/ADM
python3.11 -m alembic upgrade head
```

Rechargez ensuite le processus WSGI et refaites la validation fonctionnelle. Un
retour à un ancien tag peut être incompatible avec une migration déjà appliquée :
restaurez alors la sauvegarde correspondante selon une procédure testée, plutôt
que de lancer une migration descendante sans validation.

Si `ADM_CONFIG_PATH` n'est pas défini, la réinstallation du wheel ci-dessus
remplace `config.json` par le gabarit empaqueté : les seuils d'affichage
personnalisés depuis `/settings` sont alors réinitialisés à leurs valeurs par
défaut. Définissez `ADM_CONFIG_PATH` (section 5) avant la première mise en
production pour éviter cette perte silencieuse.

## 13. Exploitation et sécurité minimales

- imposez HTTPS et protégez l'accès au tableau de bord d'hébergement ;
- faites tourner l'application avec un compte système non privilégié ;
- limitez les accès réseau et MySQL au strict nécessaire ;
- renouvelez les secrets selon la politique de l'organisation (changer
  `ADM_SECRET_KEY` déconnecte tous les utilisateurs) ;
- appliquez régulièrement les correctifs Python, système et dépendances après
  tests sur un environnement séparé ;
- surveillez disponibilité, espace MySQL, erreurs HTTP et échecs de sauvegarde sans
  journaliser de données sensibles ;
- n'utilisez jamais le mode debug sur un serveur exposé ;
- conservez des sauvegardes chiffrées et vérifiez périodiquement leur restauration.

## 14. Variante locale SQLite (déploiement mono-processus)

SQLite fournit une installation persistante sans serveur de base de données. Le
catalogue, les évaluations et les comptes partagent un fichier relationnel unique.
Créez au préalable son répertoire, puis configurez une URL SQLAlchemy absolue :

```text
ADM_DB_BACKEND=sqlite
ADM_DATABASE_URL=sqlite:////chemin/persistant/adm.db
ADM_SECRET_KEY=<cle-de-session-longue-et-aleatoire>
```

`ADM_ACCOUNTS_URL` n'est pas utilisée avec SQLite. Le processus Web doit pouvoir
lire et écrire le fichier et son répertoire. Initialisez ensuite le schéma et le
premier compte comme pour MySQL :

```bash
cd /chemin/vers/ADM
alembic upgrade head
python scripts/create_account.py --username <nom-administrateur> --role admin
```

Arrêtez l'application avant de copier `adm.db` pour une sauvegarde cohérente. Cette
variante convient à un déploiement local avec un seul processus applicatif ; utilisez
MySQL lorsque plusieurs processus ou serveurs accèdent simultanément aux données.

## 15. Variante locale JSON (développement uniquement)

Pour une démonstration locale sans MySQL, utilisez les scripts documentés dans le
`README.md`. Si vous configurez manuellement le backend JSON, donnez des chemins
absolus vers un répertoire persistant et sauvegardé :

```text
ADM_DB_BACKEND=json
ADM_DATABASE_URL=/chemin/persistant/applications.json
ADM_ACCOUNTS_URL=/chemin/persistant/accounts.json
ADM_SECRET_KEY=<cle-de-session-longue-et-aleatoire>
```

Le processus Web doit avoir accès en lecture et écriture à ces deux fichiers et à
leur dossier. Ce mode est simple mais moins adapté à un service multi-processus ;
MySQL reste le backend recommandé pour PythonAnywhere ou un serveur équivalent.

## 16. Nettoyer ou remettre à plat une installation existante

Deux besoins distincts se présentent : repartir d'un environnement Python propre
en conservant les données (mise à jour ratée, environnement corrompu, changement
de mode d'installation), ou réinitialiser complètement une instance de test ou de
démonstration, données comprises. Ne confondez pas les deux : la seconde est
irréversible sans sauvegarde vérifiée (section 11).

### 16.1 Remettre à plat le code et l'environnement Python (données conservées)

Utile après un déploiement corrompu (par exemple le wheel défectueux décrit à
l'étape 7), un changement de virtualenv, ou un passage `--user` ↔ virtualenv. Les
données (MySQL, SQLite, JSON) et le fichier pointé par `ADM_CONFIG_PATH` ne sont
pas touchés par cette procédure.

**Avec virtualenv**

```bash
deactivate 2>/dev/null || true
rm -rf /home/<utilisateur>/.virtualenvs/adm
```

Puis reprenez l'installation à l'étape 4.1 (recréation du virtualenv,
réinstallation du wheel déjà vérifié).

**Sans virtualenv**

```bash
python3.11 -m pip uninstall -y adm-catalogue
```

Cette commande retire le module `ADM` et les métadonnées du paquet
(`adm_catalogue-*.dist-info`) de `~/.local/lib/python3.11/site-packages`. Elle ne
désinstalle pas ses dépendances (Flask, SQLAlchemy, Alembic, etc.) : les laisser
en place est sans risque, elles seront réutilisées par la réinstallation. Si des
fichiers résiduels subsistent (installations `--force-reinstall` répétées, par
exemple), supprimez-les explicitement :

```bash
rm -rf ~/.local/lib/python3.11/site-packages/ADM ~/.local/lib/python3.11/site-packages/adm_catalogue*
```

Puis reprenez l'installation à l'étape 4.3.

**Dans les deux cas**, purgez aussi le checkout Git s'il est suspect (build local
raté, fichiers non trackés) :

```bash
cd /home/<utilisateur>/ADM
git status  # vérifiez qu'aucune modification locale utile ne sera perdue
git clean -fdx
git checkout <tag-de-version>
```

`git clean -fdx` supprime tout fichier non versionné du dépôt : `dist/`,
`build/`, `*.egg-info`, les caches (`__pycache__`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`), ainsi que les résidus laissés par
`scripts/setup_demo.sh`/`.ps1` si vous les avez exécutés dans ce même dossier
(`.venv/`, `.adm-demo.env`, `.adm-demo.json`, `applications.json`,
`accounts.json`, `src/ADM/resources/static/version.txt`). Ne l'utilisez jamais
dans un dossier qui contient aussi les fichiers `applications.json`/`accounts.json`
**persistants** d'une installation JSON en production (section 15) : ces fichiers
doivent toujours vivre hors du checkout, comme documenté, pour éviter ce risque.

Pour réinitialiser uniquement les seuils d'affichage sans toucher au reste,
supprimez le fichier pointé par `ADM_CONFIG_PATH` (ou le `config.json` embarqué
si vous ne l'utilisez pas) : il est recréé automatiquement à partir du gabarit
empaqueté au démarrage suivant (section 5).

```bash
rm -f "$ADM_CONFIG_PATH"
```

Dans tous les cas, rechargez le processus WSGI depuis l'onglet **Web** de
PythonAnywhere (ou redémarrez le service sur un serveur classique) : le code et
la configuration réinstallés ne sont pris en compte qu'après ce redémarrage.

### 16.2 Réinitialiser complètement une installation (données comprises)

**Irréversible.** Sauvegardez d'abord si les données ont la moindre valeur
(section 11). Cette procédure convient à un environnement de démonstration, de
Qualification ou de Recette que l'on souhaite remettre à zéro -- jamais à une
Production sans sauvegarde vérifiée.

Effectuez d'abord la remise à plat du code (16.1), puis supprimez les données
selon le backend utilisé :

**MySQL**

```sql
DROP DATABASE adm;
CREATE DATABASE adm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Recréez ensuite le compte MySQL dédié s'il a été supprimé avec la base
(section 3.2), puis reprenez à l'étape 7 (`alembic upgrade head`) pour recréer le
schéma. Ne supprimez pas seulement les tables `applications`/`evaluations`/
`accounts` une par une : la table `alembic_version` resterait désynchronisée et
empêcherait une réinitialisation propre de l'historique des migrations.

**SQLite**

```bash
rm -f /chemin/persistant/adm.db
```

Reprenez ensuite à l'étape 14 (`alembic upgrade head`, puis création du premier
compte).

**JSON**

```bash
rm -f /chemin/persistant/applications.json /chemin/persistant/accounts.json
```

Ces deux fichiers sont recréés vides au prochain démarrage de l'application
(section 15).

**Dans tous les cas**, recréez ensuite le premier compte administrateur
(section 8) : sans lui, personne ne peut plus se connecter.

### 16.3 Décommissionner complètement une instance PythonAnywhere

Pour retirer entièrement ADM d'un compte PythonAnywhere :

1. dans l'onglet **Web**, désactivez puis supprimez l'application Web (cela
   retire aussi le mapping statique `/static/`) ;
2. supprimez la base MySQL dans l'onglet **Databases**, après une dernière
   sauvegarde si nécessaire ;
3. supprimez le virtualenv (`rm -rf /home/<utilisateur>/.virtualenvs/adm`) ou
   désinstallez le paquet `--user` (16.1) ;
4. supprimez le checkout (`rm -rf /home/<utilisateur>/ADM`) ainsi que tout
   fichier `ADM_CONFIG_PATH` ou fichier JSON persistant situé en dehors de ce
   dossier ;
5. révoquez `ADM_SECRET_KEY` et les identifiants MySQL dans le gestionnaire de
   secrets utilisé.
