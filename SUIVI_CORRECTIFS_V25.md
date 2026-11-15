# Registre de suivi — correctifs V25

Ce fichier est le journal de référence des problèmes remontés, des vérifications, des modifications et de leurs résultats. Il doit être mis à jour à chaque intervention, y compris lorsqu'un correctif échoue ou qu'un diagnostic invalide une hypothèse. Ne pas rouvrir un problème déjà résolu sans élément nouveau.

## Campagne du 15 novembre 2026 — EDT, espace élève, messagerie et bulletins

**Branche de travail :** `fix/v25-student-teacher-workflows`  
**Base :** `main` au démarrage de la campagne (V25.0.22, commit de fusion précédent `8546a2be89c0bf463588abafa87003d433d62e57`).  
**Statut global :** CI complète réussie sur la tête `01be4cde` (run #663) : tests Linux, validation macOS et régression EDT Firefox réel. Les correctifs restent à soumettre à une recette fonctionnelle réelle multi-comptes avant fusion/déploiement. Aucun changement sur l'installation locale ou les données de l'utilisateur.

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


#### 15/11/2026 — CI #661 : assertion de conservation des paramètres à actualiser

- **CI run #661 :** tests de messagerie élève (`test_v25_student_scope.py`) réussis ; tests de messagerie professeur/pièces jointes (`test_v25_mailbox_upload_scope.py`) réussis. Un test `test_teacher_cannot_modify_global_settings` a échoué car son attendu exact ne contenait pas la nouvelle préférence `subjectColors` ajoutée au jeu de données de test.
- Le comportement attendu reste que le professeur ne puisse pas modifier les paramètres globaux ; le test doit simplement vérifier que `subjectColors` existant est conservé, au même titre que `schoolName`.
- Correction du seul attendu de test, sans changement serveur supplémentaire.
- Firefox réel du run #661 était encore en cours au relevé ; la validation macOS n'était pas terminée. Nouvelle CI nécessaire après cette correction.


#### 15/11/2026 — CI complète réussie sur la tête de branche

- **Commit :** `01be4cde1560e0fc5c3cce96bf9984069442c274`.
- **GitHub Actions run #663 :** les trois jobs sont terminés avec succès : `tests`, `macos-validation` et `Régression EDT — Firefox réel`.
- Le job `tests` a exécuté avec succès les suites JavaScript et Python complètes, la compilation/syntaxe Python, la syntaxe JavaScript, les lanceurs macOS et l'installateur Linux.
- Le job macOS a exécuté avec succès l'installateur Apple Silicon, les vérifications JavaScript/Python et les suites de tests.
- Le test Firefox réel de l'EDT a réussi.
- **Conclusion :** la CI est entièrement verte sur cette tête. Cela valide les tests automatisés présents, pas encore la recette fonctionnelle réelle avec comptes direction/professeur/élève. Les parcours bulletins, messagerie et paramètres nécessitent toujours cette recette.


#### 15/11/2026 — Registre des bugs structuré et correctifs bulletins sur période

- Création de **`REGISTRE_BUGS_V25.md`**, registre synthétique distinct du présent journal technique.
- Le tableau contient les colonnes demandées : **Identifiant**, **Bug**, **Description simple du bug**, **Description détaillée**, **État**.
- Les sept anomalies initiales sont reprises avec des identifiants stables : EDT-01, EDT-02, EDT-03, SEC-01, ELEVE-01, MAIL-01 et BUL-01.
- Les états sont volontairement prudents : les sept bugs sont « En cours de résolution ». Aucun n'est déclaré « Résolu » tant que les recettes fonctionnelles nécessaires ne sont pas terminées.
- **BUL-01 — correctif supplémentaire :** le contrôle des droits tient maintenant compte des affectations et remplacements sur la période du bulletin. Un remplacement actuel ne doit pas retirer rétroactivement à un enseignant le droit de compléter une période antérieure. Un test de régression dédié a été ajouté.
- **CI run #672**, sur la tête de branche vérifiée : les trois jobs sont terminés avec succès — suite complète JavaScript/Python, validation macOS (dont installateur Apple Silicon et tests Python), et test EDT dans Firefox réel.
- **Limite importante :** la CI verte confirme les tests automatisés, pas encore la recette réelle avec comptes élève/professeur. Pour BUL-01, le message initial « Vous ne pouvez pas remplir cette case » n'a pas été retrouvé textuellement dans le frontend actuel ; le parcours complet doit encore être reproduit pour confirmer que le bon garde-fou a été corrigé.
- La PR #9 reste ouverte en brouillon ; aucun merge ni déploiement.


#### 15/11/2026 — Extension du registre après récupération de l'historique des signalements

- Relecture des signalements antérieurs : la première version du registre ne contenait que les sept anomalies de la campagne du 15/11. Plusieurs problèmes distincts signalés le 13/11 et plusieurs défauts identifiés pendant l'audit devaient aussi être suivis.
- Ajout des problèmes EDT de rafraîchissement en temps réel et de saut lors du changement de semaine/vue (EDT-04, EDT-05).
- Ajout de l'erreur historique `ReferenceError: pat is not defined` dans l'EDT élève (JS-01), du problème d'ajout de pièce jointe à un devoir (DEV-01) et du module Séances/Leçons élève avec en-tête absent (LEC-01). Le lien causal entre l'erreur JS et l'échec d'upload reste non confirmé.
- Ajout du problème distinct de visibilité des notes dans l'espace élève (EVAL-01), ainsi que des anomalies complémentaires identifiées pendant l'audit : conversion des notes sur 10 (EVAL-02), visibilité prématurée des notes non publiées/programmées (EVAL-03) et cohérence des droits de modification (EVAL-04).
- La gestion des mises à jour du serveur est enregistrée séparément comme demande d'amélioration AMEL-01, et non comme bug confirmé. Le fonctionnement manuel par commandes doit être conservé.
- Le registre comporte désormais **16 bugs** (11 en cours de résolution, 5 détectés) et **1 demande d'amélioration**. Aucun bug n'est marqué résolu sans recette.
- **État du code historique :** la référence `pat` n'apparaît plus dans le chemin actuel de `studentEventCard()`, mais le scénario exact avec un vrai compte élève n'a pas encore été reproduit. Le bug reste donc en cours de résolution, pas déclaré résolu.


#### 15/11/2026 — Recoupement du registre avec les tests existants

- Le recoupement de `tests/test_v25_student_schedule.js` et du code actuel montre que plusieurs signalements historiques disposent déjà de protections/tests, sans que cela suffise à clore la recette :
  - **EDT-04** : `refreshLiveScheduleData` et son rafraîchissement périodique sont présents ; le test vérifie le mécanisme, mais pas une synchronisation réelle entre deux comptes.
  - **EDT-05** : le test couvre les déplacements jour/semaine/mois ; il ne mesure pas encore le saut visuel signalé dans le navigateur.
  - **LEC-01** : le test vérifie que la page Séances & Leçons utilise le shell avec son en-tête ; l'actualisation des données en situation réelle reste à contrôler.
  - **JS-01** : le test interdit l'interpolation `${pat}` non définie et le chemin actuel `studentEventCard()` n'utilise plus cette variable ; le scénario historique reste à reproduire sur le compte élève.
- Le registre a été ajusté en conséquence : **16 bugs**, dont **14 en cours de résolution** et **2 détectés**. **DEV-01** (upload de pièce jointe à un devoir) et **EVAL-04** (cohérence des droits de modification des évaluations) restent au stade détecté faute de preuve suffisante d'un correctif dédié.
- La suite de tests complète du commit applicatif #672 est verte. Les exécutions déclenchées par les commits documentaires sont distinctes et doivent être suivies sans confondre leur état avec la validation applicative.


#### 15/11/2026 — Test ciblé de l'ajout de pièces jointes aux devoirs

- Le signalement historique **DEV-01** était encore au stade détecté : le message `ReferenceError: pat is not defined` apparaissait aussi lors de l'ajout d'une pièce jointe, mais l'échec du téléversement n'avait pas été reproduit.
- Ajout de `tests/test_v25_student_submission_upload.js`, qui exécute le gestionnaire d'ajout dans un contexte simulé et vérifie deux scénarios : téléversement réussi avec création/enregistrement du brouillon, et échec du téléversement avec affichage de l'erreur sans création d'un brouillon vide.
- **Limite :** ce test valide le flux frontend et ses réactions aux réponses de téléversement simulées ; il ne remplace pas un essai d'envoi réel vers le serveur avec un compte élève.
- DEV-01 passe donc de « Détecté » à « En cours de résolution ». Le registre compte désormais 16 bugs : 15 en cours, 1 détecté, 0 résolu.
- Nouvelle CI requise pour exécuter ce test ajouté.


#### 15/11/2026 — Test frontend des droits bulletin : correction du scénario et CI #683/#684

- Ajout de `tests/test_v25_bulletin_permissions.js` pour exécuter réellement le helper frontend `canEditBulletinSubject()` sur trois cas : titulaire d'une période passée malgré un remplacement actuel, remplaçant ponctuel pendant la période, enseignant sans affectation à la classe.
- **CI #683 :** échec de la suite JavaScript sur le troisième cas. Le faux compte de test était lui-même déclaré professeur principal et enseignant de la classe, avec la matière dans son profil ; le fallback de compatibilité lui accordait donc l'accès conformément à la configuration du test. Ce n'était pas une preuve d'un défaut applicatif.
- Correction du fixture : le cas « enseignant non affecté » n'a désormais ni classe dans ses affectations, ni rôle de professeur principal, ni matière dans son profil.
- **CI #684 :** suite JavaScript complète Linux réussie avec le test corrigé ; régression EDT Firefox réel réussie. La validation macOS a passé l'installateur Apple Silicon, les vérifications JavaScript et la suite JavaScript ; l'exécution des tests Python macOS est encore en cours au moment de cette entrée.
- La PR reste en brouillon. Le test automatisé ne remplace pas la recette du bulletin avec un vrai compte enseignant.


#### 15/11/2026 — EVAL-04 : droits d'édition des évaluations

- Cause confirmée : le périmètre d'une classe accessible était utilisé pour sélectionner les évaluations modifiables/supprimables. Cela ne suffisait pas à garantir que le professeur enseignait la matière concernée.
- Serveur (server.py) : le périmètre modifiable des évaluations vérifie désormais _teacher_can_edit_evaluation. Une évaluation d'une matière non enseignée reste conservée même si le client tente de la supprimer ; une tentative de changer la matière d'une évaluation existante est rejetée et l'ancienne version est restaurée.
- Interface (_all.js) : ajout de canEditEvaluation, avec prise en compte des affectations EDT, affectations explicites, dates, remplacements ponctuels et normalisation des accents. Garde-fous sur l'ouverture, la création/modification, les notes, commentaires, critères, compétences et suppressions.
- Tests ajoutés : tests/test_v25_evaluation_permissions.js (contrôle frontend) et un test dans tests/test_v25_teacher_data_scope.py (refus de modifier/supprimer une matière non enseignée).
- Régression de test rencontrée : le premier passage a révélé que tests/test_competencies_v20.js ne définissait pas authUser. Le contexte du test a été complété avec un rôle administrateur ; le contrôle applicatif n'a pas été affaibli.
- CI : run #690 — tests Linux réussis et régression Firefox réussie ; validation macOS encore en cours au dernier contrôle. Run #691, sur le correctif complémentaire protégeant aussi les notes des critères, est en cours ; tests Linux passés, Firefox et macOS en cours.
- Statut fonctionnel : correctif engagé et tests automatisés ciblés présents. Ne pas déclarer résolu avant recette avec un enseignant ayant accès à plusieurs matières et un enseignant remplaçant.


#### 15/11/2026 — EVAL-04 : contrôle du parcours d'évaluation actif

- Audit complémentaire : le flux utilisé par l'écran moderne est piloté par v217DeepOpenEvaluation / v217DeepSaveMeta / v217DeepSetGrade ; les garde-fous des anciennes fonctions ne suffisaient donc pas.
- Correctif : ajout des vérifications dans l'ouverture de l'évaluation, l'édition de sa configuration, l'enregistrement de la configuration et la saisie des notes du flux V217. Les handlers communs pour les critères, compétences, commentaires et suppressions sont également protégés.
- Tests : le test JavaScript vérifie maintenant explicitement les garde-fous du flux V217, en plus des cas d'affectation matière, accents et remplacement.
- CI : run #693 entièrement vert (tests, Firefox EDT et validation macOS). Run #696 : tests JavaScript et Python réussis ; validation macOS et Firefox en cours au dernier relevé.
- EVAL-04 reste En cours de résolution jusqu'à la recette fonctionnelle multi-comptes.


#### 15/11/2026 — DEV-01 : pièces jointes des devoirs

- Distinction faite entre les deux parcours : dépôt d'une pièce jointe au devoir par le professeur (`uploadWorkFiles`) et dépôt du rendu par l'élève (`studentAddSubmissionFiles`). Le signalement `ReferenceError: pat is not defined` est enregistré, mais son lien causal avec l'échec du téléversement n'est pas démontré.
- Côté professeur : `uploadWorkFiles` affiche maintenant le message serveur réel en cas d'échec, évite d'ajouter deux fois le même fichier au brouillon et donne un bilan si plusieurs fichiers ont des résultats différents. Le champ de sélection est réinitialisé après sélection pour permettre de choisir à nouveau le même fichier.
- Tests : ajout de `tests/test_v25_homework_attachment_upload.js` couvrant succès, refus serveur, absence de doublon et conservation des fichiers dans le brouillon. `tests/test_v25_student_submission_upload.js` couvre le parcours de dépôt élève. `tests/test_v25_student_submissions.py` couvre l'intégration serveur dépôt → sauvegarde du brouillon → envoi → lecture du fichier et refus d'un dossier appartenant à un autre élève.
- CI run #698 : tests Linux (JS et Python) réussis ; Firefox réel et validation macOS encore en cours au dernier relevé.
- État DEV-01 : En cours de résolution. La recette avec comptes réels reste nécessaire ; ne pas considérer le correctif comme confirmé.


#### 15/11/2026 — EVAL-01 / EVAL-02 / EVAL-03 : réévaluation après audit croisé

- EVAL-01 : le modèle central alimente le relevé élève ; le test V21.17 vérifie la présence des notes publiées, et le test serveur vérifie qu'un enseignant affecté peut publier une note et que l'élève reçoit uniquement sa propre note. Les notes non publiées sont exclues.
- EVAL-02 : les moyennes pondérées, les moyennes par évaluation, le carnet de notes et les statistiques de classe utilisent le barème réel (`maxScore`) pour ramener les résultats sur 20. Le test de modèle vérifie explicitement 8/10 = 16/20 et couvre aussi les coefficients.
- EVAL-03 : le filtrage est fait dans la projection serveur élève avec comparaison à l'instant exact (`_evaluation_publication_due`) ; le modèle frontend filtre aussi les brouillons et les dates de publication. Les tests couvrent publication future, date seule et heure exacte.
- Évaluation technique : les trois correctifs disposent de tests ciblés frontend/backend et les parcours principaux sont cohérents dans le code. Ils passent donc à **Supposé résolu**, jamais à « Corrigé » sans confirmation explicite de l'utilisateur.
- CI : run #698 — Linux (tous les tests JS/Python) et Firefox réel réussis ; validation macOS encore en cours au dernier relevé.


#### 15/11/2026 — EVAL-04 : passage à « Supposé résolu »

- Après l'audit du flux V217 actif, les contrôles sont présents à l'ouverture, à l'édition de configuration, à l'enregistrement, sur les notes, commentaires, critères, compétences et suppressions. Le serveur conserve les anciennes données si un enseignant tente de retirer ou de falsifier une évaluation d'une matière qu'il n'enseigne pas.
- Les tests backend de fusion des données et les tests frontend ciblés passent dans les runs #690 à #693. La protection du parcours actif a également été ajoutée au test source dédié ; run #696 a passé les tests JS/Python Linux.
- Conclusion technique : **Supposé résolu**, sous réserve de recette avec un enseignant multi-matières et un remplaçant. Ce statut n'est pas « Corrigé » et ne sera changé qu'après confirmation explicite de l'utilisateur.


#### 15/11/2026 — JS-01 : référence `pat` dans l'EDT élève

- Vérification de `_all.js` : aucune occurrence de l'identifiant `pat` ne subsiste. Le wrapper `studentEventCard(o,d)` délègue directement à `eventCard(o,d,true)`.
- Renforcement de `tests/test_v25_student_schedule.js` : en plus de vérifier l'absence de l'interpolation fautive, le test exécute le wrapper dans un contexte isolé et confirme le mode élève.
- Conclusion technique : **Supposé résolu**. La recette dans l'EDT avec un vrai compte élève reste nécessaire avant que l'utilisateur puisse confirmer « Corrigé ».

- Test serveur complémentaire ajouté dans `tests/test_v25_mailbox_upload_scope.py` : un enseignant peut déposer une pièce jointe dans `submissions/<créneau>` ; le fichier n'est lisible qu'après que la séance/devoir enregistré le référence. Cela couvre le trajet réel de permission du dépôt enseignant.


#### 15/11/2026 — Reclassement des correctifs vérifiés en « Supposé résolu »

- EDT-02 : sauvegarde par rafraîchissement ciblé et conservation du scroll, couverts par tests de code et régression navigateur.
- EDT-03 : couleurs de matière centralisées, normalisées (accents/casse/espaces) et propagées, couvertes par test dédié.
- EDT-05 : navigation jour/semaine/mois couverte par tests et régression Firefox.
- SEC-01 : commandes d'édition élève masquées dans l'interface et refus des modifications falsifiées côté serveur, couverts par tests frontend/backend.
- ELEVE-01 : page Paramètres élève, profil en lecture seule, changement de mot de passe et thème local couverts par test dédié.
- LEC-01 : en-tête et structure de la page Séances & Leçons élève vérifiés par le test de rendu.
- BUL-01 : droits d'appréciation vérifiés sur les périodes passées, accents et remplacements ponctuels par tests frontend/backend.
- Ces sept anomalies passent à **Supposé résolu** sur la base du code et des tests. L'utilisateur doit encore confirmer les parcours réels ; aucun statut « Corrigé » n'est attribué.
- EDT-01 reste en cours (parité visuelle complète à confirmer), EDT-04 reste en cours (actualisation réellement multi-comptes à confirmer), DEV-01 reste en cours (recette pièces jointes avec vrais comptes), MAIL-01 reste en cours (recette messagerie élève/professeur).
- CI run #714 : tests Linux JS/Python et Firefox réel réussis ; validation macOS encore en cours au dernier relevé.


#### 15/11/2026 — EDT-04 : test Firefox réel élève/professeur ajouté

- Le test navigateur Firefox existant ne vérifiait que la synchronisation d'une session direction. Il a été étendu : création d'un accès élève temporaire dans l'application isolée, ouverture d'une seconde session Firefox, affichage de l'EDT élève, modification de l'EDT depuis la session direction, puis attente de la mise à jour dans l'espace élève via la synchronisation périodique.
- Le test vérifie que l'élève voit d'abord le cours existant puis le nouveau cours ajouté côté professeur, sans recharger manuellement la page.
- EDT-04 reste **En cours de résolution** jusqu'à réussite du nouveau test navigateur et confirmation utilisateur.
- CI run #714 : succès complet sur Linux, Firefox réel et macOS. Run #716 : Linux et Firefox réussis ; macOS encore en cours au dernier relevé. Run #717 : exécution du nouveau test élève/professeur en cours.


#### 15/11/2026 — EDT-04 : test multi-comptes Firefox réussi

- Le test Firefox réel passe après ajout du parcours de première connexion élève (mot de passe provisoire puis changement obligatoire du mot de passe). Le navigateur ouvre une session direction et une session élève séparées ; la direction ajoute un cours et l'EDT élève le récupère automatiquement via `refreshLiveScheduleData`, sans rechargement manuel.
- Le premier essai a échoué parce que le compte élève de test était encore en état `mustChangePassword` ; le test a été complété pour suivre le parcours normal de première connexion. Le test révisé passe dans le run #720.
- EDT-04 passe à **Supposé résolu**. La confirmation de l'utilisateur dans son installation reste requise avant « Corrigé ».
- Run #720 : tests Linux réussis, Firefox réel réussi ; validation macOS encore en cours au dernier relevé. Runs #714 et #716 sont entièrement verts sur les trois jobs.


#### 15/11/2026 — MAIL-01 : boîte élève validée dans Firefox réel

- Le test navigateur crée un véritable compte professeur via `/api/admin/teacher`, l'associe à la classe, crée un compte élève et suit son premier changement de mot de passe.
- Un message envoyé par l'enseignant et adressé à l'élève est injecté dans la boîte serveur ; le compte élève ouvre ensuite `studentMessages` dans Firefox et retrouve le message dans sa boîte de réception.
- Le premier essai du test a révélé que le professeur de test n'avait pas été créé par l'API canonique : les sauvegardes `/api/save` conservent volontairement la liste `users` côté serveur et ignoraient l'insertion directe du professeur dans le JSON client. Le test utilise désormais `/api/admin/teacher`, comme l'application réelle.
- Le nouveau test Firefox passe dans le run #725 ; les tests Linux passent aussi. Validation macOS encore en cours au dernier relevé.
- MAIL-01 passe à **Supposé résolu**. La confirmation utilisateur reste requise avant « Corrigé ».


#### 15/11/2026 — DEV-01 : dépôt de devoir validé dans Firefox réel

- Le test Firefox réel passe désormais sur le parcours complet : connexion d'un compte professeur, téléversement d'un vrai objet `File` vers `/api/upload` dans `submissions/<créneau>`, enregistrement du devoir et de sa pièce jointe dans la séance, connexion d'un compte élève, ouverture du devoir et lecture effective du contenu du fichier via son URL protégée.
- Cela valide le flux de dépôt enseignant → sauvegarde serveur → projection élève → accès au fichier. Le test vérifie aussi l'absence d'erreurs JavaScript sur les pages utilisées.
- Le run #729 passe sur Linux et Firefox réel ; validation macOS encore en cours au dernier relevé.
- DEV-01 passe à **Supposé résolu**. L'utilisateur doit encore confirmer sur son installation avant le statut « Corrigé ».
