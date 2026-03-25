# Mario Parallaxe - Projet Programmation Multimedia

Un clone de Super Mario Bros en Python avec Pygame, mettant en avant l'effet de **parallaxe** (defilement multicouche) pour creer une illusion de profondeur.

## Installation

### Prerequis

- **Python 3.8+**
- **pip** (gestionnaire de paquets Python)

### Etapes

1. **Cloner le depot**

```bash
git clone https://github.com/<votre-username>/mario-parallaxe.git
cd mario-parallaxe
```

2. **Creer un environnement virtuel (recommande)**

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate          # Windows
```

3. **Installer les dependances**

```bash
pip install pygame
```

4. **Lancer le jeu**

```bash
python3 mario_parallax.py
```

> **Note :** Les sprites et sons sont inclus dans le dossier `assets/`. Aucun telechargement supplementaire n'est necessaire.

### Dependances

| Paquet | Version | Usage |
|--------|---------|-------|
| `pygame` | >= 2.0 | Moteur graphique et audio |

C'est la seule dependance. Python standard suffit pour le reste.

## Controles

| Touche | Action |
|--------|--------|
| `Fleche gauche` | Se deplacer a gauche |
| `Fleche droite` | Se deplacer a droite |
| `Espace` | Sauter (maintenir = sauter plus haut) |
| `F` | Lancer une boule de feu (etat Feu) |
| `Echap` | Quitter le jeu |
| `Espace` (Game Over) | Recommencer |

Le joueur peut se deplacer et sauter en meme temps.

## Mecanique de jeu

### Etats du joueur

| Etat | Apparence | Capacite |
|------|-----------|----------|
| **Petit** | Sprite NES 16x16 (casquette rouge, salopette bleue) | Saute tres haut (hauteur fixe) |
| **Grand** | Sprite NES 16x32 (double taille) | Casse les briques par en dessous. Saut depend de l'elan |
| **Feu** | Sprite blanc/rouge (pixel art code) | Lance des boules de feu avec `F`. Saut depend de l'elan |

### Systeme d'elan (Grand / Feu Mario)

Le grand et feu Mario utilisent un systeme d'elan pour le saut :
- **A l'arret** : saut court (force -400)
- **En courant** : saut beaucoup plus haut (force -500), progression lineaire selon la vitesse
- Le petit Mario saute toujours a la meme hauteur (force -520)

### Systeme d'items

- **Champignon** (sort des blocs `?`) :
  - Si petit -> devient grand
  - Si deja grand ou feu -> **stocke en reserve** (affiche dans le HUD)
  - Le champignon qui fait grandir n'est PAS comptabilise en reserve
- **Fleur de feu** (sort des blocs `?`) :
  - Donne le **pouvoir feu directement**, quel que soit l'etat actuel
- **Champignon en reserve** :
  - Quand le joueur prend un coup et redevient petit, le champignon stocke est automatiquement utilise pour le faire regrandir
  - Fonctionne comme une vie supplementaire

### Blocs

- **Bloc `?`** : frapper par en dessous fait apparaitre un item (champignon, fleur) ou rien (bloc vide). Le bloc devient gris apres utilisation.
- **Briques** : le petit Mario les fait rebondir, le grand/feu Mario les **casse** (avec animation de debris).

### Ennemis

- **Goombas** : patrouillent de gauche a droite avec sprites NES animes. Sauter dessus les ecrase. Etre touche par le cote inflige un degat.
- **Plantes Piranha** : sortent et rentrent des tuyaux verts de facon cyclique (mouvement sinusoidal). Le contact inflige un degat.

### Degats et mort

| Situation | Resultat |
|-----------|----------|
| Touche en etat **Feu** | Perd le feu, redevient Grand |
| Touche en etat **Grand** | Retrecit. Si champignon en reserve -> reste Grand |
| Touche en etat **Petit** | **Mort** (sauf si champignon en reserve) |
| Tombe dans le **vide** | **Mort directe**, Game Over |
| Boule de feu touche un ennemi | L'ennemi meurt |
| Saute **sur** un Goomba | Le Goomba est ecrase |

Apres un coup, le joueur clignote pendant 2 secondes d'invincibilite.

## Defilement parallaxe

Le jeu utilise un **fond parallaxe a 6 couches** qui defilent a des vitesses differentes pour simuler la profondeur.

| Couche | Vitesse | Description |
|--------|---------|-------------|
| Ciel degrade | `0.0` (fixe) | Degrade bleu, ne bouge jamais |
| Nuages NES | `0.1` | Sprites nuages extraits du tileset NES |
| Montagnes | `0.2` | Silhouettes de montagnes bleutees |
| Collines | `0.4` | Collines vertes arrondies |
| Buissons NES | `0.6` | Sprites buissons extraits du tileset NES |
| Sol / Niveau | `1.0` | Le terrain de jeu (sprites NES) |

### Comment ca fonctionne

La camera suit le joueur horizontalement avec un lissage. Chaque couche de fond est dessinee avec un decalage :

```
offset = -camera_x * vitesse_couche
```

- `vitesse 0` : le ciel ne bouge pas
- `vitesse 0.1` : les nuages se deplacent a 10% de la vitesse de la camera
- `vitesse 1.0` : le sol suit exactement la camera

Ce decalage progressif cree l'**illusion de profondeur** : les elements proches defilent vite, les elements lointains defilent lentement.

## Ressources graphiques et sonores

### Sprites NES (depuis spritesheets)

Les sprites suivants sont extraits de spritesheets NES via la classe `SpriteLoader` :

| Spritesheet | Contenu extrait |
|-------------|-----------------|
| `characters.gif` | Mario petit/grand (idle, run x3, jump), Goomba (walk x2, flat) |
| `tiles.png` | Sol, briques, blocs ?, tuyaux, nuages, buissons, bloc vide |
| `Items.png` | Champignon rouge |

### Sprites codes (pixel art dans le code)

Les elements suivants n'etant pas disponibles dans les spritesheets sont dessines pixel par pixel via `pygame.Surface.set_at()` :

| Element | Raison |
|---------|--------|
| Fire Mario (petit + grand) | Palette blanc/rouge non presente dans la spritesheet |
| Fleur de feu | Non disponible dans le tileset |
| Boule de feu | Non disponible |
| Plante Piranha | Non mappee dans les JSON d'origine |

### Sons

12 effets sonores authentiques Mario :

| Son | Declencheur |
|-----|-------------|
| `small_jump.ogg` | Saut du joueur |
| `stomp.ogg` | Ecraser un ennemi |
| `powerup.ogg` | Ramasser un champignon/fleur |
| `powerup_appears.ogg` | Item sort d'un bloc |
| `bump.ogg` | Frapper un bloc (petit Mario) |
| `brick-bump.ogg` | Casser une brique (grand Mario) |
| `death.wav` | Mort du joueur |
| `pipe.ogg` | Retrecir apres un coup |
| `coin.ogg` | Piece ramassee |
| `kick.ogg` | Coup de pied |
| `main_theme.ogg` | Musique de fond (boucle) |

## Structure du projet

```
mario-parallaxe/
├── mario_parallax.py      # Jeu complet (un seul fichier)
├── README.md              # Documentation
└── assets/                # Ressources
    ├── characters.gif     # Spritesheet personnages NES
    ├── tiles.png          # Spritesheet tuiles NES
    ├── Items.png          # Spritesheet items NES
    ├── main_theme.ogg     # Musique de fond
    ├── small_jump.ogg     # Son saut
    ├── stomp.ogg          # Son ecrasement
    ├── powerup.ogg        # Son power-up
    ├── powerup_appears.ogg# Son apparition item
    ├── bump.ogg           # Son bloc frappe
    ├── brick-bump.ogg     # Son brique cassee
    ├── death.wav          # Son mort
    ├── pipe.ogg           # Son retrecissement
    ├── coin.ogg           # Son piece
    └── kick.ogg           # Son coup de pied
