# Documentation MaClasse

## Guides actifs

| Document | Usage |
|---|---|
| [Installation](INSTALLATION.md) | Installer, démarrer et sauvegarder MaClasse |
| [Réseau local HTTPS](RESEAU_HTTPS.md) | Accès multi-appareils, certificats, adresse IP et pare-feu |
| [Gestion des mises à jour](GESTION_MISES_A_JOUR.md) | Architecture, vérifications, migration et limites du gestionnaire |
| [Signature des releases](RELEASE_SIGNING.md) | Clé Ed25519 épinglée, secret GitHub Actions et vérification côté client |
| [Configuration établissement avec ChatGPT](CONFIGURATION_ETABLISSEMENT_CHATGPT.md) | Préparer, anonymiser, prévalider et importer un JSON d'établissement (25 Mo maximum) |
| [Recette physique V25.2.0](RECETTE_PHYSIQUE_V25.2.0.md) | Contrôles sur une copie de données avant fusion et publication |

## Qualité et suivi du produit

| Document | Usage |
|---|---|
| [Audit produit V25](AUDIT_PRODUIT_V25.md) | Modules, parcours, thèmes et recette produit |
| [Registre des bugs V25](../REGISTRE_BUGS_V25.md) | Anomalies, statuts et recettes encore nécessaires |
| [Suivi des correctifs V25](../SUIVI_CORRECTIFS_V25.md) | Journal chronologique des diagnostics, modifications et résultats |
| [Branches et validations](qualite/ARCHIVES_BRANCHES_ET_VALIDATIONS.md) | Historique des PR/branches, résultats CI et plan de nettoyage |
| [Historique des versions](HISTORIQUE_VERSIONS.md) | Changelog V21/V25 et notes de livraison conservés |

## Archives historiques

Le dossier [archives](archives/) conserve les documents qui ont été remplacés ou dont les consignes ne sont plus applicables : anciens audits, états de construction, guides et ancien README. Ils sont conservés pour la traçabilité, pas comme procédures actuelles.

## Règles de maintenance documentaire

- Le README à la racine présente l'état courant du projet et oriente vers les bons guides.
- Le registre des bugs porte les statuts des anomalies ; un test automatisé réussi ne suffit pas à confirmer une correction métier.
- Le journal des correctifs conserve la chronologie, y compris les diagnostics invalidés et les tests en échec.
- L'historique des versions conserve les notes de livraison.
- Les documents archivés sont historiques : ils ne doivent pas servir de procédure d'installation courante.
- Toute campagne de branches doit conserver les liens vers les PR, commits, workflows et résultats avant suppression des références de branches.
