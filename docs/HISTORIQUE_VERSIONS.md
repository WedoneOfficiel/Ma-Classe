# Historique des versions MaClasse

> Registre historique consolidé le 25 novembre 2026. Les contenus ci-dessous sont repris intégralement des fichiers sources indiqués ; ils sont conservés à titre de mémoire de version et ne constituent pas tous des procédures encore applicables. Pour l'état actuel, consulter le [README](../README.md), le [registre des bugs](../REGISTRE_BUGS_V25.md) et les guides actifs de ce dossier.

## Candidat V25.1.0 — stabilisation, sécurité et suivi de classe (25/11/2026)

**Statut : candidat non publié**, porté par la PR #13. La CI complète #1793 est verte (Linux, macOS Apple Silicon et Firefox réel). Les recettes physiques, le provisionnement de la clé éditeur et la publication restent à effectuer.

### Stabilisation et sécurité
- Renforcement du gestionnaire de mises à jour : verrous d'installation, prévention des processus concurrents, sauvegardes atomiques, contrôle des services et rollback plus sûr.
- Supervision réseau Linux/macOS : fermeture du listener en cas de perte réseau, renouvellement du certificat serveur lors d'un changement d'IPv4 privée et redémarrage contrôlé.
- Signature Ed25519 détachée des manifestes, vérification côté client et tests du signataire. Le code est prêt ; la clé publique de production et le secret GitHub Actions restent à provisionner.
- Durcissement XSS, identifiants, pièces jointes, téléversements, tailles de requêtes et permissions des parcours élèves/enseignants.
- Corrections de la messagerie élève, des bulletins PDF, de la publication des notes, des affectations et remplacements enseignants, de l'emploi du temps et des thèmes.

### Évolution fonctionnelle et interface
- Nouvelle vue **Suivi de classe** pour la Direction et les enseignants autorisés : effectif, absences et retards sur 30 jours, travaux non rendus, évaluations publiées, échéances à venir et accès aux fiches élèves.
- Les enseignants non PP sont limités aux matières accessibles par leurs affectations ; les professeurs principaux disposent d'une vue transversale de leur classe. Aucun classement ni score de risque automatique.
- Correction du contexte Cloud : passage possible vers les espaces personnels et partagés après consultation d'une classe, sans perdre le contexte lorsqu'on reste dans l'espace Classe.
- Autorisation serveur et tests dédiés du nouveau fichier JavaScript du suivi de classe.

### Validation et réserves
- Workflow #1793 : 3/3 jobs réussis, dont installateur Linux, installateur macOS Apple Silicon, launchd réel, tests Python/JavaScript et Firefox réel avec captures clair/sombre.
- La migration doit encore être répétée sur une copie représentative des données réelles.
- La recette réseau multi-appareils doit encore être réalisée sur le Mac, le PC Fedora et les appareils clients.
- La paire Ed25519 permanente et le secret `MACLASSE_RELEASE_SIGNING_KEY_B64` doivent être provisionnés avant toute release.

## Journal V25

Source : `CHANGELOG_V25.txt` (contenu conservé intégralement).

MaClasse V25.0.25 — finalisation des parcours élèves

- La liste des enseignants joignables depuis la messagerie élève est maintenant alignée sur les droits réellement accordés côté serveur : titulaires, co-enseignants, enseignants des séances et affectations actives.
- Les comptes élèves utilisent directement la liste de destinataires filtrée par le serveur, sans la réduire une seconde fois aux seuls titulaires de classe.
- Les couleurs de matières choisies par un professeur sont désormais persistées par la fusion serveur, uniquement pour les matières qu'il enseigne ; les paramètres globaux restent protégés.
- La grille de l'emploi du temps applique désormais une vraie surface sombre dans le thème sombre au lieu de conserver son dégradé blanc, tout en gardant la surface claire en thème clair.
- L’export PDF accepte un bulletin dont la publication et la validation sont établies même si l’ancien enregistrement ne possède pas d’horodatage de publication ; les contrôles d’identité, de classe et de rôle restent appliqués.
- L’espace Résultats distingue l’état officiel du bulletin de la présence éventuelle d’une date d’affichage.
- Ajout de tests de projection des enseignants accessibles et de validation du statut officiel des bulletins.
- Ajout de la signature détachée Ed25519 du manifeste de mise à jour, avec vérification par clé publique épinglée et provisionnement du secret éditeur documenté.
- Validation CI complète #1759 sur Linux, macOS Apple Silicon et Firefox réel, incluant la signature et le démarrage HTTPS sous launchd.

### Compléments de stabilisation et de finition — 25/11/2026

- Accès central « Remplacements & co-enseignement » ajouté à l'emploi du temps, avec filtres par classe et recherche matière/jour/horaire ; les permissions restent contrôlées créneau par créneau.
- Message de confidentialité Administration actualisé : les messages, pièces jointes et ressources élève sont filtrés côté serveur au lieu d'être présentés comme désactivés.
- Gestion des anomalies, guide d'installation, index documentaire et archives historiques réorganisés sans perte du contenu des notes V21.
- CI complète #1747 verte sur Linux, macOS Apple Silicon et Firefox réel. Ce résultat valide les tests automatisés, pas les recettes physiques ni la signature indépendante de la release.

MaClasse V25.0.23 — supervision des mises à jour Linux et macOS

- Ajout d’un gestionnaire de mises à jour stable fondé sur les releases GitHub et un manifeste vérifié par SHA-256.
- Préparation isolée de chaque version et environnement Python dédié, sans écraser l’installation active.
- Supervision des services utilisateur via systemd sous Linux et launchd sous macOS.
- Ajout du pilotage des mises à jour : vérification, préparation, installation, programmation et annulation.
- Sauvegarde avant bascule, contrôle de santé HTTPS et retour automatique à la version précédente en cas d’échec.
- Protection contre les installations concurrentes et séparation des données utilisateur du code applicatif.

