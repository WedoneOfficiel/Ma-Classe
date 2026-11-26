# Traçabilité du dépôt, des branches et des validations

> État arrêté au 26 novembre 2026, après publication de V25.1.1. Ce document conserve le contexte technique avant nettoyage des branches distantes. Les PR, tags, commits et exécutions GitHub Actions restent les preuves détaillées.

## État de référence

| Élément | Valeur |
|---|---|
| Branche de référence | `main` |
| Commit de référence V25.1.1 | `b5cc07d6747605f2eac6ad11dffb3ce0bbb9ec43` |
| Main après archivage documentaire | `710c184163e8b9896ab3d539acb007911c65189e` |
| Version | `V25.1.1` |
| Tag | `v25.1.1` |
| Release | [GitHub — V25.1.1](https://github.com/WedoneOfficiel/Ma-Classe/releases/tag/v25.1.1) |
| Publication | 26/11/2026, workflow manuel #4, run [45806118500](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45806118500) |
| PR finale | [#19 — fiabiliser le gestionnaire macOS et afficher la préparation](https://github.com/WedoneOfficiel/Ma-Classe/pull/19) |

La branche `main` est la seule branche de développement de référence. Les tags et les releases versionnés doivent être conservés même après suppression des branches de campagne.

## Résultats de tests à conserver

### Campagne complète après fusion
- Workflow de validation post-fusion #1844 : [run 45804151065](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45804151065).
- Trois jobs réussis : tests Linux, validation macOS Apple Silicon/launchd réel et régression navigateur Firefox réel.
- 93 fichiers couverts par la passe générale : 55 tests JavaScript et 38 tests Python. Les scénarios spécifiques à un système sont exécutés sur le runner adapté ; ils ne sont pas artificiellement simulés sur un autre OS.
- Parcours de mise à jour ciblé : 15 tests du lanceur direct, 19 tests launchd et 33 tests du gestionnaire de versions.
- Le test Firefox réel couvre la navigation et la persistance de l'EDT, les contextes Direction/Élève, la synchronisation, les accès cloisonnés, les modules principaux et les thèmes.
- Aucun nouveau défaut logiciel n'a été reproduit pendant cette passe générale. Les échecs initiaux relevés pendant le développement concernaient des assertions de test, corrigées avant fusion.

### Publication
- Workflow #4 / run [45806118500](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45806118500) : conclusion `success`.
- Jobs réussis : validation Firefox, tests Linux, validation macOS/Apple Silicon/launchd et publication.
- Le job de publication a vérifié la cohérence du tag et de `VERSION.txt`, construit l'archive, produit le manifeste, signé le manifeste et publié les trois assets :
  - `maclasse-update.zip`
  - `maclasse-update.json`
  - `maclasse-update.sig`
- Le tag annoté `v25.1.1` pointe sur le commit `b5cc07d6747605f2eac6ad11dffb3ce0bbb9ec43`.

### Recette réelle macOS
- Départ : V25.0.23, qui téléchargeait et préparait la mise à jour mais ne lançait pas le gestionnaire indépendant.
- L'installation depuis l'interface a échoué au déclenchement de l'ancien service ; le lanceur direct ajouté dans V25.1.1 a été utilisé après préparation.
- L'utilisateur a confirmé que l'installation est finalement réussie et que MaClasse fonctionne.
- Aucun changement de schéma de données n'était requis.
- Nuance de transition : l'ancien gestionnaire V25.0.23 ne contrôlait que le SHA-256 de l'archive ; le contrôle de signature Ed25519 côté client s'applique aux mises à jour effectuées une fois V25.1.1 active.

## Historique des PR

| PR | Sujet | État au 26/11/2026 | Branche |
|---:|---|---|---|
| #1 | Comptes élèves canoniques et matières enseignants | Fusionnée | `fix/student-canonical-accounts` |
| #2 | Création de classes par enseignant et persistance élèves | Fusionnée | `fix/teacher-class-student-persistence` |
| #3 | Connexion élève, EDT et actualisation formulaire | Fusionnée | `fix/student-login-schedule-form-refresh` |
| #4 | Stabilisation globale V25.0.18 | Fusionnée | `fix/v25.0.18-stabilite-globale` |
| #5 | Récurrences EDT et import UTF-8 V25.0.19 | Fusionnée | `fix/v25.0.19-edt-certificat-import` |
| #6 | Disparition des cours dans l'EDT V25.0.21 | Fermée sans fusion, dépassée par les corrections EDT et synchronisation ultérieures | `fix/v25.0.20-edt-render-root-cause` |
| #7 | Affectations pédagogiques V25.0.22 — première proposition | Fermée, non fusionnée ; reprise par #8 | `feat/teacher-assignment-permissions` |
| #8 | Affectations pédagogiques et droits enseignants | Fusionnée | `feat/teacher-assignment-permissions` |
| #9 | Parcours EDT et espace élève V25 | Fusionnée | `fix/v25-student-teacher-workflows` |
| #10 | Gestionnaire de mises à jour AMEL-01 | Fusionnée | `feature/amel-01-update-manager` |
| #11 | Publication des correctifs applicatifs V25.0.23 | Fermée sans fusion, proposition remplacée par les releases V25.0.23, V25.1.0 et V25.1.1 | `release/v25.0.23-validated-fixes` |
| #12 | Accès élève aux bulletins et à la messagerie V25.0.23 | Fusionnée | `fix/recette-v25-0-23` |
| #13 | Stabilisation, sécurité et suivi de classe V25.1.0 | Fusionnée | `feat/v25.0.25-stabilisation-reseau-migrations` |
| #14 | Validation du certificat HTTPS macOS/X.509 | Fusionnée | `fix/v25.1.1-macos-certificate-sans` |
| #15 | Rollback macOS et notes de publication — proposition intermédiaire | Fermée, remplacée par #16 | `fix/v25.1.1-macos-rollback-release-notes` |
| #16 | Fiabilisation du rollback macOS et publication | Fusionnée | `fix/v25.1.1-macos-rollback-release` |
| #17 | Workflow manuel de publication stable | Fusionnée | `feat/v25.1.1-manual-release-workflow` |
| #18 | Lanceur réseau macOS compatible LibreSSL | Fusionnée | `fix/macos-network-launcher-libreSSL` |
| #19 | Lancement launchd, diagnostics et progression visible | Fusionnée | `fix/v25.1.1-updater-launchd-progress` |
| `fix/v25.0.20-edt-render-root-cause` | `e4dbf19c9283` | PR #6 fermée sans fusion ; remplacée par les corrections EDT et la couverture Firefox ultérieures |
| `release/v25.0.23-validated-fixes` | `bf1cca1c9b76` | PR #11 fermée ; proposition de release devenue obsolète |
| #20 | Cohérence inter-modules Évaluations/Bulletins V25.1.2 | Ouverte — campagne en cours | `fix/v25.1.2-cross-module-consistency` |

Les conversations et patches des PR demeurent accessibles sur GitHub après suppression de la référence de branche. Les liens ci-dessus sont les points d'entrée pour retrouver l'objectif, les changements et les commentaires de chaque campagne.

## Inventaire des branches et décision de nettoyage

Les SHA ci-dessous ont été relevés sur les références distantes au 26/11/2026. La suppression des branches ne supprime ni les tags de release ni les PR déjà enregistrées.

### Branches candidates au nettoyage

Ces branches correspondent à des PR fusionnées, à des propositions explicitement remplacées ou à des campagnes historiques closes sans fusion. Les PR #6 et #11 ont été clôturées après vérification de leur remplacement par le code actuellement intégré.

| Branche | SHA observé | Motif |
|---|---|---|
| `feat/teacher-assignment-permissions` | `d3d0ff098043` | PR #8 fusionnée ; PR #7 antérieure fermée |
| `feat/v25.0.25-stabilisation-reseau-migrations` | `dd032cf39a8c` | PR #13 fusionnée |
| `feat/v25.1.1-manual-release-workflow` | `5f9014db3ef3` | PR #17 fusionnée |
| `feature/amel-01-update-manager` | `f72342c15cab` | PR #10 fusionnée |
| `fix/macos-network-launcher-libreSSL` | `878d1a38436c` | PR #18 fusionnée |
| `fix/recette-v25-0-23` | `8a861fd2fcc0` | PR #12 fusionnée |
| `fix/student-accounts-canonical` | `6423536384e3` | Branche orpheline ; 0 commit en avance sur `main` |
| `fix/student-canonical-accounts` | `5d93aa24e958` | PR #1 fusionnée |
| `fix/student-login-schedule-form-refresh` | `f36c099e72f8` | PR #3 fusionnée |
| `fix/teacher-class-student-persistence` | `e581e3c6116c` | PR #2 fusionnée |
| `fix/v25-student-teacher-workflows` | `9c83ee3f38da` | PR #9 fusionnée |
| `fix/v25.0.18-stabilite-globale` | `4a4f1d19d8a8` | PR #4 fusionnée |
| `fix/v25.0.19-edt-certificat-import` | `70292d1ad8cf` | PR #5 fusionnée |
| `fix/v25.1.1-macos-certificate-sans` | `feb38c31ada6` | PR #14 fusionnée |
| `fix/v25.1.1-macos-rollback-release` | `66243aeb3738` | PR #16 fusionnée |
| `fix/v25.1.1-macos-rollback-release-notes` | `78d18414453a` | PR #15 remplacée par #16 |
| `fix/v25.1.1-updater-launchd-progress` | `9e68cb764e27` | PR #19 fusionnée |

### Branches à conserver

| Branche | Motif |
|---|---|
| `main` | Branche de référence, à conserver |
| `fix/v25.1.2-cross-module-consistency` | PR #20 ouverte ; campagne corrective en cours |

Le workflow de nettoyage recontrôle les PR ouvertes et le SHA de chaque branche avant suppression. La PR #20 reste donc protégée automatiquement pendant la campagne V25.1.2. Toute branche déplacée depuis l'inventaire ou encore référencée par une PR ouverte est ignorée.
## Workflow de nettoyage

Après vérification de cette archive, ouvrir l'onglet Actions et lancer manuellement **« Nettoyer les anciennes branches MaClasse »** depuis `main` :

[Workflow de nettoyage des branches](../../.github/workflows/cleanup-merged-branches.yml)

Le rapport du workflow indique chaque branche supprimée ou ignorée. La branche `main`, la branche de la PR #20 et tous les tags de version sont exclus.

## Politique pour les prochaines campagnes

1. Créer une branche par campagne et une PR liée à un objectif précis.
2. Conserver les logs/résultats de CI et le SHA du commit validé dans la PR ou dans cette archive.
3. Après fusion, vérifier que le commit de fusion est dans `main`, puis supprimer la branche de campagne.
4. Ne jamais supprimer une branche dont une PR est ouverte, ni une branche déplacée depuis le dernier inventaire sans réexamen.
5. Conserver les tags et les releases stables : ce sont les repères reproductibles des versions livrées.
