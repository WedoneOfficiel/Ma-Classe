# Archives des audits, états et recettes antérieurs

> **Archives historiques — documents non normatifs.** Ces fichiers décrivent des états de MaClasse antérieurs à la stabilisation V25.0.25. Certains prérequis, statuts de sécurité et résultats de tests ont depuis évolué. Ne pas utiliser ces archives comme instructions d'installation ou comme état actuel du projet. Les contenus originaux sont conservés ci-dessous à titre de traçabilité.

---

## Source originale : `AUDIT.txt`

Contenu original conservé :

AUDIT FONCTIONNEL — MaClasse V21.09
==================================

Bulletins
---------
- Nouveau parcours collectif et saisie par matière sur une seule page.
- Fiche individuelle avec moyennes, appréciations, assiduité et aperçu imprimable.
- Validation par le professeur principal, puis publication officielle de la classe.
- Consultation famille : les bulletins sont marqués publiés seulement après validation officielle.
- Les notes/moyennes proviennent des évaluations existantes ; les notes manquantes restent non notées.
- Périodes résolues à partir du mode de période de la classe.
- Les brouillons restent éditables ; les bulletins publiés sont verrouillés dans cet écran.
- Les droits de modification d’une appréciation s’appuient sur l’attribution professeur/matière de l’emploi du temps lorsqu’elle existe.

