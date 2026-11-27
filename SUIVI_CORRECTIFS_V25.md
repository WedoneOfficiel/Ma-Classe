# Registre de suivi — correctifs V25

Ce fichier est le journal de référence des problèmes remontés, des vérifications, des modifications et de leurs résultats. Il doit être mis à jour à chaque intervention, y compris lorsqu'un correctif échoue ou qu'un diagnostic invalide une hypothèse. Ne pas rouvrir un problème déjà résolu sans élément nouveau.

> **État courant — 27/11/2026 :** V25.1.1 reste la dernière version stable publiée. La PR #20 prépare V25.2.0 ; la tête `559c866ea26206eeb27c0af2a97501e55be1102e` a passé le workflow [#2114 / run 45921450586](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45921450586), **3/3 jobs réussis** : Linux, installateur macOS Apple Silicon et `launchd` réel, Firefox réel. La matrice intermodules comporte 860 invariants et l'arbre 112 fichiers de tests (68 JavaScript, 44 Python). Le paquet vérifie les dépendances runtime, tous les lanceurs racine, la clé publique Ed25519 et l'absence de données locales, bases et clés privées. Le candidat ajoute un mode TLS public DNS facultatif (FQDN + ACME DNS-01 externe + DNS local distribué par DHCP) permettant d'éviter l'import individuel de l'AC privée ; ce mode reste à configurer et à tester sur le réseau cible. La recette de l'installation physique, des vrais comptes, des sauvegardes/restaurations et des appareils clients reste distincte et nécessaire.

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


#### 15/11/2026 — EDT-01 : parité visuelle vérifiée dans Firefox réel

- Les deux écrans d'EDT s'appuient sur les mêmes fonctions de rendu semaine/jour/mois et les mêmes cartes de cours ; le mode élève désactive uniquement les commandes de modification et de glisser-déposer.
- Le test Firefox compare désormais les deux vues avec un vrai compte professeur et un vrai compte élève : présence et nombre des composants, mode d'affichage, nombre de colonnes, espacements, rayons et marges internes des panneaux, grilles, colonnes, en-têtes et cartes. Il vérifie également que l'élève ne voit aucune commande d'édition.
- Le test Firefox passe dans le run #733 ; les tests Linux passent aussi. Validation macOS encore en cours au dernier relevé.
- EDT-01 passe à **Supposé résolu**. La confirmation de l'utilisateur dans son installation reste nécessaire avant « Corrigé ».

#### Bilan de la campagne V25 au 15/11/2026

- 16 anomalies recensées.
- 16 **Supposées résolues** sur la base des correctifs et tests automatisés/navigateur ; 0 **Corrigé** sans confirmation de l'utilisateur ; 0 encore en cours de résolution.
- Les validations de recette sur l'installation réelle de l'utilisateur restent à faire pour confirmer les 16 anomalies. La PR reste en brouillon, sans merge ni déploiement.


## Campagne du 16 novembre 2026 — audit complet AMEL-01, mises à jour et sécurité

**Branche :** `feature/amel-01-update-manager` — PR #10, toujours en brouillon.  
**Portée :** nouveau gestionnaire de mises à jour, 16 anomalies applicatives du registre, contrôles de sécurité et conflits de logique.

### Défauts supplémentaires détectés et correctifs poussés

1. **AMEL-U1 — sauvegarde prise avant arrêt confirmé.** Risque de restaurer une copie plus ancienne que la dernière écriture du serveur. Les scripts Linux/macOS prennent désormais la sauvegarde après arrêt confirmé. Le test d'intégration Linux remplace `cp` par un garde-fou qui échoue si le service n'a pas encore été arrêté ; le test macOS vérifie l'ordre des opérations.
2. **AMEL-U2 — annulation launchd non vérifiée.** Le code pouvait supprimer le plist et annoncer l'annulation sans avoir confirmé le déchargement du job. Le contrôle `launchctl print` encadre maintenant le `bootout`, puis un second contrôle confirme l'arrêt avant suppression du plist.
3. **AMEL-U3 — analyse incorrecte de `launchctl list`.** Un en-tête de colonnes pouvait être pris pour un PID, ou un job chargé mais inactif confondu avec un processus en cours. Le parseur ne reconnaît plus que les PID numériques. Tests ajoutés pour un job inactif et actif.
4. **AMEL-S1 — cible de version Linux insuffisamment bornée.** Le lanceur Linux vérifie maintenant le chemin canonique du lien `data/program/current` et refuse toute cible hors de la racine ou du dossier `versions`.
5. **AMEL-S2 — redirections GitHub.** La validation de l'hôte est désormais faite avant de suivre chaque redirection, et pas seulement après le téléchargement. Tests ajoutés pour les destinations locales, externes, avec identifiants ou ports non autorisés.
6. **AMEL-U4 — versions SemVer à zéros initiaux.** Ces valeurs pouvaient créer un écart entre le dossier normalisé lors de la préparation et le chemin calculé lors de l'installation. Le moteur et le workflow de publication les refusent désormais.
7. **AMEL-U5 — concurrence d'installation.** Les scripts Linux/macOS prennent un verrou exclusif `fcntl.flock` afin d'empêcher deux bascules simultanées.

### Tests supplémentaires des bugs applicatifs

- Le test Firefox réel couvre maintenant la couleur personnalisée d'une matière dans les espaces professeur et élève.
- Il vérifie l'enregistrement d'un créneau sans rechargement ni perte de position au moment de la sauvegarde.
- Il ouvre le module Paramètres élève et contrôle le profil, la sécurité et les trois choix de thème.
- Il ouvre le module Séances & Leçons et vérifie la barre d'en-tête.
- Le test bulletin vérifie explicitement que 8/10 devient 16/20, que la moyenne normalisée attendue est calculée et qu'une note supérieure au barème est écartée.
- Un test serveur vérifie qu'un enseignant ayant assuré une matière pendant une période passée peut modifier l'appréciation correspondante, sans pouvoir modifier la matière d'un autre enseignant.

### Résultats CI observés et corrections des tests

- Le run #43842298396 a exécuté les tests Python avec succès ; le test Firefox a d'abord échoué parce que la mesure de défilement était prise avant l'ouverture de la fenêtre modale (le test mesurait le déplacement causé par l'ouverture, pas par l'enregistrement).
- Le run #43842852531 a révélé deux défauts dans les tests ajoutés : la regex SemVer n'avait pas été modifiée dans le fichier source malgré le test, et le scénario Firefox restait sur la page Séances & Leçons lorsqu'il attendait la boîte de réception. Le code SemVer a été corrigé et la mesure de défilement a été déplacée juste avant la validation du formulaire ; le test revient maintenant explicitement à `studentMessages` après ses contrôles Paramètres/Leçons.
- Les tests bulletin, droits d'affectation historique, intégration d'installation Linux et tests d'archives étaient verts dans ce run. Les deux échecs identifiés sont donc consignés comme défauts de couverture/fixtures, pas comme bugs applicatifs démontrés.
- Les commits de correction ont relancé la CI ; la validation finale de la tête courante doit encore être vérifiée. Ne pas utiliser les résultats d'un run sur un commit antérieur comme preuve pour la tête courante.
- Le job macOS est resté en file d'attente lors des derniers contrôles. Aucun essai sur le Mac réel de l'utilisateur et aucune recette Fedora n'ont été effectués.

### Statut prudent au 16/11/2026

- Les 16 anomalies historiques restent « Supposé résolu », jamais « Corrigé » sans retour explicite de l'utilisateur.
- Les 7 anomalies complémentaires AMEL-U1 à AMEL-U5 et AMEL-S1 à AMEL-S2 sont inscrites dans `REGISTRE_BUGS_V25.md` avec statut « En cours de validation CI ».
- La PR #10 reste ouverte et en brouillon ; aucune fusion, aucun déploiement et aucune modification de l'installation locale.


### Compléments de l'audit macOS et du cycle de versions — 16/11/2026

