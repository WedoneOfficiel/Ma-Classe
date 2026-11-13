# MaClasse

Application web de gestion scolaire, pensée pour centraliser les outils du quotidien d'un établissement dans une interface unique : suivi des élèves et des classes, cours, évaluations et notes, absences, bulletins, messagerie et espace documentaire/Cloud.

> **Objectif du projet :** disposer d'une application simple à utiliser, fiable et sécurisée, hébergée sur un ordinateur de la maison ou de l'établissement et accessible depuis les autres appareils du réseau local via un navigateur. Aucune exposition publique à Internet n'est prévue pour le déploiement domestique.

---

## État du projet

**Branche de référence :** `main`  
**Version de travail :** V25.0.17 (alpha)  
**Statut :** développement et sécurisation en cours — **pas prête pour une utilisation multi-postes sur le réseau local**.

### Point de synchronisation GitHub

Le commit d'import `a2e83ef` contient bien le code applicatif et les ressources de MaClasse : `server.py`, `index.html`, `_all.js`, les scripts macOS, les documents de version et les tests. La version applicative actuelle est **V25.0.17** ; `VERSION.txt` et les lanceurs affichent la version du dépôt. Le dépôt a été inspecté directement ; le constat précédent selon lequel il ne contenait que le README était erroné.

Le fichier `data/maclasse.json` est local et exclu de Git. Une installation neuve démarre sans aucun compte : l'assistant de première configuration crée uniquement le compte direction. Aucun mot de passe ou compte enseignant universel n'existe.

---

## Principes techniques et de sécurité

- Application web servie localement ; les appareils clients utilisent un navigateur.
- Le serveur doit rester lié à `127.0.0.1` tant que les protections nécessaires au réseau local ne sont pas terminées.
- Pas de redirection de ports sur le routeur et pas d'exposition publique.
- Les autorisations doivent être contrôlées **côté serveur**, jamais uniquement dans l'interface JavaScript.
- Un enseignant ne doit accéder qu'aux classes, élèves, messages et documents qui lui sont autorisés.
- Les données des autres enseignants ne doivent jamais être écrasées par une sauvegarde partielle ou concurrente.
- Les sauvegardes doivent inclure la base de données et les fichiers téléversés, et leur restauration doit être testée.
- Ne jamais modifier ou écraser la version V24.2 de référence pendant le développement de V25.

## Derniers travaux V25 rapportés

Les éléments suivants ont été annoncés comme réalisés dans les itérations V25.0.1 à V25.0.7. **Ils restent à revalider sur le code effectivement présent dans ce dépôt après sa synchronisation.**

- Authentification gérée par le serveur, sessions et protection des API.
- Changement obligatoire des mots de passe initiaux ; migration annoncée vers PBKDF2 avec sel.
- Limitation des tentatives de connexion et contrôles d'origine des requêtes.
- Premiers contrôles d'accès par rôle, classe et professeur.
- Protections côté serveur pour le Cloud, les fichiers et la messagerie.
- Détection des sauvegardes concurrentes par contrôle de version, avec refus des écritures obsolètes plutôt qu'écrasement silencieux.
- Sauvegardes ZIP incluant la base et les téléversements ; restauration avec validation de l'archive et sauvegarde préalable.

## Correctifs appliqués après l'import

- Projection des données professeur passée en liste blanche : seuls les référentiels explicitement partagés sont transmis ; les futures clés restent privées par défaut. Les paramètres sont eux-mêmes filtrés champ par champ.
- Tests de non-régression ajoutés pour empêcher la fuite de collections inconnues et de champs privés dans les paramètres.
- `.gitignore` ajouté pour exclure la base locale, les téléversements, les sauvegardes et l'environnement Python ; la base provisoire suivie par Git a été supprimée du dépôt.
- Workflow GitHub Actions ajouté dans `.github/workflows/tests.yml`. Exécution réussie sur le commit de code/test `f379a8c` : 31 tests JavaScript, les 7 scripts de test Python, `node --check _all.js` et `python -m py_compile server.py`. [Voir le run GitHub Actions](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43305047329).

Commits de cette reprise : `fe0b449` et `ffaf34b` (allowlist serveur et filtrage des paramètres), `f13eeda` et `f379a8c` (tests), `5e4b301` (CI), `71fab97` (.gitignore), `5c84254` (retrait de la base locale).

## Reste à faire — priorités

### Bloquants avant le réseau local multi-postes

- [x] Synchroniser le code V25 réel dans ce dépôt et confirmer la version exacte.
- [ ] Auditer les permissions de **toutes** les API et fonctionnalités métier : classes, élèves, notes, absences, bulletins, documents, messagerie et Cloud.
- [ ] Vérifier que les enseignants ne reçoivent que les données qui leur sont nécessaires.
- [ ] Finaliser les comptes élèves individuels et leur filtrage strict ; ne pas activer leur connexion avant cela.
- [ ] Vérifier les écritures partielles et la gestion des conflits entre plusieurs utilisateurs.
- [x] Le serveur refuse désormais tout démarrage sur une adresse LAN sans certificat TLS ; le mode réseau exige HTTPS avec TLS 1.2 minimum.
- [x] Les cookies de session portent l'attribut Secure en HTTPS et les origines HTTP sont refusées sur un serveur HTTPS.
- [ ] Finaliser la distribution et l'installation de l'autorité de certification sur tous les appareils clients, puis vérifier la confiance navigateur par navigateur.
- [ ] Valider le pare-feu local et la procédure de réservation DHCP/adresse IP stable avant activation en établissement.
- [ ] Ne configurer aucune redirection de ports sur la box.

### Fiabilité et validation

- [ ] Tester les sauvegardes et restaurations de bout en bout, y compris les fichiers téléversés.
- [ ] Réaliser une recette complète dans Firefox : connexion, rôles, classes, notes, absences, bulletins, Cloud, messagerie et déconnexion.
- [ ] Tester plusieurs navigateurs/appareils simultanément et vérifier qu'aucune modification n'est perdue.
- [ ] Vérifier l'installation propre, le redémarrage du serveur, les journaux et les erreurs.
- [ ] Maintenir les tests automatisés et ajouter un test de régression pour chaque correction.
- [ ] Mettre à jour les instructions d'installation et de sauvegarde.

## Règles de continuité pour les prochaines sessions IA

