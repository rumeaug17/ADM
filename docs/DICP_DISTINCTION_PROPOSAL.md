# Proposition — Distinguer la « classification DICP » d'ADM de l'analyse de risques DICP

Date : 2026-09-23. Document de cadrage, aucun code modifié.

## 1. Le constat

ADM demande, pour chaque application, quatre niveaux notés D1–D4, I1–I4, C1–C4
et P1–P4, présentés comme la « Classification (DICP) » dans une section
intitulée « Classification de sécurité » (`add.html`, `edit.html`,
`index.html`, `resume.html`). Ils servent uniquement à pondérer le score de
dette dans le calcul du « Risque » :
`risque = score × (((D × I × C × P) / 4 / criticité) / 2)` (`services.calculate_risk`).

Six éléments entretiennent la confusion avec la classification DICP officielle
issue de l'analyse de risques (RSSI / EBIOS RM, ISO 27005) :

| # | Élément dans ADM | Ce qu'un lecteur « sécurité » comprend | Écart réel |
|---|---|---|---|
| 1 | **P = Pérennité** (conservation long terme de l'application et de ses données) | P = **Preuve** / traçabilité | Même sigle, 4ᵉ critère différent |
| 2 | Titre « Classification de sécurité », colonne « Classification (DICP) » | La classification validée de l'application | Une saisie déclarative, faite par quiconque ajoute ou modifie la fiche, sans lien avec l'analyse officielle |
| 3 | Codes stockés et affichés `D1`…`C4` | Les mêmes codes que dans l'analyse de risques | Échelle et définitions propres à ADM (`info_texts.json`), qui peuvent diverger |
| 4 | Colonne et KPI « Risque », « Risque global » | Un risque de sécurité (vraisemblance × gravité) | Une **exposition de la dette technique**, pondérée par la sensibilité |
| 5 | Export CSV : colonnes « Disponibilité », « Intégrité », « Confidentialité », « Pérennité » | Données réutilisables comme classification officielle | Le fichier sort d'ADM sans aucun avertissement sur l'origine des valeurs |
| 6 | Criticité 1 = **très élevée**, alors que DICP 4 = critique | — | Deux échelles inversées côte à côte dans la même section, source d'erreurs de saisie |

Le risque concret : un RSSI, un auditeur ou un métier lit un export ou un
écran ADM et prend des valeurs estimées pour la classification validée, ou
l'inverse (un chef de projet recopie son DICP officiel sans voir que le P n'a
pas le même sens).

## 2. Deux orientations possibles

**Orientation A — Distinguer.** ADM garde sa propre saisie, mais la présente
clairement comme un *profil de sensibilité* déclaratif, utilisé seulement pour
pondérer la dette. Aucun lien avec l'analyse de risques.

**Orientation B — Aligner.** ADM ne saisit plus D, I et C lui-même : il reprend
les valeurs de l'analyse de risques officielle (saisie « recopiée » avec
référence et date, puis à terme import depuis le référentiel RSSI s'il existe).
La pérennité, qui n'est pas un critère de l'analyse de risques, devient un
critère distinct.

B supprime la double source de vérité, mais dépend d'une décision
organisationnelle (qui possède la donnée, existe-t-il un référentiel
exploitable ?). A est faisable tout de suite et ne ferme pas la porte à B.

**Recommandation : A maintenant (lot 1), avec un pont vers B (lot 2), à
décider avec le RSSI.**

## 3. Lot 1 — Clarifier sans migration de données (≈ 1 jour)

Uniquement du libellé, de l'aide et de la présentation : les clés techniques
(`disponibilite`, `perennite`…), les codes stockés (`D1`…`P4`), la formule du
risque, l'import/export JSON et le schéma SQL ne changent pas.

1. **Renommer la section et la colonne.**
   - « Classification de sécurité » → **« Profil de sensibilité (estimation ADM) »**.
   - « Classification (DICP) » → **« Sensibilité D·I·C »**.
   - Icône `bi-shield-check` (évoque une validation sécurité) → `bi-sliders`.
2. **Sortir la pérennité du bloc DICP.** Elle devient un critère à part,
   « **Pérennité attendue** », affiché dans sa propre colonne / son propre
   badge, avec le code affiché **« Pé »** (ex. `Pé3`) au lieu de `P3`. Le code
   stocké reste `P3` : seul le filtre d'affichage change (`dicp_label` et un
   nouveau filtre de code d'affichage dans `services.py`).
