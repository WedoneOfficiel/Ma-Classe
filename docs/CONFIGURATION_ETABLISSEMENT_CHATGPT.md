# Créer un dossier d'établissement Ma Classe avec ChatGPT

Cette fonction est réservée à la Direction. **Ma Classe ne se connecte jamais à ChatGPT** : la préparation se fait dans une conversation ChatGPT normale, puis le fichier JSON est téléchargé et importé manuellement dans Ma Classe.

## Parcours en quatre étapes

1. Dans Ma Classe, ouvrir **Administration → Configuration d'établissement** et télécharger le modèle JSON, le schéma JSON et les instructions. Pour un établissement déjà configuré, exporter également le contexte anonymisé.
2. Dans ChatGPT, décrire librement l'établissement : classes, niveaux, effectifs, matières, professeurs, spécialités, contraintes, salles et horaires.
3. Demander à ChatGPT de produire un fichier JSON conforme au format « maclasse-establishment », version 1.
4. Dans Ma Classe, sélectionner ce JSON, lire le rapport de validation, puis confirmer l'import.

Le dossier de contexte exporté par Ma Classe ne contient ni nom d'élève, ni email, ni téléphone, ni identifiant de compte : seulement les effectifs agrégés, les niveaux/groupes, les matières, des libellés de professeurs anonymisés, les salles et les créneaux existants. Ne transmettez pas de données sensibles ou inutiles à ChatGPT. Les identifiants internes et mots de passe créés lors de l'import sont toujours générés localement par Ma Classe.

## Prompt prêt à copier dans ChatGPT

> Tu es un assistant expert en organisation d'établissement scolaire et en construction d'emplois du temps.
>
> À partir de ma description, prépare une configuration complète importable dans Ma Classe au format JSON « maclasse-establishment », version 1. Si je joins un dossier contexte-etablissement-maclasse-anonymise.json, utilise-le pour éviter les doublons et comprendre les niveaux, effectifs agrégés, affectations, salles et créneaux existants. La V1 est additive : ne génère que les nouvelles classes, nouveaux comptes professeurs et nouvelles salles/cours ; ne prétends pas modifier ou réutiliser les objets existants.
>
> **Tu dois produire un seul fichier JSON**, sans commentaire ni texte autour du JSON, et respecter exactement le schéma establishment-import.v1.schema.json.
>
> Commence par identifier les informations qui manquent et pose uniquement les questions indispensables. Ne devine jamais les contraintes importantes : effectifs, matières, volumes horaires, compétences des professeurs, indisponibilités, capacité des salles, équipements, horaires de l'établissement et date de début des cours.
>
> Le fichier final doit contenir :
> - toutes les classes, y compris les classes multi-niveaux et leurs groupes ;
> - une fiche par élève, avec une clé unique, sa classe, son niveau et son groupe ;
> - les professeurs, les matières qu'ils peuvent enseigner et les classes qui leur sont attribuées ;
> - un professeur principal par classe lorsque cela est demandé ;
> - les salles, leur capacité, leur type, leurs équipements et leurs indisponibilités ;
> - tous les cours, leurs durées, jours, heures, classes/groupes, professeurs, salles et récurrences ;
> - les volumes horaires par matière dans subjectRequirements, lorsqu'ils sont fournis.
>
> **Emploi du temps :**
> - aucun professeur ne peut avoir deux cours simultanés ;
> - une classe ou un même groupe ne peut pas avoir deux cours simultanés ;
> - une salle ne peut pas être utilisée deux fois simultanément ;
> - chaque professeur doit être affecté uniquement aux matières qu'il enseigne et aux classes qui lui sont attribuées ;
> - les volumes horaires demandés doivent être respectés ;
> - les salles doivent être suffisamment grandes et posséder les équipements requis ;
> - respecter les indisponibilités déclarées ;
> - éviter les trous, les journées inutilement longues et les matières mal réparties.
>
> Les jours sont monday, tuesday, wednesday, thursday ou friday (ou les entiers 0 à 4, lundi = 0). Les heures suivent HH:MM. startDate est la date à partir de laquelle le cours peut commencer ; Ma Classe calcule la première occurrence correspondant au jour demandé. Les récurrences possibles sont weekly, biweekly, triweekly, custom (avec intervalWeeks) et once.
>
> N'invente jamais un professeur, une salle ou un groupe dans une affectation sans le déclarer dans sa rubrique. Chaque key doit être unique dans sa rubrique et toutes les références doivent exister. Pour une classe à plusieurs niveaux, indique le niveau de chaque élève ; Ma Classe créera un groupe de niveau si nécessaire.
>
> Utilise des noms fictifs si je demande un établissement de démonstration. Ne crée aucun mot de passe, compte technique, identifiant interne Ma Classe ni champ non prévu par le schéma : Ma Classe générera les identifiants et mots de passe provisoires lors de l'import.
>
> Avant de produire le fichier, contrôle le nombre d'élèves par classe, les volumes horaires, les conflits de professeurs/classes/salles, les groupes, les capacités et les trous. Si une contrainte est impossible à satisfaire, signale-le et demande une décision au lieu de produire un planning mensonger.

## Comment lire le résultat dans Ma Classe

Le contexte anonymisé sert uniquement à informer ChatGPT. La V1 de l'import est additive : elle crée de nouvelles classes, de nouveaux comptes professeurs, de nouvelles salles et leurs cours ; elle ne modifie pas les classes, comptes, salles ou cours déjà présents et ne réutilise pas leurs identifiants. Le prompt doit donc demander uniquement les nouveaux objets à créer.

Le premier passage est une prévisualisation : il ne modifie aucune donnée. Ma Classe signale les erreurs bloquantes, les avertissements et les indicateurs de trous dans les emplois du temps. L'import n'est possible qu'en l'absence d'erreur bloquante.

À la confirmation, Ma Classe crée les classes, les élèves, les profils et comptes professeurs, les salles et les créneaux. Chaque compte professeur reçoit un identifiant et un mot de passe provisoire générés localement ; le mot de passe n'est affiché qu'une fois. Aucun compte élève n'est créé automatiquement.

L'import ajoute des éléments et ne remplace jamais silencieusement les classes ou les salles déjà présentes. Une sauvegarde de sécurité est créée avant toute écriture.


## Générateur guidé — parcours actuel en trois étapes

1. **Décrire la structure** : télécharger le modèle JSON, le schéma, les instructions, et éventuellement le contexte structurel anonymisé exporté par Ma Classe.
2. **Générer le JSON manuellement dans ChatGPT** : joindre uniquement ces éléments structurels, indiquer les classes, niveaux, groupes, effectifs agrégés, matières, volumes horaires, contraintes de salles et disponibilités. Aucun transfert automatique ni appel d'API n'existe.
3. **Vérifier et importer** : sélectionner le fichier dans Ma Classe, lire les erreurs et avertissements de la prévalidation, puis confirmer séparément l'import. Aucune modification n'est écrite pendant la prévisualisation.

### Confidentialité des personnes

Ne transmettez jamais à ChatGPT de vrais noms ou prénoms d'élèves/personnels, dates de naissance, emails, téléphones, identifiants de connexion, mots de passe, commentaires individuels ou autres données sensibles. Utilisez des pseudonymes stables tels que « Élève 6A-001 » et « Professeur 01 », avec des effectifs agrégés. Les identités réelles et coordonnées se complètent ensuite localement dans Ma Classe.

Le contexte exporté par Ma Classe est structurel et pseudonymisé : il ne contient ni noms ni coordonnées d'élèves, et pseudonymise les professeurs. Les comptes et mots de passe provisoires des professeurs sont créés localement au moment de l'import.
