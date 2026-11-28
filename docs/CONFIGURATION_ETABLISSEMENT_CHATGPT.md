# Configurer un établissement Ma Classe avec ChatGPT

Cette fonction est réservée à la Direction. **Ma Classe ne se connecte jamais à ChatGPT** : aucune API ni aucun transfert automatique n'est utilisé. La Direction prépare les paramètres dans Ma Classe, copie un seul bloc de consignes et de données, le colle dans une conversation ChatGPT normale, puis importe le fichier JSON produit.

## Parcours prévu : aucun fichier à joindre à ChatGPT

1. Dans **Paramètres → Configuration de l'établissement**, compléter le formulaire de cadrage.
2. Cliquer sur **Enregistrer le formulaire dans Ma Classe**. Les réponses sont conservées dans les paramètres ; elles restent disponibles après fermeture de la fenêtre et redémarrage.
3. Cliquer sur **Copier les consignes et les données pour ChatGPT**, puis coller le texte obtenu dans une conversation ChatGPT. Il contient à la fois le rôle à donner au modèle, les règles de génération, les contraintes du format et les informations saisies dans le formulaire. Aucun modèle, schéma ou fichier d'instructions n'a besoin d'être importé dans ChatGPT.
4. Demander à ChatGPT de produire **un seul fichier JSON téléchargeable**. Si des informations indispensables manquent, il doit les demander avant de le créer et ne jamais tronquer le résultat.
5. Dans Ma Classe, choisir ce fichier JSON, examiner le rapport de prévalidation puis confirmer séparément l'import.

Le seul fichier que l'utilisateur doit ensuite sélectionner dans Ma Classe est donc le JSON final produit par ChatGPT. Le fichier est limité à 25 Mo et le schéma peut contenir jusqu'à 300 classes, 20 000 fiches élèves, 3 000 enseignants, 2 000 salles et 50 000 créneaux.

Les champs **Nombre de professeurs à prévoir** et **Nombre de salles à prévoir** sont facultatifs : un champ laissé vide signifie « non précisé », pas zéro. Lorsqu'un nombre est saisi, les consignes demandent à ChatGPT de créer exactement ce nombre de profils ou de salles. Si le nombre est indispensable mais absent du formulaire et impossible à déduire sans inventer, ChatGPT doit demander une précision avant de générer le JSON.

## Contenu du formulaire

Le formulaire guide la Direction sur les éléments nécessaires à la création d'un établissement complet, de la petite section à la terminale :

Le cadrage distingue désormais les composantes pédagogiques (sélection multiple) de l'organisation de l'établissement (groupe scolaire, cité scolaire, polyvalent, multi-sites, etc.). Un même établissement peut donc sélectionner plusieurs cycles ou filières. Les anciens formulaires à choix unique sont repris automatiquement quand la correspondance est certaine ; une ancienne valeur ambiguë est conservée dans les précisions et doit être confirmée par la Direction. Le cadrage comprend aussi l'année scolaire, l'organisation par trimestres, semestres ou régime variable et les horaires de pause/récréation. Ces précisions sont facultatives : les dossiers déjà enregistrés restent compatibles et les nouveaux champs absents restent vides au rechargement. Un récapitulatif se met à jour pendant la saisie pour rappeler les choix structurants (fiches élèves, comptes professeurs et génération des emplois du temps). Le formulaire vérifie les champs obligatoires avant l'enregistrement ou la copie. Le récapitulatif indique désormais les lignes de salles décrites et les éventuelles incohérences ; une ligne attachée à une composante désélectionnée doit être corrigée avant transmission.


- nom et année scolaire ;
- plusieurs composantes pédagogiques sélectionnables simultanément : maternelle, élémentaire, collège, lycée général, lycée technologique, lycée professionnel, post-bac, CFA/apprentissage, formation continue ou autre composante ;
- structure du regroupement distinguée des composantes : établissement autonome, groupe scolaire, cité scolaire, établissement polyvalent, réseau ou autre ;
- implantation physique séparée : site unique ou plusieurs sites/antennes ; précisions libres sur les bâtiments, les liaisons et les déplacements ;
- structure des classes saisie sous forme de lignes : composante, niveau, nombre de classes, effectif par classe et noms exacts facultatifs ;
- matières saisies sous forme de lignes : composante, niveau, matière/domaine, volume horaire, groupe, détail des sous-domaines et statut de l'horaire ; un bouton préremplit les programmes nationaux selon les composantes et les niveaux ;
- affectations des professeurs saisies sous forme de lignes : pseudonyme, composante, matières, classes et volume éventuel. Le même pseudonyme utilisé dans plusieurs composantes représente le même professeur et doit être regroupé dans un seul profil ;
- calendriers saisis séparément par composante : jours de cours, horaires de début/fin, pause méridienne, récréations et particularités ;
- anciennes précisions libres conservées dans un panneau replié afin de préserver les formulaires antérieurs et les cas atypiques ;
- création ou non des fiches élèves, avec des pseudonymes générés ;
- nombre total de professeurs et de salles ; salles détaillées par lignes (site/bâtiment, nom, type, capacité, équipements et restrictions), avec notes libres conservées en complément ;
- création ou non des comptes professeurs ; les fiches et affectations pédagogiques restent créées même sans compte ;
- génération ou non des emplois du temps, avec contrôle des contraintes communes et particulières de chaque composante.