```

### Architecture du code

| Classe | Role |
|--------|------|
| `SpriteLoader` | Charge et decoupe les spritesheets NES |
| `SoundManager` | Gere les effets sonores et la musique |
| `Player` | Joueur avec 3 etats, collisions, items, reserve |
| `Enemy` | Goomba avec patrouille et ecrasement |
| `PiranhaPlant` | Plante qui sort/rentre des tuyaux |
| `QuestionBlock` | Bloc ? avec contenu variable |
| `Brick` | Brique cassable par grand Mario |
| `Pipe` | Tuyau vert avec plante optionnelle |
| `Item` | Champignon/fleur avec emergence et deplacement |
| `Fireball` | Projectile du joueur en etat feu |
| `ParallaxBG` | Fond multicouche avec sprites NES |
| `Camera` | Suivi du joueur avec lissage |
| `Game` | Boucle principale |

### Niveau

Le niveau est defini par une grille texte (tilemap) dans `create_level()` :

```
G = Sol (herbe)       D = Terre (sous le sol)
B = Brique            ? = Bloc champignon
F = Bloc fleur        V = Bloc vide (rien dedans)
E = Ennemi Goomba     . = Vide (air)
g = Sol sous tuyau
```

Les tuyaux et plantes piranha sont definis separement par coordonnees.

## Equipe

| Membre | Nom |
|--------|-----|
| AKO | Christian |
| CERVERA | Noe |
| SIMILIEN | Carld |
| KESSAVANE | Dhanoush |

## Credits

- Sprites NES et sons : issus du projet [super-mario-python](https://github.com/mx0c/super-mario-python) (inspire de Meth-Meth-Method)
- Sprites codes (Fire Mario, fleur, piranha) : dessines dans le code
- Parallaxe et gameplay : implementation originale
