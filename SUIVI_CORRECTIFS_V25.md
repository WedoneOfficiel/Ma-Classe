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


#### 15/11/2026 — Correction après CI #615

- Le job `tests` du run #615 a échoué dans `tests/test_v216_student_report.js` : le test extrait `studentReportIsPublished()` dans un contexte isolé où `evaluationModelPublished` n'est pas défini.
- Correction : le helper de rapport reste autonome et compare directement les timestamps à l'heure courante, tout en conservant la compatibilité des dates seules.
- Le job Firefox réel et la validation macOS du run #615 étaient encore en cours au moment du diagnostic ; le run complet n'est pas vert. Un nouveau run doit confirmer la correction.


#### 15/11/2026 — Cause supplémentaire identifiée pour le refus des appréciations

- En relisant le contrôle `canEditBulletinSubject()`, j'ai repéré une anomalie plus fondamentale : son expression de normalisation contenait des antislashs doublés et ne retirait donc pas correctement les accents. Une matière comme « Français » ou « Mathématiques » pouvait être comparée différemment de sa forme non accentuée, contrairement au helper serveur `_norm_text()`.
- Correction : remplacement par la plage Unicode combinante correcte, identique dans son intention à la normalisation serveur. Ajout d'une assertion de régression dédiée.
- Cette anomalie explique directement un refus injustifié possible même lorsque l'affectation EDT est correcte ; la correction de prise en compte des remplacements ponctuels reste également incluse.
- Validation CI en cours sur les derniers commits ; ne pas déclarer la correction résolue avant la suite verte et une recette réelle.


#### 15/11/2026 — État CI après ajout du correctif de normalisation Unicode

- Les runs #617 et #618 ont terminé leurs jobs `tests` et `Régression EDT — Firefox réel` avec succès. Leur validation macOS était encore en cours lors du dernier relevé.
- Le correctif Unicode de `canEditBulletinSubject()` et son assertion de régression ont été ajoutés après le lancement de ces runs ; ils ne sont donc pas encore couverts par ces résultats. Une exécution sur la tête la plus récente reste nécessaire avant validation.


#### 15/11/2026 — Renforcement de la recette de publication programmée

- Le statut affiché dans la saisie bascule maintenant de « Publication programmée » à « Publiée » une fois l'heure atteinte.
- Ajout d'un test d'intégration de la projection élève : une évaluation programmée une heure dans le futur reste absente, tandis qu'une évaluation dont l'heure est passée est transmise avec uniquement la note de l'élève concerné.
- Ce test complète le test unitaire du helper de date/heure. Résultats CI sur ces derniers commits encore attendus.


#### 15/11/2026 — Couleur des matières unifiée dans l’EDT

- Diagnostic : la couleur était stockée sur chaque créneau et le gestionnaire regroupait les créneaux par classe/enseignant/sous-groupe. Une modification ne pouvait donc pas garantir une couleur identique pour une même matière dans toutes les classes.
- Correctif candidat : ajout d’un dictionnaire `settings.subjectColors`, indexé par le nom de matière normalisé (accents, casse et espaces neutralisés). Le rendu des EDT lit désormais cette couleur commune ; le formulaire de créneau et le gestionnaire de cours l’enregistrent au niveau de la matière.
- Lors d’une modification, les anciennes couleurs locales des créneaux de la matière sont supprimées afin qu’elles ne masquent pas la couleur commune. Les hachures restent propres aux créneaux/cours.
- Test de régression ajouté : persistance de la couleur et résolution identique pour « Français » et « francais » avec espaces/casse différents.
- **À valider :** exécution CI sur le nouveau commit, puis recette visuelle dans un compte de direction/professeur et un compte élève. Ce correctif n’est pas encore déclaré validé.


#### 15/11/2026 — Suppression du rerendu complet après sauvegarde EDT

- Diagnostic : `saveSchedule()` ne rechargeait pas le document HTML depuis le serveur, mais appelait `render()`, qui remplaçait intégralement le contenu de `#main`. Ce rerendu global expliquait l’impression de rechargement de page après chaque sauvegarde.
- Correctif candidat : après confirmation serveur, le calendrier `.schedulePage` est reconstruit puis remplacé seul dans le DOM. L’en-tête, la navigation et le reste de la vue restent en place ; la position de défilement est conservée.
- En cas d’échec, les données locales sont restaurées et le formulaire reste ouvert pour permettre de corriger ou de réessayer, au lieu de remplacer toute la page.
- Test de régression ajouté sur le rafraîchissement ciblé et l’absence de rerendu complet.
- **À valider :** CI du commit et test manuel de création/modification/suppression avec contrôle visuel de l’absence de flash/rechargement.


#### 15/11/2026 — Ajustement après échec du test EDT ciblé

- **CI runs #630, #633 et #634 : échec** des suites JavaScript Linux/macOS dans `tests/test_v25_schedule_navigation.js` au scénario de sauvegarde. Le test extrait `saveSchedule()` isolément, mais n'extrait pas le helper `refreshSchedulePage()` défini plus haut dans le fichier. Lors du scénario simulé, cet appel non fourni déclenchait le `catch` et restaurait l'état initial.
- Le helper de rafraîchissement lui-même conserve un fallback sans DOM ; le problème observé était donc un helper absent du contexte de test isolé, et non un défaut de la sauvegarde serveur.
- Correction : le test de sauvegarde fournit maintenant un stub `refreshSchedulePage()` ; le comportement du helper réel reste vérifié séparément par les assertions dédiées de `test_v25_student_schedule.js`.
- **État :** correction du test poussée ; nouvelle CI nécessaire. Aucun correctif de production supplémentaire n'a été fait dans cette étape.