À chaque reprise, lire ce README **et vérifier le code réel du dépôt** avant de modifier quoi que ce soit.

Après chaque lot de changements :

1. Inspecter les fichiers et comprendre le fonctionnement existant avant de coder.
2. Modifier le code sans supprimer de fonctionnalités sans raison validée.
3. Ajouter ou adapter les tests correspondant aux changements.
4. Exécuter les tests réellement disponibles et noter précisément leurs résultats.
5. Mettre à jour ce README : version, changements, tests, limites connues et prochaines tâches.
6. Indiquer les commits concernés et ne jamais prétendre qu'un test, un déploiement ou une vérification manuelle a été effectué si ce n'est pas le cas.
7. Conserver V24.2 intacte et ne pas activer l'accès réseau tant que les critères de sécurité ci-dessus ne sont pas satisfaits.

## Historique synthétique

| Version | Travaux annoncés |
|---|---|
| V25.0.1 | Authentification serveur, sessions, protection des API et changement du mot de passe initial |
| V25.0.2 | Renforcement des mots de passe et protection des chemins de fichiers |
| V25.0.3 | Contrôles d'accès Cloud côté serveur |
| V25.0.4 | Premier cloisonnement des données par classe et professeur |
| V25.0.5 | Cloisonnement de la messagerie et des pièces jointes |
| V25.0.6 | Détection des sauvegardes obsolètes et conflits d'écriture |
| V25.0.7 | Restauration d'archives ZIP et validation des archives |

*Historique vérifié à partir des fichiers sources et du commit d'import ; les limites de recette restent celles indiquées plus haut.*


## Correctif de confidentialité des comptes enseignants — 12/11/2026

L'audit de la projection `/api/data` a révélé que le profil du professeur connecté était transmis avec son champ `passwordHash`. Même salée et dérivée par PBKDF2, une empreinte ne doit pas être distribuée au navigateur : elle pourrait faciliter une attaque hors ligne en cas de récupération de la réponse API.

- La projection professeur conserve les informations de profil nécessaires, mais retire systématiquement `passwordHash` et tout ancien champ `password`.
- La fusion des sauvegardes professeur continuait déjà à préserver les comptes côté serveur ; ce correctif concerne la lecture et la confidentialité.
- Test dédié ajouté dans `tests/test_v25_teacher_data_scope.py`.
- Commits : `fbaf4ff` (serveur), `f6f994b` (test).
- La validation GitHub Actions du nouveau commit doit être consultée avant de considérer le lot validé.


## Correctif supplémentaire — révocation des sessions

