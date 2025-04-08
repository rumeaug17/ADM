# Documentation des Questions

## Catégorie : Urbanisation

### Question : Faible couplage de l'application dans le SI

**Clé :** `couplage`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle faiblement couplée avec le reste du SI ?**




**Éléments à vérifier :**
- Cartographie applicative
- interfaces de l'application
- schémas d’architecture
- impacts en cas d'indisponibilité

---

### Question : Existence d'une procédure de décommissionnement

**Clé :** `decommissionnement`  
**Type :** select

**Applicable pour le type d'application :** Editeur, Open source

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Une procédure de décommissionnement ou de remplacement de l'application existe ?**




**Éléments à vérifier :**
- Cartographie applicative
- procédures et contrats

---

## Catégorie : Organisation

### Question : Documentation complète et à jour

**Clé :** `doc`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application dispose-t-elle d’une documentation complète et à jour ?**

Une documentation insuffisante rend difficile la maintenance et l’évolution de l’application.


**Éléments à vérifier :**
- Manuels d’utilisation
- guides techniques
- schémas d’architecture
- Mise à jour récente

---

### Question : Équipe clairement identifiée

**Clé :** `team`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’équipe en charge de l’application est-elle clairement identifiée ?**

L’absence de responsabilité claire entraîne des difficultés de support et d’évolution.


**Éléments à vérifier :**
- Existence d’une équipe référencée
- rôles définis
- contacts accessibles

---

### Question : Roadmap claire

**Clé :** `roadmap`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Existe-t-il une roadmap claire pour l’évolution de l’application ?**

Une roadmap absente ou floue peut indiquer un manque de vision stratégique et indique un manque de visibilité sur la pérennité de l'application.


**Éléments à vérifier :**
- Présence de plans d’évolution
- backlog de développement
- alignement avec la stratégie et le SDSI

---

### Question : Support assuré sur 24 mois

**Clé :** `support_contrat`  
**Type :** select

**Applicable pour le type d'application :** Editeur, Open source

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le support de la solution existe et est assuré pour les 24 prochains mois ?**

Le suppoort de la solution, dans la version utilisée, est nécessaire pour la maintenance et les corrections de sécurité.


**Éléments à vérifier :**
- Contrat de support
- Prérequis de la solution

---

## Catégorie : Obsolescence

### Question : Technologies obsolètes

**Clé :** `tech_obsolete`  
**Type :** select

**Applicable pour le type d'application :** Interne, Open source

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application repose-t-elle sur des technologies obsolètes ?**

Les technologies obsolètes sont difficiles à maintenir et exposent à des risques de sécurité.


**Éléments à vérifier :**
- Versions des langages et frameworks utilisés
- fin de support par les éditeurs

---

### Question : Maintien en condition opérationnelle difficile

**Clé :** `mco`  
**Type :** select

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le maintien en condition opérationnelle de l’application est-il difficile ?**

Une maintenance complexe peut entraîner une augmentation des coûts et des risques opérationnels.


**Éléments à vérifier :**
- Disponibilité des compétences
- fréquence des mises à jour
- facilité de déploiement

---

### Question : Composants tiers non supportés

**Clé :** `support`  
**Type :** select

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application repose-t-elle sur des composants tiers non supportés ?**

Un composant tiers non maintenu représente un risque élevé en termes de sécurité et de pérennité.


**Éléments à vérifier :**
- Bibliothèques et dépendances utilisées
- support officiel disponible

---

### Question : Existe-t-il une version plus récente du progiciel non déployée

**Clé :** `version_recente`  
**Type :** select

**Applicable pour le type d'application :** Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Cloud, Hybride

**Options :**

