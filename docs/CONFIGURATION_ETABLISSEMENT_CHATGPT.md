# Configurer un établissement Ma Classe avec ChatGPT

Cette fonction est réservée à la Direction. **Ma Classe ne se connecte jamais à ChatGPT** : aucune API ni aucun transfert automatique n'est utilisé. La Direction prépare les paramètres dans Ma Classe, copie un seul bloc de consignes et de données, le colle dans une conversation ChatGPT normale, puis importe le fichier JSON produit.

## Parcours prévu : aucun fichier à joindre à ChatGPT

1. Dans **Paramètres → Configuration de l'établissement**, compléter le formulaire de cadrage.
2. Cliquer sur **Enregistrer le formulaire dans Ma Classe**. Les réponses sont conservées dans les paramètres ; elles restent disponibles après fermeture de la fenêtre et redémarrage.
3. Cliquer sur **Copier les consignes et les données pour ChatGPT**, puis coller le texte obtenu dans une conversation ChatGPT. Il contient à la fois le rôle à donner au modèle, les règles de génération, les contraintes du format et les informations saisies dans le formulaire. Aucun modèle, schéma ou fichier d'instructions n'a besoin d'être importé dans ChatGPT.
4. Demander à ChatGPT de produire **un seul fichier JSON téléchargeable**. Si des informations indispensables manquent, il doit les demander avant de le créer et ne jamais tronquer le résultat.
5. Dans Ma Classe, choisir ce fichier JSON, examiner le rapport de prévalidation puis confirmer séparément l'import.

Le seul fichier que l'utilisateur doit ensuite sélectionner dans Ma Classe est donc le JSON final produit par ChatGPT. Le fichier est limité à 25 Mo et le schéma peut contenir jusqu'à 300 classes, 20 000 fiches élèves, 3 000 enseignants, 2 000 salles et 50 000 créneaux.

## Contenu du formulaire

Le formulaire guide la Direction sur les éléments nécessaires à la création d'un établissement complet, de la petite section à la terminale :

- nom de l'établissement et structure des classes : niveau, nombre de classes, nom des classes et effectifs prévus ;
- création ou non des fiches élèves, avec des pseudonymes générés ;
- nombre de professeurs et répartition facultative par matières/classes ;
- création ou non des profils et comptes professeurs ;
- matières, volumes horaires et éventuels groupes ;
- nombre de salles, capacités, types, équipements et indisponibilités ;
- génération ou non des emplois du temps, jours, horaires et contraintes d'organisation.

Les consignes copiées précisent les relations entre ces données. Elles demandent de vérifier la cohérence de tous les emplois du temps simultanément : aucun chevauchement de classe/groupe, d'enseignant ou de salle, respect des compétences, affectations, capacités, équipements, indisponibilités et volumes horaires.

## Comptes professeurs et fiches élèves facultatifs

Le choix **Créer les comptes de connexion des professeurs ? — Non** signifie que ChatGPT doit retourner `createTeacherAccounts: false`, mais doit toujours renseigner tous les professeurs pseudonymisés dans `teachers` et toutes leurs affectations dans les classes, les responsabilités de professeur principal et les créneaux. Ma Classe crée et conserve alors les fiches professeurs ainsi que les emplois du temps, sans ajouter d'utilisateur de connexion ni de mot de passe. La Direction peut ouvrir ultérieurement un compte depuis la fiche du professeur. Par défaut, les anciens fichiers qui ne contiennent pas cette propriété conservent le comportement historique et créent aussi les comptes professeurs.

Le choix **Créer les fiches élèves ? — Non** signifie que ChatGPT retourne `createStudentProfiles: false` et `students: []`. Les effectifs prévus restent indiqués au niveau de chaque classe ; ils servent notamment à contrôler la capacité des salles. Les fiches nominatives seront complétées ensuite dans Ma Classe. Par défaut, les anciens fichiers continuent de créer les fiches élèves.

Lorsque les fiches élèves sont demandées, ChatGPT doit créer une ligne par élève avec des pseudonymes stables, par exemple « Élève 6A-001 ». Il ne doit jamais inventer ou utiliser l'identité réelle d'un élève ou d'un personnel.

## Confidentialité

Ne saisis et ne transmets jamais à ChatGPT de vrais noms ou prénoms d'élèves/personnels, dates de naissance, emails, téléphones, identifiants de connexion, mots de passe, commentaires individuels ou autres données personnelles. Le formulaire doit utiliser des effectifs agrégés et des pseudonymes. Les identités réelles et coordonnées sont ajoutées ensuite directement dans Ma Classe.

Les profils professeurs sont stockés séparément des comptes de connexion. Lorsqu'un compte est demandé, les mots de passe provisoires sont générés et hachés localement au moment de l'import. ChatGPT ne doit produire aucun mot de passe ni identifiant interne Ma Classe.

## Prévalidation et import

Le fichier JSON est envoyé au validateur de Ma Classe avant toute écriture. Le rapport affiche le nombre de classes, fiches élèves, professeurs, salles et créneaux, ainsi que les erreurs bloquantes, avertissements et indicateurs de trous dans les emplois du temps. En présence d'une erreur bloquante, l'import reste impossible et aucune donnée n'est modifiée.

À la confirmation, Ma Classe crée une sauvegarde de sécurité puis ajoute les éléments validés. L'import est additif : il ne remplace jamais silencieusement les classes, salles ou cours déjà présents. Les identifiants internes et les mots de passe provisoires sont générés localement. Les identifiants des comptes professeurs, lorsqu'ils existent, ne sont affichés qu'une seule fois après l'import.

Ma Classe ne peut pas garantir qu'un grand emploi du temps sera optimisé par ChatGPT sans arbitrage humain. Le contrôle serveur bloque les incohérences détectables ; la Direction doit aussi examiner le rapport, les contraintes réelles et les éventuels avertissements avant confirmation.
