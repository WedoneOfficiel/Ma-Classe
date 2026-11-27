# Réseau local HTTPS — MaClasse V25

**État au 27/11/2026 :** le superviseur réseau est commun à Linux et macOS. La CI finale candidate #2092 valide Linux, macOS Apple Silicon avec `launchd` réel et Firefox réel (3/3). La vérification sur un vrai réseau Wi-Fi, le pare-feu Fedora et les appareils clients reste à effectuer sur le matériel cible.

**Limite de confiance HTTPS côté client — non résolue :** MaClasse utilise actuellement une autorité de certification privée créée sur le serveur. Chaque nouvel appareil ou navigateur doit approuver/importer une fois le certificat public `data/tls/ca.crt`. Le serveur ne peut pas ajouter silencieusement une autorité privée au magasin de confiance d'un appareil arbitraire. Cette architecture ne satisfait donc pas une exigence de zéro réglage de certificat par ordinateur ; ne pas la présenter comme résolue par la CI.

## Principe

Un seul ordinateur héberge le serveur MaClasse. Les autres ordinateurs ouvrent son adresse HTTPS dans Firefox ou un autre navigateur, sur le même réseau privé. Il ne faut pas rediriger le port 8765 depuis Internet.

Le serveur refuse maintenant de démarrer sur une adresse LAN en HTTP. Les sessions utilisent des cookies `HttpOnly`, `SameSite=Strict` et `Secure` lorsqu'elles sont servies en HTTPS. TLS 1.2 est le minimum.

## Installer sur le serveur

### Fedora / Linux

Depuis le dossier cloné du dépôt :

```bash
./Installer-MaClasse-Linux.sh
```

Pour la première configuration, démarre localement le serveur avec `.venv/bin/python server.py`, ouvre `http://127.0.0.1:8765` sur le serveur, crée le compte direction et définis son mot de passe. Arrête ensuite le serveur local avec Ctrl+C.

Lance le mode réseau :

```bash
./Lancer-MaClasse-Reseau.sh
```

Le superviseur détecte l'adresse IPv4 privée de l'interface par défaut, crée l'autorité locale et démarre MaClasse en HTTPS. Il surveille ensuite le réseau toutes les cinq secondes : une perte de connexion ferme le listener, et un changement d'adresse régénère le certificat serveur puis relance le listener automatiquement.

Pour installer le premier service systemd utilisateur expérimental (démarrage automatique et redémarrage après incident), après cette initialisation, exécute depuis le compte Linux qui possède le dossier MaClasse :

```bash
bash Installer-Service-MaClasse-Linux.sh
```

Le script peut demander le mot de passe sudo pour activer le maintien du service au démarrage (`loginctl enable-linger`). État : `systemctl --user status maclasse.service`. Journaux : `journalctl --user -u maclasse.service -f`. Arrêt : `systemctl --user stop maclasse.service`. Désinstallation du service uniquement : `bash Desinstaller-Service-MaClasse-Linux.sh` ; le programme et les données restent en place. Ce premier service est expérimental et doit être testé sur le PC Fedora cible avant de remplacer le lancement manuel.

### macOS Apple Silicon

Lance `Installer-MaClasse.command`, initialise d'abord MaClasse en local, puis utilise `Lancer-MaClasse-Reseau.command`.

## Faire confiance au certificat sur les appareils clients

Au premier lancement, le serveur crée :

- `data/tls/ca.crt` : certificat public à copier sur chaque appareil client.
- `data/tls/ca.key` : clé privée de l'autorité ; elle doit rester sur le serveur et ne doit jamais être partagée.
- `data/tls/server.key` : clé privée du serveur ; elle doit rester sur le serveur.
- `data/tls/server.crt` : certificat du serveur pour l'adresse IP actuelle.

Copie uniquement `ca.crt` vers les clients, par un moyen local sûr. Compare l'empreinte SHA-256 affichée par le lanceur avec celle du certificat reçu avant de l'installer ; ne transfère jamais `ca.key` ou `server.key`.