MaClasse V25.0.18 — stabilisation de l’EDT, de l’espace élève et de la maintenance

- Correction du plantage de l’emploi du temps élève causé par une variable de motif non définie.
- Réparation de la structure HTML des pages Emploi du temps et Séances & leçons côté élève : le contenu n’est plus injecté dans la barre d’actions du titre.
- Harmonisation du rendu semaine/jour élève avec le moteur de calendrier commun, sur les sept jours.
- Navigation adaptée au mode affiché : jour, semaine ou mois.
- Actualisation automatique des données partagées toutes les cinq secondes sur les pages d’emploi du temps et de séances, sans écraser une saisie en cours ni un formulaire ouvert.
- Messages d’erreur de téléversement plus explicites et sauvegarde confirmée des pièces jointes et des rendus élèves.
- Envoi d’un devoir uniquement après confirmation de la sauvegarde serveur.
- Commandes de mise à jour macOS et Linux renforcées : sauvegarde préalable de data/ (y compris les fichiers téléversés), vérification des versions et contrôles après mise à jour.
- Retour automatique au commit précédent et réinstallation des dépendances précédentes si une validation post-mise-à-jour échoue.

MaClasse V25.0 — première base de correction

- Création d'une copie de travail indépendante de V24.2.
- Version serveur alignée sur V25.0.0.
- Sérialisation des sauvegardes navigateur pour éviter les requêtes concurrentes.
- Verrouillage des écritures JSON côté serveur et fichiers temporaires uniques.
- Sauvegardes ZIP complètes incluant maclasse.json et data/uploads, en plus des JSON historiques.
- Normalisation défensive des collections schedule, bulletins, attachments, etc.
- Moyennes par matière calculées sur 20 via le moteur d'évaluation et limitées aux notes publiées.
- Résultats élèves filtrés par publication, classe et groupe.
- Accès aux cours et devoirs de sous-groupe filtré strictement.
- Appels par cours filtrés selon le groupe du créneau.
- Correction du test de mode d'appel course/hour.
- cloudCanWrite dédoublonnée et restreinte à la propriété/aux partages explicites côté interface ; contrôle serveur encore à implémenter.

Sécurité : le serveur reste lié à 127.0.0.1. L'API historique n'a pas encore
d'authentification serveur complète. Ne pas exposer la V25 au LAN ou à Internet
avant la livraison du lot Sécurité.


V25.0.1 — premier lot Sécurité serveur
- Authentification professeur/direction vérifiée par le serveur Python.
- Sessions serveur aléatoires en mémoire, cookie HttpOnly et SameSite=Strict (expiration 12 h).
- API de données, PDF, Cloud et fichiers protégées par une session authentifiée.
- Comptes initiaux créés côté serveur ; changement obligatoire du mot de passe provisoire (12 caractères minimum).
- Limitation des tentatives de connexion (10 essais / 5 min / IP).
- Réinitialisation réservée à la direction ; les professeurs ne peuvent pas modifier la liste des comptes.
- Contrôle d'origine des requêtes mutantes, en-têtes de sécurité et limites de taille des requêtes/fichiers.
- Accès élève temporairement désactivé : les comptes élèves individuels et le filtrage des données côté serveur restent à développer.
- Écoute toujours limitée à 127.0.0.1 ; LAN non activé tant que TLS, hachage de mots de passe renforcé et autorisations par classe/rôle ne sont pas finalisés.


V25.0.2 — renforcement des identifiants et du stockage Cloud
- Migration transparente des mots de passe SHA-256 historiques vers PBKDF2-HMAC-SHA256 avec sel aléatoire de 16 octets et 310 000 itérations lors de la première connexion.
- Les nouveaux mots de passe sont désormais enregistrés directement avec PBKDF2 salé.
- Vérification du mot de passe actuel compatible avec les comptes historiques et migrés.
- Résolution canonique des chemins d’uploads ; rejet des traversées de répertoires et des liens symboliques qui sortent du stockage.
- Contrôles HTTP ajoutés pour les chemins malveillants et les liens symboliques.


V25.0.3 — autorisations Cloud côté serveur
- Contrôle serveur de l'accès aux espaces personnels : un professeur ne peut accéder qu'à son propre espace, sauf partage explicite.
- Contrôle des espaces classe/groupe selon les classes affectées au profil professeur.
- Application des droits de partage lecture/modification, y compris sur les dossiers parents.
- Vérification des opérations Cloud de création, téléversement, renommage, déplacement, copie et suppression.
- Les suppressions/renommages physiques exigent désormais un élément Cloud connu dans les métadonnées ; impossible de viser directement une racine de stockage.
- Les sauvegardes professeur ne peuvent plus forger un propriétaire, déplacer un élément dans l'espace d'un autre compte ou modifier les droits d'un fichier partagé sans en être propriétaire.
- Ajout de tests unitaires sur l'isolation personnelle, les classes, les partages lecture/édition et les tentatives de falsification.


V25.0.4 — cloisonnement des données scolaires par professeur
- L'API /api/data renvoie désormais une projection limitée aux classes affectées au professeur connecté.
- Les élèves, cours, évaluations, appels, bulletins, pièces jointes et rendus hors périmètre ne sont plus transmis à cette session.
- Les notes et lignes d'appel imbriquées sont filtrées individuellement par élève autorisé.
- La sauvegarde professeur fusionne uniquement les collections et enregistrements de son périmètre ; les classes, comptes, profils des collègues, matières, paramètres globaux et journaux de direction sont conservés côté serveur.
- Les suppressions dans la projection ne suppriment plus les données des autres classes.
- Les créations avec une classe non attribuée et les références à des élèves/cours hors périmètre sont ignorées ou refusées.
- Ajout de tests de projection, fusion sans écrasement et injection de références inter-classes.


