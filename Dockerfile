\
# syntax=docker/dockerfile:1.7
#
# Image de production d'ADM (Tâche 0.3 du backlog : livrable en mode conteneur).
#
# Conformément à docs/CODING_GUIDELINES.md (« un artefact ne doit jamais être
# recompilé entre deux environnements »), cette image n'installe jamais ADM
# depuis les sources : elle installe le wheel déjà construit et vérifié par le
# job `build` du pipeline (voir .gitlab-ci.yml), ou par
# `python -m build --wheel` en local. Le même wheel promu de Qualification à
# Production via INSTALL.md est donc celui embarqué dans cette image ; seule la
# configuration (variables d'environnement, secrets) change entre environnements.
#
# Construction locale, depuis la racine du dépôt :
#   git describe --tags --always > src/ADM/resources/static/version.txt
#   python -m pip install --upgrade build
#   python -m build --wheel
#   docker build -t adm:local .
#
# Détails d'exécution, de configuration et de déploiement Kubernetes :
# voir docs/CONTAINER.md.

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/tmp/matplotlib

# Compte non privilégié dédié : voir docs/CONTAINER.md et INSTALL.md section 13
# (« faites tourner l'application avec un compte système non privilégié »).
# Crée le groupe adm s'il n'existe pas déjà, puis crée l'utilisateur s'il n'existe pas
RUN groupadd -g 1000 -f adm \
    && id -u adm >/dev/null 2>&1 || useradd --uid 1000 --gid adm --create-home --shell /usr/sbin/nologin adm

WORKDIR /app

# Un seul wheel est attendu dans dist/ (celui produit par le job `build`, ou par
# `python -m build --wheel` en local) ; l'échec de ce COPY signale une
# reconstruction manquante, pas une image à corriger silencieusement.
COPY dist/*.whl /tmp/dist/
RUN WHEEL="$(ls /tmp/dist/*.whl)" \
    && python -m pip install --no-cache-dir "${WHEEL}[container]" \
    && rm -rf /tmp/dist

# Ressources nécessaires à l'exécution mais non embarquées dans le wheel :
# migrations Alembic (INSTALL.md section 7) et script de sauvegarde/restauration
# MySQL (INSTALL.md section 11 ; nécessite les clients mysqldump/mysql, absents
# de cette image, voir docs/CONTAINER.md). scripts/create_account.py n'est
# volontairement pas copié : il charge le paquet depuis un checkout src/ absent
# de cette image (voir README.md) ; l'entrypoint utilise à la place
# ADM.cli.create_account_command, déjà embarqué dans le wheel installé ci-dessus.
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts/backup_restore.py ./scripts/backup_restore.py

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /tmp/matplotlib \
    && chown -R adm:adm /app /tmp/matplotlib

USER adm

EXPOSE 8000

# Pas de volume déclaré ici pour ADM_CONFIG_PATH : le chemin concret dépend de
# l'orchestrateur (PersistentVolumeClaim Kubernetes, voir k8s/deployment.yaml
# et docs/CONTAINER.md).

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["web"]
