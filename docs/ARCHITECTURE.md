# Architecture de l'application ADM

## Découpage et dépendances

Le point d'entrée `main.py` appelle uniquement la fabrique `ADM.app.create_app`. La
fabrique lit la configuration, initialise le backend demandé et injecte dans Flask
la fabrique de sessions ainsi que le questionnaire pré-calculé.

```text
main.py → ADM.app → ADM.routes → ADM.services / ADM.validation / ADM.catalogue_io
                    ↓
              ADM.persistence → ADM.database ou ADM.database_json
```

Les dépendances vont de l'orchestration vers le métier et les contrats de
persistance. `ADM.services`, `ADM.scoring`, `ADM.schemas` et `ADM.validation` ne
dépendent pas de Flask. Les templates ne contiennent que la présentation. Les deux
backends exposent le sous-ensemble de session consommé par les routes.

## Responsabilités

| Module | Responsabilité |
| --- | --- |
| `ADM.app` | Fabrique Flask, configuration, injection et erreurs HTTP. |
| `ADM.routes` | Blueprints et orchestration courte d'une requête HTTP. |
| `ADM.services` | Calculs de score, métriques, synthèse et données d'évaluation. |
| `ADM.scoring` | Construction du barème et filtrage du questionnaire. |
| `ADM.validation` / `ADM.schemas` | Validation des formulaires et documents externes. |
| `ADM.catalogue_io` | Import et export atomiques du catalogue. |
| `ADM.persistence` | Cycle commit, rollback et fermeture d'une transaction. |
| `ADM.database` / `ADM.database_json` | Adaptateurs SQLAlchemy et JSON. |
| `ADM.config_io` | Lecture/écriture atomique de la configuration non sensible (`config.json`). |
| `ADM.accounts_service` | Opérations métier sur les comptes (création, rôle, invariant du dernier admin). |
| `ADM.accounts_json` | Persistance JSON dédiée aux comptes, isolée du catalogue. |
| `ADM.auth_providers` | Sélection et exécution du fournisseur d'authentification (`local`, extensible). |
| `scripts` | Commandes ponctuelles, sans responsabilité métier web. |

## Parcours d'une requête

1. Flask sélectionne un blueprint dans `ADM.routes` et vérifie la session et le
   jeton CSRF.
2. La route valide les entrées, ouvre une session injectée et charge les modèles.
3. Elle délègue les calculs aux services indépendants de Flask.
4. Une écriture est validée en une transaction ; une erreur attendue est annulée et
   traduite en message utilisateur générique.
5. La route ferme la session puis rend un template, une redirection ou un export.

## Vocabulaire par couche

Le domaine et l'interface utilisent les termes français **application**,
**évaluation**, **question**, **réponse**, **commentaire**, **synthèse** et
**criticité**. Le code d'infrastructure emploie l'anglais usuel (`session`,
`backend`, `commit`, `rollback`, `request`, `response`). Les identifiants historiques
`rda`, `type_app`, `hosting`, `score`, `responses`, `comments` et `evaluator_name`
sont conservés car ils font partie du schéma SQL, du format JSON ou des formulaires.
Ils ne doivent pas être renommés isolément : une migration de schéma et une version
du contrat d'import seraient nécessaires.

## Points d'entrée

- application web : `python main.py` ;
- documentation : `python scripts/generate_md_doc.py` ;
- sauvegarde/restauration : `python scripts/backup_restore.py` ;
- données factices JSON : `python scripts/generate_data_json.py` ;
- données factices MySQL : `python scripts/generate_data_mysql.py [nombre]`.

Les anciens scripts `generate-data-json.py` et `generate-data-mysql.py` à la racine
ont été remplacés par ces deux dernières commandes.