V25.0.5 — Cloisonnement messagerie et pièces jointes
- Projection serveur de mailboxV2 : un professeur ne reçoit que les messages où il est expéditeur, destinataire ou participant explicitement partagé.
- Brouillons, dossiers et états de lecture/favoris limités à la boîte du professeur connecté.
- Fusion des sauvegardes messagerie : messages envoyés immuables, ajout réservé à l'identité connectée, destinataires élèves limités aux classes affectées et conservation des données des collègues.
- Téléchargement des pièces jointes non-Cloud conditionné à leur référence dans les données visibles ou dans la messagerie autorisée.
- Suppression générique limitée aux fichiers référencés et autorisés ; les suppressions Cloud restent sur leur API dédiée.
- Téléversement dans les dossiers de messagerie d'un autre professeur refusé ; accès en écriture à la racine Cloud contrôlé selon le propriétaire.


V25.0.7 — Protection contre les sauvegardes concurrentes
- Chaque lecture de /api/data renvoie une empreinte SHA-256 de la version exacte de la base.
- Chaque sauvegarde /api/save doit fournir cette version via If-Match.
- Une sauvegarde issue d'une version dépassée est refusée avec HTTP 409 (REVISION_CONFLICT), sans écraser les données plus récentes.
- Une sauvegarde sans jeton de version est refusée avec HTTP 428.
- Le client conserve la révision reçue et la transmet lors des sauvegardes ordinaires et des restaurations.
- En cas de conflit, le message indique de recharger les données avant de continuer.
- La révision est calculée sous verrou, à la lecture comme après écriture, pour éviter une incohérence entre le contenu et son jeton.

V25.0.7 — restauration complète et contrôlée des sauvegardes
- Ajout d'une API de restauration ZIP complète, réservée au compte direction.
- Restauration coordonnée de data/maclasse.json et de data/uploads, avec sauvegarde préalable de l'état courant.
- Extraction dans un répertoire temporaire, validation du JSON et remplacement contrôlé des fichiers.
- Rejet des archives ZIP invalides, chemins absolus/relatifs dangereux, entrées dupliquées, liens symboliques, fichiers chiffrés, archives trop volumineuses ou taux de compression anormaux.
- Interface de restauration ZIP visible uniquement à la direction ; l'import JSON existant reste disponible.
- Tests HTTP : restauration refusée au professeur, acceptée à la direction, restauration des fichiers jointe et rejet d'archive malveillante.


Correctif de durcissement post-import — 12/11/2026
- Projection des données professeur convertie en liste blanche des référentiels partagés ; toute nouvelle clé top-level reste privée par défaut.
- Ajout d'un test de régression contre la fuite de collections inconnues/configurations privées.
- Ajout d'un workflow GitHub Actions pour les suites JavaScript et Python ; exécution encore à confirmer.
- Exclusion de la base locale, des uploads, des sauvegardes et de l'environnement Python via .gitignore.
- Retrait de data/maclasse.json du suivi Git public ; le serveur la recrée au premier démarrage.
- Aucun test de cette livraison n'est déclaré exécuté dans la session.

- Complément sécurité : filtrage champ par champ de settings dans la projection professeur ; seuls les champs fonctionnels connus sont transmis. Test dédié contre la fuite d'un champ privé ajouté à settings.

- Validation CI : succès sur le commit f379a8c (run 43305047329) ; 31 tests JavaScript, 7 scripts Python, contrôle syntaxique JS et compilation Python réussis.


12/11/2026 — Confidentialité des comptes professeurs
- Correction : GET /api/data ne renvoie plus passwordHash ni password dans le profil du professeur connecté.
- Test de non-régression ajouté pour les deux champs.
- Commits : fbaf4ff, f6f994b.


12/11/2026 — Sécurité des sessions
- Les sessions authentifiées sont maintenant rapprochées du compte actif en base à chaque requête.
- La suppression/désactivation d'un compte ou le retrait de son rôle autorisé révoque immédiatement sa session au lieu d'attendre 12 heures.
- Ajout d'un test HTTP vérifiant la révocation des sessions après restauration d'une base sans comptes.
- Commits : ed26a79, 7638d4f. CI réussie sur le test d'intégration (run 43306000415) et sur les trois commits documentaires suivants.


12/11/2026 — Audit en cours : export PDF des bulletins
- Constat : l'API de génération PDF fait confiance au contenu et au statut « publié » envoyés par le navigateur ; aucun bulletinId n'est transmis pour vérifier la publication réelle en base.
- Risque : production d'un PDF présentant un contenu client comme officiellement publié. Ce point concerne l'authenticité du document, pas une fuite de données serveur.
- Correction à réaliser : lier l'export à un bulletin identifié et vérifier côté serveur son accès et son état de publication.
- Statut : ouvert, non corrigé.


12/11/2026 — Export PDF : vérification du statut du bulletin
- Refus des exports officiels si le bulletin n'est pas validé et publié dans la base.
- L'identité, la classe, la période et la date officielle sont désormais issues de la base serveur.
- Test HTTP couvrant bulletin publié, brouillon non publié et classe hors périmètre.
- Limite connue : contenu pédagogique chiffré et appréciations encore transmis par le navigateur ; validation serveur à poursuivre.
- Commits : 508df20, 1a011c0. CI à confirmer.


