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
