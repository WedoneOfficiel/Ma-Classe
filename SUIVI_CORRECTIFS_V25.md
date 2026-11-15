# Registre de suivi — correctifs V25

Ce fichier est le journal de référence des problèmes remontés, des vérifications, des modifications et de leurs résultats. Il doit être mis à jour à chaque intervention, y compris lorsqu'un correctif échoue ou qu'un diagnostic invalide une hypothèse. Ne pas rouvrir un problème déjà résolu sans élément nouveau.

## Campagne du 15 novembre 2026 — EDT, espace élève, messagerie et bulletins

**Branche de travail :** `fix/v25-student-teacher-workflows`  
**Base :** `main` au démarrage de la campagne (V25.0.22, commit de fusion précédent `8546a2be89c0bf463588abafa87003d433d62e57`).  
**Statut global :** diagnostic en cours. Aucun correctif fonctionnel de cette campagne n'est encore déclaré réussi. Aucun changement sur l'installation locale ou les données de l'utilisateur.

### Demandes utilisateur (formulation conservée)

1. Pourquoi le module EDT n'a-t-il pas le même aspect chez les élèves et les professeurs ?
2. Après modification puis clic sur « Enregistrer un créneau », la page se décharge/recharge encore.
3. Pourquoi ne peut-on pas modifier la couleur d'une matière ?
4. Les élèves ont accès aux boutons de modification des séances **et** des créneaux ; ils ne doivent avoir aucun droit d'édition.
5. L'espace élève n'a pas de module Paramètres adapté à ses besoins.
6. La messagerie est inaccessible sauf tentative via le widget de la page d'accueil, qui ne fonctionne pas correctement.
7. Le problème des bulletins n'est toujours pas réglé.

### État initial vérifié dans la documentation du dépôt

- `ETAT_V25.txt` indique que la messagerie élève et le Cloud élève ont été volontairement désactivés en attendant un audit dédié (entrée du 12/11/2026).
- `CHANGELOG_V25.txt` mentionne un moteur de calendrier commun aux vues élève et professeur et des protections serveur récentes ; cela ne valide pas la parité visuelle ni l'absence de commandes d'édition dans l'interface élève.
- `AUDIT.txt` conserve des réserves sur la recette multi-comptes, les permissions globales, les bulletins et la messagerie.
- La campagne précédente a fusionné des permissions EDT/enseignants et un filtrage des évaluations publiées ; cela ne constitue pas une recette complète des parcours décrits ici.

### Suivi des sept problèmes

| ID | Problème | État initial | Diagnostic | Correctif | Tests / résultat |
|---|---|---|---|---|---|
| EDT-01 | Parité visuelle élève/professeur | Signalé par utilisateur | À faire | À faire | Non testé |
| EDT-02 | Enregistrement créneau décharge/recharge la page | Signalé par utilisateur | À faire | À faire | Non testé |
| EDT-03 | Couleur matière modifiable | Signalé par utilisateur | À faire | À faire | Non testé |
| SEC-01 | Élève voit les commandes d'édition séances et créneaux | Signalé par utilisateur ; gravité élevée | À faire (UI + serveur) | À faire | Non testé |
| ELEVE-01 | Module Paramètres adapté absent | Signalé par utilisateur | À faire | À faire | Non testé |
| MAIL-01 | Messagerie inaccessible / widget défaillant | Signalé par utilisateur ; accès élève désactivé historiquement | À faire | À faire | Non testé |
| BUL-01 | Parcours bulletins toujours défaillant | Signalé par utilisateur malgré correctifs antérieurs | À faire : reproduire le symptôme exact | À faire | Non testé |

### Journal des interventions

#### 15/11/2026 — Initialisation
- Création de la branche isolée `fix/v25-student-teacher-workflows` depuis `main`.
- Création de ce registre AVANT les modifications fonctionnelles.
- Aucune modification de `main`, aucune fusion et aucun déploiement.
- Prochaine action : localiser précisément les fonctions UI et endpoints serveur des sept sujets, puis écrire des tests de reproduction avant de corriger.

#### 15/11/2026 — Diagnostic du code (sans correctif fonctionnel déclaré)