8. **AMEL-U6 — environnement Python d'une release lié à l'ancienne version.** Le serveur préparait le venv avec `sys.executable`, qui peut désigner le Python de la version active. Le nouveau venv est maintenant créé avec `sys._base_executable` (fallback `sys.executable`) afin de ne pas dépendre d'une version susceptible d'être supprimée. Un test vérifie l'interpréteur passé à `venv`.
9. **AMEL-U7 — racine macOS perdue après une première mise à jour.** Un agent launchd pouvait lancer le script depuis le dossier de version actif, puis le script interpréter ce dossier comme la racine d'installation et chercher `data` au mauvais endroit. Le lanceur transmet maintenant `MACLASSE_ROOT` et `MACLASSE_DATA_DIR` ; les deux plists launchd les transportent, et le script dispose d'un fallback depuis `data/program/versions/Vx`. Tests des environnements immédiat et programmé ajoutés.
10. **AMEL-U8 — message d'interface macOS obsolète.** Malgré l'implémentation launchd, la carte Mises à jour affichait encore « Le support macOS sera ajouté ensuite ». Le message fournit maintenant le prérequis TLS et la commande d'installation du service macOS. Test UI ajouté.

### Limites fonctionnelles qui restent ouvertes

- Le dépôt ne contient actuellement **aucune GitHub Release stable publiée**. Le téléchargement d'une vraie archive de release, sa signature SHA-256 publiée et le parcours complet depuis un tag ne peuvent donc pas encore être validés sur un artefact réel. Les tests actuels simulent ces réponses et archives.
- Le job macOS de la CI reste nécessaire pour valider les scripts sur runner Apple. Même vert, il ne remplacera pas la recette sur le Mac réel, notamment après une première mise à jour puis une seconde (pour vérifier que les scripts continuent de trouver la racine et les données).
- La recette Fedora sur le PC cible reste à faire. Aucun changement local n'a été appliqué.



11. **AMEL-U9 — annulation systemd non confirmée.** Le timer Linux pouvait être supprimé du disque et considéré annulé même si `systemctl disable --now` n'avait pas réussi. L'annulation contrôle maintenant séparément `is-active` et `is-enabled`, et ne supprime le fichier qu'après confirmation de l'état inactif/désactivé. Un test simule un timer toujours actif et vérifie que le fichier est conservé et que l'annulation échoue.


12. **AMEL-U10 — restauration de base non atomique.** Le rollback copiait directement le JSON de sauvegarde sur le fichier actif ; une interruption pendant cette copie pouvait laisser une base partielle. Les scripts Linux/macOS copient maintenant vers un fichier temporaire sur le même volume, font un `fsync`, remplacent atomiquement avec `os.replace`, puis synchronisent le dossier. Le scénario d'intégration Linux vérifie déjà le contenu après rollback ; le test macOS vérifie le mécanisme atomique.


13. **AMEL-U11 — course entre installation immédiate et maintenance programmée.** Un démarrage immédiat pouvait décharger un job launchd dont le processus d'installation avait déjà démarré ; le chemin systemd ne refusait pas non plus explicitement un double démarrage. Le lancement immédiat et l'annulation du timer vérifient maintenant l'état du processus d'installation avant toute action ; un timer ne peut pas décharger un updater déjà actif. Tests ajoutés sur les deux plateformes.


14. **AMEL-U12 — double démarrage macOS après installation du service.** Les lanceurs manuels local et réseau ne vérifiaient que le port loopback ; le service launchd réseau pouvait donc être actif sur l'adresse LAN sans être détecté, et un second processus aurait pu écrire dans la même base. Les deux lanceurs vérifient maintenant le job launchd avant toute création de serveur, ouvrent l'URL HTTPS du certificat existant et refusent une seconde instance. Test statique et vérification de syntaxe shell ajoutés.


15. **AMEL-U13 — unités systemd/launchd restant attachées au lanceur initial.** Après une mise à jour, le service pouvait continuer d'utiliser le lanceur racine initial plutôt que le lanceur versionné ; le passage vers `current` exigeait en plus de transmettre la racine stable, faute de quoi le runner prenait le dossier de version pour la racine des données. Les unités pointent maintenant vers `data/program/current/Lancer-MaClasse-Service-*.sh` et transmettent `MACLASSE_ROOT` / `MACLASSE_DATA_DIR`. Les lanceurs résolvent la racine stable et utilisent le code de la version active. Tests de syntaxe, chemin du plist et variables systemd/launchd ajoutés.


16. **AMEL-S3 — XSS stockée via identifiants et motifs de créneaux.** L'audit a trouvé des identifiants de planning injectés directement dans des gestionnaires HTML inline et un motif injecté dans une propriété CSS. Le correctif sérialise les identifiants en littéraux JavaScript puis échappe l'attribut HTML, limite les motifs à `none`, `hatch`, `cross`, et refuse côté serveur les nouveaux identifiants non sûrs dans les enregistrements enseignant/élève et les messages/drafts de messagerie. Tests ajoutés : exécution du gestionnaire généré avec un identifiant malveillant, rejet des identifiants côté serveur, et rejet des motifs CSS arbitraires.


