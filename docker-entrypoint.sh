#!/bin/sh
# Point d'entrée de l'image ADM (Tâche 0.3 du backlog).
#
# Le même wheel embarqué dans l'image sert aussi bien au serveur web qu'aux
# opérations d'administration : ce script ne fait qu'orienter vers la bonne
# commande, sans dupliquer de logique métier. Voir docs/CONTAINER.md pour le
# détail de chaque sous-commande et son usage en Job/initContainer Kubernetes.

set -eu

command="${1:-web}"
if [ "$#" -gt 0 ]; then
    shift
fi

case "$command" in
    web)
        # gunicorn en production (jamais `python main.py`, réservé au serveur
        # de développement, voir INSTALL.md section 9). ADM_CONFIG_PATH,
        # ADM_DATABASE_URL, ADM_SECRET_KEY, ADM_DB_BACKEND sont fournis par
        # l'environnement (ConfigMap/Secret Kubernetes, voir k8s/).
        exec gunicorn \
            --bind "0.0.0.0:${ADM_HTTP_PORT:-8000}" \
            --workers "${ADM_GUNICORN_WORKERS:-2}" \
            --access-logfile - \
            --error-logfile - \
            "ADM.app:create_app()"
        ;;
    migrate)
        # Migration du schéma (INSTALL.md section 7). À exécuter comme Job ou
        # initContainer distinct du Deployment, jamais concurremment par
        # plusieurs réplicas (voir k8s/migration-job.yaml).
        exec alembic upgrade head
        ;;
    create-account)
        # Équivalent conteneurisé de scripts/create_account.py (INSTALL.md
        # section 8) : mot de passe demandé de façon interactive, jamais en
        # argument ni en variable d'environnement. Nécessite un terminal
        # interactif (docker run -it / kubectl exec -it), voir docs/CONTAINER.md.
        exec python -c "from ADM.cli import create_account_command; create_account_command()" "$@"
        ;;
    backup)
        # Nécessite le client mysqldump, absent de cette image (voir
        # Dockerfile) : à exécuter depuis une image dérivée ou un outil
        # d'exploitation qui le fournit.
        exec python scripts/backup_restore.py backup "$@"
        ;;
    restore)
        # Mêmes prérequis que `backup` (client mysql).
        exec python scripts/backup_restore.py restore "$@"
        ;;
    shell)
        exec python "$@"
        ;;
    *)
        # Toute autre commande est exécutée telle quelle, pour le diagnostic,
        # par exemple :
        #   docker run --rm adm:local python -c "import ADM; print(ADM.__file__)"
        exec "$command" "$@"
        ;;
esac