### macOS client

Dans un Terminal, depuis le dossier contenant le certificat :

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca.crt
```

### Fedora client

```bash
sudo install -m 0644 ca.crt /etc/pki/ca-trust/source/anchors/maclasse-ca.crt
sudo update-ca-trust
```

### Windows client

Ouvre `ca.crt`, choisis Installer le certificat, sélectionne Ordinateur local, puis place-le dans Autorités de certification racines de confiance. L'installation dans le magasin système nécessite les droits administrateur.

### Firefox

Si Firefox n'utilise pas automatiquement les autorités système, ouvre Paramètres → Vie privée et sécurité → Certificats → Afficher les certificats → Autorités → Importer. Sélectionne `ca.crt` et autorise cette autorité à identifier des sites web.

Une fois le certificat approuvé, ouvre l'adresse HTTPS affichée dans le terminal du serveur, par exemple `https://192.168.1.20:8765`. L'adresse réelle est celle affichée par le lanceur.

## Si Firefox affiche SEC_ERROR_UNKNOWN_ISSUER

Ce code signifie que Firefox ne reconnaît pas l'autorité qui a signé le certificat local. Il ne faut pas ajouter une exception aveugle au serveur : installe le certificat public de l'autorité MaClasse `data/tls/ca.crt` dans les autorités de confiance du navigateur. Dans Firefox : Paramètres → Vie privée et sécurité → Certificats → Afficher les certificats → Autorités → Importer ; sélectionne `ca.crt` et coche « Faire confiance à cette autorité pour identifier des sites web ». Ne sélectionne jamais `ca.key` ni `server.key`. Redémarre Firefox si nécessaire. Sur macOS, Firefox peut aussi utiliser les autorités racines ajoutées au trousseau système lorsque l'option d'approbation automatique des certificats tiers est activée.

## Adresse IP, pare-feu et renouvellement

- Une réservation DHCP reste recommandée pour conserver une URL stable. Si l'adresse change malgré tout, le superviseur la détecte automatiquement, arrête proprement le listener HTTPS, renouvelle le certificat serveur puis redémarre sur la nouvelle adresse. En cas de perte du Wi-Fi ou du câble, le listener est arrêté jusqu'au retour d'une IPv4 privée.
- Sur Fedora, vérifie la zone active de firewalld. N'autorise TCP/8765 que sur un profil de réseau privé de confiance ; ne l'ouvre pas sur une zone publique.
- N'active aucune redirection de port sur le routeur.
- Le certificat serveur est renouvelé au changement d'adresse ou lorsqu'il approche de l'expiration ; l'autorité racine et la clé privée du serveur sont conservées dans `data/tls`. Les postes clients n'ont pas à réinstaller `ca.crt`, mais doivent ouvrir la nouvelle URL HTTPS.
- Les sauvegardes MaClasse ne contiennent volontairement pas les clés TLS. Conserve une copie chiffrée hors ligne de `ca.key` et `ca.crt` si tu dois pouvoir restaurer l'identité HTTPS du serveur. Ne place jamais `ca.key` dans un partage Cloud ou sur un appareil client.

## Mise à jour

Sur macOS : `Mettre-A-Jour-MaClasse.command`.

Sur Linux : `./Mettre-A-Jour-MaClasse-Linux.sh`.

Les deux scripts refusent les modifications Git locales et les branches divergentes, sauvegardent `data/` avant la mise à jour et appliquent uniquement une avance rapide.

## État de validation

Les tests automatisés couvrent le démarrage TLS, les cookies Secure, le rejet d'une origine HTTP sur le listener HTTPS, le refus du démarrage LAN sans certificat et la simulation d'un changement DHCP/perte puis retour du réseau. Cela ne remplace pas la validation réelle sur le PC Fedora cible et les appareils clients : installation de l'autorité, pare-feu, adresse DHCP stable, accès simultanés, redémarrage, sauvegardes/restaurations et recette fonctionnelle complète restent obligatoires avant des données scolaires réelles.
