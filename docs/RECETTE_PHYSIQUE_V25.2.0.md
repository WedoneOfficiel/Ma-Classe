# Recette physique préalable à V25.2.0

**État : à effectuer.** Aucun contrôle sur l'installation réelle n'est réputé réussi sur la seule base de ce document ou de la CI.

Cette procédure est le dernier contrôle avant fusion et publication. Tous les essais destructifs doivent se faire sur une copie isolée. Ne jamais communiquer une base, des pièces jointes, des mots de passe ou des clés privées dans GitHub, ChatGPT ou un ticket.

## 1. Verrou de sécurité

- [ ] Identifier le vrai dossier MaClasse et le vrai répertoire de données : MACLASSE_DATA_DIR s'il est configuré, sinon le dossier data/ de l'installation.
- [ ] Arrêter proprement le serveur ou le service supervisé avant de faire une copie cohérente. Ne pas copier la base pendant que des écritures sont en cours.
- [ ] Faire une copie externe protégée du répertoire de données complet, y compris maclasse.json, uploads/, backups/, tls/, les paramètres et les états du gestionnaire. Conserver cette copie hors du dépôt.
- [ ] Vérifier que la copie externe est lisible et contient la base et les pièces jointes attendues. Garder cette copie originale intacte.
- [ ] Préparer une seconde copie de travail, distincte de la production, avec le code candidat V25.2.0. Tous les essais destructifs (import, suppression, restauration et rollback) se font uniquement sur cette copie.
- [ ] Isoler le service et le port de test : ne pas lancer deux instances utilisant le même data/, le même port ou le même identifiant LaunchAgent. Ne pas remplacer le plist de production par celui d'une copie sans avoir prévu son rétablissement.
- [ ] Vérifier que le serveur de production peut être redémarré depuis son dossier et ses données d'origine. Ne jamais recopier la base de test vers la production.

**Arrêt immédiat :** si la sauvegarde n'est pas vérifiée, si le chemin des données est incertain, si une instance utilise encore le dossier cloné ou si le service de production risque d'être remplacé, ne pas poursuivre.

## 2. Essais préalables sur la copie — avant publication

La V25.2.0 candidate n'est pas encore une GitHub Release stable ; le gestionnaire officiel ne doit donc pas être supposé pouvoir la télécharger. Avant la publication, tester le code de la branche candidate dans la copie isolée (sans basculer la production et sans utiliser le mécanisme de mise à jour stable).

- [ ] Démarrer la copie de travail sur le code candidat, en conservant la copie externe intacte et la production arrêtée ou isolée.
- [ ] Vérifier que la base se charge et que l'API de santé confirme une base lisible.
- [ ] Comparer les enregistrements et pièces jointes aux éléments notés avant l'essai : élèves, classes, comptes, rôles, affectations, EDT, évaluations, notes, bulletins, appels, justifications, devoirs, rendus, messages, Cloud, salles, couleurs et paramètres.
- [ ] Tester sur cette copie les notifications de maintenance, le compte à rebours, l'arrêt gracieux, le redémarrage et la reprise de service.
- [ ] Simuler une erreur de santé avec le banc de test / les fixtures de validation du gestionnaire ; vérifier que le retour arrière restaure code et base. Ne jamais provoquer une panne sur le service de production.
- [ ] Vérifier que les sauvegardes sont présentes, lisibles et distinctes de la base active.

### Après publication : mise à jour officielle signée sur la copie

Une fois la PR fusionnée et la GitHub Release signée publiée, le gestionnaire officiel peut enfin trouver le tag stable V25.2.0. Ce test ne doit pas être déplacé avant publication.

- [ ] Sur la copie isolée, vérifier que le gestionnaire détecte V25.2.0, valide la signature Ed25519 et le SHA-256, puis prépare l'archive.
- [ ] Exécuter la mise à jour supervisée depuis V25.1.1 vers V25.2.0 sur la copie ; vérifier notifications, compte à rebours, arrêt gracieux, bascule et redémarrage.
- [ ] Confirmer la version active et la santé de la base ; comparer les éléments métier et fichiers avec la sauvegarde de référence.
- [ ] Sur cette copie uniquement, simuler un échec de santé contrôlé et confirmer le retour à la version précédente ainsi que la conservation de la base et des pièces jointes.
- [ ] Redémarrer à nouveau. Si la vérification signée, l'installation, la restauration ou la reprise échoue, ne pas mettre à jour la production ; ouvrir une correction et refaire les essais sur copie avant toute diffusion en production.

## 3. Parcours des trois rôles
- [ ] Sur Firefox/macOS, vérifier l'affichage et la saisie des dates de périodes scolaires ; le format natif dépend du navigateur et de la plateforme (le rendu du runner Linux ne vaut pas validation macOS).

- [ ] Direction : connexions, paramètres, classes/salles, import établissement, bulletins, sauvegardes, gestionnaire de versions et maintenance.
- [ ] Professeur titulaire : EDT, séances, devoirs, pièces jointes, évaluations, appréciations et bulletins sur les matières autorisées.
- [ ] Professeur multi-matières, co-enseignant, remplaçant et professeur principal : affectations, remplacements, accès à la bonne classe/matière et absence de droits hors périmètre.
- [ ] Élève : EDT en lecture seule, séances/leçons, « Travail à faire », dépôt de rendu, messagerie, notifications, résultats publiés, bulletin personnel et paramètres élève.
- [ ] Nouveautés : chaque compte voit l'annonce de V25.2.0 à son premier accès ; l'accusé est mémorisé par compte/version et ne se répète pas à chaque appareil.
- [ ] Journal : consulter l'historique des versions dans les trois espaces et vérifier les sources affichées.