Les boutons « Ajouter un niveau », « Ajouter une matière », « Ajouter une affectation » et « Ajouter un calendrier » créent des lignes à compléter, sans obliger la Direction à rédiger un long descriptif. Le bouton « Préremplir les programmes nationaux » crée les niveaux et les lignes pédagogiques correspondant aux choix de composantes, de séries et de spécialités ; les effectifs restent à renseigner par la Direction. Une ligne doit toujours être rattachée à une composante. Les menus de composante suivent les cycles cochés ; si une seule composante est sélectionnée, elle est proposée par défaut.

Les salles déjà connues se décrivent une par une : site ou bâtiment, nom, type, capacité, équipements et restrictions. Le nombre total de salles peut être supérieur au nombre de lignes renseignées ; ChatGPT doit alors compléter uniquement les salles restantes sans dupliquer celles déjà déclarées. Une salle portant le même nom sur deux sites différents reste deux salles distinctes.

Le total de professeurs doit correspondre au nombre de pseudonymes uniques. Pour un professeur qui intervient dans plusieurs composantes, réutilise le même pseudonyme dans plusieurs lignes : ChatGPT doit regrouper les affectations dans un seul profil. Les calendriers peuvent varier d'une composante à l'autre.

Les anciennes réponses en texte libre sont affichées dans un panneau replié « Notes libres ou anciennes précisions ». Elles sont conservées et ajoutées comme contexte complémentaire ; elles ne remplacent pas les nouvelles lignes structurées.

Les consignes copiées précisent les relations entre ces données. Elles demandent de vérifier la cohérence de tous les emplois du temps simultanément : aucun chevauchement de classe/groupe, d'enseignant ou de salle, respect des compétences, affectations, capacités, équipements, indisponibilités et volumes horaires.

## Référentiel national préchargé (rentrée 2026-2027)

Dans l'étape **Identité et composantes**, le régime pédagogique distingue un établissement sous contrat (programmes et horaires nationaux), une situation mixte et un établissement hors contrat (référentiel proposé comme base indicative). Après avoir choisi les composantes, cliquer sur **Préremplir les programmes nationaux** ajoute les niveaux et les matières correspondants. Les séries technologiques et les spécialités de la voie générale doivent être cochées lorsqu'elles sont réellement proposées.

Le préremplissage couvre :
- **Maternelle** : TPS (accueil éventuel), petite, moyenne et grande sections ; domaines d'apprentissage et contenu détaillé (oral, vocabulaire, phonologie, premiers contacts avec l'écrit, motricité, arts, premiers outils mathématiques, découverte du monde, repères spatio-temporels et EVAR).
- **Élémentaire** : CP, CE1, CE2, CM1 et CM2, avec les horaires moyens des cycles 2 et 3 ; le français conserve ses dimensions orales, lecture/compréhension, écriture, vocabulaire, grammaire et orthographe.
- **Collège** : 6e, 5e, 4e et 3e, avec les enseignements et volumes horaires des grilles en vigueur.
- **Lycée général** : seconde générale et technologique, première et terminale générales ; les spécialités sont ajoutées uniquement parmi celles sélectionnées.
- **Lycée technologique** : seconde générale et technologique, puis première et terminale de chaque série cochée (STMG, ST2S, STI2D, STL, STD2A, STHR ou S2TMD).
- **Lycée professionnel** : seconde, première et terminale professionnelles, à partir de la grille annuelle de référence du baccalauréat professionnel. Les équivalents hebdomadaires sont des moyennes calculées sur 30 semaines, et non une promesse de créneau identique chaque semaine.

Le bouton ajoute aussi une ligne de structure pour chaque niveau, mais laisse volontairement **le nombre de classes et l'effectif par classe vides** : ces données sont propres à l'établissement et ne peuvent pas être déduites d'un programme national. Les lignes de cours sont modifiables ou supprimables. L'établissement peut ajouter des options, langues, enseignements locaux et matières complémentaires. Le champ libre correspondant est transmis à ChatGPT ; le prompt lui demande également de proposer les matières pertinentes manquantes, clairement marquées comme facultatives ou propres à l'établissement, et de demander confirmation avant de les traiter comme obligatoires.

Les statuts d'horaires sont conservés sans ambiguïté : horaire hebdomadaire, moyenne de cycle, moyenne hebdomadaire calculée depuis un volume annuel, choix de spécialité, volume global de cycle ou domaine sans quota horaire autonome. En maternelle, les **24 heures hebdomadaires concernent l'ensemble des enseignements** ; les textes ne répartissent pas un quota officiel par domaine. Ma Classe conserve donc les détails des apprentissages sans inventer des heures par sous-domaine. Un domaine sans horaire autonome n'est pas comparé à un cours isolé lors de la prévalidation du planning.

Les références réglementaires et documentaires sont conservées comme métadonnées internes pour guider la génération et le contrôle ; elles ne sont pas affichées dans les lignes du formulaire. Le formulaire ne constitue pas un remplacement de l'arbitrage de la Direction : les options réellement ouvertes, les choix de spécialité et les particularités de l'établissement doivent être vérifiés avant la génération définitive de l'emploi du temps.

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