- **EDT élève/professeur :** `studentSchedule()` réutilise bien `scheduleWeek/day/month` et `eventCard`, mais avec un mode élève. La structure calendrier est donc partagée ; les différences peuvent venir des wrappers, du shell et des règles CSS. À comparer visuellement en navigateur avant de conclure.
- **SEC-01 — défaut concret identifié :** `eventCard()` masque le bouton crayon en mode élève et désactive le drag via `draggable="false"`, mais `scheduleWeek()` et `scheduleDay()` laissent les zones `ondragover` / `ondrop` actives sans condition. Ce n'est pas une protection suffisante. De plus, `openOccurrence()` est le formulaire d'édition enseignant ; `openStudentLesson()` est actuellement un lecteur en lecture seule. Il faut vérifier les autres points d'entrée et le refus serveur.
- **EDT-03 — défaut concret identifié :** `openSchedule()` ne propose aucun champ de couleur ; `saveSchedule()` force la couleur existante ou une couleur déterministe via `subjectColor()`. L'utilisateur ne peut donc pas choisir une couleur personnalisée. Correctif à concevoir en respectant le partage de créneaux multi-classes.
- **ELEVE-01 — défaut concret identifié :** la navigation élève n'inclut aucun lien Paramètres et aucune fonction `studentSettings()` n'existe. Le module `settings()` est global et contient des paramètres d'administration ; il ne doit pas être exposé tel quel.
- **MAIL-01 — cause explicite identifiée :** `studentMessages()` affiche un écran « arrive dans une prochaine étape » ; la navigation élève n'inclut pas ce module. Côté serveur, `_student_visible_data()` retourne explicitement `conversations=[]` et `mailboxV2={}`, car les droits message par message n'ont pas été validés. Il ne faut pas simplement rendre le bouton visible : il faut d'abord implémenter et tester un modèle d'accès privé.
- **EDT-02 — piste non confirmée :** `saveSchedule()` appelle `save(true)`, attend `flushPendingSave()`, puis recharge les données via `/api/data` et rend le module. Aucun `location.reload()` n'apparaît dans `_all.js`. Le symptôme de « déchargement » peut être un rendu complet de l'application après sauvegarde, mais cela doit être reproduit pour confirmer.
- **BUL-01 :** le code comporte plusieurs étapes de calcul, sauvegarde, validation/publication et PDF ; les tests existants couvrent notamment les droits PP, la source serveur du PDF et le filtrage élève. Le dépôt ne permet pas de savoir quel symptôme l'utilisateur rencontre encore. Je ne déclarerai pas ce point résolu sur la seule base des tests antérieurs.
- **État des tests de cette campagne :** aucun test navigateur/API exécuté à ce stade ; aucune correction fonctionnelle fusionnée ou publiée.

#### 15/11/2026 — Première tranche de corrections (branche isolée)

**Modifications effectuées**
- `_all.js` : en mode élève, le bouton crayon de modification des créneaux n'est plus rendu dans le DOM.
- `_all.js` : les zones de dépôt drag-and-drop des vues jour/semaine sont maintenant conditionnées au mode enseignant ; l'élève ne reçoit plus ces gestionnaires d'édition.
- `_all.js` : le formulaire de créneau dispose maintenant d'un sélecteur de couleur ; la couleur choisie est enregistrée à la création et à la modification du créneau.
- `_all.js` : après sauvegarde, le rendu de l'application préserve la position de défilement afin d'éviter l'impression de déchargement/saut de page. La sauvegarde serveur et sa confirmation restent inchangées.
- `_all.js` : création de `studentSettings()`, avec profil en lecture seule, accès au changement de mot de passe existant et choix de thème local ; ajout du lien Paramètres dans la navigation élève.
- `tests/test_v25_student_schedule.js` : assertions sur l'absence du bouton d'édition, le retrait des drop targets, le champ couleur et la préservation du scroll.
- `tests/test_v25_student_scope.py` : nouveau test vérifiant qu'une sauvegarde élève falsifiée ne modifie ni l'EDT ni le contenu des séances.
- Nouveau `tests/test_v25_student_settings.js` : vérifie la présence et le contenu minimal du module Paramètres élève.

**État des demandes après ces modifications**
| ID | État | Résultat actuel |
|---|---|---|
| EDT-01 | En cours | Le calendrier conserve le moteur partagé ; parité visuelle complète pas encore validée en navigateur. |
| EDT-02 | Correctif candidat | La sauvegarde ne fait pas de rechargement navigateur ; elle re-rend l'application. Le scroll est maintenant préservé. Reproduction manuelle et CI nécessaires. |
| EDT-03 | Correctif candidat | Sélecteur couleur ajouté et sauvegardé par créneau/cours. Vérifier la cohérence des couleurs sur tous les cours d'une même matière. |
| SEC-01 | Renforcé | Contrôles UI et test serveur : édition EDT/séances interdite côté serveur à l'élève, et contrôles d'édition retirés de l'EDT élève. CI à exécuter. |
| ELEVE-01 | Correctif candidat | Paramètres élève ajoutés (profil lecture seule, changement de mot de passe, thème). CI et parcours navigateur à exécuter. |
| MAIL-01 | Non résolu / volontairement bloqué | L'accès élève reste désactivé tant que la projection et la fusion sécurisées des messages privés ne sont pas développées et testées. Ne pas réactiver le widget seul. |
| BUL-01 | Non résolu | Les protections existantes sont présentes, mais le symptôme fonctionnel reste à identifier ; aucune modification hasardeuse du calcul/publication n'a été faite. |

