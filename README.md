# MaClasse

MaClasse est une application web de gestion scolaire destinée à un établissement : classes et élèves, emploi du temps, séances et devoirs, évaluations, absences, bulletins, messagerie et espace documentaire. Elle est servie par un ordinateur hôte et utilisée depuis un navigateur.

## État du projet — 26 novembre 2026

| Référence | État |
|---|---|
| Dernière release GitHub publiée | **V25.1.0** (`v25.1.0`) |
| Branche `main` | **V25.1.0** |
| Correctif candidat | **V25.1.1** — validation du certificat HTTPS macOS/LibreSSL |
| Publication V25.1.1 | CI verte (3/3), en attente de la recette physique sur le Mac |

La recette réelle de la mise à jour V25.0.23 → V25.1.0 sur macOS a révélé que le superviseur rejetait à tort le certificat HTTPS local : il dépendait du format texte propre à OpenSSL pour lire le SAN, format qui varie avec LibreSSL. L'installation a été restaurée en V25.0.23 sans perte de la base ni des certificats. La V25.1.1 remplace ce contrôle par une lecture X.509 directe avec la dépendance `cryptography` déjà utilisée pour la signature des mises à jour.

Le workflow #1807 de la PR #14 est vert (3/3) : Linux, macOS Apple Silicon avec launchd réel et Firefox. Il reste à refaire le parcours de mise à jour intégré sur le Mac et à vérifier l'accès réseau depuis les appareils clients avant publication.

### Changements récents du candidat V25.1.0

- Intégrité des archives de mise à jour : contrôles de taille et de digest SHA-256 lorsque GitHub fournit ces métadonnées.
- Superviseur réseau commun Linux/macOS : fermeture du listener lors d'une perte réseau et renouvellement du certificat serveur lors d'un changement d'IPv4 privée.
- Migration de l'architecture supervisée testée sur un fixture V25.0.19 ; la copie des données de l'installation réelle reste à vérifier.
- Messagerie élève : liste des enseignants joignables alignée sur les droits serveur, titulaires, co-enseignants et affectations actives compris.
- Bulletins : statut de publication et autorisations PDF cohérents, y compris pour les bulletins anciens sans horodatage de publication.
- Emploi du temps : persistance contrôlée des couleurs de matières, fond de grille adapté au thème sombre et accès central filtrable aux remplacements/co-enseignements.
- Administration : message de confidentialité aligné sur le filtrage serveur des comptes élèves, messages, pièces jointes et ressources.

- Nouvelle vue Suivi de classe pour la Direction et les enseignants autorisés : absences/retards, travaux non rendus, évaluations publiées, échéances et accès aux fiches élèves. Les enseignants non PP restent limités aux matières accessibles par leurs affectations ; les PP disposent de la vue transversale. Aucun classement ni score de risque n'est calculé.
- Le contexte Cloud est réinitialisé lors du passage vers les espaces personnels, partagés et documentaires, sans perdre le raccourci de classe lorsqu'on reste dans l'espace Classe.
- La ressource JavaScript du nouveau module est explicitement autorisée par le serveur et couverte par un test de liste blanche.

La signature Ed25519 du manifeste est implémentée côté client et dans le workflow de publication. La clé publique de production est épinglée dans le dépôt et le secret privé reste uniquement dans GitHub Actions ; la release V25.1.0 a été construite avec ses assets de manifeste et de signature.

## Installation et démarrage

Consulter d'abord le [guide d'installation V25](docs/INSTALLATION.md).

**Linux / Fedora :**

```bash
./Installer-MaClasse-Linux.sh
.venv/bin/python server.py
```

**macOS Apple Silicon :** double-cliquer sur `Installer-MaClasse.command`, puis démarrer le serveur depuis le dossier MaClasse :

```bash
.venv/bin/python server.py
```

En local, ouvrir `http://127.0.0.1:8765`. À la première configuration, créer le compte Direction et définir son mot de passe. Les comptes Professeur et Élève sont ensuite créés depuis l'espace Direction. Il n'existe pas d'identifiant universel à utiliser.

