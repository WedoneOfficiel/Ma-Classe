# MaClasse

MaClasse est une application web de gestion scolaire destinée à un établissement : classes et élèves, emploi du temps, séances et devoirs, évaluations, absences, bulletins, messagerie et espace documentaire. Elle est servie par un ordinateur hôte et utilisée depuis un navigateur.

## État du projet — 25 novembre 2026

| Référence | État |
|---|---|
| Dernière release GitHub publiée | **V25.0.23** (`v25.0.23`, 16/11/2026) |
| Branche `main` | **V25.0.24** |
| Candidat de stabilisation | **V25.0.25**, [PR #13](https://github.com/WedoneOfficiel/Ma-Classe/pull/13), ouverte et non fusionnée |
| CI du dernier commit vérifié | **Verte** — Linux, macOS Apple Silicon et Firefox réel, workflow [#1727](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45695094364) |
| Publication V25.0.25 | Pas encore effectuée |

La CI verte valide les suites automatisées sur les runners GitHub. Elle ne remplace pas les recettes sur le Mac, le PC Fedora et les appareils clients réels. La V25.0.25 n'est pas à installer depuis la branche de développement sur une base scolaire réelle.

### Changements récents du candidat V25.0.25

- Intégrité des archives de mise à jour : contrôles de taille et de digest SHA-256 lorsque GitHub fournit ces métadonnées.
- Superviseur réseau commun Linux/macOS : fermeture du listener lors d'une perte réseau et renouvellement du certificat serveur lors d'un changement d'IPv4 privée.
- Migration de l'architecture supervisée testée sur un fixture V25.0.19 ; la copie des données de l'installation réelle reste à vérifier.
- Messagerie élève : liste des enseignants joignables alignée sur les droits serveur, titulaires, co-enseignants et affectations actives compris.
- Bulletins : statut de publication et autorisations PDF cohérents, y compris pour les bulletins anciens sans horodatage de publication.
- Emploi du temps : persistance contrôlée des couleurs de matières et fond de grille adapté au thème sombre.

La signature éditeur indépendante des releases reste un point de sécurité ouvert : un SHA-256 de manifeste détecte des écarts d'intégrité mais ne prouve pas à lui seul l'identité de l'éditeur.

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
