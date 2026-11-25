# Installation de MaClasse V25

Ce guide concerne le code courant du dépôt. Pour l'accès depuis plusieurs appareils, lire également [Réseau local HTTPS](RESEAU_HTTPS.md). Les documents placés dans `docs/archives/` sont historiques et ne remplacent pas cette procédure.

## Prérequis

- **Linux** : distribution récente, notamment Fedora, Python 3.10 ou plus récent.
- **macOS** : Mac Apple Silicon (arm64), Python 3.10 ou plus récent.
- Une connexion Internet est nécessaire pendant l'installation des dépendances Python.
- Un compte utilisateur système capable d'écrire dans le dossier MaClasse et son dossier `data/`.

## Installer les dépendances

### Linux / Fedora

Depuis le dossier du dépôt :

```bash
./Installer-MaClasse-Linux.sh
```

Le script crée `.venv/`, installe les dépendances de `requirements.txt` et vérifie que le serveur Python se compile.

### macOS Apple Silicon

Double-cliquer sur `Installer-MaClasse.command`. Le script vérifie qu'il est lancé sur un Mac Apple Silicon natif et prépare l'environnement Python local.

## Démarrer en local

Depuis le dossier MaClasse :

```bash
.venv/bin/python server.py
```

Sur le même ordinateur, ouvrir :

```text
http://127.0.0.1:8765
```

Lors de la première configuration, créer le compte Direction et définir un mot de passe personnel. Il n'existe pas d'identifiant universel à utiliser pour tous les établissements. Les comptes Professeur et Élève sont créés ensuite depuis l'espace Direction, selon les besoins.

Laisser le processus serveur actif pendant l'utilisation. Pour l'arrêter proprement, utiliser `Ctrl+C` dans le terminal. Les installations supervisées peuvent ensuite utiliser systemd sur Linux ou launchd sur macOS ; voir les scripts `Installer-Service-MaClasse-Linux.sh` et `Installer-Service-MaClasse-macOS.sh`.

## Accès depuis d'autres appareils

Ne pas exposer le serveur en HTTP sur le réseau local. Le mode réseau utilise une IPv4 privée précise et HTTPS :

- **Linux** : `./Lancer-MaClasse-Reseau.sh`
- **macOS** : `./Lancer-MaClasse-Reseau.command`

Le superviseur réseau surveille l'adresse IPv4 privée, ferme l'écoute HTTPS en cas de perte du réseau et renouvelle le certificat serveur si l'adresse change. Il conserve la même autorité locale ; les appareils clients doivent approuver son certificat public `data/tls/ca.crt`.

Suivre [Réseau local HTTPS](RESEAU_HTTPS.md) pour transférer et approuver uniquement le certificat public. Ne jamais copier `ca.key` ou `server.key` vers un appareil client. Ne créer aucune redirection de port sur le routeur.

## Données et sauvegardes

Par défaut, les données persistantes sont dans `data/`, séparées du code :

- `data/maclasse.json` : base de données ;
- `data/uploads/` : pièces jointes et fichiers déposés ;
- `data/backups/` : sauvegardes locales ;
- `data/tls/` : certificats et clés de l'identité HTTPS locale.

Le dossier `data/` est exclu de Git. Avant une opération de maintenance ou une migration, arrêter le serveur et faire une copie externe protégée du dossier `data/` complet. Les archives de sauvegarde intégrées ne contiennent volontairement pas les clés TLS : conserver séparément une copie chiffrée de `data/tls/` si la restauration de l'identité HTTPS est nécessaire.

Ne jamais transmettre le dossier `data/` : il peut contenir des informations personnelles et scolaires.

## Mises à jour

Les mises à jour officielles sont destinées à venir des GitHub Releases stables, jamais d'une branche de développement. Le gestionnaire intégré est documenté dans [Gestion des mises à jour](GESTION_MISES_A_JOUR.md). Tant qu'une release cible n'a pas été publiée et validée, ne pas appliquer manuellement une branche candidate à une installation contenant des données réelles.

## Dépannage

- Si le serveur ne démarre pas, vérifier la sortie du terminal avant de relancer.
- Si le navigateur refuse le certificat HTTPS local, suivre la procédure `SEC_ERROR_UNKNOWN_ISSUER` dans [Réseau local HTTPS](RESEAU_HTTPS.md) ; ne pas accepter une exception aveugle.
- Pour les erreurs de persistance, conserver le dossier `data/` et les journaux avant toute tentative de réparation.