12/11/2026 — Contrôles Cloud et export PDF
- Cloud : _cloud_path_allowed refuse désormais par défaut les chemins qui ne commencent pas par cloud/. Test de non-régression ajouté. Commits 5ff9364 et 4c92f9c ; CI run 43306325378 réussi.
- PDF : l'export exige un bulletinId ; vérification serveur de l'existence, de la cohérence élève/classe et du périmètre du professeur. Identité et statut de publication repris de la base. Commits a661d36, 5713ba6, 59bb9cf ; CI run 43306723332 réussi.
- Limite : moyennes, appréciations, statistiques et compétences du PDF restent fournies par le client ; génération intégrale serveur encore à réaliser.


12/11/2026 — Autorisations des bulletins côté serveur
- Protection des champs de validation/publication et de l'appréciation générale : seul le professeur principal de la classe peut les modifier.
- Les bulletins déjà publiés sont immuables pour les comptes professeurs.
- Tests de non-régression ajoutés pour les tentatives de falsification.
- Limite restante : contrôle fin des matières réellement enseignées par le professeur.
- Commits : 2ee67c0, 3705b90. CI à confirmer.


Validation : test des autorisations PP corrigé pour isoler les données projetées de la fixture source ; CI complète réussie sur le commit 1b8514e (run 43307416629).


12/11/2026 — Confidentialité CCI et intégrité des bulletins
- Messagerie : les destinataires ne voient plus les autres adresses BCC/CCI ; l'expéditeur conserve la liste complète. Commits 20dedb6 et 1db7f79 ; CI run 43307062966 réussi.
- Bulletins : l'identité d'un bulletin existant (élève, classe, période) est préservée lors d'une sauvegarde professeur ; un bulletin publié ne peut pas être retiré de la collection ni modifié par un professeur. Commits 955b904 et 575403d ; CI run 43307614719 réussi.
- Contrôle serveur de l'affectation matière du professeur : reste à auditer.


12/11/2026 — Évaluations : rattachement strict à la classe
- Protection de l'identité de classe des évaluations existantes.
- Filtrage des notes sur les élèves de la classe exacte de l'évaluation.
- Tests contre le déplacement interclasse et l'injection de notes d'élèves d'une autre classe.
- Commits : d4fe63f, 077d30f. CI à confirmer ; permissions par matière non modélisées.


Validation CI des droits d'évaluation : scénario de test ajusté pour distinguer la note légitime de l'injection interclasse ; suite complète réussie sur 6075e94 (run 43308092780).


12/11/2026 — Contrôles interclasse des présences et travaux rendus
- Présences limitées aux élèves de la classe exacte.
- Travaux rendus liés à une séance existante et à un élève de la même classe.
- Protection du périmètre des enregistrements existants contre les changements de classe falsifiés.
- Tests de non-régression ; CI complète réussie sur 3fe990d (run 43308354602).


12/11/2026 — CSP des fichiers téléversés et intégrité des travaux rendus
- Ajout d'une CSP sandbox sur les fichiers servis depuis /data/uploads/ afin de bloquer l'exécution de scripts HTML importés.
- Test HTTP sur un fichier HTML contenant un script.
- Protection de l'identité élève/séance des travaux rendus existants.
- CI complète réussie sur 91db610 (run 43308611502).


12/11/2026 — Permissions matière et cohérence des données imbriquées
- Bulletins : appréciations de matière limitées aux matières de la fiche professeur ; fonction de contrôle UI restaurée ; vérification serveur ajoutée. Commits 8437b3a, 6db9412, be30a63 ; CI run 43308130018 réussi.
- Projection : notes et présences limitées aux élèves de la classe exacte ; bulletins, pièces jointes et rendus masqués si les liens élève/classe/séance sont incohérents. Commits 67451c8 et f9fc214.
- Sauvegarde : identité élève/séance/classe d'un rendu existant préservée côté serveur. Commit 91db610 ; CI run 43308611502 réussi.
- Limite : les matières sont affectées globalement au professeur, pas encore par classe.

 
12/11/2026 — Export PDF des bulletins fiabilisé
- Recalcul intégral côté serveur du contenu métier du PDF ; les valeurs de moyennes/statistiques/compétences/présences fournies par le navigateur ne sont plus utilisées.
- Contrôles d'identité, de classe, de validation/publication et de périmètre professeur conservés avant génération.
- Test de non-régression contre les valeurs falsifiées côté client.
- CI complète réussie sur e1af32a (run 43309419995).
- Numéro applicatif inchangé : V25.0.7.


12/11/2026 — Révocation des sessions après changement de mot de passe
- Invalidation des autres sessions du compte après rotation du mot de passe ; conservation de la session qui a effectué l'opération.
- Test HTTP multi-session ; CI complète réussie sur 3001ed2 (run 43309742779).


12/11/2026 — Cloisonnement des calculs de bulletins par classe
- Les calculs serveur de moyenne générale et d'assiduité ignorent désormais toute évaluation ou feuille de présence rattachée à une autre classe.
- Test de non-régression avec données interclasses mal rattachées.
- CI complète réussie : runs 43310140332 et 43310145774.


12/11/2026 — Protection des rattachements de classe existants
- La fusion des sauvegardes professeur vérifie désormais le périmètre depuis l'enregistrement stocké et préserve les liens de classe/élève/séance/période des objets concernés.
- Tests de déplacement falsifié d'élève, séance, présence et pièce jointe entre classes attribuées.
- CI complète réussie : runs 43310380105 et 43310387814.


12/11/2026 — Préparation de l'installation Fedora
- Ajout d'un installateur, d'un lanceur et d'un guide Fedora dédiés.
- Ajout du contrôle de syntaxe des deux scripts à la CI.
- L'installation et les performances sur le PC physique restent à vérifier.


12/11/2026 — Blocage du bind réseau prématuré
- Le serveur refuse désormais tout démarrage sur une adresse non-loopback ; l'ancienne configuration se contentait d'afficher un avertissement et démarrait malgré tout.
- Test de régression sur 0.0.0.0, IP LAN, :: et les trois adresses loopback autorisées.
- CI en cours de validation sur 75207b5 et f1fa7d0.


