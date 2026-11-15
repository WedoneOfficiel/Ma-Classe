# AMEL-01 — Gestionnaire de mises à jour MaClasse

**Statut : conception validée ; socle de supervision Linux en cours, gestionnaire de mises à jour non encore implémenté.**  
**Branche de travail :** `feature/amel-01-update-manager`  
**Branche de départ :** `fix/v25-student-teacher-workflows` (PR #9 conservée intacte).

## Objectif

Permettre à la direction de rechercher, télécharger, planifier et installer une version officielle de MaClasse depuis l'interface, sans ouvrir de terminal au quotidien. Les commandes manuelles restent disponibles comme procédure de secours.

Les données métier et les fichiers téléversés ne doivent jamais être remplacés avec le code de l'application.

## Décisions d'architecture

### 1. Versions officielles

- Les versions distribuées sont des **GitHub Releases stables**, identifiées par un tag immuable (`v25.x.y`).
- La branche `main` n'est jamais installée directement sur une instance en production.
- Chaque publication fournit un manifeste versionné (version, tag, notes, version minimale du schéma de données, éventuelles migrations, empreinte SHA-256 de l'archive).
- L'archive est téléchargée depuis la release puis vérifiée avant d'être considérée comme installable. L'instance n'exécute jamais un script téléchargé depuis une URL arbitraire.
- Les versions incompatibles avec la version de données installée sont refusées avant la maintenance.

### 2. Séparation code / données

- Le code actif et les versions préparées vivent dans des répertoires de programme distincts.
- La base, les pièces jointes, les sauvegardes, les paramètres locaux et l'identité TLS restent dans le répertoire de données persistant.
- Une mise à jour ne copie, ne supprime et ne remplace jamais ce répertoire.
- Les migrations de données sont explicites, versionnées et exécutées après sauvegarde. Une migration non réversible bloque le retour automatique et doit être déclarée dans le manifeste.

### 3. Gestionnaire indépendant du serveur web

Le serveur Python ne doit pas tenter de remplacer ou redémarrer son propre processus.

- Un superviseur local indépendant contrôle le cycle de vie du serveur.
- Sur Fedora/Linux, le service utilisateur **systemd** supervise MaClasse et son gestionnaire. L'installation configure le démarrage automatique et le maintien du service après déconnexion (linger).
- Sur macOS, un agent **launchd** assure le même rôle.
- Le serveur web communique avec le gestionnaire par un canal local non exposé au réseau (socket Unix ou mécanisme local équivalent), avec permissions limitées au compte qui exécute MaClasse.
- Le gestionnaire n'accepte que des opérations prédéfinies : vérifier, préparer, programmer, annuler, installer. Aucune commande shell libre ne vient de l'interface web.

### 4. Parcours de mise à jour

1. Vérification périodique de la dernière release stable, avec temporisation et gestion des erreurs réseau.
2. Notification visible uniquement dans l'espace direction.
3. La direction choisit **Installer maintenant** ou **Télécharger et programmer**.
4. Le téléchargement et les contrôles se font avant l'interruption. Une préparation échouée ne touche pas au serveur actif.
5. Pour une installation programmée, tous les rôles reçoivent une notification avec la date et l'heure locales exactes. La direction peut annuler ou modifier l'horaire.
6. Au début de la maintenance, les nouvelles écritures sont brièvement bloquées ; le gestionnaire attend la fin des écritures déjà engagées (délai maximal borné), puis arrête le serveur proprement.
7. Une sauvegarde cohérente de la base et des paramètres locaux est créée. Les fichiers téléversés restent dans leur emplacement persistant ; leur sauvegarde relève de la politique de sauvegarde existante, pas d'une recopie à chaque mise à jour.
8. Le gestionnaire active la version préparée et redémarre le serveur.
9. Des contrôles de santé vérifient que le serveur répond, que la version attendue est active et que la base est lisible.
10. Si le démarrage ou le contrôle échoue, le gestionnaire réactive la version précédente et redémarre. La sauvegarde reste disponible.

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
- Les scripts ne gèrent ni la programmation, ni les notifications, ni l'arrêt/redémarrage supervisé, ni le contrôle de santé après redémarrage.
- Le lanceur actuel exécute `server.py` en processus enfant et attend ce processus ; ce modèle ne suffit pas pour un auto-remplacement robuste.
- Les paramètres affichent uniquement le numéro de version.

## Plan d'implémentation

### Phase A — socle de publication et de supervision
- Définir le format du manifeste et le processus de publication GitHub Release.
- [x] Ajouter le premier superviseur Linux systemd utilisateur et ses scripts d'installation/désinstallation (validation CI et recette Fedora encore nécessaires).
- Garder le mode de lancement manuel utilisable comme secours.
- Ajouter tests d'installation, de démarrage, d'arrêt, de redémarrage et de permissions.

### Phase B — gestionnaire et préparation
- Ajouter le gestionnaire local indépendant.
- Télécharger une release, vérifier son empreinte, l'extraire dans un répertoire de version isolé et effectuer les contrôles sans toucher à la version active.
- Tester les archives invalides, versions incompatibles, interruptions réseau et échecs de préparation.

### Phase C — interface et planification
- Ajouter l'API authentifiée de consultation et d'action réservée à la direction.
- Ajouter le centre de mises à jour dans Paramètres.
- Ajouter la programmation, l'annulation et les notifications multi-rôles.
- Tester les fuseaux horaires, changements d'heure, maintenance annulée et utilisateurs connectés.

### Phase D — installation atomique et reprise
- Ajouter le verrouillage bref des écritures, sauvegarde cohérente, bascule atomique de version, redémarrage et contrôle de santé.
- Simuler les pannes à chaque étape et vérifier le retour à la version précédente.
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