**Limites de validation à ce stade**
- Les tests ont été ajoutés, mais ils n'ont pas encore été exécutés dans GitHub Actions.
- Aucun test manuel Firefox n'a été effectué dans le dossier local de test.
- Aucun correctif de cette campagne n'est fusionné dans `main` ni déployé.

#### 15/11/2026 — Parité visuelle et corrections de tests CI

- Diagnostic confirmé pour **EDT-01** : l'enseignant utilisait `.schedulePage`, `.scheduleControlPanel`, `.scheduleDateControls`, `.scheduleViewSwitch`, `.scheduleLegend` et `.scheduleCalendarSurface`; l'élève avait un ancien assemblage `.toolbar` + cartes séparées et un calendrier mensuel spécifique. Le moteur semaine/jour était commun, mais pas la structure visuelle.
- Correction : `studentSchedule()` utilise maintenant la même structure visuelle et les mêmes composants de calendrier jour/semaine/mois que le professeur, en conservant une navigation élève sans actions d'édition.
- **CI run #605** : échec du test JS existant car le routeur de test ne fournissait pas le nouveau stub `studentSettings`. Correction du harnais de test.
- **CI run #607/#608** : le test de régression EDT vérifiait l'ancien helper étudiant spécifique. Mise à jour de l'attente pour le moteur calendrier partagé.
- **CI run #609** : le test de sauvegarde a révélé que le mock navigateur ne définissait pas `window.scrollTo`. Correction du mock dans `tests/test_v25_schedule_navigation.js`. Le navigateur réel Firefox a passé le job dans les runs #608 et #609.
- Les installations de test Linux/macOS et la vérification syntaxique JS/Python ont passé les étapes correspondantes dans ces runs ; la suite JavaScript complète a interrompu les tests Python à cause des assertions de test ci-dessus.
- **Statut** : pas encore de suite CI entièrement verte sur le dernier commit ; attendre le run suivant avant de qualifier les correctifs de validés.

#### 15/11/2026 — Ajustement du test de parité EDT

- **CI run #610** : les tests ont validé les correctifs précédents jusqu'à `test_v25_student_schedule.js`, qui mockait les anciens wrappers `studentScheduleWeek/Day/Month`. Le rendu élève utilise maintenant volontairement les renderers communs `scheduleWeek/Day/Month` ; le test a été adapté pour fournir ces fonctions communes.
- Le job Firefox réel du run #610 est encore en cours au moment de cette entrée ; les étapes installateur, bash et syntaxe JS ont réussi.
- Aucun résultat CI n'est considéré comme vert tant que les trois jobs ne sont pas terminés.


#### 15/11/2026 — Correctifs candidats BUL-01 ajoutés à la branche

- `_all.js` : le contrôle navigateur des cases d'appréciation reconnaît désormais le remplacement ponctuel actif via `schedule[].overrides[date].replacementTeacherId`, en cohérence avec le contrôle serveur déjà présent.
- `_all.js` : le formulaire réellement utilisé (`v217DeepMeta` / `v217DeepSaveMeta`) propose désormais brouillon invisible, publication immédiate ou programmation date/heure. La date/heure saisie dans le fuseau local de l'appareil est convertie en timestamp ISO absolu lors de l'enregistrement. L'écran de saisie indique aussi le statut de publication.
- `_all.js` : les filtres des notes élèves, de la moyenne élève et du rapport comparent les dates programmées à l'heure courante, et non plus uniquement à la date.
- `server.py` : ajout de `_evaluation_publication_due()` ; la projection serveur élève masque une note jusqu'à l'instant exact programmé. Les anciennes valeurs date seule restent compatibles ; une valeur date/heure invalide est masquée par défaut.
- Tests ajoutés : heure programmée avant/après l'instant de référence, compatibilité date seule, timestamp invalide masqué, et droit d'un remplaçant ponctuel sur la matière enseignée. Assertions JS sur le formulaire de publication actif et la reconnaissance du remplacement.
- **Validation :** les fichiers ont été commités sur `fix/v25-student-teacher-workflows`. Les tests automatisés et la CI de cette nouvelle tête de branche restent à exécuter ; aucun résultat vert n'est revendiqué à ce stade. Recette réelle avec deux comptes (enseignant et élève) encore nécessaire.