3. **Avertissement explicite.** Une ligne sous le titre de la section
   (formulaires et résumé) et en tête de chaque aide contextuelle
   (`app-disponibilite`, `app-integrite`, `app-confidentialite`,
   `app-perennite`) :
   > Estimation utilisée uniquement pour pondérer la dette technique dans ADM.
   > Elle ne remplace pas la classification DICP issue de l'analyse de risques
   > (RSSI), dont le 4ᵉ critère est la Preuve et non la Pérennité.
4. **Renommer le « Risque ».** « Risque » → **« Exposition dette »** (colonne du
   catalogue, résumé, synthèse), « Risque global » → **« Exposition globale »**,
   avec une aide qui rappelle la formule. Les clés internes (`risque`,
   `global_risk`, seuils `display_thresholds.risk`) restent inchangées.
5. **Export CSV.** En-têtes préfixés : « Sensibilité D (estimation) »,
   « Sensibilité I (estimation) », « Sensibilité C (estimation) »,
   « Pérennité attendue », « Exposition dette ». Les consommateurs actuels du
   CSV sont à identifier avant de changer les en-têtes.
6. **Criticité.** Sans changer l'échelle, afficher le sens dans les options
   (« 1 — très élevée … 4 — faible », c'est déjà le cas dans le libellé) et
   ajouter dans l'aide : « Attention : échelle inverse de la sensibilité
   (1 = le plus critique) ». L'inversion elle-même pourrait faire l'objet d'une
   tâche séparée (elle modifie la formule et nécessite une migration).
7. **Documentation.** Ajouter une section « Profil de sensibilité et analyse de
   risques » dans `docs/BUSINESS_RULES.md` et un paragraphe dans `README.md`,
   et adapter les tests qui vérifient les libellés.

Fichiers touchés : `add.html`, `edit.html`, `index.html`, `resume.html`,
`_application_row.html`, `_synthese_results.html`, `synthese.html`,
`info_texts.json`, `services.py` (filtre d'affichage), `routes.py` (en-têtes
CSV), `docs/BUSINESS_RULES.md`, `README.md`, tests associés.

## 4. Lot 2 — Faire le lien avec l'analyse de risques (à décider)

1. **Référence de l'analyse officielle** sur la fiche application : champs
   optionnels « DICP officiel » (4 codes D/I/C/P au sens RSSI),
   « Référence de l'analyse » (lien ou identifiant) et « Date de validation ».
   Nécessite une migration Alembic et l'adaptation de l'import/export JSON.
2. **Indicateur d'écart** : badge d'alerte quand l'estimation ADM de D, I ou C
   diffère du DICP officiel, et filtre « Applications sans analyse de risques ».
3. **Option d'alignement complet (orientation B)** : paramètre de
   configuration pour que le calcul d'exposition utilise le D·I·C officiel
   lorsqu'il est renseigné, l'estimation ADM ne servant qu'en l'absence
   d'analyse.

## 5. Questions à trancher

1. Orientation A seule, ou A puis B ? Le RSSI est-il d'accord pour que ADM
   référence (voire reprenne) le DICP officiel ?
2. Libellés : « Profil de sensibilité », « Pérennité attendue » et
   « Exposition dette » conviennent-ils, ou existe-t-il un vocabulaire maison
   à reprendre ?
3. Le CSV est-il consommé automatiquement par un autre outil (auquel cas le
   changement d'en-têtes doit être annoncé) ?
4. Faut-il ouvrir une tâche séparée pour réaligner l'échelle de criticité
   (1 = faible … 4 = critique) ?

## 6. Suivi — Lot 1 réalisé

Implémenté le 2026-09-23, validé par Guillaume Rumeau (orientation A, libellés
proposés retenus tels quels). Aucune migration de données : clés techniques,
codes stockés (`D1`…`P4`), formule, import/export JSON et schéma inchangés.

**Ce qui a été fait.**
- Formulaires `add.html`/`edit.html` : section renommée « Profil de
  sensibilité (estimation ADM) » (icône `bi-sliders`), avertissement sous le
  titre, champ « Pérennité attendue ».
- Catalogue (`index.html`, `_application_row.html`) : colonne « Sensibilité
  D·I·C » (D, I, C seulement) et nouvelle colonne « Pérennité attendue » ;
  « Risque » → « Exposition dette ». Les index `data-sort-col` des colonnes
  suivantes sont décalés d'un rang, `colspan` de la ligne « aucun résultat »
  passé à 12.
- Résumé (`resume.html`) : « Sensibilité D·I·C (estimation ADM) », ligne
  « Pérennité attendue » séparée, avertissement, « Exposition dette ».
- Synthèse : KPI « Exposition globale », colonne « Exposition dette ».
- Configuration (`settings.html`) : groupe de seuils « Exposition dette »
  avec rappel de la formule ; noms de champs `risk_*` inchangés.
- Nouveau filtre Jinja `sensitivity_code`
  (`services.sensitivity_display_code`) : affiche `Pé3` pour `P3`, laisse
  D/I/C et toute valeur non reconnue inchangés.
- Export CSV : en-têtes « Sensibilité D/I/C (estimation) », « Pérennité
  attendue », « Exposition dette » ; valeurs inchangées.
- Aide en ligne (`info_texts.json`) : avertissement en tête des aides D, I, C
  et P ; rappel de l'inversion d'échelle dans l'aide de criticité.
- Documentation : section « Profil de sensibilité et analyse de risques » et
  section « Exposition dette » dans `docs/BUSINESS_RULES.md`, paragraphe dans
  `README.md`. Lot 2 et réalignement de la criticité ajoutés au backlog
  (US1.4, US1.5).
- Tests : `tests/test_sensitivity_profile_labels.py` (nouveau),
  `tests/test_synthese_kpi_grid.py` adapté (« Exposition globale »).

**Points d'attention au déploiement.**
- Si `ADM_INFO_TEXTS_PATH` pointe vers une copie persistante
  d'`info_texts.json` hors du paquet, elle n'est pas mise à jour par la
  nouvelle version : reporter à la main les cinq nouvelles lignes d'aide
  (`app-criticite`, `app-disponibilite`, `app-integrite`,
  `app-confidentialite`, `app-perennite`). Les avertissements des gabarits,
  eux, s'affichent dans tous les cas.
- Prévenir les consommateurs éventuels de l'export CSV du changement
  d'en-têtes.

## 7. Suivi — Ajustement après retour utilisateurs (sensibilité « DICPé »)

2026-09-24. Les utilisateurs n'ont pas apprécié la séparation de la pérennité
dans une colonne à part : ils veulent retrouver les quatre pastilles
regroupées côte à côte, comme avant le lot 1. L'ambiguïté est désormais levée
par le nom plutôt que par la mise en page.

**Nommage retenu : « Sensibilité DICPé ».** Le sigle reste familier (lecture
immédiate des quatre critères dans l'ordre habituel), mais le « é » final le
rend visiblement différent du DICP de l'analyse de risques et renvoie
directement à la pastille `Pé`. Alternatives écartées : « D·I·C·Pé » (plus
explicite mais lourd en en-tête de colonne), « Profil ADM » (perd le lien
avec les quatre critères que les utilisateurs connaissent).

**Ce qui change par rapport au lot 1.**
- Catalogue : une seule colonne « Sensibilité DICPé » avec les pastilles
  `D` `I` `C` `Pé` côte à côte (infobulle d'en-tête expliquant le sigle et la
  différence avec le DICP officiel) ; la colonne « Pérennité attendue » est
  supprimée, les index `data-sort-col` et le `colspan` reviennent à leurs
  valeurs d'avant le lot 1.
- Résumé : une seule ligne « Sensibilité DICPé (estimation ADM) » avec les
  quatre pastilles ; l'avertissement commence par « DICPé : Disponibilité,
  Intégrité, Confidentialité, Pérennité attendue ».
- Formulaires : section « Criticité et sensibilité DICPé (estimation ADM) »,
  même définition du sigle dans l'avertissement, champ « Pérennité attendue
  (Pé) ».
- Export CSV : « DICPé - Disponibilité », « DICPé - Intégrité »,
  « DICPé - Confidentialité », « DICPé - Pérennité attendue ».
- Aide en ligne de la pérennité : mention du sigle « DICPé ».
- Inchangé : affichage `Pé1`…`Pé4`, libellé « Exposition dette », codes
  stockés, formule, import/export JSON.
- Tests (`tests/test_sensitivity_profile_labels.py`) et documentation
  (`docs/BUSINESS_RULES.md`, `README.md`) mis à jour. Contrôles `ruff`,
  `mypy` et `pytest` (350 tests, couverture 87,8 %) passants ; rendu vérifié
  par capture.
