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

## Profil de sensibilité et analyse de risques

Chaque application porte quatre niveaux de 1 à 4 — disponibilité (`D`),
intégrité (`I`), confidentialité (`C`) et pérennité attendue (`P`) — ainsi
qu'une criticité. Cette **sensibilité DICPé** (le « é » signale que le 4ᵉ
critère est la Pérennité) est une estimation déclarative,
saisie dans ADM par les utilisateurs habilités à modifier une fiche, et sert
uniquement à pondérer la dette technique (voir « Exposition dette » ci-dessous).

Il ne doit pas être confondu avec la classification DICP issue de l'analyse de
risques de l'organisation (RSSI, EBIOS RM / ISO 27005) :

- le 4ᵉ critère d'ADM est la **Pérennité** (conservation de l'application et
  de ses données sur le long terme), alors que celui de l'analyse de risques
  est généralement la **Preuve** (traçabilité) ;
- les définitions des niveaux sont propres à ADM (`info_texts.json`) et ne
  sont pas synchronisées avec l'analyse officielle.

L'interface le rend explicite : section « Criticité et sensibilité DICPé
(estimation ADM) » dans les formulaires, colonne « Sensibilité DICPé » du
catalogue et ligne « Sensibilité DICPé (estimation ADM) » du résumé, où les
quatre pastilles restent regroupées côte à côte (`D3` `I1` `C2` `Pé4`), la
pérennité étant affichée `Pé1`…`Pé4` (le code stocké reste `P1`…`P4`) ;
avertissement dans les formulaires, le résumé et l'aide en ligne ; en-têtes
de l'export CSV renommés (« DICPé - Disponibilité »… « DICPé - Pérennité
attendue », « Exposition dette »). Les clés techniques
(`disponibilite`…`perennite`), les codes stockés, l'import/export JSON et le
schéma de base sont inchangés.

L'échelle de criticité est inverse de celle du profil : le niveau `1` est le
plus critique, le niveau `4` le moins critique. L'aide en ligne le rappelle.

## Exposition dette

L'exposition dette (clé technique `risque`, libellée « Exposition dette » dans
l'interface et l'export CSV, « Exposition globale » pour la moyenne du
catalogue) combine le score, les quatre niveaux de la sensibilité DICPé et la
criticité. Ce n'est pas un risque de sécurité au sens de l'analyse de risques :

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
