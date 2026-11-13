# Réseau local HTTPS — MaClasse V25

## Principe

Un seul ordinateur héberge le serveur MaClasse. Les autres ordinateurs ouvrent son adresse HTTPS dans Firefox ou un autre navigateur, sur le même réseau privé. Il ne faut pas rediriger le port 8765 depuis Internet.

Le serveur refuse maintenant de démarrer sur une adresse LAN en HTTP. Les sessions utilisent des cookies `HttpOnly`, `SameSite=Strict` et `Secure` lorsqu'elles sont servies en HTTPS. TLS 1.2 est le minimum.

## Installer sur le serveur

### Fedora / Linux

Depuis le dossier cloné du dépôt :

```bash
chmod +x ./*.sh
./Installer-MaClasse-Linux.sh
```

Pour la première configuration, démarre localement le serveur avec `.venv/bin/python server.py`, ouvre `http://127.0.0.1:8765` sur le serveur, crée le compte direction et définis son mot de passe. Arrête ensuite le serveur local avec Ctrl+C.

Lance le mode réseau :

```bash
./Lancer-MaClasse-Reseau.sh
```

Le script détecte l'adresse IPv4 de l'interface par défaut, crée une autorité de certification locale et un certificat serveur pour cette adresse, puis démarre MaClasse en HTTPS.

### macOS Apple Silicon

Lance `Installer-MaClasse.command`, initialise d'abord MaClasse en local, puis utilise `Lancer-MaClasse-Reseau.command`.

## Faire confiance au certificat sur les appareils clients

Au premier lancement, le serveur crée :

- `data/tls/ca.crt` : certificat public à copier sur chaque appareil client.
- `data/tls/ca.key` : clé privée de l'autorité ; elle doit rester sur le serveur et ne doit jamais être partagée.
- `data/tls/server.key` : clé privée du serveur ; elle doit rester sur le serveur.
- `data/tls/server.crt` : certificat du serveur pour l'adresse IP actuelle.

Copie uniquement `ca.crt` vers les clients, par un moyen local sûr.

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

## Adresse IP, pare-feu et renouvellement

- Réserve une adresse IP stable au serveur dans le DHCP de la box. Si l'adresse change, relance le lanceur : il régénère le certificat serveur avec la nouvelle adresse en conservant la même autorité locale.
- Sur Fedora, vérifie la zone active de firewalld. N'autorise TCP/8765 que sur un profil de réseau privé de confiance ; ne l'ouvre pas sur une zone publique.
- N'active aucune redirection de port sur le routeur.
- Le certificat serveur est renouvelé à chaque démarrage ; l'autorité racine est conservée dans `data/tls`.
- Les sauvegardes MaClasse ne contiennent volontairement pas les clés TLS. Conserve une copie chiffrée hors ligne de `ca.key` et `ca.crt` si tu dois pouvoir restaurer l'identité HTTPS du serveur. Ne place jamais `ca.key` dans un partage Cloud ou sur un appareil client.

## Mise à jour

Sur macOS : `Mettre-A-Jour-MaClasse.command`.

Sur Linux : `./Mettre-A-Jour-MaClasse-Linux.sh`.

Les deux scripts refusent les modifications Git locales et les branches divergentes, sauvegardent `data/` avant la mise à jour et appliquent uniquement une avance rapide.

## État de validation

Les tests automatisés couvrent le démarrage TLS, les cookies Secure, le rejet d'une origine HTTP sur le listener HTTPS et le refus du démarrage LAN sans certificat. Cela ne remplace pas la validation réelle sur le PC Fedora cible et les appareils clients : installation de l'autorité, pare-feu, adresse DHCP stable, accès simultanés, redémarrage, sauvegardes/restaurations et recette fonctionnelle complète restent obligatoires avant des données scolaires réelles.
