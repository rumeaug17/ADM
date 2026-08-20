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

## Calcul des scores

Le score brut d'une évaluation est la somme `score de l'option × poids` des
réponses applicables. Une réponse dont le score vaut `null` ne contribue ni à la
somme ni au nombre de réponses. Le maximum affiché est actuellement calculé à
`nombre de réponses × 3` ; le pourcentage est le rapport entre le score brut et
ce maximum. Cette convention suppose donc une échelle standard de 0 à 3.

Les synthèses par axe appliquent le poids à chaque réponse, puis calculent la
moyenne des questions renseignées de l'axe. Une application sans réponse
applicable ne contribue pas à la moyenne.

## Risque

Le risque combine le score, les quatre niveaux DICP/P et la criticité :

```text
risque = score × (((D × I × C × P) / 4 / criticité) / 2)
```

La criticité doit être non nulle. Une donnée absente, mal formée ou une criticité
nulle produit un risque indéterminé (`None`) plutôt qu'une estimation trompeuse.

## Import

La racine est une liste JSON. Tous les enregistrements et leur historique sont
validés avant la transaction d'écriture : dates ISO, entiers réels (les booléens
sont refusés), objets de réponses/commentaires à clés textuelles et champs requis.
Ainsi, un seul enregistrement invalide annule l'import complet.
