# MaClasse

Application web de gestion scolaire, pensée pour centraliser les outils du quotidien d'un établissement dans une interface unique : suivi des élèves et des classes, cours, évaluations et notes, absences, bulletins, messagerie et espace documentaire/Cloud.

> **Objectif du projet :** disposer d'une application simple à utiliser, fiable et sécurisée, hébergée sur un ordinateur de la maison ou de l'établissement et accessible depuis les autres appareils du réseau local via un navigateur. Aucune exposition publique à Internet n'est prévue pour le déploiement domestique.

---

## État du projet

**Branche de référence :** `main`  
**Version de travail annoncée :** V25.0.7 (alpha)  
**Statut :** développement et sécurisation en cours — **pas prête pour une utilisation multi-postes sur le réseau local**.

### Point de synchronisation GitHub

Le commit d'import `a2e83ef` contient bien le code applicatif et les ressources de MaClasse : `server.py`, `index.html`, `_all.js`, les scripts macOS, les documents de version et les tests. La version source est confirmée par `VERSION.txt` et `server.py` : **V25.0.7**. Le dépôt a été inspecté directement ; le constat précédent selon lequel il ne contenait que le README était erroné.

Le fichier local `data/maclasse.json` ne contenait que les deux comptes provisoires. Il a été retiré du suivi Git et ajouté au `.gitignore`, afin que les futures données réelles d'élèves et d'établissement ne soient pas publiées. Le serveur recrée ce fichier au démarrage s'il est absent.

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
- [ ] Mettre en place HTTPS adapté au réseau local et documenter la confiance du certificat sur les appareils.
- [ ] N'écouter sur l'adresse LAN qu'après validation de l'authentification, des autorisations et de HTTPS.
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