#### 15/11/2026 — CI partielle et projection de la couleur dans l’espace élève

- **CI run #636** sur la tête précédente : job `tests` réussi (tous les tests JavaScript et Python) et job `Régression EDT — Firefox réel` réussi. Le job `macos-validation` était encore en cours lors de cette mise à jour.
- Vérification complémentaire : la couleur matière globale est stockée dans `settings.subjectColors`. La projection serveur élève filtrait les paramètres et ne transmettait pas encore cette propriété ; les élèves auraient donc conservé la couleur par défaut malgré le choix du professeur.
- Correction : ajout de `subjectColors` à la liste blanche des paramètres transmis à l'élève, sans exposer les autres paramètres privés. Test de projection ajouté.
- **Validation :** ce dernier correctif serveur et son test attendent leur propre exécution CI. Le run #636 ne les couvre pas.


#### 15/11/2026 — Échec CI #651 et correction de syntaxe messagerie

- **CI run #651 : échec des trois jobs** (`tests`, Firefox réel et validation macOS). Le contrôle de syntaxe Python a identifié une `IndentationError` dans `server.py` ligne 593, introduite lors de l'ajout de la validation des pièces jointes des messages sortants élèves.
- Correction : réalignement du bloc de validation du chemin et du contrôle des liens symboliques ; la validation continue à exiger un chemin dans le dossier mail propre de l'élève et un fichier existant.
- **État :** correctif de syntaxe poussé ; nouvelle exécution CI indispensable avant de juger les tests de messagerie.


#### 15/11/2026 — Échec CI #653 : filtre des brouillons appliqué au mauvais rôle

- **CI run #653 :** le contrôle de syntaxe et les tests JavaScript ont progressé, mais les tests Python ont échoué dans `tests/test_v25_mailbox_upload_scope.py`. Une modification de filtrage des pièces jointes de brouillons avait été insérée dans `_teacher_visible_mailbox()` au lieu de `_student_visible_mailbox()` ; elle utilisait donc des variables (`sid`, `teachers`) inexistantes pour un compte professeur (`NameError`).
- Correction : restauration du filtrage historique des brouillons dans la projection professeur et déplacement du filtrage strict (dossier propre à l'élève + destinataires enseignants autorisés) dans la projection élève.
- **État :** correction poussée ; nouvelle CI nécessaire. Le job Firefox du run #653 a réussi, mais la suite complète n'est pas verte.


#### 15/11/2026 — Correction ciblée après CI #655

- **CI run #655 :** les tests Python ont de nouveau échoué sur le même `NameError` dans `_teacher_visible_mailbox()`. La première tentative de déplacement du filtre avait laissé le bloc au mauvais endroit ; la vérification du contenu exact du fichier a montré que la projection professeur contenait toujours les variables de l'élève.
- Correction plus sûre : remplacement complet, par bornes de fonctions, de `_teacher_visible_mailbox()` et `_student_visible_mailbox()`. La projection professeur retrouve son comportement initial ; le filtrage strict des brouillons et de leurs pièces jointes est désormais exclusivement dans la projection élève.
- **État :** correction poussée et relue dans les deux fonctions ; nouvelle CI nécessaire. Aucun résultat vert n'est revendiqué pour la messagerie.


#### 15/11/2026 — CI #657 et remplacement complet des projections de messagerie

- **CI run #657 :** le test `MailboxAndUploadScopeTests.test_mailbox_projection_only_includes_participant_messages_and_own_private_state` et deux tests d'accès aux pièces jointes échouaient encore avec `NameError: sid is not defined` dans `_teacher_visible_mailbox()`. La tentative précédente n'avait pas effectivement remplacé le bloc résiduel.
- Correction : les deux fonctions de projection ont été réécrites intégralement par bornes de fonctions. `_teacher_visible_mailbox()` n'utilise désormais que l'identité professeur et son filtrage d'origine ; `_student_visible_mailbox()` applique séparément le filtrage élève et les pièces jointes de ses brouillons.
- **État :** tête de branche relue après écriture ; une nouvelle CI doit confirmer que les tests professeur existants et les nouveaux tests élève passent ensemble.


#### 15/11/2026 — CI #658 et projection des couleurs vers les professeurs

- **CI run #658** sur la tête précédente : job `tests` réussi (tests JavaScript et Python) et job `Régression EDT — Firefox réel` réussi ; la validation macOS était encore en cours lors du relevé.
- Vérification complémentaire de la couleur matière globale : le filtre serveur de l'espace professeur ne transmettait pas `settings.subjectColors`, ce qui aurait laissé les comptes enseignants avec la palette par défaut.
- Correction : ajout de `subjectColors` à la liste blanche de la projection professeur, avec test confirmant que la préférence est transmise sans exposer `schoolName` ni les paramètres privés. La projection élève avait déjà été corrigée et testée.
- **Validation :** cette dernière correction professeur attend une nouvelle CI.