## 4. Générateur de configuration d'établissement

- [ ] Vérifier le téléchargement du modèle, du schéma et des instructions.
- [ ] Vérifier que l'export du contexte est anonymisé : pas de noms d'élèves, dates de naissance, emails, téléphones, identifiants ou données sensibles.
- [ ] Prévisualiser un JSON valide et un JSON volontairement invalide ; confirmer que la prévisualisation ne modifie aucune donnée.
- [ ] Tester groupes simples et multi-niveaux, effectifs, professeurs, matières, volumes horaires, salles, équipements, indisponibilités, cours partagés et récurrences.
- [ ] Vérifier la limite de 25 Mo côté interface et serveur (sans importer de gros fichier sur la production).
- [ ] Sur la copie seulement, confirmer l'import additif, la sauvegarde préalable, les identifiants créés localement, la remise unique des mots de passe provisoires et leur changement à la première connexion.
- [ ] Confirmer que les classes, salles, comptes et collections existants restent présents et inchangés.

## 5. Réseau, appareils clients et PDF

- [ ] Depuis trois ou quatre clients simultanés, vérifier les connexions, permissions, synchronisation, changements d'EDT, notifications et sessions.
- [ ] Depuis un second poste, ouvrir et imprimer un bulletin PDF et télécharger une pièce jointe ; ne pas se limiter au navigateur de l'hôte.
- [ ] Vérifier la connexion après redémarrage, perte/retour Wi-Fi et renouvellement d'adresse IP ; confirmer qu'aucune instance double ne se lance.
- [ ] Vérifier le pare-feu du serveur et l'absence de redirection du port MaClasse vers Internet.

### Confiance HTTPS sans réglage par ordinateur

Le mode AC privée par défaut nécessite d'approuver une fois data/tls/ca.crt sur chaque client (ou de déployer cette confiance par une gestion centralisée). Pour éviter ce réglage individuel, le mode TLS public DNS doit être configuré au niveau de l'établissement : domaine contrôlé, certificat public, renouvellement ACME DNS-01 externe et résolution DNS locale vers l'IP privée distribuée par DHCP.

- [ ] Confirmer que le domaine et le fournisseur DNS sont maîtrisés par l'établissement.
- [ ] Installer le client ACME et le hook de renouvellement sur le serveur sans stocker le jeton DNS dans MaClasse.
- [ ] Configurer le DNS local/split-horizon et sa distribution DHCP.
- [ ] Activer le mode FQDN public dans data/tls/public-certificate.json après vérification des permissions des fichiers.
- [ ] Tester avec au moins deux appareils qui n'ont jamais approuvé l'AC privée MaClasse : HTTPS sans avertissement, URL DNS stable, connexions simultanées et après renouvellement.
- [ ] Vérifier qu'un certificat ou une paire clé/certificat temporairement invalide ne provoque ni baisse en HTTP ni arrêt prématuré du listener courant.

Tant que cette recette n'est pas passée, l'objectif « aucune configuration manuelle de certificat sur chaque ordinateur » reste **non validé**. Ne jamais contourner un avertissement TLS en ajoutant une exception aveugle ou en revenant en HTTP.

## 6. Clôture et publication

- [ ] Consigner les résultats, appareils, dates, rôles et écarts éventuels sans enregistrer inutilement d'informations personnelles.
- [ ] Obtenir la confirmation de l'utilisateur avant tout passage d'une anomalie de « Supposé résolu » à « Corrigé ».
- [ ] Après acceptation de la recette, revoir puis fusionner la PR #20 dans main.
- [ ] Exécuter et vérifier la CI post-fusion sur le commit de main.
- [ ] Publier uniquement avec le workflow officiel de release signée ; vérifier le tag, VERSION.txt, APP_VERSION, MC_VERSION, le manifeste, la signature Ed25519 et l'archive.
- [ ] Après publication, installer la release signée sur la copie d'abord, puis planifier seulement ensuite la mise à jour de la production avec sauvegarde externe vérifiée et arrêt/redémarrage contrôlés.

## État de la livraison au 27 novembre 2026

- CI de la tête exacte actuelle de la PR : Workflow #2148 / run 46004938689, commit `39156b95fae52049ebc1a3b81cf320724824ff8c` : Linux (tests), macOS Apple Silicon avec installateur et `launchd` réels, et Firefox réel — **3/3 jobs réussis**. L'arbre contient 113 fichiers de tests (68 JavaScript, 45 Python) et 860 invariants intermodules.
- Dernière release stable : V25.1.1 (v25.1.1).
- V25.2.0 : candidate, PR #20 ouverte, non fusionnée, non taguée et non publiée ; la dernière tête CI vérifie aussi la sauvegarde/restauration complète et la sécurité du paquet.
- Recette physique : non effectuée dans cette campagne ; les cases doivent être cochées à partir de résultats réels, pas supposées validées.
