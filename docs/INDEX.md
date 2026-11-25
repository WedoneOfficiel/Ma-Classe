# Documentation MaClasse

## Documents de référence

| Document | Usage |
|---|---|
| [Installation](INSTALLATION.md) | Installer, démarrer et sauvegarder MaClasse |
| [Réseau local HTTPS](RESEAU_HTTPS.md) | Accès multi-appareils, certificats, adresse IP et pare-feu |
| [Gestion des mises à jour](GESTION_MISES_A_JOUR.md) | Architecture, vérifications, migration et limites du gestionnaire |
| [Signature des releases](RELEASE_SIGNING.md) | Clé Ed25519 épinglée, secret GitHub Actions et vérification côté client |
| [Audit produit V25](AUDIT_PRODUIT_V25.md) | Audit des modules, des parcours, des thèmes et de l'interface |
| [Registre des bugs V25](../REGISTRE_BUGS_V25.md) | État courant des anomalies, demandes et recettes restantes |
| [Suivi des correctifs V25](../SUIVI_CORRECTIFS_V25.md) | Journal chronologique des diagnostics, interventions et résultats |
| [Historique des versions](HISTORIQUE_VERSIONS.md) | Changelog V25 et notes V21 conservés intégralement |

## Archives

Le dossier [archives](archives/) conserve les documents qui ont été remplacés ou dont les consignes ne sont plus applicables : anciens audits, états de construction, guides et ancien README. Ils sont conservés pour la traçabilité, pas comme procédures actuelles.

## Règle de maintenance documentaire

- Le README à la racine présente l'état du projet et oriente vers les bons guides.
- Le registre des bugs porte les statuts courants ; le journal des correctifs conserve la chronologie.
- L'historique des versions conserve les notes de livraison, y compris les notes héritées des anciennes versions.
- Les procédures actives sont tenues à jour dans `docs/`. Les documents archivés ne doivent pas être modifiés pour donner une fausse impression d'état courant.
