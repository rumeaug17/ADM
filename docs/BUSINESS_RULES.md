# Invariants métier du catalogue ADM

## Questionnaire

- Une catégorie possède un nom non vide et contient des questions nommées.
- Une question utilisable possède un libellé, un type, au moins une option et un
  poids entier strictement positif. Le poids vaut `1` lorsqu'il est omis.
- Une option possède une valeur non vide et un score entier, ou `null` pour
  « Non applicable ». Une même valeur d'option conserve le même score dans tout
  le questionnaire.
- Les filtres `app_types` et `hosting_types`, lorsqu'ils existent, sont des listes
  non vides. Leur comparaison ignore la casse et les espaces périphériques.

## Gestion des questions (US4.3)

La page `/settings/questions` (rôle `admin`) permet d'ajouter, modifier et
supprimer une question au sein d'une catégorie déjà existante : libellé, poids,
options et leurs scores, filtres `app_types`/`hosting_types`, et aide en ligne.
Dans un premier temps, les catégories elles-mêmes ne sont pas gérées par cette
page : ni création, ni renommage, ni suppression de catégorie.

La clé technique d'une question (ex. `api`) est fixée à sa création et n'est
plus modifiable ensuite : elle identifie les réponses déjà enregistrées dans
l'historique des évaluations existantes. Supprimer une question ne supprime
pas ces réponses historiques ; elles cessent seulement d'être affichées et
scorées. Toute modification revalide l'intégralité du questionnaire résultant
(pas seulement la question modifiée), afin qu'une même valeur de réponse
conserve le même score partout.

`questions.json` et l'aide en ligne (`info_texts.json`) sont réécrits à chaud
par cette page, sans redémarrage : comme `config.json` (US4.2), ils peuvent
être stockés hors du paquet installé via `ADM_QUESTIONS_PATH` et
`ADM_INFO_TEXTS_PATH`, pour qu'une mise à jour du paquet n'efface pas les
modifications apportées en production.

## Calcul des scores

Le score brut d'une évaluation est la somme `score de l'option × poids` des
réponses applicables. Une réponse dont le score vaut `null` ne contribue ni à la
somme ni au nombre de réponses. Le maximum affiché est actuellement calculé à
`nombre de réponses × 3` ; le pourcentage est le rapport entre le score brut et
ce maximum. Cette convention suppose donc une échelle standard de 0 à 3.

Les synthèses par axe appliquent le poids à chaque réponse, puis calculent la
moyenne des questions renseignées de l'axe. Une application sans réponse
applicable ne contribue pas à la moyenne.

La moyenne globale du catalogue porte uniquement sur les applications évaluées.
Les applications dont le score est absent ne sont donc pas assimilées à un score
nul, mais restent comptabilisées dans le nombre total d'applications.

## Risque

Le risque combine le score, les quatre niveaux DICP/P et la criticité :

```text
risque = score × (((D × I × C × P) / 4 / criticité) / 2)
```

La criticité doit être non nulle. Une donnée absente, mal formée ou une criticité
nulle produit un risque indéterminé (`None`) plutôt qu'une estimation trompeuse.

## Import

La réimportation totale (route `/import_data`) est réservée aux comptes de rôle
`admin` : elle supprime intégralement le catalogue existant avant d'y substituer le
contenu du fichier importé, dans une transaction unique.

La racine est une liste JSON. Tous les enregistrements et leur historique sont
validés avant la transaction d'écriture : dates ISO, entiers réels (les booléens
sont refusés), objets de réponses/commentaires à clés textuelles et champs requis.
Ainsi, un seul enregistrement invalide annule l'import complet.

## Configuration des seuils d'affichage

Les seuils `warning` et `critical` (score et risque) sont des nombres positifs
ou nuls, avec `warning` strictement inférieur à `critical`. La page `/settings`
ne modifie que la clé `display_thresholds` de `config.json` : les paramètres de
déploiement (`db_backend`, `json_connection_url`) restent en lecture seule et se
changent uniquement par variable d'environnement, suivie d'un redémarrage.

## Comptes et authentification

Le fournisseur d'authentification est sélectionné par `auth_backend`
(`config.json`) : `local` aujourd'hui, `ldap`/`oidc` reconnus mais non
implémentés — leur sélection échoue explicitement au démarrage plutôt que de
retomber silencieusement sur l'authentification locale.

Pour le fournisseur `local`, un compte a un rôle (`admin`, `user` ou `readonly`) et un
état actif/inactif. **Il doit toujours exister au moins un compte admin
actif** : la rétrogradation, la désactivation ou la suppression du dernier
compte admin actif est refusée.

Le rôle `readonly` (US6.4) permet une connexion en consultation uniquement :
l'accès aux pages de lecture (catalogue, résumé d'application, synthèse, exports
CSV/JSON) reste ouvert comme pour `user`, mais toute action de modification est
refusée avec une erreur 403, qu'elle porte sur une application (ajout,
modification, suppression), sur une notation (évaluation, réinitialisation,
réévaluation globale) ou sur la configuration. Ce dernier point est déjà couvert
par l'exigence du rôle `admin` ci-dessous, à laquelle `readonly` ne satisfait
pas plus que `user`.

Les comptes ne transitent jamais par l'import/export du catalogue
(`ADM.catalogue_io`) : leur stockage est isolé, dans un fichier ou une table
dédiés.

Le rôle `admin` est requis pour accéder à la configuration (`/settings`), pour
la réimportation totale du catalogue (`/import_data`, voir la section Import
ci-dessus), et pour la gestion des questions (`/settings/questions`, voir
« Gestion des questions (US4.3) » ci-dessus).
Aucun compte n'existe par défaut à l'installation : le premier compte
administrateur doit être créé explicitement via `scripts/create_account.py`
avant la première connexion.