17. **AMEL-S4 — XSS stockée dans les contenus riches.** Le contenu des séances, les consignes de devoir et les retours de correction étaient réinjectés en HTML brut. Un professeur pouvait accidentellement ou malicieusement publier un script, un attribut événementiel ou un lien `javascript:) exécuté dans l'espace élève. Un assainisseur HTML à liste blanche est maintenant appliqué côté serveur à la lecture et à chaque sauvegarde ; l'interface applique également un assainissement avant d'afficher ou d'éditer ces champs. Les balises de script/style/iframe/SVG sont supprimées, les attributs événementiels retirés, les liens limités à HTTP(S) et les styles aux couleurs/tailles de texte autorisées. Tests serveur et navigateur ajoutés.


### Audit approfondi du 16/11/2026 — régressions CI et correctifs ciblés

18. **AMEL-S7 — syntaxe invalide dans `cloudNewFolder()`.** Le run CI #1415 a montré que la nouvelle interpolation de `parentPath` était imbriquée dans une interpolation de template string. `node --check _all.js` échouait et l'application ne se chargeait pas ; le test Firefox EDT échouait en cascade parce que le formulaire de connexion n'apparaissait pas. Le calcul de `parentPath` a été déplacé avant le template et sa valeur est injectée par `jsArg(parentPath)` (`f12bdfd`). Le run suivant a validé `node --check` et le test Firefox réel. Statut : correctif technique appliqué, CI complète à reconfirmer sur la tête courante.

19. **AMEL-U18 — génération invalide du timer systemd.** L'audit du code a révélé que `_schedule_update_timer()` écrivait des séquences littérales `\\n` au lieu de vrais retours à la ligne. Le fichier de timer ne contenait donc pas de sections systemd séparées ; le test existant vérifiait seulement la présence de mots-clés et ne détectait pas le défaut. Le code produit maintenant de vraies lignes et le test vérifie explicitement la première ligne, les sections et l'absence de séquences littérales. Correctifs poussés dans `d4cb86e`, `9474b2f` et `a9abe43`. Statut : CI à reconfirmer.

20. **Fixture de test des compétences obsolète (hors bug applicatif).** Le test `test_competencies_v20.js` évaluait désormais `gradeTable()` sans fournir le helper global `jsArg` ajouté au rendu sécurisé. La CI échouait avec `ReferenceError: jsArg is not defined`, alors que le code applicatif disposait du helper. Le contexte du test est complété avec le helper déterministe ; correction dans `36bb248`. Statut : CI à reconfirmer.

### État de la CI au dernier contrôle
- Run #1415 : échec sur la syntaxe de `_all.js` ; le test Firefox échouait en cascade ; le job macOS avait aussi été arrêté à la même vérification syntaxique.
- Run #1417 : `node --check` Linux/macOS réussi, installateur macOS Apple Silicon réussi, régression Firefox réelle réussie ; les tests JavaScript ont ensuite échoué sur la fixture obsolète `test_competencies_v20.js`.
- Les correctifs de sérialisation du timer systemd et de la fixture JS ont été poussés après ce run. Il faut attendre une nouvelle CI complète sur le dernier commit avant de conclure.
- Aucun artefact de release stable n'est publié à ce jour : l'installation depuis une vraie release, la vérification SHA-256 contre une release publiée et les mises à jour successives restent impossibles à valider de bout en bout.
- Aucun test n'a été exécuté sur le Mac de l'utilisateur ni sur le PC Fedora cible ; aucune installation locale n'a été modifiée.


21. **Fixture de test des compétences — format des arguments.** Après ajout du helper `jsArg`, le test évaluait bien la fonction mais attendait encore des arguments sérialisés avec apostrophes simples. Le sérialiseur produit volontairement des littéraux JSON entre guillemets doubles ; l'assertion était donc obsolète. Elle attend maintenant `setCompetencyRating("e1","s1"` (`0f88e86`). Ce n'est pas un défaut fonctionnel de l'application, mais un défaut du test. La nouvelle CI doit confirmer la suite complète.


22. **Fixture de test de messagerie V21.04 — helper manquant.** Après correction de la fixture compétences, la suite JS a atteint `test_v2104_mail_model.js`, qui évaluait le rendu réel `messages()` sans fournir `jsArg`. Le test échouait donc par `ReferenceError`, sans démontrer de défaut de la messagerie. Le helper déterministe est ajouté au sandbox (`3d88655`). La CI suivante doit vérifier si d'autres anciens sandboxes nécessitent la même mise à jour.


23. **Assertion UI de messagerie V21.11 obsolète.** Le test attendait encore l'interpolation brute `${m.id}` dans le handler des favoris, alors que le code actuel utilise correctement `jsArg(m.id)`, `jsArg(role)` et `jsArg(sid)` pour éviter l'injection de code. Le test est adapté à cette sérialisation sûre (`f0e22dc`). La CI suivante doit confirmer le reste de la suite JavaScript.


24. **Assertions UI du module Résultats élève V21.17 obsolètes.** Le test attendait les anciennes interpolations directes de chaînes dans les handlers du détail d'évaluation et du sélecteur de période. Le code actuel utilise `jsArg()` pour sérialiser les identifiants ; les deux assertions sont mises à jour pour vérifier cette protection (`46fcedd`). La CI suivante doit poursuivre la suite complète.


25. **Assertion de navigation EDT obsolète.** Le test attendait encore l'interpolation directe `${iso(x)}` dans les handlers du calendrier mensuel et du mini-calendrier. Le code utilise maintenant `jsArg(iso(x))` pour sérialiser les dates dans les attributs HTML. Les assertions contrôlent cette version sûre (`1e53fc3`). Les tests de logique du calendrier eux-mêmes avaient passé jusqu'à cette assertion. CI à reconfirmer.


26. **Sandbox du test de navigation EDT — helper manquant.** Après adaptation des assertions aux handlers de dates sérialisés, le test a exécuté le vrai rendu du calendrier mensuel mais son contexte VM ne fournissait pas `jsArg`. Le helper de sérialisation est ajouté au sandbox (`8c647a3`). Les assertions de logique de navigation et de récurrence avaient été franchies avant le rendu mensuel. CI à reconfirmer.


27. **Renforcement de la recette macOS launchd.** Les tests précédents validaient la génération du plist et simulaient `launchctl` ; ils ne vérifiaient pas que le gestionnaire launchd du runner macOS acceptait réellement le bootstrap. Un test d'intégration isolé crée un HOME temporaire, installe un agent avec un lanceur factice, vérifie son démarrage effectif puis le décharge et nettoie le processus (`e667b59`). Il est limité au runner macOS et ne touche pas à une installation réelle de l'utilisateur. Il doit encore passer en CI.


28. **Sandbox du test EDT élève — helper manquant.** La suite a atteint le rendu de la page « Séances & leçons » et le test VM n'avait pas le helper `jsArg` désormais utilisé pour les dates dans les attributs. Ajout du sérialiseur au contexte du test (`60b7580`). Les vérifications précédentes du rendu élève et des fonctions de navigation avaient passé avant cette exception. CI à reconfirmer.


29. **Assertion du test systemd — échappement incorrect.** La première version du test renforcé cherchait un vrai caractère de nouvelle ligne (`\n` interprété par Python) au lieu de la séquence littérale barre oblique inversée + n. Le code de production avait bien produit des retours à la ligne ; c'est l'assertion qui échouait. L'assertion teste maintenant la séquence littérale avec le bon échappement (`40e0f2a`). Les 18 tests du gestionnaire de mises à jour et les 6 tests d'application/rollback avaient déjà passé avant cette assertion.


30. **Bornage temporel du test launchd réel.** Les commandes de lecture `launchctl print` du nouveau test d'intégration sont maintenant limitées à 10 secondes, comme l'installation (30 s) et le déchargement (10 s). Cela évite qu'un runner macOS ne bloque indéfiniment si le domaine GUI ou launchd ne répond pas (`be66a47`). À valider sur le prochain run macOS.


31. **Test launchd réel — second `launchctl print` non borné.** L'audit de la durée du job a montré qu'une des deux inspections du domaine GUI n'avait pas reçu le timeout (le remplacement initial n'avait modifié que la première occurrence). Les deux appels sont maintenant limités à 10 secondes (`49568cd`). Cela explique le risque de blocage du test sur macOS ; le prochain run doit confirmer le démarrage/déchargement réel.


32. **CI Python — durée individuelle bornée.** Le job macOS reste sur l'étape de tests Python alors que Linux a terminé. Pour identifier précisément un test qui bloquerait le runner et éviter une attente de 20 minutes sans diagnostic, chaque fichier Python est maintenant exécuté dans un sous-processus limité à 90 secondes sur Linux et macOS (`a5011f9`). Le nom du fichier est déjà affiché dans le groupe de logs ; un dépassement sera ainsi attribuable. CI à reconfirmer.


33. **Risque de chaîne d'approvisionnement — signature de release absente.** Le SHA-256 de l'archive est vérifié contre le manifeste de la même release GitHub : cela protège contre la corruption et les incohérences, mais ne constitue pas une signature d'éditeur indépendante. Une compromission du compte ou du workflow de publication pourrait remplacer à la fois manifeste et archive. Le registre contient maintenant `AUDIT-S2` : ajouter une signature détachée ou une attestation vérifiable avec clé publique épinglée. Ce point exige une décision/configuration de clé de signature dans GitHub Actions ; il est bloquant avant toute release stable de production.


34. **Campagne CI Linux — run #1452.** Résultat vert sur la tête `957f6e1` : installateur Linux réel, `node --check`, syntaxe des lanceurs, 45 fichiers de tests JavaScript, compilation Python et 30 fichiers de tests Python. Les 188 cas `unittest` exécutés dans les suites Python sont tous verts, notamment les 18 tests `update_manager`, les 6 tests d'application/rollback et le test de timer systemd. La régression EDT Firefox réel est encore en cours sur ce run ; le job macOS est en attente.


34. **Test XSS EDT — faux événement de glisser-déposer incomplet.** Le test appelait le gestionnaire inline ondragstart dans Node VM sans lui fournir un objet navigateur event/DataTransfer complet. La CI échouait donc dans le harnais de test, pas dans le rendu ou la sérialisation des identifiants. Le test fournit maintenant un faux DataTransfer réaliste et vérifie la valeur transmise (0c9e770, puis ajustement de l'assertion dans 431e485). Le run #1460 a confirmé que la suite JavaScript Linux et macOS passait après cette correction.

35. **AUDIT-U2 — mise à jour macOS historique non sûre en mode supervisé.** Mettre-A-Jour-MaClasse.command pouvait encore effectuer un git merge directement dans le code actif. Ajout d'un refus explicite si data/update-manager.enabled existe et d'un contrôle pgrep qui impose l'arrêt du serveur pour le parcours initial non supervisé. Deux tests fonctionnels couvrent le refus en mode supervisé et le refus si le serveur est actif (b07dd00, 7efc952). La migration initiale depuis V25.0.19 devra être répétée sur une copie de données avant de donner une procédure utilisateur.

36. **AUDIT-U3 — bannière de maintenance masquée pendant l'installation.** L'API ne publiait que l'état scheduled ; au passage à installing, elle renvoyait une absence de maintenance. Ajout de _public_update_maintenance() avec projection minimale des données, état in_progress, bannière « Maintenance en cours » et tests Python/UI (507f13d, ab8291c, 8dd978e, c432453). CI à confirmer sur la tête finale.

37. **CI #1459 — défaut de fixture de test, pas défaut d'application.** Le test test_v25_schedule_xss.js a d'abord échoué car l'objet de glisser-déposer n'était pas fourni au contexte VM, puis son assertion observait le mauvais sandbox. Les deux défauts du test ont été corrigés. Le run #1460 a ensuite passé tous les tests JavaScript et Python Linux ; sur macOS, les tests JavaScript et l'intégration launchd réelle ont également passé, tandis que les tests Python continuaient au dernier contrôle.



38. **AUDIT-S4 — publication stable sans dépendance aux tests.** Le workflow publish-release.yml validait le tag et VERSION.txt, mais pouvait publier une release même si les tests de l'application échouaient. Le workflow tests.yml expose maintenant workflow_call et la publication dépend du job réutilisable validate, qui exécute la matrice Linux, macOS et Firefox. Test statique du lien de dépendance ajouté dans test_v25_update_scripts.py (commits 26e25cb, e862dbe, 7c3113d). À confirmer sur un vrai déclenchement par tag avant toute release.



39. **AUDIT-U4 — adresse DHCP macOS modifiée pendant l'exécution.** Le lanceur renouvelle le certificat lorsque le LaunchAgent démarre, mais le serveur reste lié à son adresse IP actuelle pendant toute sa vie. Si le routeur attribue une nouvelle IP sans redémarrage du service, l'ancienne écoute et le certificat ne correspondent plus à l'adresse utilisée. Pas de correctif automatique engagé : une surveillance réseau doit être conçue sans entrer en conflit avec les redémarrages de mise à jour. Recommandation temporaire : réserver l'adresse DHCP du Mac dans le routeur et redémarrer le service après tout changement.



40. **CI complète #1477 — tête 7990ae5.** Résultat vert sur les trois jobs : Linux (installateur réel, syntaxe, tous les tests JavaScript et Python), Firefox réel (parcours EDT avec comptes direction/professeur/élève, pièces jointes de devoir, messagerie élève, paramètres élève, synchronisation et structure EDT enseignant/élève) et macOS Apple Silicon (installateur, syntaxe, tous les tests JavaScript, bootstrap/déchargement launchd réel et tous les tests Python). Les 11 tests de tests/test_macos_supervisor.py ont été exécutés deux fois et réussis ; les 7 tests de tests/test_v25_update_scripts.py passent également (un test Linux-only est ignoré sur macOS). Cette réussite CI ne remplace pas la recette sur le Mac et le PC Fedora de l'utilisateur, ni le test d'une vraie GitHub Release.



41. **AMEL-U19 — échec du test macOS de mise à jour HTTPS de bout en bout.** Le run #1486 a passé l'installation Apple Silicon, la syntaxe et les tests JavaScript, mais le scénario réel launchd → serveur HTTPS → mise à jour → health-check n'a pas obtenu de réponse HTTP sur la version initiale. Le test launchd isolé passait. Le run #1489 a reproduit l'échec ; le test a été instrumenté pour journaliser le lanceur, l'état des processus et les sockets TCP, et son client HTTPS local utilise maintenant un opener sans proxy. Les jobs Linux et Firefox du run #1490 sont verts ; le job macOS a été annulé par les commits suivants. Un nouveau run #1492 est en attente. Ne pas déclarer la chaîne macOS validée avant réussite du test de bout en bout et de tous les tests Python macOS.

42. **MIG-01 — migration initiale V25.0.19 non validée.** L'installation actuelle ne possède pas encore le gestionnaire supervisé. L'architecture cible utilise data/program/current, des versions isolées et un dossier data persistant. La préparation vérifie schemaVersion contre min_data_schema=25011 ; si le champ est absent ou trop ancien, elle bloque la mise à jour. Aucun script de migration complet n'a été testé sur une copie représentative. Le registre REGISTRE_BUGS_V25.md marque ce point bloquant avant toute procédure utilisateur : sauvegarde externe, vérification du schéma, préservation base/uploads/certificats, migration et rollback sur copie.


## Campagne du 25 novembre 2026 — stabilisation produit et documentation

**Branche :** `feat/v25.0.25-stabilisation-reseau-migrations`  
**PR :** #13 (ouverte, non fusionnée)  
**Tête CI vérifiée :** `94b86d9b8b85f15a9b78a0eeccd0905d5a82ad91` — workflow #1727, trois jobs réussis.

### Correctifs applicatifs engagés

1. **MAIL-02 — messagerie élève.** Projection serveur fondée sur le calcul central des enseignants accessibles (titulaires, co-enseignants, séances et affectations actives). L'interface ne filtre plus une seconde fois les destinataires. Tests de projection ajoutés.
2. **BUL-03 — consultation PDF.** Contrôle serveur strict du statut officiel et de la propriété du bulletin. Les anciens bulletins validés et publiés restent téléchargeables même sans `publishedAt`. Tests d'autorisation et de compatibilité legacy ajoutés.
3. **EDT-06 — couleurs matière.** Fusion contrôlée de `settings.subjectColors` côté serveur, limitée aux matières effectivement enseignées par le professeur. Test de refus des couleurs hors périmètre ajouté.
4. **EDT-07 — thème sombre.** Remplacement explicite du dégradé blanc de la grille journalière par une surface sombre. Test visuel de non-régression ajouté.

### Organisation documentaire

- Création de `docs/HISTORIQUE_VERSIONS.md` : changelog V25 et notes V21.12 à V21.22 / correctif V21.11.3 repris intégralement.
- Création des archives historiques d'audits, d'états, de guides antérieurs et de l'ancien README.
- Nouveau guide d'installation V25, index documentaire et README racine recentré sur l'état courant.
- Mise à jour des documents réseau, gestionnaire de mises à jour, audit produit et registres de bugs.

### Résultat de validation

La CI #1727 a passé les jobs Linux, macOS Apple Silicon et Firefox réel après correction d'une fixture de test qui partageait par erreur une référence Python au lieu de simuler la copie JSON reçue par le navigateur. Les échecs précédents du test n'étaient pas un défaut applicatif ; le scénario a été corrigé pour reproduire le vrai passage HTTP.

### Recettes encore nécessaires

- Confirmer MAIL-02 avec un vrai compte élève et un professeur remplaçant.
- Ouvrir un bulletin officiel depuis le compte élève et un poste client différent du serveur.
- Vérifier les couleurs de matières et le thème sombre sur le Mac et le PC Fedora, avec des emplois du temps fournis.
- Tester la migration sur une copie de la base réelle, sans jamais prendre la base utilisateur comme fixture.
- Tester l'accès HTTPS depuis plusieurs appareils, le pare-feu et l'approbation de l'autorité locale.
- Décider et implémenter une signature/attestation de release avant de présenter l'update manager comme une chaîne de confiance complète.


## Complément d'audit UI — découverte des remplacements et cohérence des espaces (25/11/2026)

- **AFFECT-02 :** ajout d'un accès central « Remplacements & co-enseignement » dans la barre d'actions de l'EDT. Il liste les seuls créneaux que l'utilisateur peut gérer, permet de filtrer par classe et de rechercher une matière, un jour ou un horaire, puis ouvre l'éditeur existant. Les restrictions de rôle et la règle de suppression par créateur sont conservées.
- **Administration :** correction du texte de confidentialité qui affirmait à tort que la messagerie et le Cloud élève étaient désactivés ; le message décrit maintenant le filtrage serveur des données, messages, pièces jointes et ressources.
- **BUL-04 :** revue de `createAllBulletins` et du test `test_v25_bulletin_persistence.js` : génération idempotente, sauvegarde attendue avant confirmation, rechargement serveur, rollback local si la sauvegarde échoue.
- **VIE-01 :** vérification du code actif `studentLife()` : la rubrique ne présente que les absences, avec états justifiées/non justifiées.
- **UI-ADM-01 / UI-SET-01 / UI-PROFIL-01 / VER-01 :** règles CSS et affichage version partagés localisés dans le code actif ; tests de présence ajoutés dans `test_v25_visual_consistency.py`.

Ces points sont désormais distingués entre implémentation présente dans la branche et recette réelle à faire. La CI #1727 valide la tête antérieure au présent complément ; une nouvelle CI est nécessaire sur le dernier commit.


### Résultat de la première CI du répertoire de remplacements — workflow #1742

Le premier test complet après l'ajout du bouton « Remplacements & co-enseignement » a révélé une dépendance inutile au global `authUser` pendant le rendu de `schedule()`. Le test de navigation EDT construit volontairement la page dans un contexte isolé sans session ; le bouton ne doit donc pas lire ce global à la construction. Le contrôle d'accès est maintenant concentré dans `openScheduleAssignmentDirectory()`, qui ne liste que les créneaux autorisés via `canManageScheduleAssignments()`. Le bouton est seulement un point d'entrée ; il ne donne aucun droit supplémentaire.

**État :** correction committée dans `d66a78f`. Workflow #1742 a aussi passé Firefox réel ; les jobs Linux/macOS ont échoué sur cette erreur de test de rendu. Une nouvelle CI complète est attendue sur le commit corrigé.


## Validation finale du candidat V25.0.25 — 25/11/2026

**Commit testé :** `7c5f80b47e8bcb0cb4b86de59e77da5216514728`  
**Workflow :** [#1754](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45699459140)  
**Résultat :** succès sur les trois jobs Linux, macOS Apple Silicon et Firefox réel.

- Le test de navigation EDT qui échouait dans le workflow #1742 est maintenant vert : le bouton Remplacements ne lit plus `authUser` pendant la construction de la page ; le filtrage demeure appliqué dans `openScheduleAssignmentDirectory()`.
- Le test de l'interface d'affectations est vert : accès central, filtrage par classe/recherche, rôle Direction/professeur et droits de retrait.
- Les 24 assertions de cohérence visuelle sont vertes, en plus des tests de modèle, autorisations, persistance, serveur et mises à jour.
- Le runner macOS a validé l'installateur Apple Silicon, les tests JavaScript, le superviseur launchd réel et tous les tests Python.
- La régression EDT Firefox réel est verte et a produit un artefact de 74 captures.

**À ne pas confondre avec une recette de livraison :** aucune publication ni fusion de la PR #13 n'a été effectuée. La base réelle, le réseau Wi-Fi physique et les comptes utilisateur restent à vérifier avant release.


## Vérification de la tête finale après clarification du filtre — workflow #1754

La tête `7c5f80b` est entièrement verte sur le workflow [#1754](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45699459140) : tests Linux, Firefox réel et macOS Apple Silicon. Le dernier ajustement a remplacé le filtre « Toutes mes classes » par « Toutes les classes accessibles », libellé valable aussi bien pour la Direction que pour un professeur ; l'assertion associée est incluse dans cette exécution.


## AUDIT-S2 — Signature Ed25519 du manifeste de mise à jour (25/11/2026)

- Ajout de `release_signing.py` : décodage strict, clé publique Ed25519 épinglée dans `release-signing-public-key.txt`, vérification de la signature détachée sur les octets exacts du manifeste.
- Le gestionnaire `update_manager.py` exige maintenant exactement un asset `maclasse-update.sig` et vérifie sa signature avant d'interpréter le manifeste, de vérifier le SHA-256 de l'archive ou de préparer une version. L'absence de signature ou de clé publique bloque la mise à jour.
- Ajout de `scripts/generate_release_signing_key.py` : génération locale d'une paire ; clé privée créée hors du dépôt et permissions POSIX 0600 ; seule la clé publique est destinée à Git.
- Ajout de `scripts/sign_release.py` : le workflow signe le manifeste avec le secret `MACLASSE_RELEASE_SIGNING_KEY_B64`, après comparaison de la clé privée dérivée avec la clé publique versionnée.
- Le workflow de publication installe la dépendance cryptographique, signe le manifeste et publie l'asset de signature. Il échoue fermé si le secret n'est pas configuré.
- Ajout de tests offline : signature valide, altération du manifeste, clé privée ne correspondant pas à la clé publique, signature absente/ambiguë/malformée et vérification côté client.

**Limite opérationnelle :** la paire réelle et le secret ne peuvent pas être provisionnés par un commit de code. Il faut exécuter la génération sur un poste de confiance, committer la clé publique seulement et créer le secret dans les paramètres GitHub du dépôt. Tant que ce provisionnement n'est pas réalisé, aucune nouvelle release ne doit être publiée et le vérificateur refuse les nouvelles mises à jour.


### CI #1758 — module Ed25519 absent du fixture launchd macOS

Le workflow #1758 a passé les tests Linux, les nouveaux tests de signature Ed25519 et Firefox réel. Le job macOS a échoué dans `test_launchd_starts_real_maclasse_server_over_local_https` parce que son installation temporaire copiait `server.py` et `update_manager.py`, mais pas le nouveau module importé `release_signing.py`. Le serveur de test quittait donc immédiatement avec `ModuleNotFoundError`; le code de production était bien présent dans l'archive Git.

**Correction :** le fixture copie maintenant aussi `release_signing.py` et vérifie sa présence avant de démarrer launchd. Ce diagnostic ne doit pas être confondu avec une erreur du superviseur ni avec une panne du service macOS réel. Nouvelle CI complète nécessaire sur le commit corrigé.


## Validation complète de la signature Ed25519 et du service macOS — 25/11/2026

**Commit testé :** `b3f44aa135b61a2334628f1c75cc4043371c49e8`  
**Workflow :** [#1759](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45704572819)  
**Résultat :** succès Linux, Firefox réel et macOS Apple Silicon.

- Tests Linux : succès, dont tous les scénarios Ed25519 et les refus fail-closed.
- Firefox réel : succès.
- macOS : installateur Apple Silicon, syntaxe, tests JavaScript, démarrage HTTPS réel sous launchd et suite Python : succès.
- Un premier run #1758 a échoué parce que le fixture launchd ne copiait pas `release_signing.py`. Le fixture a été corrigé pour reproduire le contenu complet de l'application ; aucun contrôle de sécurité n'a été supprimé.

La clé publique et le secret GitHub ne sont pas encore provisionnés. Les tests utilisent une paire éphémère créée dans un répertoire temporaire ; cela prouve le mécanisme de signature, pas l'identité de la future clé éditeur.


## Validation des outils de signature et synchronisation finale — 25/11/2026

**Commit testé :** `b06f8ef1baa46f230d16220d2608b63678161a80`  
**Workflow :** [#1763](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45706617681)  
**Résultat :** 3 jobs sur 3 réussis : Linux, macOS Apple Silicon et Firefox réel.

Les nouveaux scénarios vérifient en plus :
- génération effective d'une paire Ed25519 dans un répertoire temporaire ;
- conservation de la clé privée hors du dépôt et permissions POSIX `0600` ;
- signature effective du manifeste par le script CLI puis vérification de cette signature ;
- refus de signer lorsque le secret GitHub Actions est absent, sans création d'asset ;
- compilation des trois scripts cryptographiques.

Le commit courant a également corrigé la règle `.gitignore` pour le véritable nom du fichier de clé privée. La clé éditeur de production reste non provisionnée ; les tests utilisent des clés éphémères.


## Campagne du 25 novembre 2026 — Suivi de classe, Cloud et validation finale

- Création de la vue transversale Suivi de classe, accessible à la Direction et aux enseignants selon leurs affectations ; les professeurs principaux conservent la vue complète de leur classe.
- Ajout des indicateurs factuels d'assiduité sur 30 jours, travaux non rendus, évaluations publiées, échéances et accès aux fiches élèves ; aucun classement ni score automatique.
- Correction du chargement statique de `class_tracking.js` dans la liste blanche serveur et ajout d'un test dédié.
- Correction du changement d'espace Cloud pour que les espaces personnels/partagés ne soient plus bloqués par un contexte de classe conservé.
- Tests unitaires et Firefox réel couvrant permissions, groupes, publication, contexte Cloud et refus d'accès élève.
- CI #1793 : 3/3 jobs réussis sur Linux, macOS Apple Silicon (installateur et launchd réels) et Firefox réel.
- Restent hors CI : provisionnement de la clé Ed25519 de production, migration sur copie des données réelles et recette réseau multi-appareils.


## Clôture de la campagne V25.1.1 — 26 novembre 2026

### Parcours de mise à jour macOS
- Symptôme d'origine : depuis V25.0.23, le téléchargement et la préparation de V25.1.1 aboutissaient à l'état « prête », mais le gestionnaire indépendant ne démarrait pas.
- Premier défaut : le contrôle du certificat HTTPS lisait la sortie texte d'OpenSSL avec un format supposé ; macOS LibreSSL présentait la même information sous une forme différente. Le certificat conservé était valide et contenait bien l'adresse IP dans son SAN.
- Deuxième défaut : l'ancien déclencheur launchd de V25.0.23 ne parvenait pas à démarrer le gestionnaire indépendant. Une fois la version téléchargée et préparée, le lanceur direct de secours a exécuté le même moteur d'installation/rollback sans modifier lui-même la base.
- V25.1.1 corrige le parseur X.509, le démarrage du LaunchAgent, la journalisation des erreurs et le retour visuel de préparation.
- **Recette réelle :** l'utilisateur a confirmé que la mise à jour a finalement fonctionné sur son Mac après utilisation de la commande de secours.

### Traçabilité CI
- PR #19 fusionnée dans `main` : commit `b5cc07d6747605f2eac6ad11dffb3ce0bbb9ec43`.
- CI post-fusion #1844, run `45804151065` : jobs Linux, macOS Apple Silicon/launchd et Firefox réel réussis.
- Passe générale : 93 fichiers de tests (55 JavaScript, 38 Python), les tests propres à chaque plateforme étant exécutés sur le runner correspondant.
- Couverture ciblée : 15 tests du lanceur direct, 19 tests launchd, 33 tests du gestionnaire de versions, plus les suites applicatives et d'intégration.
- Workflow manuel de publication #4, run `45806118500` : les trois jobs de validation et le job de publication réussis.
- Assets effectivement publiés : `maclasse-update.zip`, `maclasse-update.json` et `maclasse-update.sig`.

### Résultat et limites
- Version publiée : `V25.1.1` ; tag `v25.1.1` pointant sur le commit validé.
- Aucun changement de schéma de base ni migration supplémentaire.
- Le premier passage lancé depuis V25.0.23 s'appuyait sur la vérification SHA-256 de l'ancien gestionnaire ; les mises à jour suivantes utilisent la vérification Ed25519 du gestionnaire V25.1.1.
- Les détails des branches, PR, commits et recommandations de nettoyage sont conservés dans [l'archive des branches et validations](docs/qualite/ARCHIVES_BRANCHES_ET_VALIDATIONS.md).


## Campagne de cohérence inter-modules V25.1.2 — 26 novembre 2026 (en cours)

**Branche :** fix/v25.1.2-cross-module-consistency  
**PR :** [#20 — cohérence des notes, moyennes et bulletins](https://github.com/WedoneOfficiel/Ma-Classe/pull/20)  
**Objectif de version :** V25.1.2, correctif non majeur sans migration de schéma.

### Défauts confirmés pendant l'audit
- La moyenne générale du bulletin utilisait un ancien parcours de calcul et n'appliquait pas intégralement les règles du moteur partagé (publication, période, classe et groupe). Elle pouvait diverger des moyennes par matière et du relevé élève.
- Plusieurs vues affichaient les notes brutes comme /20, y compris quand le barème d'origine était /10, /25 ou autre.
- Certains appels du filtre de publication transmettaient une date seule : un timestamp prévu plus tard le même jour était traité comme déjà dû côté navigateur.
- Le calcul des bulletins PDF comparait publishAt à une date par ordre lexical ; les publications déjà arrivées le jour courant pouvaient être omises.
- Le moteur JavaScript pouvait laisser passer une note négative dans une moyenne, tandis que le calcul serveur PDF la rejetait. La cause était un repli conditionnel incomplet dans evaluationModelNumericGrade.

### Correctifs codés sur la branche
- v101StudentAverage délègue désormais à evaluationModelVisible et applique le périmètre de l'élève, la période et la publication explicite.
- Les vues concernées utilisent evaluationGradeLabel, qui conserve le barème original et distingue une note absente ou une évaluation qualitative.
- Les calculs de moyenne générale, de moyenne par matière et de statistiques de publication passent l'horodatage ISO complet.
- evaluationModelNumericGrade rejette toute valeur inférieure à zéro ou supérieure au maximum.
- evaluationModelPublished exige désormais published=true ; un champ absent ne peut plus être compté comme publié dans les statistiques enseignant quand le serveur le masque à l'élève.
- _bulletin_pdf_data applique le helper serveur _evaluation_publication_due avec une référence temporelle explicite. Une date seule passée en paramètre reste interprétée comme la fin de cette journée afin de préserver les rapports historiques ; un objet datetime utilise l'instant exact.

### Tests ajoutés ou renforcés
- Nouveau test JavaScript tests/test_v25_cross_module_invariants.js : plus de 500 assertions déterministes supplémentaires sur 13 barèmes, sept valeurs représentatives par barème, coefficients, publication, heures exactes, fuseaux, périodes, groupes, classes, valeurs invalides et vues utilisant les notes.
- Test PDF serveur tests/test_v25_bulletin_pdf_data.py renforcé pour comparer une publication déjà due et une autre programmée une seconde après l'instant de référence.
- Les anciens tests V25 de publication élève et de PDF bulletin restent actifs et exécutés dans les trois runners adaptés.

### Journal des premiers résultats et corrections
- Premier run PR #20 : les tests Linux/macOS ont d'abord révélé un helper de date manquant dans le contexte isolé du nouveau test ; le test a été corrigé.
- Deuxième run : la matrice a mis en évidence le défaut applicatif réel des notes négatives (exemple : -1 et 12/20 produisaient 5,50). Le moteur commun a été corrigé pour retourner null hors barème.
- Le filtre du PDF serveur a également été corrigé : un rapport construit pour un instant précis respecte désormais les timestamps du jour ; une date seule de référence continue de signifier la fin de cette journée.
- Le relevé Résultats séparé a été aligné à son tour : il utilise l'instant de référence complet, filtre la classe/groupe de l'élève et rejette les notes hors barème.
- La moyenne par matière utilise maintenant evaluationModelVisible et weightedAverageForEvaluations au lieu de dupliquer le filtre classe/groupe/publication/période.
- Les statistiques du tableau de bord Évaluations et les moyennes de classe normalisent les identifiants classe et ciblent uniquement les élèves du groupe concerné.
- La liste de notes élève et le détail d'une note réutilisent eux aussi les règles communes de visibilité et de validation.
- Le panneau Suivi d'un élève utilisait seulement sa classe pour compter et présenter les devoirs ; il réutilise maintenant studentWorkEligible, comme les listes élève et agrégats globaux.
- Les corrections du PDF et le test exact à l'instant ont été ajoutés après cette découverte. **CI finale réussie :** run [45819080457](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45819080457), 3/3 jobs réussis sur Linux, macOS Apple Silicon/launchd réel et Firefox réel. La PR #20 est validée automatiquement ; elle reste non fusionnée et la release V25.1.2 n'est pas publiée.

Aucun changement du schéma de données n'est prévu.


### Deuxième vague de tests inter-modules — plus de 500 contrôles supplémentaires
- 30 combinaisons classe/groupe croisées avec les élèves de la base, vérifiées à la fois sur les ensembles ciblés et sur la visibilité réelle de chaque élève.
- 60 cas d'éligibilité des devoirs (classes numériques/texte, groupes absents/explicites, devoir présent/absent).
- 12 jeux de données déterministes de classes, groupes, séances, rendus et doublons ; chaque scénario compare les compteurs enseignant, la liste des rendus manquants et le suivi individuel de chaque élève.
- Cas croisés entre moyenne par matière, moyenne générale et moyenne de classe lorsque les identifiants de classe sont numériques dans une table et textuels dans une autre.
- Cas du tableau de bord Évaluations : élèves ciblés, groupes, brouillons, statut de publication absent, total d'évaluations, notes saisies et moyenne calculée.
- Cas de la liste de notes élève, du suivi enseignant et du détail d'une note.

La dernière matrice ajoute plus de 500 assertions générées et déterministes, en complément des tests précédents. La dernière tête versionnée V25.1.2 a passé la CI complète : run 45819080457, 3/3 environnements réussis. La vérification réelle sur l'installation de référence et les comptes de l'établissement reste une étape séparée.


### Résultat de validation finale du candidat versionné
- Commit validé : `59092e9685ba1113e7cd497e4b1664689fea88fb`.
- Run GitHub Actions : [45819080457](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45819080457).
- Linux : réussi, 15 étapes.
- macOS Apple Silicon : réussi, 16 étapes, incluant le vrai test `launchd`.
- Firefox réel : réussi, 9 étapes.
- Matrice inter-modules : 838 invariants dans `test_v25_cross_module_invariants.js`, plus les tests spécifiques Student Report, bulletins persistants, compétences, publication et permissions.
- Version du candidat : `VERSION.txt=V25.1.2`, `APP_VERSION=25.1.2`, `MC_VERSION=V25.1.2`.
- Aucun changement de schéma ni migration de données.

Le candidat est techniquement prêt pour revue/merge. Il n'est pas encore dans `main`, n'a pas de tag `v25.1.2` et n'a pas de release publiée.


### Dernier ajout d'audit — compétences du bulletin HTML et appréciations seules

La revue des sorties HTML et PDF d'un même bulletin a révélé une divergence : le PDF serveur ne reprend que les évaluations publiées, à l'heure exacte et ciblant l'élève ; le bloc Compétences de l'impression HTML utilisait une synthèse de classe qui pouvait conserver des évaluations en brouillon ou des valeurs d'un autre sous-groupe.

**Correctif codé sur la PR #20 :**
- Le bilan enseignant conserve les évaluations de son périmètre, mais chaque appréciation doit provenir d'un élève effectivement ciblé par l'évaluation.
- Pour un bulletin individuel, `competencySummaryForPeriod` utilise désormais `evaluationModelVisible` avec l'identifiant de l'élève, la période et un horodatage complet.
- `bulletinCompetencyBlock` réutilise cette synthèse individuelle ; le rendu HTML suit ainsi les mêmes règles que le PDF serveur.

**Tests ajoutés :** élèves hors groupe, notes parasites dans un autre sous-groupe, brouillon, publication future, autre classe et période hors bulletin. Les assertions comparent le bilan enseignant, la synthèse individuelle et le HTML du bulletin.

La même passe du relevé élève a aussi été complétée : une appréciation seule est maintenant libellée « Appréciation » et n'est plus comptée comme un résultat qualitatif de compétences.

Le run [45819080457](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45819080457) reste la validation complète de la base candidate antérieure. La dernière tête de PR #20 doit repasser la CI Linux, macOS Apple Silicon/launchd et Firefox réel avant que le candidat V25.1.2 soit déclaré validé.


### Fiche élève et contrôle des anciens liens de notes

La comparaison des parcours de fiche élève a identifié deux fonctions historiques qui n'étaient pas encore raccordées aux règles communes :
- `studentEvaluations` et le helper `avg` pouvaient reprendre une note d'un enregistrement où l'élève n'était pas réellement ciblé par le groupe.
- `studentWorkItems` ne filtrait que la classe, contrairement à la liste élève et au nouveau panneau de suivi.

Correctifs codés sur la PR #20 :
- Historique et moyenne de la fiche : filtrage par `evaluationModelTargetStudents`, en conservant l'accès interne professeur aux brouillons.
- Travaux à venir de la fiche : réutilisation de `studentWorkEligible`.
- Détail d'une note : contrôle `evaluationModelVisible` au moment de l'ouverture, avant le contrôle numérique du barème. Un ancien lien ne peut donc plus contourner la publication ou le périmètre de groupe.

Tests : deux groupes dans une même classe, note parasite d'un autre groupe, travaux partagés et individuels, brouillon, publication future, ancien lien et note valide.

La revalidation complète de la tête courante reste obligatoire sur Linux, macOS Apple Silicon/launchd et Firefox réel.


### Validation finale de la dernière tête V25.1.2 — 26 novembre 2026

- Commit : `eae1433c8c12bb7e84ae0b9749633864fa2388c1`.
- Run : [45822162433](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45822162433).
- Linux : tests JavaScript et Python complets — réussi.
- macOS Apple Silicon : installateur, compilation Python, tests JavaScript, intégration `launchd` réelle et tests Python — réussi.
- Firefox réel : régression EDT et parcours modules — réussi.
- Résultat : **3/3 jobs réussis**.
- Matrice inter-modules : **860 invariants** réussis.
- Version : V25.1.2 dans `VERSION.txt`, `APP_VERSION` et `MC_VERSION`.
- Aucun changement de schéma ni migration de données.

La PR #20 reste ouverte pour revue ; la version n'est pas encore fusionnée, taguée ni publiée. La recette sur l'installation physique et les comptes de l'établissement reste distincte de la CI hébergée.


## Audit individuel, parcours Firefox et finition responsive — 26 novembre 2026

### Périmètre étendu

L’audit ne se limite plus aux contrats entre modules. Il combine :
- des tests isolés de logique, filtres, autorisations, persistance et rendu des composants ;
- des scénarios Firefox réels avec des comptes temporaires Direction, Professeur et Élève ;
- l’inspection des captures en clair/sombre, aux largeurs desktop, 900 px et 390 px ;
- les invariants inter-modules, conservés en complément.

Le test Firefox exerce notamment la création d’un compte professeur dans l’interface Direction, sa désactivation/réactivation, la création et la persistance d’un créneau, les échanges entre rôles, un devoir avec pièce jointe, la messagerie V2 et le cloisonnement Cloud. Les captures couvrent les vues Direction, Professeur et Élève.

### Corrections supplémentaires

- **STU-WORK-01 :** la page « Travail à faire » est redevenue accessible comme module autonome. Elle présente les catégories À faire, En retard, Rendus, Corrigés et Tous ; l’accueil et le menu y conduisent et un badge signale les retards. « À venir » reste une vue distincte du cahier de cours.
- **ID-MIXED-01 :** les comparaisons d’identifiants ont été harmonisées autour de `sameId` dans l’annuaire, l’assiduité, les filtres classe/groupe de l’EDT élève, les rendus et brouillons, le suivi rapide, les notifications, les bulletins et la fiche élève 360°.
- **UI-STU-02 :** le tableau « Travail à faire » se transforme en fiches à deux colonnes sous 650 px. Les libellés de cellules sont visibles, l’état reste lisible et le bouton Ouvrir conserve une largeur utile ; le tableau desktop est préservé.

### Tests ajoutés ou complétés

- `tests/test_v25_legacy_id_module_scope.js` : identifiants mixtes dans l’historique d’assiduité, les compteurs, l’annuaire, le suivi, l’EDT, les rendus/brouillons, les notifications, les résultats officiels et le suivi rapide.
- `tests/test_v25_student_schedule.js` et `tests/test_v25_schedule_navigation.js` : fixtures mises à jour pour charger le comparateur commun et le nouveau module routé.
- `tests/test_v25_student_work_responsive.py` : présence du layout mobile, des libellés et de la route autonome.
- `tests/browser/test_v25_schedule_firefox.py` : assertion réelle sur la structure deux colonnes, les cinq cellules nommées et la largeur minimale du bouton mobile.

### Validation de la tête courante

- Commit : `f8640bd5ccc900bdf0d2b1b4f4fb6969095c6dfe`.
- Run : [45842659573](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45842659573).
- Linux : succès.
- macOS Apple Silicon : succès, installateur et véritable `launchd`.
- Firefox réel : succès.
- Résultat : **3/3 jobs réussis**.
- Matrice croisée : 860 invariants.
- Dépôt : 97 fichiers de tests (57 JavaScript, 40 Python).

La PR #20 demeure ouverte, non fusionnée et non publiée. Aucune installation locale ni donnée réelle n’a été modifiée. La recette sur les comptes et données physiques reste nécessaire.


## Candidat V25.2.0 — cycle des devoirs, vie scolaire et administration — 26 novembre 2026

### Cycle des devoirs
- Les états « brouillon » et « transmis » sont distingués dans les vues élève/professeur et les notifications.
- Les compteurs de rendus reçus et à corriger sont recalculés depuis les soumissions réellement transmises.
- Les listes de travaux manquants restent distinctes des retards : une échéance future peut figurer dans le suivi global sans être présentée comme déjà en retard.
- Les identifiants historiques texte/nombre sont acceptés dans les opérations de dépôt, recherche et correction.
- Le parcours professeur → élève → dépôt → correction → restitution est exercé par un test de scénario ciblé.

### Cycle de vie scolaire
- Les appels sont retrouvés par identifiants normalisés pour la classe, le cours, l'élève et l'appel lui-même.
- L'enregistrement conserve les statuts/motifs non touchés lors d'une modification partielle ; l'édition d'une date ou d'un créneau ne provoque pas de perte de saisie.
- Les saisies non confirmées sont isolées ; l'annulation et le changement de contexte sont couverts par des tests.
- La file à traiter, la justification, la date de traitement et les décomptes absences/retards sont recalculés après sauvegarde.
- Les synthèses par classe ne doublonnent pas un élève dont les identifiants historiques ont des types différents.

### Administration, affectations et données
- Les formulaires de compte professeur conservent les affectations existantes.
- Les vues Direction/Professeur principal et classes enseignées normalisent et dédupliquent les identifiants.
- Les suppressions d'élèves nettoient les références liées.
- Le centre de notifications et les permissions de bulletin retrouvent les objets avec identifiants texte/nombre.

### Vérification
- Le dernier commit fonctionnel testé `3522e5dd2d09facd1d694b218a2a6e5718350cf3` a passé le run [45896370692](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45896370692), Linux, macOS Apple Silicon/launchd et Firefox réel : **3/3 jobs réussis**.
- La campagne comprend 860 invariants intermodules et 109 fichiers de tests (67 JavaScript, 42 Python).
- VERSION.txt, APP_VERSION et MC_VERSION sont alignés sur V25.2.0 sur cette tête fonctionnelle.
- La PR #20 demeure ouverte, non fusionnée et non publiée. La dernière version stable reste V25.1.1.
- La recette de l'installation physique, des vrais comptes et des appareils clients reste à confirmer ; les états des anomalies ne passent pas à « Corrigé » sur la seule base de CI.


## Optimisation du validateur d'import d'établissement — 26 novembre 2026

**Branche :** `fix/v25.1.2-cross-module-consistency`  
**PR :** [#20 — V25.2.0](https://github.com/WedoneOfficiel/Ma-Classe/pull/20)

### Défaut de performance constaté
Le validateur acceptait jusqu'à 50 000 créneaux mais comparait initialement toutes les paires, y compris celles sans ressource partagée. Les contrôles d'effectifs et les analyses de trous répétaient également des parcours complets.

### Modifications codées
- Index classe/professeur/salle et balayage d'intervalles pour réduire la comparaison aux ressources et horaires concernés.
- Index dédié des groupes parallèles pour ne pas comparer les cours de groupes distincts.
- Index des effectifs par classe/groupe, des cours par classe et des cours hebdomadaires par enseignant/jour.
- Arrêt de l'énumération des conflits dès que 200 erreurs publiques sont disponibles.
- Conservation des contrôles existants de récurrence, d'exceptions, de capacité, d'équipement et d'indisponibilité.

### Tests et preuve
- Nouveau fichier `tests/test_v25_establishment_import_scalability.py` avec quatre tests, dont deux cas de 5 000 créneaux/groupes parallèles.
- Commit fonctionnel : `3522e5dd2d09facd1d694b218a2a6e5718350cf3`.
- Run [45896370692](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45896370692) : Linux 15/15, macOS 17/17, Firefox réel 9/9.
- Aucun changement de schéma.

## Préparation de la V25.2.1 — constats à auditer après la recette V25.2.0

1. **Planner :** appliquer la capacité et les équipements saisis lors de la recherche d'un créneau, et valider le choix de salle jusqu'au brouillon du cours.
2. **Échéances des devoirs :** faire respecter l'heure `dueTime` dans les états « À faire », « En retard », les compteurs et les notifications, avec une règle explicite pour les anciennes données sans heure.
3. **Sauvegardes :** étendre les tests de restauration à des archives volumineuses, pièces jointes nombreuses et archives invalides.
4. **Accessibilité :** poursuivre les tests clavier, focus et lecteur d'écran.

Ces éléments constituent un backlog proposé ; aucun n'est annoncé comme corrigé. Ils seront traités dans une branche dédiée après la recette réelle du candidat V25.2.0.


## Stabilisation finale V25.2.0 — 27 novembre 2026

**Branche :** `fix/v25.1.2-cross-module-consistency`  
**PR :** [#20 — V25.2.0](https://github.com/WedoneOfficiel/Ma-Classe/pull/20)  
**Tête validée automatiquement :** `e4969e765a1faee2d5480768a62c1bb88b0aba84`

### Défauts supplémentaires identifiés et corrigés

- **Écran des nouveautés — ouverture automatique :** `release_notes.js` s'exécute en mode strict. `openAutomatic()` affectait `pendingAutomaticPayload` sans déclaration, ce qui levait une `ReferenceError` et empêchait l'annonce du premier accès. La variable est maintenant déclarée dans la portée du module ; un test unitaire exerce l'ouverture automatique, le chargement de l'historique et le rendu du modal.
- **Tests de publication déterministes :** la matrice de publication des évaluations dépendait de la date réelle du runner. Une date future dans le cas de test devenait le jour courant selon l'heure du job. L'horloge du test est maintenant figée avant l'initialisation du modèle, sans changer l'horloge de production.
- **Tests de Paramètres :** un contrôle de grille était placé après `unittest.main()` et n'était donc pas découvert par le runner. Il est réintégré dans la classe de tests ; les assertions utilisent les sélecteurs CSS effectivement appliqués.
- **Firefox / Playwright :** suppression d'une déclaration `free_port()` dupliquée ; les deux appels de rendu des Paramètres (desktop et mobile) transmettent désormais un seul objet à `Page.evaluate()`, comme l'exige l'API Playwright.
- **Grille Direction — carte Données :** `grid-column:auto!important` annulait le placement `grid-area:data` et faisait retomber la carte dans la première colonne. La déclaration contradictoire est retirée ; la carte reste dans la colonne de droite, sous Version, tandis que le responsive conserve ses zones à deux colonnes et à une colonne.
- **Import d'établissement — groupes implicites multi-niveaux :** la capacité d'une salle ne comptait que le champ `group` explicite des élèves, alors que `build_data()` génère un groupe `NomClasse/Niveau` lorsque le JSON ne le fournit pas. Le calcul du validateur utilise maintenant le même groupe effectif que l'import final.
- **Import d'établissement — cours partagés :** la capacité était contrôlée par classe séparément alors qu'un créneau partagé crée plusieurs enregistrements liés dans la même salle. Le calcul additionne les élèves de toutes les classes ciblées (ou de leur groupe commun) avant de comparer la capacité ; l'équipement de la salle n'est contrôlé qu'une fois pour le créneau.
- **Import établissement — taille des fichiers :** le navigateur et les deux routes serveur (prévalidation et import confirmé) imposaient auparavant 10 Mo, alors que le schéma permet des configurations volumineuses. La limite est maintenant de 25 Mo aux deux niveaux ; le test UI vérifie l'alignement des trois contrôles.
- **Archive de release — couverture complète :** le test `test_v25_release_package_contents.py` vérifie maintenant dynamiquement que tous les scripts `.sh` et `.command` à la racine se trouvent dans le ZIP, et interdit aussi les fichiers `.key`. La tête `f22f4b9` a passé la CI #2092, 3/3.

### Preuves de validation

- Workflow final [#2088 / run 45917072089](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45917072089), commit `e4969e765a1faee2d5480768a62c1bb88b0aba84` : **Linux, macOS Apple Silicon et Firefox réel réussis (3/3)**.
- Linux : installateur réel, vérification JavaScript, compilation Python et tous les tests JavaScript/Python.
- macOS : installateur Apple Silicon, suites JavaScript/Python et véritable démarrage du service `launchd`.
- Firefox : scénarios Direction, Professeur et Élève, journal des versions, générateur et géométrie des Paramètres sur desktop/mobile ; captures des modules en thèmes clair et sombre.
- Les captures ont été téléchargées depuis l'artefact `maclasse-v25-product-screenshots` (113 fichiers) et inspectées. La carte Données est maintenant alignée sous Version dans la colonne de droite ; les vues mobiles restent sans débordement horizontal du contenu principal.
- Aucun changement de schéma ni migration de données. Aucune donnée de l'installation locale n'a été modifiée.

### Vérification complémentaire de l'archive de release

Le test `tests/test_v25_release_package_contents.py` reproduit la commande `git archive` du workflow officiel et vérifie que le ZIP contient le runtime, `requirements.txt`, `update_manager.py`, `network_supervisor.py`, `release_signing.py`, `release-signing-public-key.txt`, les modules JavaScript requis, les lanceurs essentiels Linux/macOS, la note V25.2.0, l'historique consolidé et les trois sources historiques utilisées par le journal. Le contrôle de présence des composants est passé dans la CI #2088 ; le contrôle complémentaire d'exclusion des dossiers `data/`, bases locales, certificats et clefs privées a passé la CI #2091 sur le commit de test `5f2b4ab`.

### Limites avant publication

La V25.2.0 n'est pas encore fusionnée ni publiée. La CI hébergée ne remplace pas la sauvegarde et la recette sur une copie représentative des données réelles, puis la vérification sur le Mac et les appareils clients avec les vrais comptes. La dernière version stable reste V25.1.1 ; aucun tag ni asset V25.2.0 n'a été créé.


## Limite produit restante — confiance des certificats HTTPS client (27/11/2026)

Le mode réseau actuel crée une autorité de certification privée sur le serveur. Chaque poste ou navigateur qui ne connaît pas déjà cette autorité doit approuver/importer le certificat public `data/tls/ca.crt` une fois. Les tests de CI valident le listener TLS, les cookies Secure, la supervision réseau et le renouvellement du certificat serveur ; ils ne peuvent pas rendre une AC privée automatiquement fiable dans le magasin de confiance d'un appareil tiers.

Cette architecture ne satisfait donc pas l'objectif de zéro réglage manuel du certificat sur chaque ordinateur. Ne pas contourner le contrôle par une exception TLS automatique ni par un retour HTTP. Il faut arbitrer une vraie solution : certificat reconnu publiquement pour un nom DNS contrôlé avec résolution LAN adaptée, ou déploiement centralisé de l'AC via MDM/gestion de parc. Le contrôle depuis de vrais appareils et cette décision restent à faire avant de déclarer l'accès multi-postes conforme à l'objectif.
