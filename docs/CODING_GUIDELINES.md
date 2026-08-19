# Guide de développement Python

Ce document définit le socle minimal de qualité applicable au projet **Exemple Python Project DF**.

Le code doit respecter **PEP 8** : indentation de quatre espaces, conventions de nommage, imports organisés, lignes raisonnablement courtes, commentaires utiles et priorité donnée à la lisibilité.

## Les sept règles du projet

| Règle | Raison | À éviter |
| --- | --- | --- |
| **1. Fonctions courtes, sans variables globales modifiables** | Facilite la compréhension, les tests et la réutilisation. | État global et effets de bord cachés. |
| **2. Noms explicites** | Rend le code compréhensible sans interprétation. | `x`, `tmp`, `data1`. |
| **3. Validation et erreurs explicites** | Évite de produire silencieusement un résultat faux. | `except:` générique et entrées non contrôlées. |
| **4. Séparer métier et technique** | Permet de tester les calculs sans Airflow ni système externe. | Calcul métier mêlé aux fichiers, API ou bases. |
| **5. Protéger secrets et données sensibles** | Évite les fuites dans Git, les logs et les prompts. | Secrets en dur et données réelles dans les tests. |
| **6. Limiter et documenter les dépendances** | Réduit les risques et améliore la reproductibilité. | Dépendance inutile, non déclarée ou non maîtrisée. |
| **7. Code simple, lisible et testable** | Facilite la maintenance dans la durée. | Duplication, complexité et absence de tests. |

## Gestion des secrets

Ne jamais mettre de secret, notamment un mot de passe ou un jeton, dans le code ni dans un fichier de configuration versionné. Les secrets doivent être gérés par des variables d'environnement ou par un gestionnaire de secrets externe.

Cette règle s'applique également aux tests, à la documentation, aux exemples et à l'historique Git. Les valeurs factices utilisées dans les exemples doivent être clairement identifiables comme telles et ne donner accès à aucun système.

## Contrôles avant intégration

```text
ruff check .
ruff format --check .
mypy src main.py
pytest
```

Le code produit par un LLM doit être relu et validé par un développeur.

# Cycle de vie applicatif

Le développement d'une application suit plusieurs environnements successifs. Chaque environnement a un objectif précis et ne doit pas être utilisé en dehors de celui-ci.

| Environnement | Objectif | Réalisé par | Déploiement |
| --- | --- | --- | --- |
| **DEV** | Développement, débogage, tests unitaires, validation locale | Développeur | Local sur le poste de développement |
| **Qualification** | Assemblage, tests d'intégration technique et de bout en bout avec des données représentatives | Équipe de développement | Déploiement manuel des livrables, puis CI/CD |
| **Recette** | Validation fonctionnelle, tests de volume et validation avant production | Utilisateurs métiers avec le support de l'équipe projet | Déploiement manuel des livrables, puis CI/CD |
| **Production** | Exploitation de l'application | Équipe d'exploitation | Déploiement supervisé, auditable et automatisé |

## DEV

Le poste de développement sert à développer, déboguer, exécuter les tests unitaires et les traitements locaux, et utiliser Git et les outils de développement. Le développement est réalisé sur une branche Git dédiée. Aucun développement ne doit être réalisé directement en Qualification, Recette ou Production.

## Qualification

La Qualification valide l'assemblage des composants, le packaging, les intégrations techniques, les parcours de bout en bout et les jeux de données représentatifs. Le déploiement est d'abord manuel, puis automatisé via la chaîne CI/CD.

## Recette

La Recette est destinée aux tests utilisateurs, à la validation fonctionnelle, aux tests de charge et de volume et à la validation des résultats. Aucun développement n'y est réalisé. Le déploiement est identique à celui de la Qualification.

## Production

La Production est uniquement destinée à l'exploitation : stabilité, disponibilité, supervision, traçabilité et auditabilité. Tout déploiement doit être validé, tracé, reproductible et réalisé par la procédure officielle. À terme, la chaîne CI/CD automatise entièrement les déploiements.

## Flux de promotion

```text
Développement → DEV → Revue de code → Qualification → Recette → Production
```

Chaque promotion nécessite une revue de code, des tests unitaires réussis, des tests d'intégration à partir de Qualification et une validation métier avant la Production.

## Bonnes pratiques

- Le dépôt Git est la seule source de vérité.
- Aucun développement n'est réalisé directement hors DEV.
- Les environnements sont reproductibles et les déploiements traçables et auditables.
- Les données de Production ne sont jamais utilisées en développement sans anonymisation ou pseudonymisation.
- Le même artefact est promu de DEV jusqu'à Production ; seule la configuration change.
- Le code métier est identique dans tous les environnements.

> **Principe important :** un artefact ne doit jamais être recompilé entre deux environnements. Le package validé en Qualification est exactement celui promu en Recette puis en Production. Seule la configuration évolue.

## Vérification statique du typage avec mypy

Python est dynamiquement typé. Les annotations améliorent la lisibilité et mypy détecte des incohérences sans exécuter le code :

```python
def calculate_total(amount: float, rate: float) -> float:
    return amount * rate


calculate_total("1000", 0.03)
```

mypy signale que `"1000"` est une chaîne alors que `amount` attend un flottant. mypy complète Ruff et pytest, mais ne les remplace pas.

Avant toute intégration, exécuter les quatre contrôles indiqués plus haut.

# Gestion du code source avec Git

Toutes les modifications du code, de la documentation et de la configuration doivent être versionnées dans Git.

## Stratégie de branches

Le projet utilise le **Trunk-Based Development**. `main` représente la dernière version validée. Les développements sont réalisés dans des branches temporaires, courtes et limitées à un sujet, par exemple :

```text
feature/configuration-yaml
feature/logging
feature/tests-unitaires
bugfix/calcul-provision
hotfix/erreur-production
```

Les développements de longue durée sont à éviter.

## Fusion dans la branche principale

Une branche est fusionnée après revue de code, succès des tests unitaires et validation des contrôles automatiques. Les déploiements vers Qualification, Recette et Production partent exclusivement de `main`, jamais d'une branche de développement.

## Gestion des versions

Chaque version déployée porte un tag Git immuable suivant **Semantic Versioning** :

- **MAJOR** : changement incompatible ;
- **MINOR** : nouvelle fonctionnalité compatible ;
- **PATCH** : correction sans modification fonctionnelle.

Exemples : `v1.0.0`, `v1.0.1`, `v1.1.0`, `v2.0.0`. Les tags sont permanents et ne sont jamais déplacés.

## Versions déployées

| Environnement | Version d'exemple |
| --- | --- |
| Qualification | `v1.4.0` |
| Recette | `v1.3.2` |
| Production | `v1.3.1` |

Le même tag est successivement promu de DEV à Qualification, Recette puis Production, sans recompilation.

## Déploiements

Tout déploiement part d'un commit présent sur `main` et d'un tag identifié. Les artefacts sont identiques entre Qualification, Recette et Production ; seule la configuration change.

## Bonnes pratiques Git

- Commiter régulièrement avec des messages explicites.
- Une branche et une Pull Request correspondent à un sujet.
- Ne jamais développer directement sur `main` ni modifier le code hors DEV.
- Supprimer les branches après fusion.
- Identifier les versions déployées par des tags et ne jamais déplacer ou supprimer ces tags.

## Exemple de cycle de développement

```text
main → feature/configuration-yaml → revue et tests → main → tag v1.5.0
     → Qualification → Recette → Production
```

Ce cycle garantit que le code testé est exactement celui exécuté en production.
