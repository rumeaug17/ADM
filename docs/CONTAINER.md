# Livrable conteneurisé et déploiement Kubernetes

Ce guide décrit le livrable conteneurisé d'ADM (Tâche 0.3 du backlog) : image
Docker, manifestes Kubernetes fournis dans `k8s/`, et procédure de déploiement,
de mise à jour et de sauvegarde correspondante. Il complète
[`INSTALL.md`](../INSTALL.md) (installation traditionnelle par wheel) et
[`docs/CODING_GUIDELINES.md`](CODING_GUIDELINES.md) (cycle de vie et gestion des
versions), dont les principes s'appliquent ici sans changement : le même
artefact est promu de Qualification à Production, seule la configuration
change.

> ADM est un démonstrateur (voir `README.md`). Les manifestes fournis dans
> `k8s/` sont un point de départ standard, pas une configuration prête pour un
> cluster de production précis : adaptez ressources, classe de stockage,
> politique réseau et exposition HTTPS à votre environnement.

## 1. Principe : une image dérivée d'un wheel déjà construit

Le `Dockerfile` n'installe **jamais** ADM depuis les sources. Il installe le
wheel déjà construit et vérifié par le job `build` du pipeline (voir
`.gitlab-ci.yml`), exactement comme les installations traditionnelles décrites
dans `INSTALL.md`. L'image est donc un second emballage du même artefact
immuable, pas un artefact concurrent : un wheel qui a échoué à la construction,
au contrôle du contenu ou aux tests ne peut pas devenir une image utilisable.

En local, avant `docker build`, reproduisez ce que fait le job `build` :

```bash
git checkout <tag-de-version>
python -m pip install --upgrade build
git describe --tags --always > src/ADM/resources/static/version.txt
python -m build --wheel
docker build -t adm:<tag-de-version> .
```

Le `Dockerfile` échoue explicitement si `dist/` ne contient aucun wheel : ne
contournez jamais cette vérification en copiant `src/` dans l'image à la place.

## 2. Construire et publier l'image depuis la CI

Le job `build-image` du pipeline (voir `.gitlab-ci.yml`) réutilise l'artefact
du job `build` via `needs:artifacts`, sans reconstruire le wheel, puis publie
l'image dans le registre de conteneurs GitLab avec deux étiquettes, le tag Git
(`$CI_COMMIT_TAG`) et `latest`, en affichant au passage l'empreinte SHA-256 du
wheel embarqué pour permettre de vérifier qu'il s'agit bien du même artefact
que celui publié par le job `build`. Comme les jobs `deploy-*`, il ne se
déclenche que sur un tag protégé de `main`.

L'image publiée est ensuite celle référencée, sans modification, par les
Déploiements de Qualification, Recette et Production — via le champ `newTag`
de `k8s/kustomization.yaml` (section 4).

## 3. Variables d'environnement et secrets

Les mêmes variables que l'installation traditionnelle s'appliquent (voir
`README.md`, section Configuration, et `INSTALL.md` section 5), réparties entre
`k8s/configmap.yaml` (non sensible) et un `Secret` (sensible) :

| Variable | Emplacement | Rôle |
| --- | --- | --- |
| `ADM_SECRET_KEY` | Secret | Signe les sessions Flask. |
| `ADM_DATABASE_URL` | Secret | URL SQLAlchemy MySQL, mot de passe inclus. |
| `ADM_DB_BACKEND` | ConfigMap | `mysql` par défaut dans le gabarit fourni. |
| `ADM_CONFIG_PATH` | ConfigMap | `/var/lib/adm/config.json`, sur la PVC montée (section 5). |
| `ADM_HTTP_PORT` | ConfigMap | Port d'écoute de gunicorn dans le conteneur (`8000` par défaut). |
| `ADM_GUNICORN_WORKERS` | ConfigMap | Nombre de workers gunicorn (`2` par défaut). |

`k8s/secret.example.yaml` est un **gabarit** avec des valeurs factices, jamais
appliqué directement (voir `kustomization.yaml`). Avant tout déploiement :

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
# éditez k8s/secret.yaml avec vos propres valeurs
```

`k8s/secret.yaml` est exclu de Git (`.gitignore`) : ne le committez jamais, même
rempli. En Production, préférez l'injection par le gestionnaire de secrets de
votre organisation (External Secrets Operator, Sealed Secrets, Vault, etc.)
plutôt qu'un `Secret` Kubernetes en clair versionné localement, même ignoré par
Git — cette règle prolonge `docs/CODING_GUIDELINES.md`, règle 5.

## 4. Déployer sur Kubernetes

Éditez `k8s/kustomization.yaml` pour pointer `images:` vers votre registre et
le tag à déployer (celui publié par `build-image`, section 2), puis :

```bash
cp k8s/secret.example.yaml k8s/secret.yaml   # une fois, voir section 3
# éditez k8s/secret.yaml

