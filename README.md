# MaClasse

MaClasse est une application web de gestion scolaire destinée à un établissement : classes et élèves, emploi du temps, séances et devoirs, évaluations, absences, bulletins, messagerie et espace documentaire. Elle est servie par un ordinateur hôte et utilisée depuis un navigateur.

## État du projet — 27 novembre 2026

| Référence | État |
|---|---|
| Dernière release GitHub publiée | **V25.1.1** (`v25.1.1`), publiée le 26/11/2026 |
| Candidat suivant | **V25.2.0**, PR #20 ouverte ; non fusionnée et non publiée |
| CI du candidat | Run #2114 réussi sur Linux, macOS Apple Silicon/launchd et Firefox réel (3/3), tête `559c866` |
| Branche `main` | **V25.1.1**, HEAD `710c184` (commit documentaire après le commit de release `b5cc07d`) |
| Publication | Workflow #4 réussi : validation Linux, macOS Apple Silicon/launchd, Firefox, archive, manifeste et signature |
| Installation de référence | Premier passage depuis V25.0.23 effectué sur macOS ; fonctionnement confirmé par l'utilisateur |

La recette réelle V25.0.23 → V25.1.0 sur macOS a révélé deux défauts de transition : l'analyse du certificat dépendait du format texte OpenSSL (incompatible avec la sortie LibreSSL de macOS), puis l'ancien déclencheur launchd ne lançait pas le gestionnaire indépendant. V25.1.1 remplace l'analyse textuelle par une lecture X.509, fiabilise le lancement launchd, conserve les diagnostics et fournit un lanceur direct de secours pour ce premier passage.

La PR #19 est fusionnée dans `main`. La CI post-fusion #1844 a validé les 93 fichiers de tests (55 JavaScript et 38 Python) sur les runners adaptés, ainsi que Firefox réel et macOS Apple Silicon/launchd. Le workflow de publication #4 (run `45806118500`) a ensuite réussi ses quatre jobs et publié les trois assets signés. La mise à jour a enfin été installée sur le Mac de référence et confirmée fonctionnelle. Voir le [registre des branches et validations](docs/qualite/ARCHIVES_BRANCHES_ET_VALIDATIONS.md).

### Évolutions livrées en V25.1.0

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

### Candidat V25.2.0 — PR #20

Le candidat V25.2.0 harmonise les règles de publication des évaluations et bulletins, les parcours « Travail à faire » et vie scolaire, les affectations, les salles et les créneaux partagés. Il ajoute un générateur manuel de configuration d'établissement (JSON jusqu'à 25 Mo), un écran des nouveautés par compte et un journal historique. Les sources historiques et la clé publique Ed25519 nécessaires à ces fonctions sont contrôlées dans le paquet de mise à jour.

Le workflow #2114 passe sur Linux, macOS Apple Silicon avec `launchd` réel et Firefox réel (3/3) sur la tête `559c866`. Les contrôles de paquet excluent les données locales, bases, certificats et clés privées ; tous les lanceurs racine sont vérifiés. Le candidat inclut un mode TLS public DNS facultatif : avec un domaine contrôlé, un certificat public renouvelé par ACME DNS-01 et un DNS local distribué aux appareils via DHCP, les postes peuvent ouvrir MaClasse sans importer l'AC privée. Ce mode n'est pas configuré ni recetté sur le réseau cible ; sans ces prérequis, le mode AC privée par défaut demande toujours une approbation par appareil. La recette sur une copie représentative des données, les vrais comptes et au moins deux appareils clients reste nécessaire avant fusion et publication. Voir les [notes candidates V25.2.0](docs/releases/v25.2.0.md), le [guide HTTPS](docs/RESEAU_HTTPS.md), le [guide du générateur](docs/CONFIGURATION_ETABLISSEMENT_CHATGPT.md) et le [registre des anomalies](REGISTRE_BUGS_V25.md).

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
| [Qualité, branches et validations](docs/qualite/ARCHIVES_BRANCHES_ET_VALIDATIONS.md) | Traçabilité des PR, branches candidates, tests CI et publication V25.1.1 |

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


### Journal des versions et écran des nouveautés — V25.2.0

Après l’installation d’une nouvelle version, chaque compte Direction, Professeur ou Élève dispose d’un écran des nouveautés. La consultation est mémorisée côté serveur par compte et par version. Le journal complet est accessible depuis les Paramètres des trois espaces.

Les entrées historiques sont issues des notes de version, des audits/recettes archivés et de l’ancien README conservés dans le dépôt. Les versions sans trace exploitable ne sont pas complétées par supposition.


Le générateur d'établissement guide la Direction en trois étapes, accepte un fichier JSON de 25 Mo maximum et effectue une prévalidation avant confirmation. Consulte le [guide du générateur](docs/CONFIGURATION_ETABLISSEMENT_CHATGPT.md). N'envoie jamais de données personnelles réelles à ChatGPT : utilise des pseudonymes puis complète les identités directement dans Ma Classe. Il n'existe aucune API ChatGPT ni aucun transfert automatique.