- Non (Score: 0)
- Oui, patch (Score: 1)
- Oui, mineure (Score: 2)
- Oui, majeure (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **La version de la solution est-elle la dernière version disponible ?**

S'il existe une version pluis récente non déployée, il y a des risques de trou de maintenance ou de problèmes de sécurité non corrigés.


**Éléments à vérifier :**
- Roadmap
- support officiel

---

## Catégorie : Qualité et Développement

### Question : Alignement avec l’état de l’art

**Clé :** `etat_art`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle alignée avec l’état de l’art ?**

Une application trop en retard sur les bonnes pratiques entraîne une dette technique accrue.


**Éléments à vérifier :**
- Adoption des patterns modernes
- architecture modulaire

---

### Question : Respect des standards et des principes d'architecture

**Clé :** `respect`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application et son code respectent-ils les standards et principes d’architecture de l’organisation ?**

 Un non-alignement peut entraîner des incompatibilités et des coûts supplémentaires, ainsi qu'un manque d'homogénéité dans le SI.


**Éléments à vérifier :**
- Conformité aux principes et aux standards
- conformité aux décisions d'architecture
- audit de code

---

### Question : Code source maintenable et documenté

**Clé :** `code_source`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le code source est-il maintenable et documenté ?**

Un code non maintenable augmente la complexité des évolutions et des corrections.


**Éléments à vérifier :**
- Présence de commentaires
- structure modulaire
- normes de codage respectées

---

### Question : Échanges via des API

**Clé :** `echanges_api`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les échanges avec le reste du SI est effectué à travers des API sur des technologies standards ?**

L'usage d'API standards simplifie l'intégration de la solution, et sa maintenance.


**Éléments à vérifier :**
- Architecture applicative
- Contrat de service

---

### Question : Pour un progiciel, développements spécifiques intégrés

**Clé :** `specifique`  
**Type :** select

**Applicable pour le type d'application :** Editeur, Open source

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Y a-t-il des développements spécifiques, au delà du paramétrage prévu par la solution pour intégrer l'application dans le SI ?**

Les développements spécifiques sont toujuors des ralentisseurs sur la maintenance et l'évolution.


**Éléments à vérifier :**
- Architecture applicative
- Dossier d'intégration

---

### Question : Tests automatisés

**Clé :** `tests`  
**Type :** select

**Applicable pour le type d'hébergement :** On prem, Cloud, Hybride

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Des tests automatisés sont-ils en place ?**

L’absence de tests automatisés complique les évolutions et augmente le risque de régressions.


**Éléments à vérifier :**
- Couverture des tests
- intégration continue
- tests unitaires et fonctionnels

---

## Catégorie : Sécurité et Conformité

### Question : Conformité aux exigences de sécurité

**Clé :** `securite`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle conforme aux exigences de sécurité ?**

Un défaut de conformité expose l’entreprise à des cyberattaques et des sanctions réglementaires.


**Éléments à vérifier :**
- Tests de sécurité
- audits
- respect des normes et des règlements (DORA, RGPD, etc.)

---

### Question : Vulnérabilités connues non corrigées

**Clé :** `vulnerabilites`  
**Type :** select

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Des vulnérabilités connues sont-elles non corrigées ?**

Des failles non corrigées augmentent considérablement les risques de cyberattaques.


**Éléments à vérifier :**
- Résultats d’analyses de vulnérabilités
- fréquence des correctifs appliqués

---

### Question : Mécanismes de surveillance et d’alerte

**Clé :** `surveillance`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Des mécanismes de surveillance et d’alerte en cas d’incident de sécurité sont-ils en place ?**

L’absence de surveillance empêche la détection rapide des attaques.


**Éléments à vérifier :**
- Logs
- SIEM
- alertes en cas d’anomalies
- audit de sécurité

---

## Catégorie : Exploitation et Performance

### Question : Incidents récurrents

**Clé :** `incidents`  
**Type :** select

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application présente-t-elle des incidents récurrents ?**

Un taux élevé d’incidents réduit la disponibilité et la satisfaction des utilisateurs.


**Éléments à vérifier :**
- Statistiques de tickets
- temps moyen de résolution
- impact des incidents

---

### Question : Performances satisfaisantes

**Clé :** `performances`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les performances de l’application sont-elles satisfaisantes ?**

Une application lente nuit à l’expérience utilisateur et à la productivité.


**Éléments à vérifier :**
- Temps de réponse
- taux d’erreur
- monitoring des performances

---

### Question : Application scalable

**Clé :** `scalable`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle scalable ?**

Une application non scalable devient rapidement un goulot d’étranglement en cas de montée en charge.


**Éléments à vérifier :**
- Architecture distribuée
- support du cloud
- capacité d’auto-scaling

---

## Catégorie : Fonctionnel

### Question : Couverture des besoins métier

**Clé :** `besoins_metier`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application couvre-t-elle efficacement les besoins métier ?**

Une application mal adaptée entraîne une perte d’efficacité et une démultiplication des outils.


**Éléments à vérifier :**
-  Retour des utilisateurs
- adéquation avec les processus métier

---

### Question : Périmètre applicatif spécifique identifié

**Clé :** `recouvrement`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le périmètre de l’application est-il clairement identifié et n’entre pas en conflit avec d’autres applications ?**

Un chevauchement fonctionnel complique la gestion du SI et augmente la dette applicative.


**Éléments à vérifier :**
- Cartographie du SI
- analyse des interactions entre applications

---

### Question : Évolutivité pour nouvelles demandes métier

**Clé :** `evolutivite`  
**Type :** select

**Options :**

- Oui total (Score: 0)
- Partiel (Score: 1)
- Insuffisant (Score: 2)
- Non total (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle facilement évolutive pour répondre aux nouvelles demandes métier ?**

Une application rigide empêche l’innovation et nécessite des développements coûteux.


**Éléments à vérifier :**
- Modularité de l’architecture
- facilité d’ajout de nouvelles fonctionnalités

---

### Question : Fonctionnalités obsolètes ou inutilisées

**Clé :** `fonctions`  
**Type :** select

**Options :**

- Non (Score: 0)
- Partiellement (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Existe-t-il des fonctionnalités obsolètes ou inutilisées ?**

Le maintien de fonctionnalités inutiles alourdit l’application et accroît les coûts de maintenance.


**Éléments à vérifier :**
- Analyse des usages
- désactivation des modules non utilisés

---
