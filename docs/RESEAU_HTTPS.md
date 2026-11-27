# Réseau local HTTPS — MaClasse V25

**État au 27/11/2026 :** le superviseur réseau est commun à Linux et macOS. Le workflow #2114 valide la tête `559c866` sur Linux, macOS Apple Silicon avec `launchd` réel et Firefox réel (3/3). Le test de renouvellement ACME vérifie que le listener reste actif pendant le remplacement progressif d'une paire certificat/clé, puis s'arrête proprement lorsque la paire valide est prête. La validation sur le Wi-Fi cible, le DNS/routeur, le pare-feu Fedora et au moins deux appareils clients reste à effectuer.

**Deux modes de confiance existent :** le mode AC privée par défaut nécessite encore d'approuver/importer `data/tls/ca.crt` sur chaque appareil (ou de la distribuer centralement). Le mode facultatif TLS public DNS, documenté ci-dessous, permet d'éviter cette étape par poste si le domaine, le renouvellement ACME et le DNS local sont configurés au niveau de l'établissement. Il n'est pas encore activé ni recetté sur le réseau cible ; ne pas le considérer comme opérationnel avant le test de deux appareils.

## Principe

Un seul ordinateur héberge le serveur MaClasse. Les autres ordinateurs ouvrent son adresse HTTPS dans Firefox ou un autre navigateur, sur le même réseau privé. Il ne faut pas rediriger le port 8765 depuis Internet.

Le serveur refuse maintenant de démarrer sur une adresse LAN en HTTP. Les sessions utilisent des cookies `HttpOnly`, `SameSite=Strict` et `Secure` lorsqu'elles sont servies en HTTPS. TLS 1.2 est le minimum.

## Option : certificat publiquement reconnu avec nom DNS (sans import sur les clients)

Le mode AC privée décrit ci-dessus reste le mode par défaut. Un mode facultatif peut utiliser un certificat publiquement reconnu pour un nom DNS de l'établissement. Il permet aux navigateurs de faire confiance au certificat via leur magasin public habituel, sans importer `ca.crt` sur chaque ordinateur.

Cette option exige trois éléments qui doivent être configurés une fois au niveau de l'établissement :

1. **Un nom de domaine contrôlé par l'établissement**, par exemple `maclasse.exemple.fr`.
2. **Un certificat public renouvelé automatiquement.** Le challenge ACME DNS-01 permet de prouver le contrôle du domaine avec un enregistrement TXT, sans exposer le port web MaClasse sur Internet. Utilise un client ACME externe (Certbot, acme.sh ou équivalent) et un jeton API DNS à portée minimale, stocké dans le fichier d'identifiants propre à ce client, jamais dans MaClasse. Le serveur MaClasse ne demande ni ne stocke le jeton DNS.
3. **Une résolution DNS locale (split-horizon ou surcharge DNS sur le routeur)** qui fait résoudre `maclasse.exemple.fr` vers l'adresse IPv4 privée du Mac sur le réseau de l'établissement. Distribue ce DNS par DHCP afin que les postes le reçoivent automatiquement ; aucun fichier hosts ni réglage individuel n'est nécessaire. Sans DNS local contrôlé par le routeur ou un serveur DNS interne, l'accès sans configuration par poste n'est pas garanti.

Aucune redirection de port 80/443/8765 vers le serveur MaClasse n'est nécessaire avec DNS-01. Ne publie pas le port 8765 sur Internet.

### Configuration du certificat dans MaClasse

Après avoir installé MaClasse, créé le compte Direction et préparé le répertoire `data/tls/`, place le certificat complet (`fullchain.pem`) et sa clé privée dans des fichiers lisibles uniquement par le compte qui exécute le service. Le renouvellement ACME doit recopier/remplacer ces deux fichiers de façon atomique, puis attribuer les fichiers au compte qui exécute MaClasse et appliquer `chmod 600` à la clé privée. Sur Linux, un hook de déploiement Certbot/acme.sh peut copier les fichiers depuis le répertoire ACME protégé vers un répertoire TLS dédié accessible au compte systemd utilisateur ; sur macOS, le client ACME peut fonctionner sous le compte de session qui lance le LaunchAgent. Le superviseur refuse une clé privée lisible par le groupe ou les autres utilisateurs. Exemple de configuration :

```json
{
  "hostname": "maclasse.exemple.fr",
  "certificate": "/chemin/protege/fullchain.pem",
  "private_key": "/chemin/protege/privkey.pem"
}
```

Enregistre cet objet dans `data/tls/public-certificate.json`, puis protège le fichier de configuration et la clé :

```bash
chmod 600 data/tls/public-certificate.json
chmod 600 /chemin/protege/privkey.pem
```

Les chemins du certificat et de la clé doivent être absolus. La clé doit être lisible par le compte du service, sans être lisible par les autres utilisateurs. Le fichier JSON ne contient que le nom DNS et des chemins ; il ne contient ni clé privée ni identifiant ACME/DNS.

Au démarrage, le superviseur vérifie le nom DNS dans le SAN du certificat, sa validité (plus de 24 heures restantes), la correspondance de la clé privée et les permissions du fichier de configuration. Le serveur accepte le FQDN configuré dans les contrôles stricts `Host` et `Origin` tout en restant lié à l'adresse IPv4 privée détectée. L'URL annoncée devient `https://maclasse.exemple.fr:8765`.

Le superviseur surveille les fichiers toutes les cinq secondes. Quand le client ACME renouvelle le certificat et remplace les fichiers configurés, il détecte leur nouvelle empreinte SHA-256, arrête proprement l'ancien listener et redémarre avec la nouvelle chaîne TLS. Une configuration ou un certificat invalide fait échouer le démarrage : aucun repli vers HTTP ni exception de certificat n'est créé. Sans le fichier `public-certificate.json`, le mode historique AC privée reste actif.

### Limites opérationnelles

- MaClasse ne choisit pas le fournisseur DNS, n'émet pas le certificat et n'exécute pas le client ACME. La configuration du fournisseur, du jeton à portée minimale et du renouvellement doit être réalisée sur le serveur.
- Le routeur/DNS interne doit distribuer le nom DNS vers l'adresse privée. Si le routeur ne propose pas de surcharge DNS locale, il faut un DNS interne géré par l'établissement ; modifier manuellement chaque poste ne répondrait pas à l'objectif.
- Cette configuration doit être testée depuis au moins deux appareils clients avec le vrai certificat public et le DNS local avant de considérer la confiance HTTPS comme résolue.
- Le mode AC privée reste disponible sans changement pour les installations qui ne possèdent pas de domaine public ou de DNS local adapté.

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
