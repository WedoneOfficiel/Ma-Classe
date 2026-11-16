# AMEL-01 — Gestionnaire de mises à jour MaClasse

**Statut : première chaîne Linux complète implémentée en code (détection, préparation, installation immédiate ou programmée, notifications et rollback) ; CI en cours de validation, recette Fedora et macOS restantes.**  
**Branche de travail :** `feature/amel-01-update-manager`  
**Branche de départ :** `fix/v25-student-teacher-workflows` (PR #9 conservée intacte).

## Objectif

Permettre à la direction de rechercher, télécharger, planifier et installer une version officielle de MaClasse depuis l'interface, sans ouvrir de terminal au quotidien. Les commandes manuelles restent disponibles comme procédure de secours.

Les données métier et les fichiers téléversés ne doivent jamais être remplacés avec le code de l'application.

## Décisions d'architecture

### 1. Versions officielles

- Les versions distribuées sont des **GitHub Releases stables**, identifiées par un tag versionné (`v25.x.y`), qui ne doit jamais être déplacé après publication.
- Le workflow `publish-release.yml` construit l'archive depuis les fichiers suivis par Git, vérifie la concordance tag/`VERSION.txt` et publie un manifeste avec SHA-256 et le schéma de données minimal. L'archive n'embarque donc pas les données locales non suivies par Git.
- La branche `main` n'est jamais installée directement sur une instance en production.
- Chaque publication fournit un manifeste versionné (version, tag, notes, version minimale du schéma de données et empreinte SHA-256 de l'archive). Les migrations éventuelles devront être déclarées explicitement avant d'être activées.
- L'archive est téléchargée depuis la release puis vérifiée avant d'être considérée comme installable. L'instance n'exécute jamais un script téléchargé depuis une URL arbitraire.
- Les versions incompatibles avec la version de données installée sont refusées avant la maintenance.

### 2. Séparation code / données

- Le code actif et les versions préparées vivent dans `data/program/versions/`. Le lien relatif `data/program/current` désigne la version active, ce qui permet de déplacer/restaurer le dossier sans casser la cible. Le lanceur manuel Linux utilise lui aussi ce lien pour démarrer la bonne version. Le serveur reçoit `MACLASSE_DATA_DIR` pour conserver base, pièces jointes et certificats hors des versions.
- La base, les pièces jointes, les sauvegardes, les paramètres locaux et l'identité TLS restent dans le répertoire de données persistant.
- Une mise à jour ne copie, ne supprime et ne remplace jamais ce répertoire.
- Les migrations de données sont explicites, versionnées et exécutées après sauvegarde. Une migration non réversible bloque le retour automatique et doit être déclarée dans le manifeste.

### 3. Gestionnaire indépendant du serveur web

Le serveur Python ne doit pas tenter de remplacer ou redémarrer son propre processus.

- Un superviseur local indépendant contrôle le cycle de vie du serveur.
- Sur Fedora/Linux, le service utilisateur **systemd** supervise MaClasse et son gestionnaire. L'installation configure le démarrage automatique et le maintien du service après déconnexion (linger).
- Sur macOS, un agent **launchd** assure le même rôle.
- Le serveur web déclenche uniquement des unités systemd prédéfinies via des appels locaux fixes. Aucun endpoint réseau ne permet de lancer une commande shell libre.
- Le service reste sans privilèges root et les unités limitent les écritures au dossier de données. Le superviseur et le serveur tournent sous le même compte système dédié à MaClasse.

### 4. Parcours de mise à jour

1. Vérification périodique de la dernière release stable, avec temporisation et gestion des erreurs réseau.
2. Notification visible uniquement dans l'espace direction.
3. La direction choisit **Installer maintenant** ou **Télécharger et programmer**.
4. Le téléchargement et les contrôles se font avant l'interruption. Une préparation échouée ne touche pas au serveur actif.
5. Pour une installation programmée, tous les rôles reçoivent une notification avec la date et l'heure locales exactes. La direction peut annuler ou modifier l'horaire directement depuis Paramètres.
6. À l'heure prévue, le serveur cesse d'accepter de nouvelles connexions ; son arrêt gracieux attend la fin des requêtes déjà engagées. systemd borne l'attente à 120 secondes avant arrêt forcé.
7. Une copie horodatée de la base JSON (qui contient aussi les paramètres) est créée avant l'arrêt. En cas d'échec, cette copie est restaurée avant de redémarrer l'ancienne version. Les fichiers téléversés restent dans leur emplacement persistant et ne sont pas recopiés pendant la mise à jour.
8. Le gestionnaire active la version préparée et redémarre le serveur.
9. Des contrôles de santé vérifient que le serveur répond, que la version attendue est active et que la base est lisible.
10. Si le démarrage ou le contrôle échoue, le gestionnaire réactive la version précédente et redémarre. La sauvegarde reste disponible. Après une installation réussie, le nettoyage conserve les trois versions récentes ainsi que la version active et son prédécesseur pour le retour arrière.

### 5. Notifications et sécurité

- Seule la direction voit les informations de version et les actions de mise à jour.
- Tous les comptes reçoivent uniquement l'annonce de maintenance programmée, sa date/heure et le rappel d'enregistrer leur travail.
- Une maintenance annulée ou reprogrammée met à jour la notification.
- Les actions de gestion sont authentifiées côté serveur et réservées au rôle administrateur ; masquer un bouton dans le navigateur ne constitue jamais un contrôle d'accès.
- Les archives et manifestes sont vérifiés ; les chemins d'archive sont contrôlés contre les traversées de répertoires et les liens symboliques dangereux.
- Le gestionnaire n'écoute pas sur l'interface réseau et ne donne pas de privilèges généraux au serveur web.

## État actuel constaté

- `VERSION.txt`, `server.py` et `_all.js` exposent un numéro de version, mais aucun contrôle de release n'est intégré.
- Les scripts macOS et Linux font actuellement un `git fetch origin main` puis une avance rapide du clone local.
- Le module `update_manager.py` interroge la dernière release stable, valide son manifeste, limite les téléchargements aux hôtes GitHub en HTTPS, vérifie l'empreinte SHA-256 et extrait l'archive sans liens symboliques ni chemins traversants dans `data/program/versions/Vx.y.z/`. Il prépare aussi un environnement Python propre à la version et vérifie la compilation Python/JavaScript.
- La vérification des releases stables est lancée à la connexion de la direction puis répétée toutes les six heures ; la direction peut aussi la relancer manuellement depuis Paramètres. Une nouvelle version est signalée uniquement à la direction.
- La direction peut télécharger/préparer une version compatible depuis Paramètres. Chaque version préparée possède son propre `.venv` et un marqueur `maclasse-prepared.json`. Le serveur actif n'est pas interrompu.
- La direction dispose désormais d'une carte Paramètres « Mises à jour » et d'une route serveur de vérification réservée au rôle administrateur.
- Le moteur indépendant `Appliquer-Mise-A-Jour-MaClasse-Linux.sh` sauvegarde `maclasse.json`, attend la fin des requêtes engagées (limite systemd de 120 s), bascule atomiquement le lien de version, redémarre et contrôle la santé HTTPS. En cas d'échec, il restaure la base et le code précédents avant de relancer le service. Le moteur de mise à jour est lui-même exécuté depuis le lien de version active afin que les correctifs du moteur soient repris à chaque nouvelle release. Le moteur est appelé depuis la version active pour que ses correctifs restent à jour au fil des releases. Il n'a pas encore été exécuté sur le PC Fedora cible.
- La base, les pièces jointes et les certificats sont désormais servis depuis `MACLASSE_DATA_DIR`, indépendamment du dossier de code versionné. Le serveur attend la fin des requêtes déjà engagées lors de l'arrêt supervisé.
- La direction peut programmer une installation à une date/heure précise ou l'annuler. Un timer systemd ponctuel UTC déclenche le même moteur d'installation que l'action immédiate.
- Une bannière de maintenance est exposée à tous les rôles authentifiés, avec date/heure locale et rappel d'enregistrer le travail. Elle est actualisée à la connexion puis périodiquement.
- Le lanceur systemd utilise `data/program/current` pour sélectionner le code actif. Le lancement manuel classique reste distinct et n'expose pas les actions d'installation depuis l'interface.
- Le secours CLI `Mettre-A-Jour-MaClasse-Linux.sh` détecte une installation supervisée et utilise le même vérificateur de releases, la même préparation et le même service d'installation ; il n'effectue aucun `git pull` dans ce mode. En mode historique non supervisé, il refuse désormais de modifier le code si un serveur MaClasse est actif.
- Les paramètres affichent uniquement le numéro de version.

## Plan d'implémentation

### Phase A — socle de publication et de supervision
- [x] Définir le format du manifeste et le processus de publication GitHub Release.
- [x] Ajouter le premier superviseur Linux systemd utilisateur et ses scripts d'installation/désinstallation (validation CI et recette Fedora encore nécessaires).
- Le socle Linux est expérimental : après initialisation locale et création du compte direction, l'installation se lance avec `bash Installer-Service-MaClasse-Linux.sh`. L'arrêt se fait avec `systemctl --user stop maclasse.service` ; les journaux sont consultables avec `journalctl --user -u maclasse.service -f`.
- L'installateur active le maintien du gestionnaire utilisateur au démarrage via `loginctl enable-linger` (demande sudo si nécessaire). Il ne supprime ni le programme ni les données lors de la désinstallation.
- Garder le mode de lancement manuel utilisable comme secours.
- Ajouter tests d'installation, de démarrage, d'arrêt, de redémarrage et de permissions.
- Les tests unitaires du vérificateur couvrent versions, releases instables, manifeste, empreinte, hôtes non approuvés et chemins ZIP dangereux ; le job Linux a réussi sur le commit précédent, la nouvelle suite d'intégration est en cours de CI.

### Phase B — gestionnaire et préparation
- [x] Ajouter le premier module de vérification des releases et la préparation d'archive isolée.
- [x] Ajouter les routes serveur réservées à la direction pour vérifier et préparer une version.
- Tester les archives invalides, versions incompatibles, interruptions réseau et échecs de préparation.

### Phase C — interface et planification
- [x] Ajouter l'API authentifiée de consultation et d'action réservée à la direction (vérification, préparation et demande d'installation immédiate).
- [x] Ajouter le centre de mises à jour dans Paramètres, visible uniquement à la direction.
- [x] Ajouter la programmation ponctuelle, l'annulation et la reprogrammation depuis l'interface via timer systemd.
- [x] Ajouter la bannière de maintenance visible par tous les rôles.
- Tester les fuseaux horaires, changements d'heure, maintenance annulée et utilisateurs connectés.

### Phase D — installation atomique et reprise
- [x] Ajouter la première chaîne Linux : environnement par version, sauvegarde de la base, arrêt propre avec attente des requêtes, bascule atomique, redémarrage, health-check HTTPS et rollback du code et de la base.
- [x] Ajouter un scénario d'intégration Linux simulant une installation réussie et un health-check défaillant ; vérifier la bascule, la restauration du code et de la base.
- Les tests automatisés couvrent aussi le timer, l'annulation, les accès par rôle, la bannière et les scripts systemd. La CI du dernier commit et les pannes supplémentaires restent à valider.
- Tester sur Fedora avec le matériel cible avant toute utilisation avec des données scolaires réelles.

### Phase E — macOS
- Ajouter le superviseur launchd et reprendre les mêmes tests de cycle de vie.
- Conserver les commandes `.command` comme secours.

## Critères d'acceptation

- Une version préparée ou téléchargée ne modifie jamais le service actif.
- Une version non officielle, corrompue ou incompatible est refusée.
- Les données métier, les pièces jointes et l'identité TLS survivent à une mise à jour.
- Une installation immédiate et une installation programmée suivent le même moteur.
- Les notifications de maintenance sont cohérentes pour tous les rôles.
- Une mise à jour qui ne passe pas le contrôle de santé restaure automatiquement le code précédent.
- Aucun statut « terminé » n'est affiché avant confirmation du redémarrage et du contrôle de santé.
- Les tests Linux, macOS, API, navigateur et scénarios de panne sont verts avant de qualifier la fonctionnalité de « supposée résolue ».

## Hors périmètre

- Pas d'installation automatique sans accord de la direction.
- Pas de fenêtres de maintenance récurrentes.
- Pas de système complexe de récupération de sessions ou de brouillons côté navigateur.
- Pas d'exécution de commandes arbitraires depuis l'interface.
- Pas de déploiement sur l'installation de l'utilisateur pendant le développement.