- L'audit a identifié qu'une session conservait son rôle et son identité pendant sa durée de vie, même après désactivation ou suppression du compte.
- `Handler._session_user`" revalide désormais le compte dans la base à chaque requête authentifiée. Un compte supprimé, désactivé ou dont le rôle n'est plus autorisé perd immédiatement sa session ; les changements de rôle et d'identifiant professeur sont aussi reflétés dans la session.
- Le test HTTP d'intégration vérifie désormais qu'après restauration d'une sauvegarde qui supprime les comptes, les cookies de session précédemment ouverts ne permettent plus d'accéder à l'API.
- Le premier run CI du correctif serveur seul a échoué parce que le test simulait des sessions sans comptes persistés, alors que la nouvelle vérification exige un compte actif en base. Le test a été corrigé pour conserver les comptes pendant les scénarios normaux, puis vérifier leur révocation après restauration. Le run du commit de test `7638d4f` est réussi : [GitHub Actions #43306000415](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43306000415). Les runs des trois mises à jour documentaires sont également réussis.
- Serveur : commit `ed26a79` ; test : commit `7638d4f`.


## Point d'audit suivant — génération PDF des bulletins

La route `POST /api/bulletin-pdf` reçoit le contenu du bulletin depuis le navigateur et construit le PDF à partir de ce contenu. Le navigateur n'envoie actuellement aucun identifiant de bulletin ; le serveur ne retrouve donc pas l'enregistrement correspondant dans la base. En particulier, la mention « Bulletin publié officiellement » est déclenchée par les champs `published` et `publishedAt` fournis par le client, et non par une vérification serveur de la publication.

- Ce constat ne révèle pas les données d'un autre élève : le PDF est construit à partir du corps transmis par le client.
- En revanche, le document peut présenter comme officiellement publié un contenu falsifié côté navigateur. Le PDF ne doit donc pas être considéré comme une preuve d'authenticité.
- Correction appliquée : le navigateur transmet maintenant `bulletinId` ; le serveur vérifie que le bulletin existe, que l'élève correspond à la classe enregistrée et que le professeur est affecté à cette classe. Le nom de l'élève, la classe, la période et l'état/date de publication sont repris de la base, pas du JSON client.
- Limite restante : les moyennes, appréciations, statistiques et compétences du PDF sont encore calculées côté navigateur et transmises au serveur. L'export est lié à un bulletin autorisé, mais ne garantit pas encore l'authenticité de toutes les valeurs.
- Statut : **contrôle d'identité, de périmètre et de publication corrigé ; génération entièrement serveur encore à faire**.

Les correctifs de confidentialité des empreintes et de révocation des sessions sont documentés plus haut. CI réussie sur les commits serveur/test concernés ; le run de révocation après adaptation du test est [#43306000415](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43306000415).


### Suite du correctif PDF — contrôle du statut officiel

Le serveur refuse maintenant l'export PDF officiel si le bulletin enregistré n'est pas à la fois validé et publié, ou si sa date de publication manque. Le test HTTP couvre le refus d'un brouillon non publié et l'acceptation d'un bulletin publié dans une classe attribuée au professeur. L'identité de l'élève, la classe, la période et la date officielle sont reprises depuis la base, et non depuis le navigateur.

- Commits : `508df20` (contrôle serveur), `1a011c0` (test).
- La génération utilise encore les moyennes, appréciations, statistiques et compétences transmis par le navigateur. Ces valeurs doivent faire l'objet d'une prochaine étape de recalcul/validation côté serveur avant de considérer le PDF comme une preuve intégrale de l'exactitude des résultats.
- CI du nouveau lot : à vérifier.


## Correctif Cloud — refus par défaut hors de l'espace Cloud

- `_cloud_path_allowed` renvoyait auparavant `True` pour tout chemin qui ne commençait pas par `cloud/`. Cela pouvait rendre des métadonnées Cloud atypiques trop permissives.
- Les chemins hors de `cloud/` sont maintenant refusés par défaut ; les chemins Cloud continuent de passer par les contrôles d'espace, de propriétaire, de classe et de partage.
- Test ajouté pour les chemins `general/` et `lessons/`.
- Commits : `5ff9364` (serveur), `4c92f9c` (test). CI réussie : [run #43306325378](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43306325378).

## Correctif PDF — contrôle serveur du bulletin

- `POST /api/bulletin-pdf` exige désormais un `bulletinId` valide.
- Le serveur vérifie l'existence du bulletin, la cohérence bulletin/élève/classe et l'appartenance du professeur à la classe.
- L'identité affichée et l'état/date de publication sont reconstruits depuis la base.
- Test HTTP ajouté : bulletin inexistant refusé (404), bulletin d'une autre classe refusé au professeur (403).
- Commits : `a661d36` (serveur), `5713ba6` (client), `59bb9cf` (tests). CI réussie : [run #43306723332](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43306723332).
- Limite : les données chiffrées et appréciations du PDF sont encore transmises par le client ; une génération complète depuis la base reste nécessaire avant de qualifier le PDF de preuve officielle.


## Autorisations des bulletins — rôle du professeur principal

L'audit de la fusion des sauvegardes a montré que les restrictions de validation et de publication des bulletins étaient auparavant essentiellement contrôlées dans l'interface. La fusion serveur protège maintenant ces champs : un professeur qui n'est pas professeur principal de la classe ne peut pas modifier l'appréciation générale, valider ou publier le bulletin. Un bulletin déjà publié est conservé intégralement lors d'une sauvegarde professeur ; seule la direction peut le corriger par une sauvegarde administrative.

- Les professeurs peuvent modifier uniquement les appréciations dont la matière figure dans leur fiche professeur (`teachers[].subjects`) ; ce contrôle est maintenant appliqué côté interface et côté serveur. Il s'agit d'une liste de matières par professeur, pas encore d'une affectation matière/classe.
- Tests ajoutés pour la falsification du statut de publication et la modification d'un bulletin déjà publié.
- Commits : `2ee67c0` (droits PP), `3705b90` (tests), `1b8514e` (fixtures), `8437b3a` (droits matière), `6db9412` (contrôle UI), `be30a63` (tests).
- CI réussie pour le lot matière : [run #43308130018](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43308130018).


### Validation des droits de bulletin — résultat CI

Le premier test de non-régression a échoué à cause d'un défaut dans le test lui-même : la projection utilisée par le test partageait les mêmes objets Python que sa fixture source, contrairement à une requête HTTP réelle sérialisée en JSON. Le test a été corrigé pour isoler la charge utile avec une copie profonde. Le workflow complet est maintenant réussi sur le commit `1b8514e` : [GitHub Actions #43307416629](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43307416629).


## Correctif messagerie — confidentialité du CCI

- Un message reçu par un professeur exposait auparavant la liste complète des destinataires BCC/CCI.
- La projection serveur masque maintenant le champ `bcc` pour les destinataires ; l'expéditeur conserve sa liste complète.
- Test de non-régression : le destinataire ne voit aucun autre destinataire CCI, tandis que l'expéditeur conserve la liste.
- Commits : `20dedb6` (serveur), `1db7f79` (test). CI réussie : [run #43307062966](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43307062966).

## Renforcement des bulletins — identité et suppression

- La fusion serveur rattache désormais un bulletin existant à son identité initiale : un professeur ne peut pas le déplacer vers un autre élève ou une autre classe en falsifiant les champs d'identité.
- Un bulletin publié reste conservé même si le client tente de le retirer de la collection envoyée ; les modifications/suppressions de bulletins publiés restent réservées à la direction.
- Tests ajoutés pour le déplacement d'identité et la suppression d'un bulletin publié.
- Commits : `955b904` (serveur), `575403d` (tests). CI réussie : [run #43307614719](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43307614719).
- Le contrôle fin des matières réellement enseignées par le professeur reste à auditer.


## Évaluations — rattachement strict à la classe

La fusion des sauvegardes professeur protège désormais aussi l'identité de classe d'une évaluation existante : une évaluation ne peut pas être déplacée vers une autre classe, même si le professeur est affecté aux deux. Les notes imbriquées sont filtrées sur les élèves de la classe exacte de l'évaluation, et non simplement sur l'ensemble des élèves des classes du professeur.

- Tests ajoutés : déplacement d'une évaluation entre deux classes attribuées et injection d'un élève d'une autre classe dans les notes.
- Commits : `d4fe63f` (serveur), `077d30f` (tests).
- CI à confirmer.
- Limite : le modèle actuel ne contient pas d'affectation professeur/matière exploitable de façon fiable ; les droits restent donc au niveau de la classe. Ne pas prétendre qu'une restriction par discipline est en place.


Validation du contrôle des évaluations : le premier scénario de test remplaçait toute la liste de notes et ne conservait donc pas la note légitime de l'élève de la classe initiale. Le scénario a été corrigé pour conserver cette note tout en ajoutant une note interclasse falsifiée. Le code filtre correctement l'injection ; la suite complète est verte sur `6075e94` : [GitHub Actions #43308092780](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43308092780).


### Renforcement supplémentaire — présence et travaux rendus

Les contrôles serveur des évaluations, présences et travaux rendus ont été resserrés :
- Les lignes de présence ne peuvent référencer que des élèves de la classe exacte de la feuille.
- Un travail rendu doit être lié à une séance existante dans une classe attribuée au professeur, et l'élève doit appartenir à cette même classe.
- Pour les évaluations, présences et travaux rendus existants, le périmètre est déterminé à partir de l'enregistrement déjà stocké, afin qu'une modification falsifiée de classe ne fasse pas sortir l'élément du contrôle de sécurité.
- Si un travail rendu existant est modifié avec un élève ou une séance incohérents, l'enregistrement précédent valide est conservé.

Tests de non-régression ajoutés pour l'injection d'élève dans une présence et dans un travail rendu. Suite complète JavaScript + Python réussie sur `3fe990d` : [GitHub Actions #43308354602](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43308354602).


## Protection active des fichiers téléversés

Les fichiers servis depuis `/data/uploads/` reçoivent maintenant une politique CSP dédiée avec `sandbox` et `default-src 'none'`. Cela empêche un fichier HTML importé ou téléversé d'exécuter du JavaScript actif dans l'origine de MaClasse. Le test HTTP téléverse/sert un fichier HTML contenant un script et vérifie les en-têtes de protection.

Le contrôle des travaux rendus a également été renforcé : un rendu existant conserve son élève et sa séance d'origine, empêchant une requête falsifiée de le réassocier à un autre élève ou une autre classe. Suite complète JS + Python réussie sur `91db610` : [GitHub Actions #43308611502](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43308611502).


## Cloisonnement exact des données imbriquées

- La projection professeur filtre maintenant les notes et présences selon la classe exacte de l'évaluation ou de la feuille, même si le professeur intervient dans plusieurs classes.
- Bulletins, pièces jointes et travaux rendus ne sont transmis que lorsque les identifiants de classe, d'élève et de séance présents dans l'enregistrement concordent. Un rendu associant un élève d'une classe à une séance d'une autre classe est masqué.
- À la sauvegarde, les associations élève/séance/classe d'un rendu existant sont conservées depuis l'enregistrement serveur ; le client ne peut pas déplacer le rendu vers un autre élève ou une autre séance.
- Commits : `67451c8` (projection), `f9fc214` (tests), `91db610` (préservation de l'identité du rendu).
- CI réussie : [run #43308611502](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43308611502).


## Bulletins PDF — contenu reconstruit côté serveur

Le point d'intégrité de l'export PDF est maintenant corrigé de bout en bout. Le navigateur ne fournit plus que `bulletinId` ; après vérification de l'existence, de l'élève, de la classe, de la publication et du périmètre du professeur, le serveur reconstruit lui-même le document à partir de la base : identité, période, appréciation générale, matières, moyennes, statistiques, appréciations de matière, compétences et absences/retards. Les valeurs calculées envoyées par le navigateur sont ignorées.

- Le calcul serveur reprend les règles métier existantes : barèmes sur 20, coefficients, groupes, périodes, publication des évaluations pour les moyennes par matière et niveaux de compétences.
- Test unitaire ajouté avec des valeurs falsifiées côté client ; le constructeur n'utilise que les enregistrements canoniques.
- CI complète réussie sur `e1af32a` : [GitHub Actions #43309419995](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43309419995).
- La version applicative reste V25.0.7 : correctif incrémental de sécurité, sans changement du numéro de version.


## Sessions — révocation après changement de mot de passe

Un changement de mot de passe invalide maintenant toutes les autres sessions actives du même compte ; seule la session ayant effectué le changement reste ouverte. Cela évite qu'un ancien navigateur ou appareil conserve son accès avec une session déjà authentifiée après une rotation du mot de passe.

- Test HTTP ajouté : deux sessions ouvertes pour le même compte, changement de mot de passe depuis l'une, ancienne session refusée (401), session courante conservée.
- CI complète JS + Python réussie : [run #43309742779](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43309742779).


## Bulletin PDF — cloisonnement des calculs par classe

Un contrôle supplémentaire a été ajouté après revue du calcul serveur : les moyennes générales et les absences/retards du PDF sont maintenant calculés exclusivement à partir des évaluations et feuilles de présence de la classe du bulletin. Même une donnée historique mal rattachée (par exemple une note de l'élève insérée dans une évaluation d'une autre classe) ne peut plus contaminer le document.

- Test de non-régression avec une fausse note et une fausse absence provenant d'une autre classe.
- CI complète JS + Python réussie : [run #43310145774](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43310145774) et [run #43310140332](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43310140332).


## Protection des rattachements de classe à la sauvegarde

L'audit des sauvegardes professeur a révélé un autre cas à verrouiller : un professeur intervenant dans plusieurs classes ne doit pas pouvoir déplacer un enregistrement existant d'une classe à une autre en modifiant son JSON avant sauvegarde. Le serveur détermine désormais le périmètre d'un enregistrement existant depuis sa version stockée et préserve ses liens de classe (ainsi que les liens élève/séance/période concernés) pour les élèves, cours, séances, présences, pièces jointes, évaluations, bulletins et travaux rendus.

- Tests ajoutés contre le déplacement d'un élève, d'une séance, d'une feuille de présence et d'une pièce jointe entre deux classes toutes deux attribuées au professeur.
- CI complète JS + Python réussie : [run #43310380105](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43310380105) et [run #43310387814](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43310387814).



## Verrouillage strict de l'écoute localhost

Le serveur refusait déjà les chemins d'accès non autorisés, mais son ancienne configuration pouvait encore démarrer sur une interface réseau si `MACLASSE_HOST` était modifié. Ce n'est plus possible : le démarrage s'arrête avec une erreur si l'adresse demandée n'est pas une adresse loopback (`127.0.0.1`, `localhost` ou `::1`). L'écoute réseau n'est donc pas seulement déconseillée par la documentation ; elle est bloquée par le code.

- Test dédié des adresses loopback acceptées et des adresses réseau refusées.


## Audit supplémentaire des conversations et du partage de messages — 12/11/2026

- Une conversation historique existante ne peut plus être réaffectée à une autre classe/enseignant ni voir ses participants ou son contenu réécrits via une sauvegarde professeur.
- Les seules modifications conservées sur ces conversations sont les états personnels de lecture, d'archivage, de suppression, de favori et de classement du professeur connecté.
- Les nouveaux messages de la messagerie V2 valident désormais aussi `sharedWith` : un partage vers un élève hors des classes attribuées est refusé, comme un destinataire `to`/`cc`/`bcc` invalide.
- Tests de régression ajoutés pour la falsification d'une conversation et le partage à un élève hors périmètre. Les commits de code/test sont `15f9218`, `f07a1c7`, `07d26cf` et `9dfe6f9`.
- Les workflows déclenchés par ces commits doivent être consultés avant de considérer ce lot validé.


## Cible de livraison macOS Apple Silicon — 12/11/2026

- La plateforme cible est un Mac Apple Silicon (puce M5, macOS 27), et non Fedora.
- L'installateur vérifie macOS, arm64 natif et Python >= 3.10, crée .venv, installe requirements.txt et compile server.py.
- Le lanceur exige l'environnement installé, ouvre Firefox si disponible (sinon le navigateur par défaut) et démarre le serveur sur 127.0.0.1:8765.
- Le workflow vérifie la syntaxe des deux lanceurs macOS. Une CI verte ne remplace pas l'essai réel sur le Mac M5/macOS 27.
- La V25 reste une édition locale de validation, pas une version autorisée pour un usage scolaire réel en réseau : les comptes élèves, l'audit complet des autorisations et les tests fonctionnels restent des conditions de livraison.


## Validation macOS et correction des chemins physiques — 12/11/2026

- La suite complète s'exécute désormais aussi sur un runner macOS : syntaxe des lanceurs, JavaScript, compilation Python et tous les tests Python.
- Le premier passage macOS a mis au jour le traitement de /var et /private/var : les chemins canoniques d'uploads sont maintenant calculés relativement à la racine réelle, et la création de dossiers Cloud vérifie cette même racine réelle.
- Test de régression ajouté pour les chemins résolus via realpath.
- Validation macOS + Ubuntu réussie : [run #43313321068](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43313321068).
- Les deux fichiers .command sont enregistrés avec le bit exécutable Git (mode 100755), indispensable au double-clic dans Finder.
- Ce résultat ne remplace pas un essai sur le Mac M5 exact ni une recette Firefox manuelle.


### Essai sur un réseau privé (expérimental)

Pour un test avec un second ordinateur connecté à la même box privée, lance `Lancer-MaClasse-Reseau.command` sur le Mac serveur. Le script affiche l'adresse à saisir sur l'autre PC. Le serveur se lie à l'adresse IPv4 privée du Mac, jamais à toutes les interfaces. Le mode réseau a depuis été renforcé : il exige désormais HTTPS et un certificat local approuvé sur les clients. La recette multi-appareils reste à effectuer avant tout usage réel.


## Essai LAN privé et première tranche de l'espace élève — 12/11/2026

### Réseau privé expérimental

- `Lancer-MaClasse-Reseau.command` lie le serveur à l'adresse IPv4 privée précise détectée sur le Mac ; le lanceur local reste lié à loopback.
- Le mode LAN exige que les mots de passe provisoires direction et enseignant aient été changés. Il n'écoute pas sur `0.0.0.0` et refuse les adresses publiques.
- Le contrôle Host est lié à l'adresse configurée pour limiter le DNS rebinding.
- À cette date, le mode LAN utilisait HTTP non chiffré. Cette limitation a été corrigée depuis : le serveur exige maintenant HTTPS, mais la confiance des certificats sur les clients et la recette réseau restent à valider.

### Comptes élèves individuels — première tranche

- La direction peut créer un compte élève lié à une fiche existante, avec identifiant et mot de passe provisoire d'au moins 12 caractères ; le changement est imposé à la première connexion.
- La connexion élève est maintenant authentifiée côté serveur. La projection `/api/data` ne transmet que sa fiche, sa classe, ses cours, ses évaluations publiées avec ses propres notes, ses lignes d'assiduité, ses bulletins publiés et validés et ses propres rendus.
- Les élèves peuvent téléverser et envoyer des travaux uniquement dans leur dossier personnel `submissions/<studentId>/`. Le serveur conserve les corrections et les champs canoniques ; un élève ne peut pas modifier sa fiche, les notes, les données d'un camarade ou une correction.
- Les pièces jointes ne sont accessibles que si elles sont référencées dans les données visibles de l'élève.
- La messagerie élève et le Cloud élève restent volontairement masqués/non activés tant que les autorisations spécifiques ne sont pas auditées.
- Tests ajoutés : intégration HTTP de connexion et de cloisonnement, envoi de rendu, accès aux fichiers et tests unitaires de projection/fusion.
- Validation CI du lot : réussite Ubuntu + macOS Apple Silicon, run GitHub Actions #43318282845.


## Préférences d'apparence — 12/11/2026

- Ajout d'un choix explicite dans Paramètres : Automatique (suit le système), Clair et Sombre.
- Le choix est mémorisé localement sur chaque navigateur/appareil ; il ne modifie pas les données scolaires partagées entre les utilisateurs.
- Le thème est appliqué dès le chargement, y compris avant la connexion, puis immédiatement lors d'un changement dans les paramètres.
- Première harmonisation des surfaces, champs, boutons, tableaux, calendriers, messages, badges et notifications en clair/sombre afin de réduire les contrastes incohérents.
- Test de non-régression ajouté pour la présence des trois choix, la persistance locale et les feuilles de style explicites.
- Commits : `299e560` (préférences), `1e36676` (styles), `596e95d` (tests).
- Limite : cette première passe doit encore être vérifiée visuellement dans Firefox sur les pages et composants réels. La CI automatise la présence des règles et les tests existants, mais ne remplace pas une recette visuelle exhaustive.


## Interface et organisation — V25.0.9 · 13/11/2026

- Le Cloud suit désormais une structure de page constante : bandeau général du module, navigation entre les espaces, en-tête de l'espace sélectionné, indicateurs et zone de contenu. L'espace Documents reprend la même architecture.
- Les niveaux de classe sont présentés dans une grille élargie pour éviter le débordement des libellés « Première » et « Terminale ».
- Les cases à cocher utilisent un seul dessin de coche CSS, sans glyphes concurrents susceptibles de produire une seconde marque.
- Le répertoire des élèves sépare visuellement la recherche et les filtres du tableau.
- Les paramètres sont organisés en trois colonnes : Apparence et Salles à gauche, Périodes scolaires au centre, Version et Données à droite (adaptation en deux colonnes puis une colonne sur les écrans plus étroits).
- Les notes techniques de migration de version restent dans ce README et ne sont plus affichées dans la page Professeurs.
- Les onglets de préparation des bulletins restent alignés à gauche et sont centrés verticalement dans leur barre.

La version affichée dans Paramètres doit être incrémentée à chaque mise à jour de l'application. Toute modification de version doit être reportée dans `_all.js`, `index.html`, `VERSION.txt` et ce README.


## Corrections d’interface et audit des comptes — V25.0.10 · 13/11/2026

### Corrections d’interface

- Élèves : la ligne de recherche et le filtre de classe utilisent maintenant une grille à deux colonnes avec un espacement horizontal explicite ; ils passent l’un sous l’autre sur petit écran.
- Paramètres : correction du conflit qui empêchait la disposition annoncée. Une ancienne règle imposait encore `grid-column: 1 / -1 !important` à la carte Données, et les anciennes coordonnées de grille continuaient de primer sur les zones nommées. Les placements historiques sont maintenant neutralisés avant d’appliquer les cinq zones : Apparence et Salles à gauche, Périodes au centre, Version et Données à droite.
- Bulletins : les onglets sont centrés horizontalement dans le panneau, avec un très léger ajustement optique vers la droite et vers le haut. Sur petit écran, le défilement horizontal reste prioritaire.
- Suppression de la mention de compatibilité V19.x dans les paramètres : elle n’a plus de raison d’être pour la nouvelle base.
- Synchronisation du numéro de version entre l’interface, le serveur, `VERSION.txt` et ce README.

### Refonte des comptes — audit et architecture cible (à implémenter)

L’audit du code actuel confirme trois problèmes structurels :

1. Le serveur crée automatiquement un compte direction **et** un compte enseignant provisoires.
2. Le navigateur recrée lui aussi un compte enseignant par défaut dans `ensureUsers()`.
3. L’identité professeur est dupliquée entre `users[]` (identifiants, mot de passe, état du compte) et `teachers[]` (nom, matières, téléphone, classes, profil). Le lien `teacherId` rapproche les deux objets, mais ne supprime pas cette double source de vérité.
4. Le lanceur réseau exige actuellement que les deux mots de passe provisoires, direction et enseignant, aient été changés. Cela impose de configurer un compte enseignant fictif avant même que la direction ait créé l’équipe.

**Décision d’architecture pour la suite :**

- Au premier démarrage, un seul accès est initialisé : celui de la direction. Son mot de passe d’administration est défini avant l’ouverture du réseau local.
- Aucun compte enseignant fictif n’est créé au démarrage. La direction peut créer les fiches et les accès enseignants depuis l’application, y compris lorsqu’elle utilise MaClasse depuis un autre ordinateur du Wi-Fi.
- Une identité professeur devient un enregistrement canonique unique : profil, identifiant, authentification, état actif et paramètres personnels sont portés par le même identifiant. Les classes, matières, fonctions de PP et permissions se rattachent directement à cet identifiant. Il ne doit plus exister de compte enseignant miroir dans une collection séparée.
- La création, la modification, la désactivation et la réinitialisation d’un accès enseignant sont regroupées dans le même parcours que la fiche professeur. Le professeur peut ensuite modifier ses informations personnelles et son mot de passe sans synchroniser deux objets indépendants.
- Les comptes élèves restent un cas distinct lié à une fiche élève ; leurs permissions et leur cycle de vie seront revus dans le même audit, sans ouvrir prématurément les modules qui ne sont pas encore sécurisés.
- Le lancement sur le réseau privé ne dépendra que de la sécurisation du compte direction initial. Les comptes enseignants seront créés ensuite par la direction. Le mode LAN restera expérimental tant que HTTPS et l’audit complet des permissions ne seront pas validés.

**Compatibilité des données :** la V25 est une nouvelle édition de développement. Nous ne chercherons pas à maintenir la compatibilité avec les anciennes sauvegardes V19.x ou avec les anciens modèles de comptes. Le nouveau schéma devra être propre et explicite. En revanche, aucune base V25 existante ne sera effacée silencieusement : une éventuelle remise à zéro devra être annoncée et déclenchée volontairement.

**Ordre de réalisation prévu :**

1. Définir le schéma canonique et les invariants d’identité/permissions.
2. Refaire l’initialisation serveur et supprimer le compte enseignant de démonstration, côté serveur comme côté navigateur.
3. Regrouper création et gestion d’un professeur dans un seul parcours ; supprimer les synchronisations croisées entre deux fiches.
4. Adapter les sessions, projections de données, sauvegardes, messagerie, Cloud et contrôles d’accès à l’identifiant professeur canonique.
5. Simplifier le lanceur réseau pour qu’il vérifie uniquement le compte direction initial.
6. Ajouter des tests d’intégration couvrant première installation, création d’un professeur depuis le réseau, connexion, modification du profil, désactivation et séparation des données entre deux enseignants.

Ce plan est une décision d’architecture, **pas une affirmation que la refonte des comptes est déjà terminée**. Le mode réseau ne doit pas être considéré comme prêt pour des données scolaires réelles.


## Refonte des comptes et de la première installation — V25.0.12 · 13/11/2026

### Modèle canonique

- La collection persistée `users` est la source de vérité des identités et des authentifications.
- Un professeur est un compte unique : identifiant, prénom, nom, e-mail, téléphone, matières, notes de profil, empreinte de mot de passe et statut actif sont stockés ensemble dans le même enregistrement.
- Il n'existe plus de collection persistée `teachers`. La liste `db.teachers` du navigateur est une projection calculée des comptes `users` de rôle `teacher`, pour alimenter les modules qui affichent les profils.
- Les classes référencent directement l'identifiant du compte professeur dans `teacherIds` et `principalTeacherId`. Les classes enseignées sont calculées depuis ces relations, pas synchronisées dans une deuxième fiche.
- Les comptes élèves restent dans `users` avec un lien vers une fiche élève par `studentId`, car l'élève est une personne scolarisée dont le dossier existe indépendamment de son accès numérique.

### Première installation

- Le serveur ne crée plus de comptes au démarrage.
- `GET /api/auth/setup-status` indique si la base est vierge.
- L'assistant de première ouverture demande le nom, l'identifiant et un mot de passe de direction d'au moins 12 caractères.
- `POST /api/auth/setup` est à usage unique : il refuse toute seconde initialisation ou une base déjà occupée. Il crée un seul compte direction et ouvre sa session.
- Il n'existe plus de compte `enseignant`, de mot de passe universel, ni d'étape locale consistant à sécuriser un professeur fictif.
- La connexion est unifiée : le serveur identifie le rôle à partir du compte, sans demander de choisir à l'avance un espace qui pourrait ne pas encore exister.

### Gestion des professeurs

- L'administration crée et modifie le compte et le profil dans un seul formulaire.
- La route serveur `/api/admin/teacher` valide les champs, l'unicité de l'identifiant, le mot de passe provisoire et les classes/PP attribuées. L'empreinte est calculée côté serveur.
- Le professeur modifie son propre profil via `/api/teacher/profile`. Le changement de mot de passe reste une opération d'authentification séparée, vérifiant le mot de passe actuel.
- La désactivation passe par `/api/admin/user-status` et invalide immédiatement les sessions de ce compte.
- Les sauvegardes générales ne peuvent ni créer, ni remplacer, ni écraser les comptes ou leurs empreintes. Les comptes sont gérés exclusivement par les routes dédiées.
- Les réponses `/api/data` n'exposent jamais les empreintes de mots de passe au navigateur, y compris dans la projection de fiche professeur.

### Réseau local et sauvegardes

- Le lanceur réseau vérifie désormais uniquement la présence d'un compte direction initialisé avec une empreinte PBKDF2 sécurisée ; aucun compte enseignant n'est requis.
- Les comptes enseignants peuvent être créés depuis l'interface direction, donc depuis un poste du réseau local lorsque le mode LAN sera autorisé.
- Les sauvegardes n'exportent plus de collection professeur séparée. À la restauration, l'ancienne clé `teachers` est ignorée : le schéma V25.0.12 est volontairement neuf et ne promet pas la compatibilité avec les anciennes sauvegardes.
- Le mode LAN reste expérimental. Depuis la mise à jour de sécurisation TLS, le serveur refuse HTTP sur le réseau ; la validation de la confiance des certificats et la recette complète restent nécessaires.

### Vérifications attendues

Les tests d'intégration couvrent l'initialisation unique, le refus des identifiants par défaut, la création d'un compte professeur par la direction, le changement du mot de passe provisoire, la protection des empreintes, la désactivation et l'isolation des données par classe.


### Derniers verrouillages du modèle canonique — V25.0.12

- Les contrôles de périmètre, les autorisations Cloud et les boîtes de messagerie identifient désormais un professeur à partir de l'identifiant du compte canonique, sans lire une ancienne collection de fiches professeur.
- Les comptes élèves reçoivent les noms des enseignants de leur classe depuis les comptes canoniques, avec une projection limitée au prénom et au nom.
- Les anciennes fiches `teachers[]` ne sont plus utilisées comme solution de repli dans les permissions, les projections ou les sauvegardes. La clé historique est écartée à l'initialisation/restauration.
- La direction peut également changer son propre mot de passe après la première configuration.
- Les tests de permissions Cloud, messagerie, espace élève, profil professeur et sauvegarde utilisent désormais le modèle canonique.


## Comptes élèves et enregistrement avant déconnexion — V25.0.13 · 13/11/2026

- La fiche de direction demande maintenant un prénom et un nom distincts ; ces deux champs sont conservés dans le compte canonique.
- La création d'un professeur peut générer automatiquement un mot de passe provisoire aléatoire. Il est affiché une seule fois après création ; le changement vers un mot de passe personnel d'au moins 12 caractères reste obligatoire à la première connexion. Un mot de passe provisoire saisi manuellement peut faire 8 caractères ou plus.
- Les professeurs peuvent créer les accès des élèves de leurs propres classes depuis le module Élèves. Le serveur vérifie le rattachement réel de la classe au professeur : impossible de créer un accès pour un élève hors périmètre.
- Les accès élèves peuvent recevoir un mot de passe provisoire aléatoire, affiché une seule fois après création ; l'élève doit le remplacer par un mot de passe personnel d'au moins 12 caractères.
- Correction d'un risque de perte de fiches lors de la déconnexion : l'enregistrement était différé de 180 ms, mais la déconnexion vidait immédiatement la base locale en mémoire. Le minuteur pouvait donc enregistrer un instantané vide après la déconnexion. La déconnexion attend maintenant la sauvegarde en attente et est annulée si celle-ci échoue.
- Ces changements ne rendent pas le mode réseau prêt pour un établissement : le serveur exige désormais HTTPS, mais la confiance CA sur les appareils et les tests réels multi-postes restent à effectuer. Ne pas y stocker de données scolaires réelles.


## V25.0.13 — comptes élèves, identifiants provisoires et déconnexion

- La configuration initiale accepte désormais le prénom et le nom distincts de la direction, tout en conservant la compatibilité avec les clients historiques qui transmettent un seul champ de nom.
- La création d'un compte professeur génère un mot de passe provisoire aléatoire si le champ est laissé vide. Le mot de passe est communiqué une seule fois dans la réponse de création ; l'obligation de changement vers un mot de passe personnel d'au moins 12 caractères reste active.
- Les professeurs peuvent créer des comptes élèves uniquement pour les élèves de leurs classes. Le serveur vérifie cette appartenance et génère un mot de passe provisoire si aucun n'est fourni.
- La projection de données professeur inclut les informations publiques des comptes élèves de son périmètre, sans transmettre les empreintes de mots de passe.
- La déconnexion attend la fin de la sauvegarde différée ; si celle-ci échoue, la déconnexion est annulée au lieu de vider l'état local.
- Tests HTTP ajoutés pour la création d'élèves par un professeur, le refus d'un élève hors périmètre, l'accès au compte créé et sa visibilité sans empreinte de mot de passe.
- Une mise à jour macOS non destructive est fournie par `Mettre-A-Jour-MaClasse.command` : elle vérifie l'état Git, sauvegarde `data/`, refuse les branches divergentes, applique uniquement une avance rapide et vérifie le serveur. Elle ne remplace pas une sauvegarde externe régulière.

**Validation CI :** le run [#43425595733](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/43425595733) a terminé avec succès sur Ubuntu et macOS, y compris l'installateur Apple Silicon et tous les tests Python/JavaScript. Cela valide les tests automatisés, pas une recette multi-appareils réelle.

**Mise à jour locale :** dans un clone Git propre de MaClasse, double-cliquer sur `Mettre-A-Jour-MaClasse.command`. Ne pas supprimer `data/`. Si l'installation n'est pas un clone Git, ne pas utiliser ce script : une procédure de migration dédiée est nécessaire.

**Limite réseau :** le mode LAN est maintenant chiffré en HTTPS et HTTP est refusé sur une adresse privée. Il reste réservé aux tests tant que la confiance CA des clients et la recette réseau ne sont pas validées.


## Réseau local HTTPS — sécurisation technique en cours

Le serveur ne démarre plus en HTTP lorsqu'il est lié à une adresse IPv4 privée : il exige `MACLASSE_TLS_CERT` et `MACLASSE_TLS_KEY`, utilise TLS 1.2 au minimum, marque les cookies de session `Secure` et refuse une origine HTTP sur le listener HTTPS.

- Mac : `Configurer-MaClasse-Reseau.command` puis `Lancer-MaClasse-Reseau.command`.
- Linux/Fedora : `Installer-MaClasse-Linux.sh`, puis `Lancer-MaClasse-Reseau.sh`.
- Le certificat racine public `data/tls/ca.crt` doit être installé comme autorité de confiance sur chaque appareil client. Les clés privées `ca.key` et `server.key` restent exclusivement sur le serveur et sont exclues de Git.
- Les scripts Linux de mise à jour et de configuration réseau sauvegardent les données locales avant toute mise à jour.

**Important :** cette évolution verrouille le serveur contre le démarrage LAN non chiffré, mais elle ne constitue pas encore une recette réseau complète. La confiance CA côté clients, le renouvellement du certificat, le pare-feu, les changements d'adresse IP, les tests réels entre plusieurs appareils et les tests de charge restent à valider. Aucun usage avec des données scolaires réelles n'est autorisé avant cette recette.


Guide opératoire : [docs/RESEAU_HTTPS.md](docs/RESEAU_HTTPS.md) — installation Fedora/Linux, lancement HTTPS, import de l'autorité de certification sur macOS/Fedora/Windows, pare-feu, adresse IP stable et sauvegarde des clés.


## V25.0.17 — accès élèves administrables et réseau HTTPS

- Les enseignants peuvent désormais consulter les accès des élèves de leurs classes, réinitialiser un mot de passe perdu (nouveau provisoire aléatoire, affiché une seule fois), suspendre un accès et le réactiver.
- Le serveur vérifie les droits sur la classe pour chaque réinitialisation et changement d'état ; les sessions de l'élève sont révoquées lors d'une réinitialisation ou d'une désactivation.
- Une réinitialisation ne réactive pas implicitement un compte déjà désactivé.
- Le mode réseau exige HTTPS, TLS 1.2 minimum, cookies Secure, HSTS et une origine HTTPS stricte. Le serveur refuse de démarrer en HTTP sur une adresse LAN.
- Scripts d'installation, de mise à jour et de lancement HTTPS ajoutés pour Fedora/Linux, en complément des scripts macOS.
- Guide détaillé : [Réseau local HTTPS](docs/RESEAU_HTTPS.md).
- Tests automatisés couvrant les comptes élèves (création, périmètre, réinitialisation, suspension, réactivation), la génération de l'autorité/certificat TLS, les cookies Secure, HSTS et le refus du LAN HTTP.

**Limite de livraison :** la CI et les tests d'intégration automatisés ne remplacent pas encore la recette sur le PC Fedora cible et les postes clients réels. Tant que la confiance CA sur les navigateurs, le pare-feu, la stabilité IP, les sauvegardes/restaurations et les tests multi-utilisateurs n'ont pas été vérifiés physiquement, MaClasse reste en alpha et ne doit pas contenir de données scolaires réelles.


### Comptes élèves canoniques et matières des enseignants — V25.0.17

- La fiche élève est désormais l'enregistrement canonique du compte : identifiant interne unique, identifiant de connexion, empreinte du mot de passe, état actif et changement obligatoire du mot de passe provisoire sont conservés sur le même objet dans `students[]`.
- Aucun deuxième compte élève n'est créé dans `users[]`. L'API construit une projection publique compatible avec les écrans existants, sans jamais exposer les empreintes de mots de passe.
- La connexion, les sessions, le changement de mot de passe, la réinitialisation et l'activation/désactivation des élèves utilisent directement la fiche canonique.
- Les professeurs peuvent créer des élèves dans leurs classes et leur attribuer un identifiant ainsi qu'un mot de passe provisoire affiché une seule fois.
- L'enregistrement d'une fiche élève attend maintenant la confirmation du serveur ; en cas d'échec, l'interface restaure l'état précédent au lieu d'annoncer une réussite fictive.
- Les enseignants retrouvent la modification libre de leurs matières depuis leur profil. Ces matières restent utilisées par l'emploi du temps et les règles de bulletins.
- Les anciennes sauvegardes V25 utilisant deux enregistrements séparés pour les élèves ne sont pas migrées par cette version : repartir d'une base neuve, comme prévu pour cette recette.
- Tests d'intégration HTTP : création d'un élève par un professeur, sauvegarde, accès canonique, connexion, changement de mot de passe, réinitialisation et désactivation.


### Intégrité des bulletins — publication et groupes

Le recalcul serveur des bulletins PDF a été renforcé après ajout d'un test de non-régression : les moyennes officielles excluent désormais les évaluations non publiées, les évaluations dont la date de publication est future, les périodes hors trimestre et les évaluations réservées à un autre groupe. Les statistiques de classe sont recalculées élève par élève avec les mêmes règles de groupe ; les compétences suivent le même périmètre. Les absences et retards restent limités à la classe et à la période du bulletin.

### Persistance lors de la fermeture du navigateur

La déconnexion attend la sauvegarde en attente. En complément, le navigateur affiche maintenant son avertissement natif si l'utilisateur tente de fermer ou recharger l'onglet alors qu'une sauvegarde est en attente ou en échec. Cela réduit le risque de perte en cas de fermeture brutale ; il faut toujours attendre l'état « Enregistré » avant de quitter.


## V25.0.19 — correction du moteur EDT et des noms de fichiers

- La date « À partir du » est maintenant interprétée comme la borne de début de la période ; le premier cours est le premier jour correspondant au jour choisi, à cette date ou après.
- Les récurrences « une seule fois », toutes les deux semaines, toutes les trois semaines et toutes les N semaines sont ancrées sur cette première occurrence, et non sur le lundi de la date de début. Cela évite les cours absents lorsque le jour choisi n'est pas un lundi.
- Les tests de calendrier couvrent désormais les sept jours, les premières occurrences, les semaines intermédiaires et les retours de navigation ; le même moteur d'occurrences sert aux vues enseignant et élève.
- Les noms de fichiers sont transmis en UTF-8 percent-encodé dans un en-tête ASCII, puis décodés côté serveur. Les apostrophes typographiques, accents et caractères combinés ne font plus échouer `fetch`.
- Le certificat HTTPS local est émis par l'autorité MaClasse. Chaque appareil client doit approuver `data/tls/ca.crt` ; ne jamais contourner l'avertissement ni partager `ca.key` ou `server.key`.