kubectl apply -k k8s/                        # crée ConfigMap, Secret, PVC, Service, Deployment
kubectl delete job/adm-migrate --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/adm-migrate --timeout=120s
```

`k8s/migration-job.yaml` exécute `alembic upgrade head` (voir `docker-entrypoint.sh`
et `INSTALL.md` section 7) une seule fois, séparément du `Deployment` : ne
déclenchez jamais les migrations depuis plusieurs répliques simultanément. Les
Jobs étant immuables, celui-ci est supprimé puis recréé à chaque déploiement
plutôt que réutilisé ; c'est sans risque, `alembic upgrade head` ne faisant rien
si le schéma est déjà à jour. Attendez que le Job se termine avant de
considérer le déploiement prêt.

Créez ensuite le premier compte administrateur, comme documenté dans
`INSTALL.md` section 8, mais depuis un pod du Deployment :

```bash
kubectl exec -it deploy/adm -- docker-entrypoint.sh create-account --username <nom-administrateur> --role admin
```

Le mot de passe est demandé de manière interactive (jamais en argument ni en
variable d'environnement). Sans ce compte, aucune connexion à l'interface n'est
possible.

## 5. Persistance de `config.json`

`ADM_CONFIG_PATH` pointe vers `k8s/pvc.yaml`, une `PersistentVolumeClaim`
`ReadWriteOnce` montée sur `/var/lib/adm`. Elle est recréée automatiquement à
partir du gabarit empaqueté au premier démarrage si le fichier est absent (même
comportement que l'installation traditionnelle, voir `README.md`). Aucune autre
donnée n'y transite : le catalogue, les évaluations et les comptes vivent dans
MySQL, jamais sur cette PVC.

Le catalogue, les évaluations et les comptes doivent être sauvegardés au niveau
de MySQL (`INSTALL.md` section 11), pas au niveau de cette PVC : elle ne
contient que des seuils d'affichage reconstructibles.

## 6. Faire évoluer le nombre de répliques

`k8s/deployment.yaml` démarre volontairement avec `replicas: 1` : une PVC
`ReadWriteOnce` ne garantit pas qu'elle puisse être montée en écriture par des
pods répartis sur plusieurs nœuds. Deux options pour dépasser une réplique :

- utiliser une classe de stockage `ReadWriteMany` (NFS, CephFS, etc.) pour
  `k8s/pvc.yaml`, si votre cluster en fournit une ;
- ou renoncer à la persistance de `config.json` en ne montant pas la PVC : les
  seuils d'affichage restent alors ceux définis dans `k8s/configmap.yaml`
  (`display_thresholds` du `config.json` embarqué), et toute modification faite
  depuis `/settings` est perdue au redémarrage du pod — acceptable si ces
  seuils sont gérés par la configuration versionnée plutôt que depuis
  l'interface.

Dans les deux cas, `ADM_DB_BACKEND=mysql` reste indispensable dès plusieurs
répliques ou plusieurs processus (voir `README.md`) : ni SQLite ni le backend
JSON ne conviennent à un déploiement Kubernetes à plusieurs répliques.

## 7. Sondes de vivacité et de disponibilité

La route publique `GET /healthz` vérifie que l'application peut effectuer une
lecture sur son backend de persistance. Elle renvoie `200` et
`{"status":"ok"}` lorsque le service est disponible, ou `503` et
`{"status":"unavailable"}` lorsque la persistance ne répond pas. La réponse
ne contient ni détail de connexion ni donnée métier. `k8s/deployment.yaml`
utilise cette route pour ses `readinessProbe` et `livenessProbe`.

## 8. Sécurité du conteneur

- Utilisateur non privilégié dédié (`uid`/`gid` 1000), jamais `root`, cohérent
  avec `INSTALL.md` section 13.
- `readOnlyRootFilesystem: true` sur les deux conteneurs (`adm`, `migrate`) ;
  seuls `/var/lib/adm` (PVC, `config.json`) et `/tmp` (`emptyDir`, cache de
  polices matplotlib pour le radar chart) sont montés en écriture.
- `allowPrivilegeEscalation: false` et toutes les capacités Linux retirées
  (`capabilities.drop: ["ALL"]`).
- Aucun secret dans `k8s/configmap.yaml` ni dans l'image : voir section 3.
- HTTPS n'est pas géré par l'application elle-même (voir `INSTALL.md`
  section 13, « imposez HTTPS ») : terminez TLS au niveau de l'Ingress ou d'un
  load-balancer, voir `k8s/ingress.example.yaml`.

## 9. Exposition HTTPS

`k8s/ingress.example.yaml` est un **gabarit** non appliqué par défaut (commenté
dans `kustomization.yaml`), pour un contrôleur `ingress-nginx` et cert-manager.
Adaptez au minimum le nom d'hôte, `ingressClassName` et l'émetteur TLS à votre
cluster, puis décommentez la ressource dans `kustomization.yaml`.

## 10. Mise à jour et retour arrière

Le principe est identique à `INSTALL.md` section 12 (même artefact promu, sans
reconstruction), transposé à l'image :

```bash
# 1. Mettre à jour le tag dans k8s/kustomization.yaml (newTag) vers la nouvelle version
kubectl apply -k k8s/
# 2. Rejouer le Job de migration de cette nouvelle version avant tout rollout
kubectl delete job/adm-migrate --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/adm-migrate --timeout=120s
# 3. Ne relancer le rollout du Deployment qu'une fois le Job de migration terminé
kubectl rollout restart deployment/adm
kubectl rollout status deployment/adm
```

Un retour à une version antérieure peut être incompatible avec une migration
déjà appliquée : restaurez la sauvegarde MySQL correspondante selon une
procédure testée plutôt que de revenir à une image plus ancienne sans
validation (même avertissement qu'`INSTALL.md` section 12).

## 11. Limites connues de ce livrable

- Sauvegarde/restauration MySQL (`scripts/backup_restore.py`) nécessite les
  clients `mysqldump`/`mysql`, volontairement absents de l'image applicative
  (image minimale) : exécutez ces opérations depuis un outil d'exploitation ou
  une image dérivée qui les fournit, jamais depuis le conteneur `adm` en
  production.
- Pas de sonde de supervision dédiée tant que la Tâche 3.5 n'est pas réalisée
  (section 7).
- Pas de `NetworkPolicy`, de `PodDisruptionBudget` ni de `HorizontalPodAutoscaler`
  fournis : à ajouter selon les standards de votre cluster si nécessaire.
