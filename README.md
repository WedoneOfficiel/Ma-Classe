# MaClasse

Application web de gestion scolaire, pensée pour centraliser les outils du quotidien d'un établissement dans une interface unique : suivi des élèves et des classes, cours, évaluations et notes, absences, bulletins, messagerie et espace documentaire/Cloud.

> **Objectif du projet :** disposer d'une application simple à utiliser, fiable et sécurisée, hébergée sur un ordinateur de la maison ou de l'établissement et accessible depuis les autres appareils du réseau local via un navigateur. Aucune exposition publique à Internet n'est prévue pour le déploiement domestique.

---

## État du projet

**Branche de référence :** `main`  
**Version de travail annoncée :** V25.0.7 (alpha)  
**Statut :** développement et sécurisation en cours — **pas prête pour une utilisation multi-postes sur le réseau local**.

### Point de synchronisation GitHub

Lors de la vérification du dépôt le 12 novembre 2026, la branche `main` ne contenait que ce README (aucun code applicatif ni fichier de version n'était visible dans le dépôt). Les versions V25.0.1 à V25.0.7 ont été travaillées dans les échanges précédents et annoncées sous forme d'archives, mais leur présence dans ce dépôt n'est donc **pas confirmée**.

Avant de poursuivre les modifications du code, synchroniser ici les vrais fichiers de la dernière version V25. Ne pas considérer ce README comme la preuve que ces changements sont déjà intégrés au dépôt.

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

## Reste à faire — priorités

### Bloquants avant le réseau local multi-postes

- [ ] Synchroniser le code V25 réel dans ce dépôt et confirmer la version exacte.
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

*Cet historique reflète les travaux rapportés avant la synchronisation du dépôt ; il devra être confirmé à partir des commits et des fichiers sources.*
