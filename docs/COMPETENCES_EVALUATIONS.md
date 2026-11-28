# Créer et évaluer des compétences

Ce guide décrit le parcours actuel dans Ma Classe. Il distingue trois notions qui ne sont pas interchangeables :

- **Compétence** : savoir-faire ou apprentissage que l'enseignant souhaite observer chez l'élève.
- **Critère** : dimension précise d'une grille, avec des niveaux descriptifs. Un critère appartient à une grille.
- **Niveau de maîtrise** : résultat attribué à un élève pour une compétence donnée dans une évaluation.

## 1. Créer une compétence

Deux accès mènent au même référentiel :

1. Ouvrir **Évaluations → Référentiel de compétences** pour créer ou gérer la bibliothèque.
2. Depuis **Évaluations → Nouvelle évaluation**, choisir la classe et la matière, puis cliquer sur **Créer ou gérer les compétences** sous la liste des compétences.

Le deuxième accès est conçu pour éviter de perdre le travail déjà commencé. Ma Classe conserve temporairement la classe, le groupe, la matière, le titre, la date, le barème, les critères, les compétences déjà cochées et le mode de publication. Après l'enregistrement de la nouvelle compétence, le formulaire d'évaluation est rouvert avec ces informations et la nouvelle compétence sélectionnée.

Pour créer une compétence, renseigner :
- un intitulé explicite, formulé comme un savoir-faire observable ;
- une matière, si la compétence doit être réservée à cette matière ;
- un ou plusieurs niveaux, si elle n'est pas destinée à tous les niveaux ;
- une description facultative pour préciser ce qui doit être observé.

Ne sélectionner aucun niveau signifie que la compétence reste disponible à tous les niveaux. Laisser la matière vide signifie qu'elle est disponible pour toutes les matières. Le nom d'une compétence déjà utilisée ne peut pas être modifié dans la bibliothèque : les évaluations et les résultats enregistrés utilisent ce libellé comme référence. Sa disponibilité et sa description peuvent en revanche être ajustées.

Exemples d'intitulés :
- « Comprendre un texte et en dégager les idées principales »
- « Justifier une réponse à l'aide d'un exemple précis »
- « Utiliser les unités et les conversions adaptées »
- « Construire une argumentation organisée »

## 2. Ajouter des compétences à une évaluation

Dans le formulaire d'évaluation :

1. Choisir la classe.
2. Saisir la matière et le titre.
3. Dans **Compétences à évaluer**, cocher les compétences pertinentes.
4. Si la liste est vide ou si une compétence manque, cliquer sur **Créer une compétence**. Après sa création, Ma Classe revient au formulaire sans effacer les autres choix.
5. Créer l'évaluation.

La liste est filtrée à partir du niveau de la classe et de la matière. Une compétence valable pour toutes les classes ou toutes les matières reste visible. Une compétence limitée à un autre niveau ou une autre matière n'est pas proposée dans ce contexte.

Une grille n'est pas obligatoire. Une évaluation peut rester une simple note, utiliser des compétences, des critères, ou les deux. Les critères servent à décomposer une grille en dimensions observables ; ils ne remplacent pas le référentiel de compétences.

## 3. Saisir les niveaux de maîtrise

Après la création, le tableau de saisie affiche une colonne par compétence sélectionnée. Pour chaque élève, choisir l'un des niveaux suivants :

| Valeur | Niveau affiché |
|---|---|
| 1 | Insuffisant |
| 2 | Fragile |
| 3 | Bien |
| 4 | Très bien |
| vide | Non évalué |

La note chiffrée et le niveau de maîtrise sont deux informations distinctes. Saisir un niveau pour une compétence ne modifie pas la note sur le barème. Laisser la cellule vide signifie que cette compétence n'a pas été évaluée pour cet élève.

Les résultats sont enregistrés dans la fiche de l'évaluation et peuvent être consultés dans le bilan des compétences. Les notes et niveaux déjà enregistrés restent associés à leur libellé de compétence.

## 4. Données historiques et compatibilité

Les anciennes compétences enregistrées sous forme de simples intitulés restent utilisables. Les compétences présentes dans les anciennes grilles et évaluations sont réintégrées au référentiel lorsqu'elles n'y figurent pas encore. Le mécanisme évite de créer une seconde entrée lorsqu'un libellé existe déjà, y compris si une ancienne chaîne de texte coexiste avec une fiche structurée.

La saisie des niveaux de maîtrise conserve les clés existantes dans `competencyRatings`. Les notes chiffrées, commentaires et résultats des autres compétences ne sont pas modifiés lorsqu'un niveau est ajouté ou effacé.

## 5. Parcours conseillé pour démarrer

Pour une première utilisation, créer deux ou trois compétences simples, limitées à la matière et au niveau concernés. Ouvrir ensuite une nouvelle évaluation de cette matière, les sélectionner, créer l'évaluation, puis attribuer un niveau à un élève dans chaque colonne. Le bilan des compétences permet ensuite de retrouver les résultats saisis.

Éviter de créer plusieurs compétences quasi identiques avec des formulations différentes. Utiliser une même compétence lorsqu'elle décrit réellement le même savoir-faire ; créer une variante si le niveau d'exigence ou le sens pédagogique est différent.