Validation CI complémentaire — 12/11/2026
- Verrouillage localhost : tests complets réussis, run 43310801471 (f1fa7d0).
- Scripts Fedora + suites JavaScript/Python : run 43310869800 (ebb910a) réussi.
- Documentation : run 43310879305 (8ccbba9) réussi.


## 12/11/2026 — Cloisonnement conversations et messagerie
- Conversations historiques verrouillées contre le changement de propriétaire, classe, participants et contenu par un enseignant.
- Préservation des seuls états personnels de conversation.
- Validation des destinataires `sharedWith` dans la messagerie V2, avec contrôle du périmètre des élèves.
- Tests de régression ajoutés ; CI en cours au moment de cette entrée.


12/11/2026 — Préparation de l'installation Mac Apple Silicon
- Vérification explicite macOS + architecture arm64 native.
- Environnement Python .venv obligatoire et compilation du serveur après installation.
- Lanceur macOS simplifié : vérification des dépendances, ouverture de Firefox si présent, serveur local sur 127.0.0.1 et arrêt par Ctrl+C.
- Documentation de sauvegarde avant mise à jour et rappel des limites de sécurité locales.
- La CI vérifie la syntaxe des lanceurs macOS ; aucun test réel sur le Mac M5/macOS 27 n'est revendiqué.


12/11/2026 — Compatibilité macOS et validation croisée
- Correction des chemins uploads/Cloud pour utiliser systématiquement la racine réelle du stockage, notamment sur macOS où /var peut pointer vers /private/var.
- Test de non-régression dédié.
- CI complète réussie sur macOS et Ubuntu : run 43313321068.
- Lanceurs .command passés en mode exécutable 100755 pour le double-clic Finder.
- Validation réelle sur Mac M5/macOS 27 et recette Firefox restent à effectuer.


## 12/11/2026 — réseau privé expérimental et espace élève