Contrôles réellement exécutés
-----------------------------
- node --check sur _all.js : réussi.
- node --check sur le JavaScript intégré à index.html : réussi.
- Tous les tests tests/*.js : réussis.
- Test dédié test_v2109_bulletins.js : réussi.
- python -m py_compile sur server.py : réussi.

Limites de recette
------------------
- Pas de test visuel navigateur automatisé dans cette livraison.
- Les droits doivent être vérifiés avec les comptes enseignants réels de l’établissement.
- L’aperçu PDF utilise le flux d’impression du navigateur ; la génération et la mise en page doivent être vérifiées sur le poste de l’utilisateur.


AUDIT FONCTIONNEL — MaClasse V21.01
==================================

Messagerie
----------
- Réponse : vérification automatisée de la création d’un nouvel échange comprenant une copie du message source et la réponse ; le fil source reste inchangé.
- Confidentialité : la copie du message source retire les destinataires CCI ; un transfert n’emporte pas la liste des CCI d’origine.
- Rangement : champs archivedBy, deletedBy, starredBy et folderByUser sont propres à l’utilisateur et initialisés sans migration destructive.
- Lecture : les compteurs et le marquage lu utilisent des règles de destinataires plus strictes, avec traitement particulier des messages historiques de classe sans destinataires explicites.
- Réponse à un message : chaque message reçu propose une action de réponse ciblée sur son identifiant.
- Transfert : création d’un nouvel échange et conservation d’une référence vers le message source.

Correctifs V21.01
-------------
- Correction de la référence à la variable inexistante s dans la boîte enseignant.
- Favoris scindés correctement entre les profils enseignant et élève.
- Recherche : focus et position du curseur restaurés après rafraîchissement des résultats.
- Test de non-régression dédié dans tests/test_v2111_mail_ui.js.

Contrôles réellement exécutés
-----------------------------
- node --check sur _all.js : réussi.
- node --check sur le JavaScript intégré à index.html : réussi.
- Tous les tests présents dans tests/*.js, dont test_v211_messaging.js : réussis.
- La recette visuelle complète dans Firefox/macOS n’a pas été réalisée.

Limites connues
---------------
- Les brouillons ne sont pas persistés après fermeture du formulaire.
- La messagerie est interne à MaClasse et ne se connecte pas à un service e-mail externe.
- Le test de migration sur une copie réelle des données de production reste à effectuer avant déploiement.




AUDIT FONCTIONNEL — MaClasse V19.7
==================================

Objet
----
Première passe de stabilisation de la branche V19.x, basée sur V19.6.
Ce document distingue les contrôles techniques réellement exécutés des parcours
métier qui restent à vérifier. Il ne certifie pas que tous les modules sont
entièrement opérationnels.

Contrôles et corrections inclus dans V19.7
-----------------------------------------
- La réinitialisation des données crée maintenant une copie de sécurité dans
'data/backups/' avant l'effacement. Si la copie échoue, l'effacement est annulé.
- L'API refuse les données enregistrées lorsque la racine JSON n'est pas un objet.
- Le contrôle de cohérence détecte davantage de références manquantes : classes,
  créneaux d'emploi du temps, élèves évalués, appels, rendus, comptes liés et
  dossiers documentaires parents.
- Le contrôle reste non destructif : il signale les anomalies, mais ne les
  corrige pas automatiquement.
- Les fichiers JavaScript intégrés et séparés restent synchronisés.

État de la revue statique par module
-----------------------------------
- Navigation et espaces : revue statique effectuée ; la navigation V19.5 est
  conservée. Le parcours complet doit encore être rejoué dans Firefox.
- Comptes et rôles : revue partielle ; les permissions doivent être testées avec
  plusieurs comptes réels et les accès croisés doivent faire l'objet d'une recette.
- Élèves et classes : fonctions présentes dans le code ; création, modification,
  archivage/suppression et réaffectation restent à tester de bout en bout.
- Emploi du temps : fonctions présentes ; récurrences, exceptions, déplacements
  et cohérence avec les séances/appels restent à tester.
- Séances et devoirs : fonctions présentes ; création, échéances, fichiers,
  rendus et corrections restent à tester en parcours complet.
- Évaluations et bulletins : fonctions présentes ; calculs, coefficients, périodes,
  notes manquantes et transfert vers les bulletins restent à vérifier sur des jeux
  de données de test.
- Appels : fonctions présentes ; création, correction, doublons et statistiques
  restent à tester sur plusieurs dates et modes d'appel.
- Messagerie : fonctions présentes ; les identifiants historiques 'teacher-local'
  sont encore utilisés à plusieurs endroits. Le cloisonnement entre plusieurs
  comptes enseignants doit être audité avant de considérer ce module comme validé.
- Documents et fichiers : fonctions présentes ; droits d'accès, partage, déplacement,
  suppression et cohérence entre métadonnées et fichiers physiques restent à tester.
- Sauvegarde/restauration : garde-fous renforcés ; restauration testée par revue
  statique, mais le parcours complet doit encore être testé dans l'interface.
- Paramètres et journal : fonctions présentes ; export du journal et cohérence des
  événements restent à vérifier dans les parcours métier.

Tests réellement exécutés pour cette livraison
----------------------------------------------
- node --check sur _all.js : réussi.
- python -m py_compile sur server.py : réussi.
- Égalité exacte du JavaScript intégré à index.html et de _all.js : réussie.
- Test HTTP isolé : lecture des données réussie.
- Test HTTP isolé : rejet d'une racine JSON de type liste : réussi (HTTP 400).
- Test HTTP isolé : réinitialisation avec copie de sécurité restaurable : réussi.
- Intégrité de l'archive ZIP : réussie.

Non vérifié
-----------
- Exécution réelle dans Firefox sur macOS.
- Recette complète de chaque module avec des scénarios utilisateur.
- Import/export et migration sur la copie réelle des données de l'utilisateur.

Prochaine étape recommandée — V19.8
----------------------------------
1. Auditer et corriger le cloisonnement des comptes et de la messagerie.
2. Rejouer les parcours élèves/classes, emploi du temps, séances/devoirs,
   évaluations/bulletins et appels avec un jeu de données fictif.
3. Tester les fichiers et droits d'accès, puis la sauvegarde/restauration.
4. Corriger les régressions observées et documenter chaque test réussi.

AUDIT FONCTIONNEL — MaClasse V19.8
==================================

Périmètre
---------
V19.8 poursuit la stabilisation de la branche V19.x à partir de V19.7.
Cette livraison traite un défaut identifié dans la messagerie : plusieurs opérations
utilisaient en dur l'identifiant historique « teacher-local », y compris lorsque
un autre compte enseignant était connecté.

Corrections incluses
--------------------
- Résolution de l'identifiant enseignant actif depuis authUser.teacherId.
- Création d'une conversation enseignant avec le bon identifiant d'expéditeur et
  le bon propriétaire de conversation.
- Routage d'un nouveau mail envoyé par un élève vers l'identifiant de l'enseignant
  effectivement sélectionné dans le formulaire.
- Filtrage de la boîte de réception et gestion des dossiers selon l'identité active.
- Compteurs de messages non lus limités aux conversations auxquelles le compte
  enseignant a accès.
- Marquage comme lu limité aux messages adressés au compte courant, ainsi qu'aux
  réponses d'élèves dans les conversations dont ce compte est responsable.
- Affichage des messages envoyés qui compare l'expéditeur à l'identité active.
- Conservation de la compatibilité historique avec « teacher-local ».

Tests exécutés
--------------
- node --check _all.js : réussi.
- python -m py_compile server.py : réussi.
- Script tests/test_messaging_identity.js : réussi. Il vérifie l'identité active,
  le routage élève→enseignant, la visibilité séparée entre deux comptes, le compteur
  de non-lus et le marquage de lecture ciblé.
- Synchronisation exacte du JavaScript intégré dans index.html avec _all.js : réussie.
- Test HTTP isolé : GET / et GET /api/data : réussis.
- Intégrité de l'archive ZIP : réussie.

État des autres modules
----------------------
- Navigation : corrections antérieures conservées ; test complet Firefox à faire.
- Comptes/rôles : correction ciblée de la messagerie ; les droits de chaque module
  nécessitent toujours une recette complète avec plusieurs comptes.
- Élèves/classes, emploi du temps, séances/devoirs, évaluations/bulletins et appels :
  présents dans le code, mais parcours métier de bout en bout non certifiés.
- Documents/fichiers : droits, partage et cohérence physique à tester.
- Sauvegarde/restauration : garde-fous V19.6/V19.7 conservés ; recette complète
  dans l'interface avec copie des données à effectuer.

Non vérifié
-----------
- Exécution réelle dans Firefox sur macOS.
- Recette complète de tous les modules et des scénarios de plusieurs utilisateurs.
- Migration et restauration sur la copie réelle des données de l'utilisateur.

Prochaine étape proposée — V19.9
--------------------------------
1. Continuer la recette multi-comptes et des permissions.
2. Tester les parcours classes/élèves, emploi du temps, séances/devoirs, évaluations,
   bulletins et appels avec un jeu de données fictif.
3. Tester les opérations de fichiers et une restauration complète.
4. Corriger uniquement les défauts reproductibles, puis refaire les tests de régression.

AUDIT FONCTIONNEL — MaClasse V19.9
==================================

Périmètre
---------
V19.9 poursuit la stabilisation depuis V19.8. La correction porte sur la cohérence
entre le nom/niveau d’une classe et les groupes enregistrés sur les fiches élèves.

Défaut corrigé
--------------
Les groupes d’une classe à double niveau sont construits à partir du nom de classe
(par exemple « CM1-CM2/CM1 »). Lors du renommage, les groupes générés changeaient,
mais les affectations des élèves pouvaient conserver les anciens libellés. Cela
créait des références de groupe orphelines dans les fiches élèves et les choix de
connexion élève.

Corrections incluses
--------------------
- Renommage des affectations d’élèves quand une classe à double niveau est renommée.
- Conservation de l’affectation si le niveau existe toujours dans la classe modifiée.
- Suppression de l’affectation de groupe si le niveau correspondant a été retiré.
- Nettoyage des anciens groupes générés si la classe redevient une classe simple.
- Pour les classes à groupes manuels, conservation des groupes encore valides et
  retrait des affectations qui pointent vers un groupe supprimé.
- Les élèves appartenant à une autre classe ne sont pas modifiés.
- Corrections V19.8 de messagerie multi-comptes conservées.

Tests exécutés
--------------
- node --check _all.js : réussi.
- python -m py_compile server.py : réussi.
- tests/test_class_group_migration.js : réussi (renommage, niveau supprimé,
  conversion en classe simple, groupes manuels et isolation d’une autre classe).
- tests/test_messaging_identity.js : réussi.
- Synchronisation exacte du JavaScript intégré à index.html avec _all.js : réussi.
- Test HTTP isolé du serveur : réussi sur une copie temporaire (GET /, GET /api/data,
  POST /api/save et rejet d’une racine JSON non objet).
- Intégrité ZIP : réussi.

État de la recette globale
--------------------------
- Classes/groupes : correction ciblée automatisée ; interface Firefox à tester.
- Comptes/rôles/messagerie : tests ciblés de régression ; droits de tous les modules
  pas encore certifiés.
- Élèves, emploi du temps, séances/devoirs, évaluations/bulletins et appels : présents
  dans le code, mais parcours métier de bout en bout encore à tester.
- Documents/fichiers : droits, partage et cohérence des fichiers à tester.
- Sauvegarde/restauration : garde-fous antérieurs conservés ; recette complète dans
  l’interface sur une copie des données à effectuer.

Non vérifié
-----------
- Exécution réelle dans Firefox sur macOS.
- Recette complète de tous les modules et des scénarios multi-utilisateurs.
- Migration et restauration sur la copie réelle des données de l’utilisateur.

Étape suivante proposée — V20.0.0 après recette
----------------------------------------------
Avant de lancer la version majeure, compléter les scénarios de bout en bout avec des
jeux de données fictifs, vérifier les droits par rôle, et tester les opérations de
fichiers et la restauration. Ne déclarer une fonction terminée qu’après validation.

AUDIT MaClasse V20.0.0

Changements
- Tableau de bord enrichi : quatre raccourcis et récapitulatif des créneaux du jour.
- Évaluations : compétences facultatives, niveaux individuels par élève, stockage distinct des notes et commentaires.
- Normalisation compatible avec les évaluations anciennes ; pas de migration destructive prévue.
- index.html synchronisé avec _all.js.

Vérifications exécutées
- node --check _all.js : réussi.
- node --check du JavaScript intégré à index.html : réussi.
- tests/test_messaging_identity.js : réussi.
- tests/test_class_group_migration.js : réussi.
- tests/test_competencies_v20.js : réussi.

Limites
- Tests unitaires ciblés, pas une recette complète de tous les modules.
- Pas de validation réelle dans Firefox sur macOS pendant cette livraison.
- Les impressions, exports de bulletins et affichage des compétences dans les bulletins ne sont pas modifiés par cette version.

AUDIT MaClasse V20.1

Changements couverts
- Grilles d'évaluation réutilisables enregistrées dans evaluationTemplates.
- Bibliothèque de compétences normalisée sans suppression des anciennes évaluations.
- Application d'un modèle aux champs matière/titre/compétences d'une évaluation.
- Synthèse des niveaux par classe et matière.
- Cloud : filtres de types, indicateurs d'espace, import de dossier avec conservation des sous-dossiers lorsque webkitRelativePath est disponible.
- Script principal index.html synchronisé avec _all.js.

Tests automatisés
- test_messaging_identity.js
- test_class_group_migration.js
- test_competencies_v20.js
- test_evaluation_grids_v201.js
- test_cloud_filters_v201.js
- test_cloud_identity_v201.js

Limites
- Tests de fonctions et contrôles syntaxiques ne remplacent pas une recette manuelle complète dans Firefox sur macOS.
- Import de dossier dépend de la prise en charge par le navigateur de l'attribut webkitdirectory et de webkitRelativePath.
- Le Cloud reste un stockage servi par le serveur local de MaClasse. Pas de synchronisation distante multi-appareils, de service hébergé ni de connexion à un fournisseur tiers ajoutés dans cette version.
- Les tailles affichées reposent sur les métadonnées des fichiers connus de MaClasse ; ce n'est pas une mesure du disque entier.

AUDIT TECHNIQUE — MaClasse V20.2

Base : V20.1. Aucun remplacement volontaire du dossier data/ ni des données de l’utilisateur.

ÉVOLUTIONS CONTRÔLÉES
- Visibilité des actions Grilles & compétences et Bilan compétences dans la version active du module Évaluations.
- Synthèse de compétences filtrée par période et ajoutée à la feuille imprimable du bulletin.
- Centre de notifications : messages, rendus, notes à saisir et partages directs Cloud au compte courant.
- Cloud : vue en cartes, icônes SVG de dossiers, miniatures images/vidéos si disponibles, sélection multiple, déplacement/suppression groupés, menu contextuel, tri par taille.
- Fichier partagé directement : affichage dans la racine « Partagés avec moi » si son dossier parent n’est pas accessible.
- EDT : professeur habituel associé au cours, gestion groupée de l’intitulé/couleur/professeur, exceptions ponctuelles de remplacement, horaire, salle et annulation.
- index.html embarque le même script que _all.js.

VALIDATIONS EXÉCUTÉES
- node --check _all.js : OK.
- python -m py_compile server.py : OK.
- Tests automatisés : migration classe/groupes, filtres Cloud, identité Cloud, niveaux de compétences, grilles réutilisables, identité messagerie et test V20.2 : OK.
- Test ciblé V20.2 : cours distingués par professeur habituel ; bilan filtré par période ; fichier partagé directement listé sans dossier parent partagé.
- Intégrité de l’archive ZIP : vérifiée avant livraison.
- Test HTTP local (page, lecture/sauvegarde API et opération Cloud) : vérifié dans un serveur temporaire.

LIMITES / NON TESTÉ
- Pas de recette manuelle complète sur Firefox/macOS dans cette session.
- Les aperçus vidéo dépendent du navigateur et du codec.
- Pas de synchronisation Cloud Internet multi-appareils ajoutée.

AUDIT TECHNIQUE — MaClasse V20.3

Base : archive V20.2 vérifiée. Modifications incrémentales dans _all.js et synchronisation du script embarqué dans index.html. Pas de suppression du dossier data/ ni de migration destructive volontaire.

CHANGEMENTS
- Niveaux de compétence harmonisés : Insuffisant, Fragile, Bien, Très bien ; styles de couleur associés.
- Modèles de grilles : critères avec barème en points, distincts des compétences ; les critères sont enregistrés dans le modèle, transférés à l’évaluation, affichés par élève et totalisés. Les critères sont facultatifs.
- Navigation : Notifications retiré des groupes principaux et route legacy redirigée vers Centre d’activité. Les notifications de partage/messages/actions sont réunies au fil d’activité.
- Sidebar : nav flex avec overflow-y auto et hauteur contrainte à la fenêtre.
- Cloud : cartes carrées, miniatures bornées dans le conteneur, styles de badges de type fichier étendus.
- EDT : identité de cours basée sur classe, matière/intitulé, professeur habituel et sous-groupe ; remplacement séparé dans les overrides.

VALIDATIONS
- node --check _all.js : OK.
- python -m py_compile server.py : OK.
- Tests JS existants : 7/7 OK (migration classe/groupes, filtres Cloud, identité Cloud, compétences, grilles, identité messagerie, fonctions V20.2).
- Test ciblé supplémentaire : barème critère, total maximal et total obtenu par élève : OK.
- Archive ZIP : contrôle d’intégrité effectué avant livraison.

LIMITES
- Pas de test manuel complet sous Firefox/macOS.
- Pas de synchronisation Internet multi-appareils ajoutée.

AUDIT TECHNIQUE — MaClasse V20.4

Base : MaClasse_V20_3.zip, extraite et vérifiée avant modification.

CHANGEMENTS
- Routes legacy today/notifications redirigées vers activity ; entrée « Aujourd’hui » supprimée du menu principal. « Voir la journée » fait défiler vers la section Aujourd’hui du Centre d’activité.
- Bibliothèque de compétences séparée de la création des grilles ; association facultative de plusieurs niveaux par compétence ; grille unique combinant compétences et critères notés.
- Carnet de notes : repères colorés des compétences et total des points des critères visibles sous la note quand les données existent.
- CSS de réduction réelle de la barre latérale, avec maintien du scroll vertical.
- Cloud : fil d’Ariane dans la zone principale, suppression du dropzone autonome, vue liste compacte, grille d’icônes plus compacte et actions contextuelles. Les cartes ne sont pas re-rendues au clic simple afin de préserver le double-clic d’ouverture.
- EDT : apparence gérée au niveau du cours. Édition d’un créneau sans champs couleur/motif préserve les valeurs existantes. Les valeurs de motif utilisent les enums existants « none », « hatch », « cross ».
- Gestion des cours regroupe les créneaux par classe, intitulé, titulaire et sous-groupe sans supprimer les séances.

VALIDATIONS
- node --check sur le script embarqué : OK.
- Tests JS : 8/8 OK après synchronisation de _all.js avec le script embarqué.
- Test V20.4 de cohérence des modules et de l’interface : OK.
- Intégrité ZIP : à exécuter lors de la construction finale.

LIMITES
- Pas de test manuel complet sous Firefox/macOS.
- Pas de synchronisation Internet multi-appareils ajoutée.


AUDIT TECHNIQUE — MaClasse V20.5

- Ajout du statut brouillon/publiée et d’une date de publication facultative pour les évaluations.
- Les résultats publiés côté élève incluent la note, le commentaire, les critères notés et les niveaux de compétence ; les brouillons et publications futures restent cachés.
- Ajout d’un écran de suivi des absences et retards avec filtres de classe et d’état, justification et motif/commentaire modifiables sans rouvrir l’appel d’origine.
- Les onglets du Centre d’activité affichent maintenant la catégorie sélectionnée au lieu de réafficher toutes les actions.
- Migration EDT ponctuelle et idempotente : les créneaux partageant classe, matière, professeur titulaire et sous-groupe récupèrent une apparence commune (couleur/motif majoritaires) ; exceptions datées préservées.
- Consolidation des fichiers de notes de version en un seul AUDIT.txt et un seul LISEZ-MOI.txt.

VALIDATIONS V20.5
- Vérifications de syntaxe JavaScript et tests automatisés exécutés après assemblage.
- Recette manuelle complète sous Firefox/macOS non réalisée dans cette session.


AUDIT TECHNIQUE — MaClasse V20.6

- EDT : après modification des informations d’un cours de référence, le planning sous-jacent est rerendu avant de rouvrir la fenêtre de gestion ; il s’actualise donc sans changer de module.
- Appels : ajout d’un accès visible au suivi des absences et retards depuis le module Appels. Le suivi permet de filtrer par classe, élève, statut et période, puis de modifier justification et commentaire. Les retards traités sortent de la liste « À traiter ».
- Grilles : remplacement de la saisie des critères au format texte par un éditeur en tableau, avec points maximum, descriptions de niveaux facultatives, ajout de critères réutilisables et modification des grilles existantes.
- Espace élève : les évaluations publiées affichent les résultats des critères, leurs descriptions de niveau lorsqu’elles existent, les compétences et le commentaire. Les brouillons et publications futures restent masqués.
- Documentation : historique V20.6 ajouté à cet audit unique ; pas de nouveau fichier d’audit ou de Lisez-moi par version.

VALIDATIONS V20.6
- Syntaxe JavaScript : OK.
- Tests automatisés existants : 9/9 OK.
- Recette manuelle complète sous Firefox/macOS : non réalisée.


AUDIT TECHNIQUE — MaClasse V20.7

CHANGEMENTS
- Barème d’évaluation configurable : 20 par défaut sans grille, total des critères proposé à l’application d’une grille, modification libre par le professeur. La note brute est conservée avec son dénominateur.
- Moyennes et statistiques normalisées sur 20 ; saisie des notes bornée par le barème de l’évaluation. Les évaluations historiques sans barème explicite conservent le comportement sur 20.
- Carnet de notes enseignant adapté au barème propre à chaque évaluation.
- Résultats élèves présentés sous forme de cartes colorées, avec note brute et équivalent sur 20, grille détaillée, progression visuelle par critère, niveaux de compétence et commentaire lorsqu’il existe.
- Bouton de repli de la barre latérale stylé dans les deux états ; menu replié centré sur les icônes, infobulles conservées, déconnexion masquée dans le menu replié (elle reste disponible dans le menu ouvert).
- CSS d’évaluation renforcé avec couleurs lisibles, focus visibles et repères distincts pour les niveaux de maîtrise.
- Historique consolidé dans ce fichier unique.

VALIDATIONS V20.7
- Syntaxe du JavaScript embarqué et de _all.js : OK.
- Suite de tests automatisés : 10/10 OK après assemblage.
- Recette manuelle complète sous Firefox/macOS : non réalisée.


AUDIT TECHNIQUE — MaClasse V20.8

CHANGEMENTS
- Barre latérale : suppression du bouton « Ouvrir l’espace élève » de l’espace enseignant. Le bouton « Se déconnecter » reste visible dans le menu ouvert et replié ; en mode replié, l’icône ↪ reste centrée et accessible avec une infobulle. Le clic ne déclenche plus l’ouverture de la palette de commandes.
- Résultats élèves : conservation de la présentation en cartes avec note sur son barème, équivalent sur 20, critères, descriptions, compétences et commentaire. L’organisation reprend les repères documentés d’École Directe (notes, moyennes, évaluations, compétences et appréciations), sans copier son interface.
- Sécurité d’affichage : les brouillons et évaluations dont la date de publication est future restent masqués côté élève.

VALIDATIONS V20.8
- Vérifications automatisées et syntaxe exécutées après assemblage ; recette visuelle manuelle Firefox/macOS non réalisée.

AUDIT TECHNIQUE — MaClasse V20.9

CHANGEMENTS
- Remplacement de la liste de cartes de résultats par un relevé tabulaire par période, regroupé par matière.
- Sélecteur de période basé sur les périodes configurées dans les paramètres (trimestre ou semestre).
- Chaque matière présente les évaluations cliquables et sa moyenne pondérée normalisée sur 20 ; la moyenne générale de la période est également affichée.
- Une note conserve son barème d’origine dans le relevé ; le barème est explicité lorsqu’il est différent de 20 et les coefficients différents de 1 sont affichés.
- La fenêtre de détail présente critères, points, descriptifs de niveaux, compétences, appréciation et conversion sur 20.
- Les résultats non publiés et les publications futures restent masqués.
- Renforcement CSS ciblé sur le bouton de déconnexion en état ouvert et replié.

VALIDATIONS V20.9
- Syntaxe du JavaScript embarqué : OK.
- Syntaxe de _all.js : OK.
- Tests automatisés hérités et test V20.9 : résultats consignés lors de la génération de l’archive.
- Recette visuelle Firefox/macOS : non réalisée.

AUDIT TECHNIQUE — MaClasse V20.10

CHANGEMENTS
- Rendus élèves : remplacement de la confirmation native JavaScript par une fenêtre intégrée à MaClasse, avec le titre du travail, l’échéance et la liste des fichiers avant envoi.
- Prévention des doubles envois : contrôle de l’existence d’un rendu déjà envoyé et vérification de l’état au moment de la confirmation.
- Distinction explicite entre « Évaluation » (travail de préparation/évaluation prévue à une prochaine séance) et « Évaluer le rendu (grille et note) » (le fichier remis lui-même est noté).
- Les rendus évalués sont reliés à l’évaluation et à la note de l’élève. Depuis le détail de la note, l’élève peut consulter le fichier rendu ; depuis la saisie des notes et la correction du rendu, le professeur peut ouvrir l’historique du fichier remis.
- Les rendus non évalués restent consultables dans le suivi sans création automatique d’une note.
- Bouton de déconnexion : couleurs et contraste adaptés aux variables du thème, en barre latérale ouverte et repliée.

VALIDATIONS V20.10
- Syntaxe JavaScript embarquée : OK.
- Syntaxe de _all.js : OK.
- Tests automatisés hérités : OK.
- Test V20.10 : confirmation locale, distinction des cas, accès à l’historique et contraste CSS vérifiés.
- Recette visuelle manuelle dans Firefox/macOS : non réalisée.


LIVRAISON V21.04 — REFONTE DE LA MESSAGERIE
- Présentation repensée en trois zones : navigation/dossiers, liste, lecture.
- Navigation et recherche intégrées, favoris par compte, dossiers personnels conservés.
- La refonte réutilise les contrôles d’accès et la persistance existants pour éviter une migration risquée des données.
- Recette visuelle réelle navigateur non effectuée dans cet environnement.


LIVRAISON V21.04 — RECONSTRUCTION DU MODULE DE MESSAGERIE
- Nouveau modèle autonome : messages individuels, références de fil, références de réponse et de transfert.
- État de boîte par utilisateur et par message : dossier, lu/non lu, favori.
- Nouvelle interface en trois panneaux : dossiers, liste, lecture.
- Répondre et répondre à tous créent un message distinct ; le fil est une vue calculée à partir de threadId.
- Transfert dans un nouveau fil, sans divulguer les destinataires CCI de la source.
- Pièces jointes via le service local d’upload existant.
- La première ouverture de la messagerie réinitialise l’ancien stockage de messagerie sans migration ; les autres données MaClasse restent conservées.
- Tests dédiés au modèle ajoutés. Les tests automatisés existants, les tests du modèle et les vérifications de syntaxe passent.
- Limite connue : la recette visuelle manuelle dans Firefox/macOS reste à faire ; le navigateur de test a bloqué l’ouverture de la page dans cet environnement.


AUDIT DE LIVRAISON — V21.04
===========================

- Le module actif est installé par `installMailV2104`; les anciennes vues ne sont plus les vues rendues pour `messages` et `studentMessages`.
- Le schéma `db.mailboxV2` passe en version 2 et initialise un stockage de messagerie neuf sans migration des conversations historiques.
- Les messages sont indépendants ; les fils sont des regroupements calculés par `threadId`.
- Les réponses créent un nouvel échange comprenant une copie du message source sans CCI et la réponse, avec référence `inReplyTo`/`copiedFrom`.
- Dossiers et lecture sont stockés par utilisateur et par message.
- Brouillons persistants avec pièces jointes ; dossiers personnels ; archive, corbeille, restauration et suppression masquée par compte.
- Sécurité de présentation : corps de message échappé avant rendu ; visibilité contrôlée avant lecture/réponse/transfert ; CCI non exposées aux destinataires.
- Tests automatisés exécutés à la livraison : voir les sorties de recette et le dossier `tests`.


CORRECTIF V21.05 (03/10/2026)
- Corrige le crash « messages is not defined » : le routeur appelle explicitement window.messages et window.studentMessages, définis par le nouveau module.
- Le test de rendu de la boîte enseignant utilise le point d’entrée public du module.
- Le test d’interface vérifie les nouveaux points d’entrée globaux.
- Validation : syntaxe JavaScript et suite de tests automatisés.

CORRECTIF V21.06 — 03/10/2026
- Compatibilité : les widgets historiques de l’espace élève appellent désormais les adaptateurs du nouveau modèle de boîte mail au lieu de dépendre de l’ancien tableau de conversations.
- Rédaction : l’éditeur riche commun à MaClasse est réutilisé. Le HTML est conservé pour brouillons/envois et assaini avant affichage ; les scripts, attributs d’événements et balises non permises ne sont pas conservés.
- Pièces jointes : réutilisation de cloudFileVisual pour les icônes et prévisualisation locale dans une modale des formats que le navigateur peut afficher.
- Validation : tests automatisés, test de régression V21.06 et syntaxe JavaScript. Pas de recette visuelle réelle Firefox/macOS.


---

## Source originale : `ETAT_V25.txt`

Contenu original conservé :

ÉTAT DE CONSTRUCTION — MaClasse V25.0.25 (candidat de stabilisation, 25/11/2026)

Base de travail indépendante issue de V24.2. La V24.2 d'origine n'est pas modifiée.

Corrections fonctionnelles antérieures conservées :
- Sérialisation des sauvegardes différées côté navigateur et verrouillage JSON côté serveur.
- Sauvegardes ZIP complètes de maclasse.json et data/uploads.
- Normalisation défensive des collections.
- Moyennes par matière normalisées sur 20 et limitées aux évaluations publiées.
- Filtrage des résultats, cours, devoirs et appels par publication/classe/groupe.
- Correctifs Cloud d'interface et de cohérence des suppressions.

Sécurité intégrée V25.0.1 à V25.0.7 :
- Authentification serveur pour les comptes direction et professeur.
- Sessions aléatoires côté serveur, cookie HttpOnly/SameSite=Strict, expiration glissante de 12 h.
- API données, PDF, Cloud, téléversements et téléchargements protégés par session.
- Changement obligatoire du mot de passe provisoire (12 caractères minimum).
- Migration transparente des anciens SHA-256 vers PBKDF2-HMAC-SHA256 (sel aléatoire, 310 000 itérations).
- Limitation des tentatives de connexion et contrôle Origin sur les requêtes mutantes.
- Réinitialisation réservée à la direction ; liste des comptes protégée contre les sauvegardes professeur.
- Contrôle canonique des chemins de fichiers ; traversées et liens symboliques sortants refusés.
- Contrôles Cloud côté serveur par propriétaire, classe et partages (lecture/modification), y compris sur les opérations physiques et les métadonnées.
- Les éléments Cloud ne peuvent pas être réattribués à un autre espace ou à un autre propriétaire par une sauvegarde professeur.
- Accès élève désactivé en attendant les comptes individuels et les autorisations côté serveur.
- API de données professeur limitée aux classes affectées ; sauvegardes fusionnées sans écraser les classes et comptes des autres utilisateurs.
- Messagerie privée (mailboxV2) filtrée côté serveur par expéditeur/destinataire/participant ; brouillons et états isolés par compte ; messages existants immuables dans les sauvegardes professeur.
- Pièces jointes non-Cloud accessibles uniquement si elles sont référencées dans les données visibles ou la messagerie autorisée ; suppression générique et dossiers de messagerie protégés.
- Sauvegardes optimistes : empreinte de révision SHA-256 liée au chargement ; les écritures basées sur une version périmée sont refusées en HTTP 409 plutôt que d’écraser les changements d’un autre onglet ou poste.
- Les sauvegardes sans révision sont refusées ; le client transmet la révision pour les sauvegardes et restaurations.
- Notes, lignes d’appel et rendus contrôlés contre les références d’élèves/cours hors périmètre.

Tests exécutés sur cette copie :
- 31/31 tests JavaScript réussis.
- 8 tests dédiés aux autorisations Cloud côté serveur réussis.
- 6 tests dédiés à la messagerie privée et aux pièces jointes côté serveur réussis.
- Scripts Python de régression, persistance et authentification HTTP réussis.
- Test HTTP supplémentaire : deux clients chargés sur la même révision ; le premier enregistre, le second reçoit HTTP 409 et ne peut pas écraser le premier.
- Test HTTP incluant migration PBKDF2, accès anonyme refusé, changement initial obligatoire, rôles, traversée de chemin et lien symbolique sortant.
- Compilation Python et vérification syntaxique JavaScript réussies.

BLOQUANTS AVANT ACCÈS AU RÉSEAU LOCAL :
- TLS/HTTPS pour protéger les identifiants et cookies sur le réseau.
- Vérifier et compléter le filtrage de chaque fonctionnalité métier et des documents selon les cas d’usage réels ; comptes élèves individuels toujours absents.
- Comptes élèves individuels sécurisés et accès parent éventuel.
- Transactions multi-collections plus fines et interface de résolution/récupération après conflit (la première protection anti-écrasement est maintenant en place).
- Recette Firefox complète et test réel de restauration de sauvegarde.

Le serveur écoute exclusivement sur 127.0.0.1. Ne pas définir MACLASSE_HOST=0.0.0.0 à ce stade. Ne pas exposer cette version au Wi-Fi/LAN.

V25.0.7 — restauration ZIP complète
- Une restauration complète de l'archive JSON + uploads est disponible via une API réservée à la direction.
- La restauration crée d'abord une sauvegarde de l'état courant, valide le ZIP et le JSON, rejette les chemins dangereux et remplace la base et les fichiers téléversés.
- L'interface propose l'import ZIP uniquement pour la direction ; l'import JSON reste distinct.
- Tests HTTP de rôle et tests de restauration/fichiers/archives malveillantes réussis.

Attention : cette étape améliore la capacité de restauration, mais ne constitue pas encore une recette de reprise après sinistre sur un poste séparé. Le serveur reste sur 127.0.0.1 tant que TLS et la recette complète des autorisations métier ne sont pas terminés.


CORRECTIF DE DURCISSEMENT APRÈS IMPORT — 12/11/2026
---------------------------------------------------
- La projection serveur des données professeur utilise désormais une liste blanche de référentiels explicitement partagés : settings, subjects, competencyLibrary, evaluationTemplates, evaluationCriteriaLibrary et métadonnées de schéma.
- Les nouvelles clés de premier niveau sont privées par défaut et ne sont pas transmises aux comptes professeur.
- Test de non-régression ajouté dans tests/test_v25_teacher_data_scope.py pour vérifier l'absence de fuite de collections inconnues et de configuration privée.
- Ajout de .gitignore pour data/maclasse.json, data/uploads/, data/backups/, .venv/ et les fichiers Python temporaires.
- Le fichier data/maclasse.json suivi par Git (qui ne contenait que les deux comptes provisoires) a été retiré du dépôt public. server.py recrée la base si elle est absente, puis initialise les comptes provisoires.
- Workflow .github/workflows/tests.yml ajouté pour lancer les tests JavaScript et Python sur push et pull request.

ÉTAT DES VALIDATIONS DE CE CORRECTIF
- Modification et test publiés sur main : oui.
- GitHub Actions : succès sur le commit f379a8c (run 43305047329).
- 31/31 tests JavaScript réussis ; 7/7 scripts Python exécutés avec succès.
- node --check _all.js : réussi ; python -m py_compile server.py : réussi.
- Le run comprend le nouveau test de non-divulgation des collections inconnues et des champs privés de settings.
- Recette visuelle Firefox/macOS : non réalisée.
- Version applicative conservée : V25.0.7 (correctif de sécurité incrémental, sans changement de numéro de version).

Commits : fe0b449 (serveur), f13eeda (test), 5e4b301 (workflow), 71fab97 (.gitignore), 5c84254 (retrait de la base locale).

- Complément : l'objet settings transmis aux professeurs est maintenant filtré champ par champ (rooms, termMode, terms, competencyLevels, courseAppearanceMigrationV205). Les autres champs, y compris toute future clé sensible, ne sont pas exposés.
- Test de régression étendu pour vérifier qu'un champ privé ajouté à settings n'est pas transmis.
- Commits complémentaires : ffaf34b (filtrage settings), f379a8c (test).


CORRECTIF DE CONFIDENTIALITÉ DES COMPTES PROFESSEURS — 12/11/2026
-----------------------------------------------------------------
- L'audit de GET /api/data a détecté que le profil du professeur connecté était transmis avec son empreinte passwordHash (et un éventuel ancien champ password).
- Même protégée par PBKDF2, une empreinte ne doit pas être exposée au navigateur : elle pourrait permettre des tentatives de cassage hors ligne.
- La projection professeur retire désormais passwordHash et password de son propre profil, tout en conservant les champs d'identité utiles à l'interface.
- Les sauvegardes professeur préservaient déjà les comptes côté serveur ; aucune modification de ce comportement.
- Test de non-régression ajouté : test_teacher_projection_never_exposes_password_material.
- Commits : fbaf4ff (serveur), f6f994b (test).
- GitHub Actions du lot : à vérifier après exécution ; aucune recette Firefox n'est revendiquée.


CORRECTIF D'AUTHENTIFICATION — RÉVOCATION DES SESSIONS
-----------------------------------------------------
- Constat : une session conservait son rôle et son identité en mémoire jusqu'à 12 h, même si le compte était supprimé ou désactivé dans la base.
- Correction dans Handler._session_user : relecture du compte courant à chaque requête authentifiée ; suppression de la session si le compte n'existe plus, est désactivé ou possède un rôle non autorisé ; actualisation des attributs de session depuis le compte courant.
- Test HTTP ajouté : après restauration d'une archive qui retire les comptes, les sessions admin/professeur préexistantes doivent recevoir HTTP 401.
- Premier run CI après modification du serveur : échec attendu du test ancien qui supprimait les comptes pendant le scénario avant de terminer ses vérifications. Test adapté pour conserver les comptes durant les vérifications normales puis tester la révocation après restauration. Le run du commit de test 7638d4f est réussi (GitHub Actions #43306000415). Les trois runs des mises à jour documentaires sont également réussis.
- Commits : ed26a79 (serveur), 7638d4f (test).
- Version applicative inchangée : V25.0.7.


POINT D'AUDIT À CORRIGER — AUTHENTICITÉ DES BULLETINS PDF
-------------------------------------------------------
- POST /api/bulletin-pdf génère le document à partir du JSON fourni par le navigateur.
- Le client ne transmet pas d'identifiant de bulletin ; le serveur ne vérifie donc ni l'enregistrement source, ni l'appartenance à une classe, ni l'état réel de publication.
- La mention « Bulletin publié officiellement » dépend actuellement des booléens/dates fournis par le client. Un client modifié peut donc faire produire un PDF qui affirme une publication non vérifiée.
- Il ne s'agit pas d'une lecture de données serveur non autorisée : le contenu PDF vient du corps envoyé par le client. Le risque concerne l'intégrité et l'authenticité du document.
- Correction réalisée : _all.js transmet bulletinId ; server.py vérifie l'existence du bulletin, la cohérence élève/classe et l'affectation du professeur à la classe. L'identité et le statut/date de publication proviennent de la base.
- Tests HTTP : bulletin inexistant = 404 ; bulletin d'une autre classe = 403.
- Limite restante : moyennes, statistiques, appréciations et compétences restent transmises par le navigateur ; les valeurs ne sont pas encore toutes recalculées depuis la base côté serveur.
- Statut : contrôle d'identité/périmètre/publication corrigé ; génération entièrement serveur encore nécessaire pour garantir le contenu.

CI des correctifs précédents : succès sur les commits serveur/test ; test de révocation des sessions validé par le run 43306000415.


COMPLÉMENT — CONTRÔLE DU STATUT POUR L'EXPORT PDF
------------------------------------------------
- L'API refuse désormais un bulletin non validé, non publié ou sans date de publication enregistrée.
- L'identité de l'élève, la classe, la période et la date de publication sont lues depuis la base serveur ; le professeur doit être affecté à la classe.
- Test HTTP : refus d'un bulletin non publié, refus d'un bulletin hors périmètre et génération acceptée pour un bulletin validé/publié dans le périmètre.
- Commits : 508df20 (serveur), 1a011c0 (test).
- Limite restante : moyennes, statistiques, appréciations et compétences PDF restent encore fournies par le client. Il faut les recalculer ou les vérifier côté serveur avant de certifier l'intégrité complète du document.
- CI à confirmer.


CORRECTIF CLOUD — REFUS PAR DÉFAUT HORS CLOUD
---------------------------------------------
- _cloud_path_allowed refusait auparavant les chemins invalides, mais autorisait par erreur les chemins valides situés hors cloud/.
- Les chemins non Cloud sont maintenant refusés par défaut.
- Test ajouté pour general/ et lessons/.
- Commits : 5ff9364 (serveur), 4c92f9c (test).
- CI réussie : run 43306325378.

CORRECTIF EXPORT PDF — CONTRÔLE DU BULLETIN SOURCE
-------------------------------------------------
- Le client transmet bulletinId ; le serveur retrouve le bulletin et vérifie sa cohérence avec l'élève et la classe.
- Un professeur ne peut générer le PDF que pour une classe qui lui est affectée ; un bulletin inexistant renvoie 404, un bulletin hors périmètre 403.
- Le nom de l'élève, la classe, la période et le statut/date de publication sont déterminés depuis la base, et non depuis le JSON client.
- Limite : notes, moyennes, appréciations et compétences restent fournies par le client. Ne pas considérer le PDF comme preuve d'authenticité complète avant génération serveur de ces valeurs.
- Commits : a661d36, 5713ba6, 59bb9cf.
- CI réussie : run 43306723332.
- Version inchangée : V25.0.7.


AUTORISATIONS BULLETINS — PROTECTION DU PROFESSEUR PRINCIPAL
----------------------------------------------------------
- La fusion serveur des sauvegardes professeur préserve désormais validated/validatedAt/published/publishedAt et overall si le professeur n'est pas PP de la classe.
- Un bulletin déjà publié est conservé intégralement ; un professeur ne peut pas le modifier via /api/save.
- Les appréciations par matière restent modifiables dans le périmètre classe ; le contrôle précis de l'affectation matière doit encore être audité.
- Tests ajoutés : non-PP ne peut pas valider/publier/modifier overall ; bulletin publié immuable pour un professeur.
- Commits : 2ee67c0 (serveur), 3705b90 (tests), 1b8514e (isolation des fixtures de test).
- CI réussie : run 43307416629.


VALIDATION DU CONTRÔLE PP — CI
-----------------------------
- Le premier test a révélé un défaut du test : la projection de données partageait les objets de la fixture, ce qui modifiait artificiellement la source avant la fusion. La fixture est maintenant copiée en profondeur pour simuler le transfert HTTP JSON.
- CI complète réussie sur 1b8514e : run 43307416629.


CORRECTIF MESSAGERIE — CONFIDENTIALITÉ CCI
-------------------------------------------
- Les destinataires d'un message ne reçoivent plus la liste des autres destinataires BCC/CCI ; l'expéditeur conserve la liste complète.
- Test dédié validé par CI : run 43307062966.
- Commits : 20dedb6 (serveur), 1db7f79 (test).

RENFORCEMENT BULLETINS — IDENTITÉ ET SUPPRESSION
------------------------------------------------
- La fusion serveur conserve studentId/classId/termId d'un bulletin existant ; une sauvegarde professeur ne peut pas déplacer un bulletin vers un autre élève ou une autre classe.
- Un bulletin publié reste dans la base même si le client l'omet de sa sauvegarde ; seule la direction peut le modifier/supprimer via une sauvegarde administrative.
- Tests dédiés : identité non modifiable et suppression d'un bulletin publié refusée.
- Commits : 955b904 (serveur), 575403d (tests).
- CI réussie : run 43307614719.
- Contrôle matière réalisé : les appréciations sont limitées aux matières listées dans teachers[].subjects, côté interface et côté serveur. Limite : cette liste est globale au professeur, pas affectée par classe.


ÉVALUATIONS — CLOISONNEMENT PAR CLASSE EXACTE
--------------------------------------------
- L'identité classId d'une évaluation existante ne peut plus être modifiée par une sauvegarde professeur.
- Les notes ne sont conservées que si l'élève appartient à la classe exacte de l'évaluation (pas uniquement à une autre classe également attribuée au professeur).
- Tests ajoutés pour le déplacement d'une évaluation et l'injection d'une note d'un élève d'une autre classe.
- Commits : d4fe63f (serveur), 077d30f (tests). CI à confirmer.
- Le schéma ne fournit pas actuellement de lien professeur/matière suffisamment explicite ; les permissions restent à ce stade basées sur les classes attribuées.


VALIDATION CI — ÉVALUATIONS
--------------------------
- Le premier test de déplacement d'évaluation remplaçait à tort toutes les notes, y compris la note légitime. Le test a été corrigé pour conserver la note d'origine et ajouter une injection d'élève d'une autre classe.
- Suite complète JavaScript + Python réussie sur 6075e94 : run 43308092780.


PRÉSENCES ET TRAVAUX RENDUS — CONTRÔLES INTERCLASSE
--------------------------------------------------
- Présences : les lignes imbriquées sont filtrées sur les élèves de la classe exacte de la feuille.
- Travaux rendus : séance obligatoire dans une classe affectée au professeur ; l'élève doit appartenir à la classe de cette séance ; une incohérence conserve l'enregistrement précédent.
- Pour évaluations, présences et travaux rendus, le contrôle de périmètre d'un enregistrement existant se base sur sa classe déjà stockée, pas sur une classe falsifiée dans la requête.
- Tests ajoutés contre l'injection d'élèves interclasse.
- Suite complète JS + Python réussie sur 3fe990d : run 43308354602.


FICHIERS TÉLÉVERSÉS — CSP ET PROTECTION XSS
------------------------------------------
- Les réponses /data/uploads/ incluent désormais une CSP dédiée : sandbox, default-src 'none', images locales/data et styles inline autorisés.
- Un document HTML importé ne peut donc pas exécuter de script dans l'origine de l'application.
- Test HTTP de non-régression sur un fichier HTML téléversé.
- Les travaux rendus existants conservent leur élève et leur séance d'origine ; les réassociations falsifiées sont rejetées.
- CI complète JS + Python réussie sur 91db610 : run 43308611502.


BULLETINS — DROITS PAR MATIÈRE
-----------------------------
- Le serveur filtre maintenant subjectData selon les matières listées dans la fiche du professeur (teachers[].subjects).
- La fonction d'interface canEditBulletinSubject manquante a été rétablie ; l'interface et le serveur utilisent la même liste de matières.
- Un professeur ne peut ni modifier une appréciation d'une matière non attribuée, ni ajouter une nouvelle matière à son bulletin.
- Commits : 8437b3a (serveur), 6db9412 (interface), be30a63 (test).
- CI réussie : run 43308130018.
- Limite : affectation des matières par classe non modélisée.

PROJECTION — COHÉRENCE DE CLASSE DES DONNÉES IMBRIQUÉES
-------------------------------------------------------
- Notes et présences filtrées selon la classe exacte de l'évaluation/feuille.
- Bulletins, pièces jointes et travaux rendus filtrés lorsque les identifiants élève/classe/séance ne concordent pas.
- Les liens élève/séance/classe d'un rendu existant sont préservés depuis la base lors d'une sauvegarde professeur.
- Commits : 67451c8, f9fc214, 91db610.
- CI réussie : run 43308611502.

 
BULLETINS PDF — SOURCE DE VÉRITÉ SERVEUR
---------------------------------------
- La route /api/bulletin-pdf exige un bulletin existant, validé et publié, un élève réellement rattaché à la classe du bulletin, et une classe accessible au professeur.
- Le navigateur ne fournit plus que bulletinId ; les moyennes, statistiques, appréciations, compétences, présences, identité, classe et période envoyées par le client sont ignorées.
- Le serveur reconstruit le contenu du PDF à partir de la base : résultats par matière, moyennes de classe, appréciations, moyenne générale, compétences et absences/retards.
- Tests couvrant les données canoniques et une tentative de falsification des valeurs côté client.
- CI complète JS + Python réussie : run 43309419995, commit e1af32a.
- Version conservée : V25.0.7 (correctif incrémental).


SESSIONS — RÉVOCATION APRÈS CHANGEMENT DE MOT DE PASSE
-----------------------------------------------------
- Après modification du mot de passe, toutes les autres sessions du même compte sont supprimées ; la session courante reste valide.
- Test HTTP de non-régression : session secondaire refusée (401) après rotation, session courante toujours autorisée.
- CI complète JS + Python réussie : run 43309742779, commits serveur 96c4c5c et test 3001ed2.


BULLETIN PDF — CONTRÔLE DE PÉRIMÈTRE RENFORCÉ
--------------------------------------------
- Moyenne générale recalculée à partir des seules évaluations de la classe du bulletin.
- Absences et retards comptabilisés uniquement depuis les feuilles de présence de cette même classe.
- Test avec données interclasses mal rattachées : note et absence étrangères ignorées.
- CI complète JS + Python réussie : runs 43310140332 et 43310145774.


SAUVEGARDE PROFESSEUR — IMMUTABILITÉ DES RATTACHEMENTS
-----------------------------------------------------
- Le périmètre d'un enregistrement existant est déterminé à partir de sa version déjà stockée, pas des liens fournis par le navigateur.
- Les liens de classe sont préservés pour élèves, emploi du temps, séances et présences ; les liens classe/élève/séance sont préservés pour les pièces jointes ; les protections précédentes restent actives pour évaluations, bulletins et rendus.
- Tests interclasses avec un professeur affecté aux deux classes.
- CI complète JS + Python réussie : runs 43310380105 et 43310387814.


INSTALLATION FEDORA — PREMIÈRE PRÉPARATION
-----------------------------------------
- Ajout d'un installateur Fedora créant un environnement Python isolé et installant requirements.txt.
- Ajout d'un lanceur Fedora dédié, conservant l'écoute localhost-only.
- Guide INSTALLATION_FEDORA_V25.txt ajouté.
- Syntaxe bash -n intégrée à la CI.
- Limite : installation réelle et mesure des performances sur le PC Fedora (4 Go RAM) pas encore exécutées.


DÉMARRAGE — BLOCAGE DES ADRESSES RÉSEAU
--------------------------------------
- Le serveur refuse maintenant de démarrer si MACLASSE_HOST n'est pas 127.0.0.1, localhost ou ::1.
- La tentative de bind sur 0.0.0.0, une IP LAN ou :: se termine par une erreur de sécurité (code de sortie 2), au lieu de lancer une écoute réseau avec un simple avertissement.
- Test dédié ajouté ; CI en cours de validation sur commits 75207b5 et f1fa7d0.


VALIDATION CI — INSTALLATION FEDORA ET DÉMARRAGE LOCAL
-----------------------------------------------------
- Syntaxe bash des scripts Fedora contrôlée dans le workflow.
- Tests complets JavaScript + Python réussis après le verrouillage localhost : run 43310801471 (commit f1fa7d0).
- Workflow complet incluant les scripts Fedora réussi : run 43310869800 (commit ebb910a).
- Documentation complète validée : run 43310879305 (commit 8ccbba9).


Audit messagerie/conversations — 12/11/2026
- Conversations historiques : propriétaire, classe, participants, titre, date et messages préservés depuis la base. Seuls les états personnels du professeur (lecture/archivage/suppression/favori/classement) peuvent évoluer.
- Messagerie V2 : `sharedWith` est maintenant soumis aux mêmes contrôles de destinataires que `to`, `cc` et `bcc`; pas de partage vers un élève hors des classes du professeur.
- Tests ajoutés ; validation CI à vérifier sur les derniers commits.


CIBLE DE DÉPLOIEMENT CORRIGÉE — 12/11/2026
- La machine cible est un Mac Apple Silicon M5 sous macOS 27. Fedora n'est pas la cible d'installation.
- Les lanceurs macOS vérifient arm64 natif, Python >= 3.10, installent les dépendances dans .venv et ouvrent Firefox si présent.
- La syntaxe des lanceurs est vérifiée en CI ; l'installation réelle et le parcours Firefox doivent encore être effectués sur le Mac cible.
- Ne pas présenter la V25 comme prête pour un réseau local ou un usage scolaire réel tant que les contrôles d'autorisation et la recette complète ne sont pas validés.


NOTE DE CONTINUITÉ — 12/11/2026
Les anciennes notes d'installation Fedora ci-dessus sont historiques et ne correspondent plus à la machine cible. Elles sont remplacées par la préparation Mac Apple Silicon M5 / macOS 27 décrite dans INSTALLATION_MAC_V25.txt.


VALIDATION MACOS — 12/11/2026
- Suite complète exécutée sur runner macos-latest : syntaxe des lanceurs, JavaScript, compilation Python, 7 scripts Python. Résultat : succès, run 43313321068.
- Découverte et correction d'un écart de chemin sur macOS (/var -> /private/var) affectant les contrôles Cloud et les pièces jointes.
- Test de non-régression ajouté pour la racine réelle du stockage uploads.
- Les deux lanceurs .command ont le mode Git 100755.
- À faire sur le matériel cible : installation et test interactif Firefox sur le Mac M5 sous macOS 27.


MISE À JOUR — RÉSEAU PRIVÉ EXPÉRIMENTAL ET ESPACE ÉLÈVE — 12/11/2026
- Le lancement local habituel reste sur 127.0.0.1. Un lanceur séparé Lancer-MaClasse-Reseau.command permet un essai sur une IPv4 privée précise, après changement des mots de passe initiaux direction et enseignant.
- Le mode LAN utilise HTTP non chiffré : réseau privé isolé et données fictives uniquement. Pas de réseau de l'établissement, pas de redirection de ports, pas d'usage scolaire réel. HTTPS et audit complet du déploiement restent à faire.
- Première tranche de comptes élèves : création par la direction, mot de passe PBKDF2 côté serveur et changement obligatoire à la première connexion.
- Le portail élève donne accès à sa fiche limitée, sa classe, son emploi du temps en lecture seule, ses séances/devoirs, ses résultats publiés, ses absences et ses bulletins publiés/validés. Les rendus peuvent être téléversés uniquement dans le dossier propre à l'élève ; le serveur protège notes, fiche, autres élèves et corrections.
- Messagerie élève et Cloud élève restent désactivés jusqu'à audit dédié. Les comptes élèves sont encore une première tranche, pas une version complète.
- CI Ubuntu + macOS Apple Silicon réussie : run 43318282845. Les scripts .command sont en mode Git 100755.
- Restent à faire : test physique sur le Mac M5/macOS 27, test réel du second PC sur la box privée, test Firefox complet, audit RBAC global, messagerie/Cloud élève, HTTPS et validation avant données réelles.


MISE À JOUR — V25.0.15 — COMPTES ÉLÈVES CANONIQUES ET MATIÈRES ENSEIGNANTS — 13/11/2026
- La fiche élève porte maintenant les identifiants de connexion, l'empreinte PBKDF2, l'état d'accès et le changement obligatoire du mot de passe provisoire : aucun compte élève séparé n'est ajouté à users[].
- La connexion, les sessions, le changement de mot de passe, la réinitialisation et l'activation/désactivation consultent et modifient cette fiche canonique.
- Un professeur peut inscrire un élève dans une de ses classes ; la sauvegarde n'affiche le succès qu'après confirmation serveur.
- Les enseignants peuvent de nouveau modifier librement leurs matières depuis leur profil.
- Les anciennes sauvegardes qui séparent fiche élève et compte ne sont pas migrées : recette prévue sur base neuve.
- CI complète Ubuntu + macOS Apple Silicon réussie pour le code : tests JavaScript, compilation Python, tests HTTP et tests Python.
- À faire avant validation utilisateur : recette manuelle dans Firefox sur Mac, création d'élève depuis l'espace professeur, attribution du code provisoire, première connexion élève et changement du mot de passe.
- Le mode réseau local expérimental reste hors périmètre de cette correction et n'est pas déclaré prêt pour des données réelles.


MISE À JOUR DE SYNCHRONISATION — 25/11/2026 — V25.0.25 (candidat)
- Le lot de stabilisation V25.0.25 aligne les marqueurs applicatifs et VERSION.txt sur cette version.
- Le gestionnaire vérifie désormais les tailles et digests SHA-256 de l'API GitHub pour le manifeste et l'archive lorsqu'ils sont exposés ; la vérification SHA-256 du manifeste reste obligatoire pour l'archive téléchargée.
- Ces digests sont des contrôles d'intégrité fournis par GitHub et ne remplacent pas une signature Ed25519 ou une attestation de provenance vérifiée par le client. La signature éditeur reste un point ouvert.
- La suite macOS contient un parcours d'installation/rollback launchd + HTTPS et un test de migration d'une installation existante vers le service supervisé ; le fixture de migration est maintenant V25.0.19.
- CI GitHub Actions #1573 réussie : Linux, macOS/launchd et Firefox réel. Aucune recette sur le Mac physique, le PC Fedora ou le Wi-Fi réel n'est revendiquée ici.
- Le redémarrage automatique du service macOS lors d'un changement d'adresse DHCP n'est pas encore implémenté. Réserver une IP au niveau du routeur et redémarrer le service après modification demeure la mesure de précaution.


MISE À JOUR — SUPERVISION DHCP ET REBINDING HTTPS — 25/11/2026
- Ajout de network_supervisor.py, commun au service systemd Linux, au service launchd macOS et au lanceur réseau manuel macOS.
- Surveillance toutes les cinq secondes de l'adresse IPv4 privée de l'interface par défaut. En cas de changement, le serveur HTTP est arrêté proprement, le certificat serveur est renouvelé pour la nouvelle IP sous la même autorité locale, puis le listener HTTPS est redémarré.
- En cas de perte de l'interface ou de l'adresse, le listener est fermé ; le superviseur attend le retour du réseau avant de rouvrir l'accès. Les données, la CA et la clé privée du serveur restent dans le stockage persistant.
- Le script de configuration des certificats respecte maintenant MACLASSE_DATA_DIR.
- Tests automatisés ajoutés pour macOS/Linux, changement d'adresse, perte/retour du réseau et certificat SAN/expiration. La recette Wi-Fi sur les appareils physiques reste à effectuer.


MISE À JOUR — AUDIT PRODUIT ET SYNCHRONISATION APPLICATIVE — 25/11/2026
- Un dossier dédié docs/AUDIT_PRODUIT_V25.md inventorie les modules actifs Direction/Professeur/Élève et le plan de recette : navigation, apparence claire/sombre, EDT, évaluations, bulletins, messagerie, séances/devoirs, Cloud, appels, profils et rationalisation.
- La messagerie active est le moteur V21.04 Mail V2 via window.messages et window.studentMessages. Les tests de cloisonnement, d'identité, d'état par boîte et de pièces jointes existent ; la recette avec un compte élève sur l'installation de référence reste ouverte. Un ancien écran placeholder est du code mort remplacé par le point d'entrée actif.
- Le moteur actif d'Évaluations est V21.17 ; plusieurs anciennes définitions restent dans _all.js. Bulletins V21.09 est également actif. Une consolidation future devra conserver les parcours réellement utilisés.
- Le thème est appliqué via html[data-mc-theme]. Les règles prefers-color-scheme relevées dans le document d'impression du bulletin ne pilotent pas l'interface principale ; la parité visuelle complète n'est pas encore vérifiée.
- Ajout de GET /api/sync-status (révision uniquement, sans données métier) et d'une surveillance globale du navigateur toutes les cinq secondes ; la récupération attend la fin des saisies locales.
- Ajout d'une fusion à trois versions des changements indépendants et d'un état de conflit explicite. Les tests dédiés et la régression Firefox doivent encore être stabilisés.
- Le test Firefox révèle un défaut de propagation d'un créneau ajouté à distance vers l'EDT élève. Cette anomalie est conservée comme point ouvert ; aucune affirmation de synchronisation générale validée.
- Les correctifs de supervision DHCP, d'intégrité des mises à jour et de migration V25.0.19 restent conservés sur la même branche.


MISE À JOUR — RENDU EDT ÉLÈVE — 25/11/2026
- Diagnostic Firefox : l'endpoint de révision et la lecture serveur fonctionnent ; le modèle élève contient le créneau Sciences ; recurring(), dayOcc() et studentScheduleOcc() le renvoient ; studentSchedule() et scheduleWeek() produisent le HTML attendu.
- Le DOM de .scheduleCalendarSurface restait cependant sur l'ancien HTML et ne contenait aucun élément du nouveau créneau. Le défaut était donc un rendu navigateur obsolète, et non un problème de projection serveur ou de récurrence.
- Correction candidate : toute nouvelle révision adoptée déclenche maintenant render() lorsque l'écran ne contient pas de saisie locale active, même si le JSON local est déjà égal au payload reçu.
- Un test unitaire couvre maintenant précisément le cas modèle déjà identique / DOM périmé. Résultat CI du dernier commit à confirmer ; aucune clôture définitive tant que Firefox réel ne passe pas.
- La suite navigateur inclut un smoke pass des 16 pages enseignant et des vérifications du thème manuel sombre sous OS clair et clair sous OS sombre ; l'audit visuel détaillé reste ouvert.


---

## Source originale : `TESTS_V24_1.txt`

Contenu original conservé :

Recette locale effectuée dans l’environnement de construction
=============================================================
OK : compilation Python de server.py, router_server.py et test_v241_router_integration.py.
OK : tests/test_v240_aria_core.py — homework upsert, update de séance, suppressions, conflits et dates.
OK : tests/test_v241_router_integration.py — contrat de réponse routeur, rejet des extensions invalides, fallback hors ligne.
Tests JavaScript : 30 réussis, 2 échecs historiques.
Échecs historiques :
- test_v204_coherence.js attend une ancienne structure de navigation antérieure à V24.
- test_v221_local_ai.js attend un comportement de modèle local antérieur à V24.
Ces deux échecs sont cohérents avec les limites documentées dans NOTES_V24_0.txt.
Non vérifié dans cet environnement : chargement MLX réel, car MLX nécessite un Mac Apple Silicon et le modèle de base doit être téléchargé au premier lancement.