Pour l'accès depuis d'autres appareils, utiliser exclusivement le mode **HTTPS sur le réseau privé**. Lire [Réseau local HTTPS](docs/RESEAU_HTTPS.md) avant de démarrer le superviseur. Ne pas exposer le port sur Internet et ne pas rediriger le port 8765 sur le routeur.

## Données et sécurité

- Les données persistantes sont dans `data/` par défaut, séparées du code : base `maclasse.json`, téléversements, sauvegardes et identité TLS.
- Le dossier `data/` est exclu de Git. Ne jamais le publier ni le partager : il peut contenir des informations personnelles et scolaires.
- Le serveur contrôle les permissions par rôle et périmètre côté Python ; masquer un bouton dans l'interface ne suffit jamais.
- Les sauvegardes et restaurations doivent conserver la base et les pièces jointes. Avant une migration ou une mise à jour, faire une copie externe protégée du dossier `data/`.
- Sur les appareils clients, installer uniquement le certificat public `data/tls/ca.crt`. Ne jamais partager `ca.key` ni `server.key`.
- Aucune redirection de ports Internet n'est prévue.

Pour la gestion des releases, des migrations et du retour arrière, voir [Gestion des mises à jour](docs/GESTION_MISES_A_JOUR.md).

## Documentation

| Document | Contenu |
|---|---|
| [Index de la documentation](docs/INDEX.md) | Guides actifs et archives |
| [Installation](docs/INSTALLATION.md) | Prérequis, installation, démarrage et sauvegardes |
| [Réseau local HTTPS](docs/RESEAU_HTTPS.md) | Certificats, clients, DHCP et pare-feu |
| [Gestion des mises à jour](docs/GESTION_MISES_A_JOUR.md) | Architecture du gestionnaire, migration et validation |
| [Signature des releases](docs/RELEASE_SIGNING.md) | Génération de la clé éditeur et configuration du secret GitHub |
| [Audit produit V25](docs/AUDIT_PRODUIT_V25.md) | Modules, expérience utilisateur, thèmes et recette |
| [Registre des bugs](REGISTRE_BUGS_V25.md) | Anomalies ouvertes et statuts de recette |
| [Suivi des correctifs](SUIVI_CORRECTIFS_V25.md) | Journal chronologique des interventions |
| [Historique des versions](docs/HISTORIQUE_VERSIONS.md) | Notes V21 et V25 regroupées sans perte de contenu |

Les anciens guides, états et audits ont été déplacés dans [docs/archives](docs/archives/). Ils sont conservés à titre historique ; leurs instructions ne doivent pas être utilisées pour installer la version courante.

## Structure du dépôt

| Chemin | Rôle |
|---|---|
| `server.py` | Serveur HTTP/HTTPS, authentification, autorisations, données et API |
| `index.html` | Structure et styles de l'application |
| `class_tracking.js` | Vue de suivi de classe et synthèse des données autorisées |
| `_all.js` | Navigation, modules métier et interactions |
| `update_manager.py` | Vérification et préparation des mises à jour |
| `network_supervisor.py` | Supervision du listener HTTPS et changements réseau |
| `tests/` | Tests Python, JavaScript et navigateur Firefox |
| `docs/` | Documentation active, historique et archives |

## Vérifications automatisées

La CI GitHub Actions exécute les contrôles Linux, macOS Apple Silicon et la régression EDT dans Firefox réel. Pour des vérifications locales rapides :

```bash
node --check _all.js
python -m py_compile server.py
```

Les tests complets sont lancés par le workflow [MaClasse — tests automatisés](.github/workflows/tests.yml). Toute release stable doit être créée depuis un tag versionné cohérent avec `VERSION.txt`, `APP_VERSION` et `MC_VERSION`, puis attendre la réussite du workflow de publication. Ne pas publier une release depuis une branche candidate.