- Ajout du lanceur macOS `Lancer-MaClasse-Reseau.command` avec liaison IPv4 privée précise, opt-in explicite, contrôle Host et refus du démarrage tant que les mots de passe initiaux ne sont pas changés.
- Ajout des comptes élèves individuels liés à une fiche élève, authentification serveur et changement obligatoire du mot de passe provisoire.
- Ajout d'une projection serveur limitée à l'élève connecté et de contrôles pour les rendus personnels et leurs fichiers ; aucune modification des notes, de la fiche ou des corrections n'est acceptée depuis un compte élève.
- Messagerie et Cloud élève restent désactivés en attendant un audit de permissions dédié.
- Tests HTTP et unitaires ajoutés ; CI Ubuntu + macOS Apple Silicon réussie (run #43318282845).



13/11/2026 — V25.0.15 : comptes élèves canoniques et matières enseignants
- La fiche élève devient l'unique enregistrement de son compte : les identifiants de connexion, l'empreinte PBKDF2, l'état du compte et le changement obligatoire du mot de passe provisoire sont intégrés à la fiche.
- Suppression du doublon de compte élève dans users[] ; l'API ne fournit qu'une projection publique expurgée des secrets pour les écrans de gestion.
- Connexion, validation de session, changement de mot de passe, réinitialisation et activation/désactivation alignés sur l'identifiant canonique de la fiche.
- Création d'élèves depuis l'espace professeur dans une classe attribuée, puis création de leur accès provisoire.
- Sauvegarde des fiches élèves confirmée côté serveur avant affichage du succès ; restauration de l'état local en cas d'échec.
- Les enseignants peuvent de nouveau gérer librement leurs matières depuis leur profil, comme auparavant.
- Les anciennes sauvegardes V25 avec fiches et comptes élèves séparés ne sont pas migrées : la recette V25.0.15 se fait sur une base neuve.
- CI Ubuntu et macOS Apple Silicon : tests JavaScript, tests Python et intégration HTTP.


17/11/2026 — V25.0.24 : corrections issues de la recette V25.0.23
- Répare l’accès des élèves à la messagerie et à leurs bulletins PDF, avec vérification serveur stricte du propriétaire du bulletin.
- Génère les bulletins PDF sur le serveur afin que les postes connectés au réseau utilisent le même service que le poste hôte.
- Fiabilise la création et la sauvegarde des bulletins : confirmation serveur, absence de doublons et restauration locale en cas d’échec.
- Autorise les professeurs à gérer les affectations temporaires uniquement sur leurs propres créneaux, avec contrôles serveur et protection des affectations de la Direction.
- Simplifie la Vie scolaire côté élève et corrige plusieurs problèmes d’affichage : couleurs de matières, fond de l’EDT, navigation Direction, paramètres, profils et numéro de version commun.
- Validations automatisées Linux, macOS Apple Silicon et Firefox réel réussies sur le code candidat.


25/11/2026 — V25.0.25 : fiabilisation du gestionnaire de mises à jour
- Le gestionnaire compare désormais les tailles et empreintes SHA-256 indépendantes fournies par l'API GitHub pour le manifeste et l'archive, lorsqu'elles sont disponibles.
- Une empreinte GitHub mal formée ou différente de celle du manifeste bloque la préparation ; l'archive téléchargée est également contrôlée contre sa taille annoncée et son SHA-256.
- Les releases historiques sans métadonnées de digest restent compatibles : le contrôle SHA-256 du manifeste continue de s'appliquer. Ce mécanisme renforce l'intégrité des fichiers mais ne constitue pas une signature cryptographique de l'éditeur.
- La recette de migration macOS couvre maintenant explicitement une installation historique V25.0.19, avec conservation de la base, des certificats, des pièces jointes et du lien de version active.
- Version applicative, interface et VERSION.txt alignées sur V25.0.25.
- Validation CI Linux, macOS/launchd et Firefox réel réussie sur le commit 46ef83f (run GitHub Actions #1573, 25/11/2026). La recette physique sur le Mac, le PC Fedora et le Wi-Fi reste distincte et n'est pas revendiquée.

- Le serveur supervisé Linux/macOS surveille désormais l'IPv4 privée : il ferme le listener en cas de perte réseau, renouvelle le certificat serveur sous la même CA et rebinde automatiquement lors d'un changement DHCP. Les lanceurs manuels macOS utilisent le même superviseur.
- Tests ajoutés pour la détection Linux/macOS, le rejet d'adresses non privées, la validité SAN/expiration, le changement d'adresse et la perte/retour du réseau.


25/11/2026 — Audit produit et synchronisation applicative (candidat de branche)
- Ajout de docs/AUDIT_PRODUIT_V25.md : inventaire des modules actifs, état des tests, dettes de maintenance, risques de migration et plan de recette Direction/Professeur/Élève.
- Le navigateur dispose désormais d'un endpoint de révision léger et d'un mécanisme de surveillance global des données, au-delà des seules pages EDT/Séances ; la lecture complète des données est déclenchée lorsqu'une révision change et qu'aucune saisie locale n'est en cours.
- Ajout d'une première fusion à trois versions pour les modifications indépendantes, et d'un état explicite pour les conflits sur un même champ ; les deux versions peuvent être exportées avant arbitrage.
- Ajout de tests d'intégration pour l'endpoint de révision et de tests ciblés de fusion concurrente. Les tests Firefox et la validation complète de cette évolution restent en cours : ne pas considérer la synchronisation générale comme validée à ce stade.
- L'audit produit identifie un parcours de mise à jour du calendrier élève après une modification distante qui échoue encore dans le test Firefox ; le défaut reste ouvert et ne doit pas être masqué en assouplissant l'assertion.


25/11/2026 — Diagnostic et correction du rendu EDT élève
- Le test Firefox a confirmé que la synchronisation de données fonctionnait : le créneau Sciences figurait dans les données reçues, dans le calcul des occurrences et dans le HTML généré par le moteur de calendrier élève.
- Le DOM visible gardait malgré tout l'ancien calendrier (aucun élément avec l'identifiant du nouveau créneau). Le garde-fou de synchronisation qui ne redessinait la page que lorsque le JSON semblait différent était donc insuffisant pour réparer un DOM devenu obsolète.
- Correction dans _all.js : lorsqu'une nouvelle révision serveur est adoptée et qu'aucune saisie locale n'est active, le module actuellement ouvert est systématiquement rendu à nouveau, même si le modèle JSON paraît déjà identique.
- Test de régression ajouté : nouvelle révision avec modèle local déjà identique doit tout de même déclencher le rendu. La recette Firefox complète sur le dernier commit reste en attente.
- Les tests smoke Firefox couvrent aussi le rendu des modules Direction/Professeur et l'application du thème manuel clair/sombre à contre-sens du thème système ; le contrôle visuel complet reste à faire.


---

## Archive source : `NOTES_V21_12.txt`

Contenu original conservé :

MaClasse V21.12 — notifications de bulletins et harmonisation de l’interface

Inclus :
- Notification côté élève quand un bulletin est officiellement publié.
- Notification dans le Centre d’activité et sur l’accueil élève, avec badge non lu et accès direct au PDF.
- Marquage comme lu conservé dans les données locales ; une nouvelle publication (nouvel horodatage) crée une nouvelle notification.
- La republication sans dépublication préalable ne réinitialise pas artificiellement la date de publication.
- Harmonisation visuelle transversale : espacement, arrondis, états de focus clavier, champs, tableaux, cartes et affichage mobile.
- Aucune refonte du module Évaluations dans cette version.

Vérifications réalisées : syntaxe JavaScript (node --check), compilation Python (py_compile), intégrité de l’archive ZIP. Pas de test navigateur automatisé effectué.


---

## Archive source : `NOTES_V21_13.txt`

Contenu original conservé :

MaClasse V21.13 — finition approfondie de l'espace élève (résultats)

Objectif : stabiliser durablement l'écran élève des résultats sans engager la refonte du module d'évaluation côté enseignant.

Inclus :
- Refonte visuelle des boutons de notes : titre/date hiérarchisés, résultat mis en valeur, flèche d'accès, survol et focus clavier visibles.
- Relevé de résultats plus lisible : entête, sélecteur de période, moyenne générale, lignes par matière et ligne de moyenne générale.
- Affichage mobile repensé : matières en blocs, évaluations en cartes pleine largeur, colonnes non écrasées.
- Détail d'une évaluation mieux structuré : métadonnées, score et équivalent sur 20 mieux hiérarchisés.
- Compétences présentées en cartes avec espacement, libellés longs mieux gérés et badges alignés.
- Tableaux de critères plus respirants et défilement horizontal préservé sur petit écran.
- Conservation des fonctions existantes : filtres de période, notes publiées uniquement, calculs, coefficients, détail des critères/compétences et commentaires.
- Conservation de la notification élève à la publication officielle du bulletin introduite en V21.12.
- Harmonisation générale de l'interface V21.12 conservée.

Périmètre : écran de résultats côté élève uniquement pour la finition du module d'évaluation. La refonte complète du module côté enseignant reste hors périmètre.

Vérifications réalisées : node --check sur _all.js ; py_compile sur server.py ; intégrité de l'archive ZIP. Pas de test navigateur réel effectué.


---

## Archive source : `NOTES_V21_14.txt`

Contenu original conservé :

MaClasse V21.14 — sécurisation et robustesse

- Serveur : suppression du CORS wildcard ; les requêtes web d'une autre origine sont refusées.
- Serveur : accès statique limité à l'interface et aux fichiers du Cloud uploadés ; les fichiers internes du projet ne sont plus servis par HTTP.
- Cloud : /api/cloud-delete refuse désormais '.', '..' et les chemins réduits au dossier racine uploads.
- Sauvegardes : passage de 15 copies consommées à chaque enregistrement à une copie au plus toutes les 6 heures, conservée pendant 30 jours. La réinitialisation force toujours une copie préalable.
- Bulletins : les matières contenant apostrophes ou guillemets ne sont plus injectées dans les onclick ; les onglets et champs de saisie passent par des data-* sûrs.
- Version affichée : V21.14.

Vérifications réalisées avant livraison : node --check, py_compile, tests serveur locaux sur copie de travail et test de génération du HTML des bulletins avec une matière contenant une apostrophe.


---

## Archive source : `NOTES_V21_15.txt`

Contenu original conservé :

MaClasse V21.15 — fiabilisation des tests, données et Cloud

- Tests : les contrôles concernés ont été réalignés sur _all.js, qui est le point d’entrée JavaScript réel.
- Données : ajout d’un parseur numérique central pour accepter les notes décimales françaises (ex. « 14,5 ») dans les calculs sans modifier la valeur enregistrée.
- Cloud : après renommage d’un dossier, les serverName de tous ses descendants sont réécrits avec le nouveau préfixe physique ; les URL des fichiers descendants sont resynchronisées.
- Aucun grand module n’est reconstruit dans V21.15 ; les reconstructions restent planifiées à partir de V21.16.
- Version affichée : V21.15.


---

## Archive source : `NOTES_V21_16.txt`

Contenu original conservé :

MaClasse V21.16 — Refonte Résultats élèves

Correctif V21.16.1 — régression UI corrigée
- Les boutons de détail des évaluations généraient un onclick HTML mal quoté.
- Le changement de période utilisait le même motif et pouvait produire un handler JavaScript invalide.
- Les deux handlers utilisent désormais des arguments JS protégés dans l'attribut HTML.
- studentReportDetail reçoit maintenant directement evaluationId + studentId.
- Test de régression ajouté.

Moteur V21.16
- buildStudentReport(db, studentId, termId, today) centralise le calcul.
- Résultats élève et Accueil élève partagent le moteur.
- Publication, période, coefficients, barèmes et décimales françaises sont couverts par les tests.


---

## Archive source : `NOTES_V21_17.txt`

Contenu original conservé :

MaClasse V21.17 — Refonte du module Évaluations

Cette version introduit un moteur métier centralisé pour les évaluations, séparé du rendu de l’interface.

Moteur :
- evaluationModelMaxScore / coefficient / publication / période
- evaluationModelStudentReport
- evaluationModelClassStats
- saisie centralisée des notes, critères et compétences
- normalisation des notes décimales françaises
- barèmes réels ramenés sur 20 pour les calculs comparables

Interface :
- tableau Évaluations reconstruit autour du moteur V21.17
- création / modification d’une évaluation
- saisie des notes, critères, compétences et observations
- statistiques de classe cohérentes avec les règles de publication

Compatibilité :
- aucune migration destructive
- données d’évaluations existantes conservées
- grilles et compétences existantes conservées

Tests :
- test_v217_evaluation_model.js
- tous les tests JavaScript existants
- régression sécurité V21.14
- node --check _all.js
- py_compile server.py

V21.17 n’inclut pas encore la refonte du module Professeur principal, du Cloud ou des fondations V22.

V21.17 deep UX — refonte ergonomique

La V21.17 approfondit la reconstruction du module Évaluations :
- parcours création → configuration → saisie simplifié ;
- évaluation simple sans grille obligatoire ;
- bibliothèque de grilles présentée comme option réutilisable ;
- tableau de saisie large avec élèves en colonne fixe ;
- saisie des notes en texte avec virgule décimale ;
- navigation clavier Entrée / ↑ / ↓ / Tab ;
- sauvegarde immédiate conservée ;
- configuration modifiable sans quitter la saisie ;
- compatibilité avec les critères, compétences et observations existants.

Cette version conserve les données existantes et n’effectue aucune migration destructive.



---

## Notes historiques V21 complémentaires

### Archive source : `NOTES_V21_17_1.txt`

Contenu original conservé :

MaClasse V21.17.1 — Finition du module Évaluations

Objectif : terminer la refonte V21.17 sans créer une nouvelle V21.18 prématurément.

- sélection des compétences repensée : référentiel filtré automatiquement par niveau scolaire et matière ;
- prise en charge des anciennes compétences liées aux niveaux via settings.competencyLevels ;
- sélection par cases à cocher, recherche, tout sélectionner / tout désélectionner ;
- conservation des compétences déjà sélectionnées lors d'un changement de filtre dans une évaluation ;
- grilles : création/modification avec niveau, matière, compétences et critères ;
- réutilisation d'une grille filtrée selon le contexte de l'évaluation ;
- les compétences sélectionnées restent propres à l'évaluation et ne modifient pas les modèles existants ;
- compatibilité conservée avec les anciennes bibliothèques de compétences stockées sous forme de chaînes ;
- interface de sélection conçue pour éviter les longues listes et la sélection Cmd/Ctrl obligatoire ;
- ajout du test test_v2171_competency_picker.js.

Vérifications :
- 26/26 tests JavaScript OK ;
- régression sécurité V21.14 OK ;
- node --check _all.js OK ;
- python3 -m py_compile server.py OK ;
- aucune migration destructive des données.

Non testé : validation visuelle complète dans Firefox/macOS.


### Archive source : `NOTES_V21_18.txt`

Contenu original conservé :

MaClasse V21.18 — Passe UI/UX globale

- Standardisation globale des contrôles visibles : sélecteurs MaClasse, champs, zones de texte, boutons et états de focus.
- Les valeurs des <select> natifs restent dans le DOM pour préserver FormData et les handlers existants ; leur rendu est remplacé par le composant MaClasse.
- Remplacement de la confirmation native du dépôt définitif d’un travail par une modale MaClasse.
- Suppression visuelle des spinners natifs des champs numériques.
- Base CSS UI centralisée : focus clavier, états hover/disabled, file inputs, responsive.
- Passe destinée à être poursuivie écran par écran pour corriger les incohérences CSS restantes sans changer les données métier.


### Archive source : `NOTES_V21_19.txt`

Contenu original conservé :

MaClasse V21.19 — Professeur principal et consolidation UI

Objectif
- Finaliser le chantier Professeur principal sans reconstruire les écrans déjà aboutis.
- Corriger la recherche globale et son raccourci clavier.
- Consolider les contrôles UI dynamiques.

Travail réalisé
- Le tableau de bord Professeur principal a été renforcé : identité de la classe, KPI, accès rapides, groupes, points d’attention, activité récente et suivi synthétique des élèves.
- Les actions du PP réutilisent les modules existants et le contexte de classe ; aucune nouvelle copie du modèle de données n’a été créée.
- La Messagerie et les bulletins existants sont conservés comme références visuelles ; ils n’ont pas été reconstruits inutilement.
- Cmd/Ctrl-K donne désormais le focus au champ de recherche globale visible dans la barre supérieure. La Command Palette reste un fallback si aucun champ de recherche n’existe.
- Le panneau de résultats de la recherche globale est replacé dans un contexte de superposition maîtrisé : la barre supérieure n’utilise plus contain:paint, le panneau passe au-dessus du contenu normal mais reste sous les modales.
- Le runtime des Select MaClasse observe les changements d’options d’un select déjà transformé et reconstruit son menu peint lorsque le contenu dynamique change.
- Version visible passée à V21.19.
- Test ajouté : tests/test_v219_pp_ui.js.

Validation
- node --check _all.js : OK
- python3 -m py_compile server.py : OK
- Suite JS existante : OK
- test_v219_pp_ui.js : OK
- test_v214_security.py : OK
- La validation visuelle automatisée Chromium n’est pas considérée comme acquise dans cet environnement.


### Archive source : `NOTES_V21_20.txt`

Contenu original conservé :

MaClasse V21.20 — MaClasse 27 Design System

Objectif : unifier l’époque visuelle de l’application autour d’un langage contemporain inspiré des interfaces Apple récentes sans transformer MaClasse en copie de macOS.

- primitives communes harmonisées : navigation, cartes, boutons, champs, onglets, tableaux, modales, badges ;
- surfaces neutres et hiérarchisées ;
- suppression visuelle des gradients historiques sur les surfaces communes ;
- sidebar modernisée sans toucher à l’identité fonctionnelle ;
- recherche globale placée dans un vrai contexte de premier plan ;
- Cmd/Ctrl-K focalise la recherche globale ;
- Messagerie et Bulletins conservés comme designs spécialisés déjà aboutis ;
- états focus/disabled et réduction des animations ajoutés ;
- responsive renforcé ;
- aucune modification du modèle de données.

La validation visuelle navigateur complète reste à faire dans un environnement Chromium fonctionnel.


### Archive source : `NOTES_V21_21.txt`

Contenu original conservé :

MaClasse V21.21 — UX & EDT 7 jours

Objectif : optimiser les actions récurrentes et rendre l’emploi du temps hebdomadaire complet.

- EDT semaine : 7 jours, lundi → dimanche, côté enseignant et élève.
- Le formulaire de créneau propose les 7 jours.
- Appel : les actions principales ouvrent directement le nouvel appel au lieu de faire passer par la page historique.
- Nouvel appel : préselection automatique de la première classe ayant un cours aujourd’hui, et du cours lorsqu’un appel est lancé depuis une séance EDT.
- Depuis une séance EDT, action directe « Faire l’appel ».
- Connexion : premier choix professeur focalisable immédiatement au clavier.
- Design MaClasse 27 conservé ; Messagerie et Bulletins non reconstruits.


### Archive source : `NOTES_V21_22.txt`

Contenu original conservé :

MaClasse V21.22 — Liquid UI + EDT fit

- EDT semaine : 7 jours en grille fluide sans largeur minimale sur desktop.
- Rail horaire compact et densité adaptée aux écrans courants.
- Sur très petites largeurs, défilement horizontal conservé pour préserver la lisibilité.
- MaClasse 27 renforcé : surfaces liquides, blur, highlights, transparence et profondeur sur navigation, topbar, cartes, contrôles, recherche et modales.
- Messagerie et Bulletins conservés comme identités spécialisées.
- Dark mode harmonisé avec le matériau liquide.


### Archive source : `CORRECTIF_V21_11_3.txt`

Contenu original conservé :

MaClasse V21.11.3 — correctifs ciblés

- Déclare activeConversationId pour éviter l’erreur de référence au clic dans la navigation enseignant.
- Espace Cloud : vignettes adaptatives, noms de fichiers visibles en mode Icônes, icône de dossier adaptée aux couleurs du thème plutôt qu’un SVG codé en dur.
- Espace élève : n’affiche que les bulletins officiellement publiés. Les bulletins publiés sont accessibles dans Mes résultats et Vie scolaire.
- Bulletin : choix entre prévisualiser le PDF dans l’application et télécharger le PDF.

Le message « No Listener: tabs:outgoing.message.ready » provient généralement d’une extension du navigateur et n’est pas la cause de l’erreur JavaScript activeConversationId.


