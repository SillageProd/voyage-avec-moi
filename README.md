# Voyage avec moi

Petite sœur de [Lis avec moi](https://github.com/SillageProd/lis-avec-moi) : une app pour apprendre les pays et les capitales (enfants de 6 à 13 ans).
Adresse : https://sillageprod.github.io/voyage-avec-moi/ (édition néerlandaise « Reis met mij » : https://sillageprod.github.io/voyage-avec-moi/nl/).
Elle s'installe sur iPad et iPhone depuis Safari : **Partager → Sur l'écran d'accueil**. Elle marche ensuite hors ligne.

- Jusqu'à 6 profils, sans mot de passe.
- On choisit l'**Union européenne** (les 27 pays membres) ou un continent : Europe, Afrique, Asie, Amérique du Nord (avec l'Amérique centrale et les Caraïbes), Amérique du Sud, Océanie.
- Quatre jeux, **sans chrono** :
  - **Trouve la capitale** : le pays (drapeau, nom, place sur la carte) → choisir sa capitale.
  - **Trouve le pays** : la capitale → choisir son pays.
  - **Place les pays** : toucher le pays sur la carte.
  - **Place les capitales** : toucher la ville sur la carte.
- 10, 20 ou tous les pays ; pour les deux premiers jeux, 3, 4 ou 6 réponses au choix.
- Une erreur n'arrête rien : l'enfant réessaie, l'app lui dit à quoi correspond sa mauvaise réponse ; sur la carte, le bon endroit clignote après deux essais ratés.
- Les pays manqués se retrouvent dans **Revoir mes erreurs**. Étoiles et progrès par continent, gardés sur l'appareil.
- Le bouton 🔊 lit la question à voix haute (utile pour les plus jeunes).

## Les pays

195 pays : les 193 membres de l'ONU, plus le Vatican et le Kosovo. La Russie est rangée en Europe, la Turquie en Asie, Chypre en Europe.
Quelques capitales choisies parmi plusieurs possibles : Sucre (Bolivie), Jérusalem (Israël), Sri Jayawardenapura Kotte (Sri Lanka), Yamoussoukro (Côte d'Ivoire), Pretoria (Afrique du Sud).
Pour changer un nom ou une capitale : `source/pays.txt` (français) et `source/pays-nl.txt` (néerlandais), puis reconstruire.

## Fichiers

- `index.html`, `sw.js`, `manifest.webmanifest`, `icone-*.png`, `version.json` : l'app en ligne (GitHub Pages).
- `nl/` : l'édition néerlandaise (mêmes fichiers).
- `source/` : la version de travail.
  - `app.html` : le code de l'app (les deux éditions).
  - `pays.txt`, `pays-nl.txt` : pays, capitales, continent, Union européenne.
  - `cartes.mjs` → `cartes.json` : les cartes de chaque continent, tirées de Natural Earth (domaine public).
  - `build.py` : produit les fichiers en ligne.

## Mettre à jour

1. Changer `source/app.html` (et augmenter `VERSION` : l'app propose alors la mise à jour).
2. Si `pays.txt` ou les cartes changent : `cd source && npm install && node cartes.mjs`.
3. `python3 source/build.py` (il faut Python avec Pillow), puis publier sur GitHub.
