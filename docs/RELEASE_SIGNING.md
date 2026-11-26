# Signature des releases MaClasse

## Objectif

Chaque release MaClasse doit contenir trois fichiers :
- `maclasse-update.zip` : archive de l'application ;
- `maclasse-update.json` : manifeste et empreinte SHA-256 de l'archive ;
- `maclasse-update.sig` : signature Ed25519 détachée des octets exacts du manifeste.

Le client vérifie la signature avec `release-signing-public-key.txt`, qui fait partie du code MaClasse déjà installé. Le SHA-256 reste utile pour l'intégrité de l'archive, mais c'est la signature qui authentifie le manifeste et donc l'empreinte attendue.

## 1. Générer la paire de clés sur un poste de confiance

Depuis le dossier MaClasse, après installation des dépendances :

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/generate_release_signing_key.py
```

Le script crée :
- la clé privée dans `~/.config/maclasse/release-signing-private-key.b64` (permissions POSIX 0600) ;
- la clé publique dans `release-signing-public-key.txt` à la racine du dépôt.

La clé privée ne doit **jamais** être ajoutée à Git, à une archive, à une pièce jointe, à un ticket ou à une conversation. Conserver une sauvegarde chiffrée hors du poste. La perte de cette clé bloque la publication de futures mises à jour jusqu'à la réalisation d'une rotation de confiance. Si le script indique qu'une clé existe déjà, ne pas utiliser `--force` : il faut d'abord décider explicitement d'une rotation de clé et préparer les clients qui font déjà confiance à l'ancienne.

## 2. Committer uniquement la clé publique

Vérifier le contenu de `release-signing-public-key.txt` : il doit contenir une seule valeur Base64 correspondant à 32 octets. Committer ce fichier sur la branche de livraison, puis fusionner le changement dans la branche qui servira à créer le tag. Ne jamais committer le fichier privé.

## 3. Créer le secret GitHub Actions

Dans le dépôt GitHub :

1. Ouvrir **Settings**.
2. Ouvrir **Secrets and variables** puis **Actions**.
3. Dans **Repository secrets**, choisir **New repository secret**.
4. Nommer le secret exactement `MACLASSE_RELEASE_SIGNING_KEY_B64`.
5. Coller le contenu du fichier privé `~/.config/maclasse/release-signing-private-key.b64`, sans ajouter de préfixe ni de guillemets.
6. Enregistrer.

La valeur du secret n'est jamais affichée par le workflow. Avant de publier, le script de signature dérive la clé publique de la clé privée et la compare à la clé versionnée. Une différence arrête la publication.

## 4. Vérifier la chaîne

Le workflow `.github/workflows/publish-release.yml` :
1. attend le succès des tests Linux, macOS et Firefox ;
2. vérifie la cohérence du tag et de `VERSION.txt` ;
3. choisit les notes versionnées dans `.github/release-notes/<tag>.md` lorsqu'elles existent, sinon utilise les notes générées par GitHub ;
4. construit l'archive et le manifeste avec ces mêmes notes ;
5. signe le manifeste avec le secret GitHub Actions ;
6. publie les trois assets et utilise le même fichier de notes pour le corps de la release.

Pour une release qui nécessite une description rédigée, ajouter le fichier correspondant avant de créer le tag (par exemple `.github/release-notes/v25.1.1.md`). Ainsi, le texte affiché sur GitHub et le champ `release_notes` du manifeste signé restent identiques. Les releases sans fichier dédié conservent le comportement générique de génération automatique.
Côté client, le gestionnaire exige exactement un asset de signature et valide Ed25519 avant de parser le manifeste ou de préparer l'archive. L'absence de la clé publique, du secret, de la signature ou une incohérence entre les deux clés bloque la mise à jour.

## 5. Pont de migration des anciennes installations

La dernière release stable antérieure à cette évolution est V25.0.23 et ne vérifie pas encore Ed25519. Une installation V25.0.23 utilise donc son ancien mécanisme pour recevoir V25.1.0, qui embarque le vérificateur. Ce premier passage est un **pont de migration** : il ne faut pas prétendre qu'il est déjà authentifié par la nouvelle clé. Dès que V25.1.0 est installée avec la clé publique de production configurée, toutes les mises à jour suivantes doivent être signées et vérifiées.

## 6. Rotation de clé

Ne pas remplacer directement la clé publique en production : les clients existants ne feraient plus confiance aux signatures de la nouvelle clé. Une rotation doit être préparée en deux étapes avec une version qui embarque temporairement les deux clés publiques, puis une version ultérieure qui retire l'ancienne. Tant que cette procédure n'est pas développée, protéger la clé privée et conserver une sauvegarde chiffrée.
