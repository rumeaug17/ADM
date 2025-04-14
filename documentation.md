# Documentation des Questions

## Catégorie : Architecture & Intégration

### Question : L'application utilise-t-elle des API standardisées pour interagir avec les autres systèmes ?

**Clé :** `api`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui uniquement (Score: 0)
- Quelques exceptions (Score: 1)
- API incomplètes (Score: 2)
- Aucune API (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les échanges avec le reste du SI est effectué à travers des API sur des technologies standards ?**

Par API standards il faut comprendre des échanges via des procoles standardisés tels que des API REST, des services SOAP avec contrat de service.

Un échange par fichier, en mode batch, peut également être considéré comme un échange standard, si le format est standard.

Ces services sont standards s'ils ne sont pas développés spécifiquement pour l'intégration dans le SI cible.

L'usage d'API standards simplifie l'intégration de la solution, et sa maintenance.




**Éléments à vérifier :**
- Architecture applicative
- Contrat de service

---

### Question : Le couplage avec les autres applications du SI est-il minimal et documenté ?

**Clé :** `couplage`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Couplage minimal (Score: 0)
- Couplage intrusif (Score: 1)
- Dépendances biridectionnelles (Score: 2)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle faiblement couplée avec le reste du SI ?**

Ces services sont standards s'ils ne sont pas développés spécifiquement pour l'intégration dans le SI cible.

Plus un couplage est important et intrusif dans un SI, plus la gestion des évolutions et des remplacements devient complexe.




**Éléments à vérifier :**
- Cartographie applicative
- interfaces de l'application
- schémas d’architecture
- impacts en cas d'indisponibilité

---

### Question : Existe-t-il une procédure claire de décommissionnement ou de remplacement de l'application ?

**Clé :** `décommissionnement`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Non, ou avec beaucoup de travail (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Existe-t-il une procédure de décommissionnement de la solution, ou une procédure de remplacement par une autre solution sur le même périmètre ?**

Dans l'idéal cette procédure a été testée.

Par définition, l'ajout dans le SI d'une application que l'on ne peut pas remplacer ou décommissionner simplement est une dette.




**Éléments à vérifier :**
- Cartographie applicative
- procédures et contrats
- Documentation produit
- Architecture d'intégration

---

### Question : L'application peut-elle être migrée ou portée facilement sur un autre environnement ?

**Clé :** `portabilite`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Non, ou avec beaucoup de travail (Score: 3)
- Non applicable (Score: N/A)

**Aide :** _Aucune aide disponible._

---

### Question : Existe-il un recouvrement fonctionnel avec d’autres parties du SI ?

**Clé :** `recouvrement`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Non (Score: 0)
- Un peu (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les fonctionnalités principales de la solution existe ailleurs dans le SI ?**

Le périmètre de l’application doit être clairement identifié et ne pas entrer en conflit avec d’autres applications.

Un chevauchement fonctionnel complique la gestion du SI et augmente la dette applicative.




**Éléments à vérifier :**
- Cartographie fonctionnelle du SI
- Analyse des interactions entre applications

---

## Catégorie : Documentation & Gouvernance

### Question : La documentation fonctionnelle et technique est-elle complète et à jour ?

**Clé :** `documentation`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Documentation inexistante (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application dispose-t-elle d’une documentation complète et à jour ?**

Une documentation insuffisante rend difficile la maintenance et l’évolution de l’application.




**Éléments à vérifier :**
- Manuels d’utilisation
- Guides techniques
- Schémas d’architecture
- Mises à jour récentes

---

### Question : Une équipe dédiée est-elle clairement identifiée avec des rôles précis et à jour ?

**Clé :** `équipe`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Non, personne (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’équipe en charge de l’application est-elle clairement identifiée ?**

L’absence de responsabilité claire entraîne des difficultés de support et d’évolution.




**Éléments à vérifier :**
- Existence d’une équipe référencée
- Rôles définis
- Contacts accessibles

---

### Question : Existe-t-il une roadmap claire et compatible avec la stratégie d'entreprise ?

**Clé :** `roadmap`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Non, ou incompatible (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Une roadmap a été publiée indiquant les prochaines évolutions envisagées de la solution ?**

Une roadmap absente ou floue peut indiquer un manque de vision stratégique et indique un manque de visibilité sur la pérennité de l'application.

Une roadmap allant dans une direction incompatible avec celle envisagée par l'entreprise indique une solution à remplacer.




**Éléments à vérifier :**
- Présence de plans d’évolution
- backlog de développement
- alignement avec la stratégie et le SDSI

---

### Question : Existe-t-il une version plus récente de la solution non déployée ?

**Clé :** `version_recente`  
**Type :** select

**Applicable pour le type d'application :** Editeur, Open source

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

### Question : Les compétences nécessaires au MCO de l’application sont-elles faciles à trouver sur le marché ?

**Clé :** `compétences`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplète (Score: 1)
- À vérifier (Score: 2)
- Non, difficiles à trouver (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Est-il facile de trouver des personnes ayant les compétences nécessaires pour le maintient en condition opérationnelle de la solution ?**

La difficulté à trouver des personnes peut rendre la maintenance complexe voire impossible dans des coûts acceptables.




**Éléments à vérifier :**
- Support
- Contrat avec un intégrateur ou une TMA
- veille de marché

---

### Question : Le support est-il assuré sur 24 mois ?

**Clé :** `support`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplet (Score: 1)
- À vérifier (Score: 2)
- Non, pas de support (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le support de la solution existe et est assuré pour les 24 prochains mois ?**

Le support de la solution, dans la version utilisée, est nécessaire pour la maintenance et les corrections de sécurité.




**Éléments à vérifier :**
- Contrat de support
- Communauté active
- Prérequis de la solution

---

### Question : Une date de fin de vie est planifiée ou estimée ?

**Clé :** `fin`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Non (Score: 0)
- Oui, à lon terme (Score: 1)
- Oui, à moyen terme (Score: 2)
- Oui, à court terme (Score: 3)
- Non applicable (Score: N/A)

**Aide :** _Aucune aide disponible._

---

## Catégorie : Sécurité & Conformité

### Question : Un mécanisme efficace de gestion et une revue régulière des habilitations existent-ils ?

**Clé :** `habilitations`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplet (Score: 1)
- À vérifier (Score: 2)
- Non, inexistant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les accès et habilitations de la solution sont correctement gérés, une procédure de revue et de contrôle existe ?**

Tout accès à une solution du SI doit être protégée et la gestion des habilitations 
doit se faire dans le respects des standards et des procédures en vigueur dans l'entreprise.




**Éléments à vérifier :**
- Standards et procédures
- Documentation

---

### Question : L'application dispose-t-elle d’un système efficace de sauvegarde et de restauration, testé régulièrement ?

**Clé :** `sauvegarde`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplet (Score: 1)
- À vérifier (Score: 2)
- Non, inexistant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Un système de sauvegarde et de restauration existe et est testé régulièrement ?**

En cas de problème technique ou humain, il est parfois nécessaire de restaurer une version stable de la solution ou de ses données.




**Éléments à vérifier :**
- Standards et procédures
- Documentation

---

### Question : Les logs applicatifs et systèmes sont-ils accessibles et analysés régulièrement ?

**Clé :** `logs`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplet (Score: 1)
- À vérifier (Score: 2)
- Non, inexistant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L'application propose-t-elle un moyen simple d'accéder aux logs ?**

Les logs sont-ils intégrables et utilisables dans un système de surveillance externe ?




**Éléments à vérifier :**
- Standards et procédures
- Documentation

---

### Question : Toutes les vulnérabilités identifiées sont-elles corrigées dans les délais recommandés ?

**Clé :** `vulnérabilités`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les vulnérabilités et problèmes de sécurité sont-ils identifiés rapidement et corrigés dans les délais acceptables ?**

Un système qui ne peut être corrigé correctement pose des problèmes de sécurité et de maintenance.




**Éléments à vérifier :**
- Standards et procédures
- Documentation
- Historique de sécurité

---

### Question : L'application respecte-t-elle les exigences réglementaires (RGPD, DORA, etc.) ?

**Clé :** `réglements`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les règlements applicables sur le périmètre de la solution sont pleinement respectés et implémentés ?**

Un défaut de conformité doit être corrigé, c'est une dette par définition.




**Éléments à vérifier :**
- Standards et procédures
- Documentation</li

---

## Catégorie : Technologies

### Question : Les langages et Frameworks de programmation utilisés sont-ils à jour, couramment utilisés, et supportés officiellement ?

**Clé :** `langages`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, en déclin (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les langages et framework de développement utilisés sont-ils obsolètes ?**

Cela peut rendre la maintenance plus complexe, voire impossible.




**Éléments à vérifier :**
- Étude du marché
- Documentation technique</li

---

### Question : Les dépendances technologiques (Bases de données, middleware) sont-ils à jour, couramment utilisés, et supportés officiellement ?

**Clé :** `outils`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Oui, en déclin (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les outils et dépendances utilisés sont-ils obsolètes ?**

Cela peut rendre la maintenance plus complexe, voire impossible.




**Éléments à vérifier :**
- Étude du marché
- Documentation technique</li

---

### Question : L'infrastructure et les composants matériels nécessaires sont compatibles avec les standards ?

**Clé :** `infra`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les composants d'infrastructure nécessaires au fonctionnement nominal de la solution sont compatibles avec les standards de l'entreprise ?**

S'il y a du matériel, des solutions réseaux ou d'infrastructure spécifiques à mettre en oeuvre, alors la maintenance de la soltion sera plus complexe.




**Éléments à vérifier :**
- Architecture technique
- Documentation technique</li

---

### Question : Le système repose-t-il de composants tiers obsolètes ou non supportés ?

**Clé :** `composants`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Non (Score: 0)
- Un peu (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Des composants tiers obsolètes ou non supportés sont-ils nécessaires pour le bon fonctionnement ?**




**Éléments à vérifier :**
- Architecture technique
- Documentation technique</li

---

### Question : Le système est-il intégré dans les chaines standards CI/CD de l'entreprise ?

**Clé :** `ci_cd`  
**Type :** select

**Applicable pour le type d'application :** Interne, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud

**Options :**

- Oui totalement (Score: 0)
- Oui, incomplet (Score: 1)
- À vérifier (Score: 2)
- Non, inexistant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L'application est-elle intégrée dans les processus standards de CI/CD de l'entreprise ou dans un pipeline spécifique aux technologies en jeux mais standard ?**

Un pipeline CI/CD permet une gestion des montées de version et des corrections fluides et en suivant les processus de l'entreprise.




**Éléments à vérifier :**
- Architecture technique
- Documentation technique</li

---

## Catégorie : Qualité du Code & Maintenance

### Question : Alignement avec l’état de l’art

**Clé :** `etat_art`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle alignée avec l’état de l’art ?**

Une application trop en retard sur les bonnes pratiques entraîne une dette technique accrue.




**Éléments à vérifier :**
- Adoption des patterns modernes
- architecture modulaire

---

### Question : Le code source est-il propre, maintenable et modulaire ?

**Clé :** `code`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le code source de l'application est-il lisible, modulaire, maintenable et évolutif ?**

Une code de mauvaise qualité est plus difficile à maintenir et à faire évoluer.




**Éléments à vérifier :**
- Documentation du code
- Code source
- Avis des mainteneurs
- Analyses d'outils tels que Sonar

---

### Question : Le code source est-il documenté ?

**Clé :** `code_doc`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques manques (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Le code source est-il suffisamment documenté ?**

Une code doit être documenté afin d'aider à son évolution.




**Éléments à vérifier :**
- Documentation du code
- Code source
- Avis des mainteneurs
- Analyses d'outils tels que Sonar

---

### Question : Existe-t-il une couverture significative par des tests automatisés (unitaires, intégration, régression) ?

**Clé :** `tests`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Des tests automatisés sont-ils en place ?**

L’absence de tests automatisés complique les évolutions et augmente le risque de régressions.




**Éléments à vérifier :**
- Couverture des tests
- intégration continue
- tests unitaires et fonctionnels

---

### Question : Existe-t-il des développements spécifiques propriétaires au delà du paramétrage et des adaptations standards de la solution ?

**Clé :** `specifique`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Non (Score: 0)
- Un peu (Score: 1)
- Majoritairement (Score: 2)
- Totalement (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Y a-t-il des développements spécifiques, au delà du paramétrage prévu par la solution pour intégrer l'application dans le SI ?**

Les développements spécifiques sont toujours des ralentisseurs sur la maintenance et l'évolution.




**Éléments à vérifier :**
- Architecture applicative
- Dossier d'intégration

---

### Question : L'application et son implémentation respectent les standards et les principes d'architecture de l'entreprise ?

**Clé :** `standards`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L'application, son implémentation et son intégration respectent-ils les standards en vigueur et les principes d'architecture ?**

Des exceptions ou des dérogations ont-elles été décidées, ou implémentées pour cette solution ?




**Éléments à vérifier :**
- Architecture applicative
- Dossier d'architecture
- Dossier d'intégration
- Registre des décisions d'architecture
- Analyses d'outils tels que Sonar

---

## Catégorie : Exploitation

### Question : L'application souffre-t-elle fréquemment d'incidents impactant les utilisateurs ?

**Clé :** `incidents`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Non (Score: 0)
- Un peu (Score: 1)
- Souvent (Score: 2)
- Tout le temps (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application présente-t-elle des incidents récurrents ?**

Un taux élevé d’incidents réduit la disponibilité et la satisfaction des utilisateurs.




**Éléments à vérifier :**
- Statistiques de tickets
- temps moyen de résolution
- impact des incidents

---

### Question : Les performances actuelles sont-elles conformes aux attentes ?

**Clé :** `performances`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Les performances de l’application sont-elles satisfaisantes ?**

Une application lente nuit à l’expérience utilisateur et à la productivité.




**Éléments à vérifier :**
- Temps de réponse
- taux d’erreur
- monitoring des performances

---

### Question : L'application est-elle scalable facilement en cas de montée en charge ?

**Clé :** `scalabilité`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle suffisamment scalable par rapport aux besoins et évolution du besoin ?**

Une application non scalable devient rapidement un goulot d’étranglement en cas de montée en charge.




**Éléments à vérifier :**
- Architecture distribuée
- support du cloud
- capacité d’auto-scaling

---

## Catégorie : Adéquation Fonctionnelle

### Question : L'application couvre-t-elle efficacement l'ensemble des besoins métier actuels ?

**Clé :** `couverture_fonctionnelle`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application couvre-t-elle efficacement les besoins métier ?**

Une application mal adaptée entraîne une perte d’efficacité et une démultiplication des outils.




**Éléments à vérifier :**
-  Retour des utilisateurs
- adéquation avec les processus métier

---

### Question : Les fonctionnalités inutilisées ou obsolètes sont-elles régulièrement supprimées ou désactivées ?

**Clé :** `fonctions_inutilisées`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **Existe-t-il des fonctionnalités obsolètes ou inutilisées ?**

Le maintien de fonctionnalités inutiles alourdit l’application et accroît les coûts de maintenance.




**Éléments à vérifier :**
- Analyse des usages
- désactivation des modules non utilisés

---

### Question : L’application est-elle facilement adaptable à l’évolution des besoins métier ?

**Clé :** `adaptable`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :**

> **L’application est-elle facilement évolutive pour répondre aux nouvelles demandes métier ?**

Une application rigide empêche l’innovation et nécessite des développements coûteux.




**Éléments à vérifier :**
- Modularité de l’architecture
- facilité d’ajout de nouvelles fonctionnalités

---

### Question : L’expérience utilisateur (ui/ux) est-elle en adéquation avec les standards actuels ?

**Clé :** `ux`  
**Type :** select

**Applicable pour le type d'application :** Interne, Editeur, Open source

**Applicable pour le type d'hébergement :** On prem, Hybride, Cloud, SaaS

**Options :**

- Oui totalement (Score: 0)
- Quelques exceptions (Score: 1)
- Partiellement (Score: 2)
- Non, insatisfaisant (Score: 3)
- Non applicable (Score: N/A)

**Aide :** _Aucune aide disponible._

---
