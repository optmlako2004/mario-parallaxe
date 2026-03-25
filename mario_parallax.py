"""
Mario-like Platformer avec Parallaxe - Programmation Multimedia
================================================================
Sprites NES extraits de spritesheets + sprites codes pour Fire Mario/Piranha.
Sons authentiques Mario. Parallaxe multicouche.

Controles :
  Fleches gauche/droite : se deplacer
  Espace : sauter (maintenir = plus haut)
  F : lancer boule de feu (etat feu)
  Echap : quitter
"""

import pygame
import math
import random
import os
import sys

# =============================================================================
# CONFIGURATION
# =============================================================================
SCREEN_W, SCREEN_H = 800, 600
FPS = 60
TILE = 32
GRAVITY = 900
MAX_FALL = 500
JUMP_FORCE_SMALL = -520
JUMP_FORCE_BIG_STAND = -400
JUMP_FORCE_BIG_RUN = -500
JUMP_CUT = -100

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (228, 0, 0)
MARIO_RED = (228, 0, 0)
GREEN = (50, 180, 50)
PIPE_GREEN = (0, 168, 0)
PIPE_GREEN_LIGHT = (0, 210, 0)
PIPE_GREEN_DARK = (0, 120, 0)
BLUE = (0, 0, 200)
YELLOW = (255, 200, 0)
BROWN = (160, 100, 50)
DARK_BROWN = (100, 60, 20)
ORANGE = (255, 160, 0)
SKIN = (255, 180, 120)
SHOE_BROWN = (120, 60, 0)
SKY_BLUE = (107, 140, 255)

STATE_SMALL = 0
STATE_BIG = 1
STATE_FIRE = 2

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


# =============================================================================
# CHARGEMENT SPRITES DEPUIS SPRITESHEETS
# =============================================================================
class SpriteLoader:
    """Charge et decoupe les spritesheets NES."""

    def __init__(self):
        self.characters = None
        self.tiles_sheet = None
        self.items_sheet = None
        self.loaded = False

    def load(self):
        try:
            self.characters = pygame.image.load(
                os.path.join(ASSET_DIR, "characters.gif")
            ).convert()
            self.tiles_sheet = pygame.image.load(
                os.path.join(ASSET_DIR, "tiles.png")
            ).convert()
            self.items_sheet = pygame.image.load(
                os.path.join(ASSET_DIR, "Items.png")
            ).convert()
            self.loaded = True
        except FileNotFoundError as e:
            print(f"Spritesheet manquante: {e}")
            self.loaded = False

    def extract(self, sheet, x, y, w=16, h=16, scale=2, colorkey=None):
        """Extrait un sprite de la spritesheet."""
        surf = pygame.Surface((w, h))
        surf.blit(sheet, (0, 0), (x, y, w, h))
        if colorkey == -1:
            surf.set_colorkey(surf.get_at((0, 0)))
        elif colorkey:
            surf.set_colorkey(colorkey)
        if scale != 1:
            surf = pygame.transform.scale(surf, (w * scale, h * scale))
        return surf

    def extract_tile(self, tx, ty, scale=2):
        """Extrait une tile 16x16 par index de grille."""
        return self.extract(self.tiles_sheet, tx * 16 + tx, ty * 16 + ty,
                            16, 16, scale, BLACK)

    def get_mario_sprites(self):
        """Extrait tous les sprites Mario depuis characters.gif."""
        s = self.characters
        sprites = {}

        # Petit Mario (16x16)
        small = [
            ("idle", 276, 44),
            ("run1", 290, 44),
            ("run2", 304, 44),
            ("run3", 321, 44),
            ("jump", 355, 44),
        ]
        for name, x, y in small:
            img = self.extract(s, x, y, 16, 16, 2, -1)
            sprites[f"small_R_{name}"] = img
            sprites[f"small_L_{name}"] = pygame.transform.flip(img, True, False)

        # Grand Mario (16x32)
        big = [
            ("idle", 259, 1),
            ("run1", 276, 1),
            ("run2", 296, 1),
            ("run3", 315, 1),
            ("jump", 369, 1),
        ]
        for name, x, y in big:
            img = self.extract(s, x, y, 16, 32, 2, -1)
            sprites[f"big_R_{name}"] = img
            sprites[f"big_L_{name}"] = pygame.transform.flip(img, True, False)

        return sprites

    def get_fire_mario_sprites(self):
        """Extrait les sprites Fire Mario (palette blanc/rouge) depuis characters.gif."""
        s = self.characters
        sprites = {}

        # Fire Mario petit (16x16) - meme layout que small normal mais y decale
        # Fire palette commence a y=168 pour petit (blanc+rouge)
        fire_small = [
            ("idle", 276, 168),
            ("run1", 290, 168),
            ("run2", 304, 168),
            ("run3", 321, 168),
            ("jump", 355, 168),
        ]
        for name, x, y in fire_small:
            img = self.extract(s, x, y, 16, 16, 2, -1)
            sprites[f"small_R_{name}"] = img
            sprites[f"small_L_{name}"] = pygame.transform.flip(img, True, False)

        # Fire Mario grand (16x32) - y=125
        fire_big = [
            ("idle", 259, 125),
            ("run1", 276, 125),
            ("run2", 296, 125),
            ("run3", 315, 125),
            ("jump", 369, 125),
        ]
        for name, x, y in fire_big:
            img = self.extract(s, x, y, 16, 32, 2, -1)
            sprites[f"big_R_{name}"] = img
            sprites[f"big_L_{name}"] = pygame.transform.flip(img, True, False)

        return sprites

    def get_goomba_sprites(self):
        s = self.characters
        sprites = {}
        sprites["walk1"] = self.extract(s, 296, 187, 16, 16, 2, -1)
        sprites["walk2"] = self.extract(s, 315, 187, 16, 16, 2, -1)
        sprites["flat"] = self.extract(s, 277, 187, 16, 16, 2, -1)
        return sprites

    def get_mushroom_sprite(self):
        return self.extract(self.items_sheet, 0, 16, 16, 16, 2, -1)

    def get_tile_sprites(self):
        tiles = {}
        # Sol
        tiles["ground"] = self.extract_tile(0, 0)
        # Briques
        tiles["bricks"] = self.extract_tile(1, 0)
        # Bloc vide (apres utilisation)
        tiles["empty"] = self.extract_tile(27, 0)
        # Bloc ? frames
        tiles["qblock1"] = self.extract_tile(24, 0)
        tiles["qblock2"] = self.extract_tile(25, 0)
        tiles["qblock3"] = self.extract_tile(26, 0)
        # Tuyau
        tiles["pipeL"] = self.extract_tile(0, 10)
        tiles["pipeR"] = self.extract_tile(1, 10)
        tiles["pipe2L"] = self.extract_tile(0, 11)
        tiles["pipe2R"] = self.extract_tile(1, 11)
        # Nuages
        for i, name in enumerate(["cloud1_1", "cloud1_2", "cloud1_3"]):
            tiles[name] = self.extract_tile(i, 20)
        for i, name in enumerate(["cloud2_1", "cloud2_2", "cloud2_3"]):
            tiles[name] = self.extract_tile(i, 21)
        # Buissons
        for i, name in enumerate(["bush_1", "bush_2", "bush_3"]):
            tiles[name] = self.extract_tile(11 + i, 11)
        # Ciel
        tiles["sky"] = self.extract_tile(3, 23)
        return tiles


# =============================================================================
# SPRITES CODES (Fire Mario, fleur, boule de feu, piranha)
# =============================================================================
def px(surface, x, y, color):
    if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
        surface.set_at((x, y), color)


def draw_pixels(surface, pixels, color):
    for x, y in pixels:
        px(surface, x, y, color)


def make_surface(w, h):
    s = pygame.Surface((w, h))
    s.fill((0, 255, 0))
    s.set_colorkey((0, 255, 0))
    return s


def create_fire_mario_small(facing_right=True, frame=0):
    s = make_surface(16, 16)
    hat = WHITE
    shirt = WHITE
    overall = RED
    skin = SKIN
    hair = DARK_BROWN
    draw_pixels(s, [(x, 0) for x in range(3, 8)], hat)
    draw_pixels(s, [(x, 1) for x in range(2, 12)], hat)
    draw_pixels(s, [(2, 2), (3, 2), (4, 2)], hair)
    draw_pixels(s, [(5, 2), (6, 2), (7, 2), (8, 2)], skin)
    draw_pixels(s, [(9, 2)], hair)
    draw_pixels(s, [(1, 3), (2, 3)], hair)
    draw_pixels(s, [(3, 3), (4, 3), (5, 3)], skin)
    draw_pixels(s, [(6, 3)], hair)
    draw_pixels(s, [(7, 3), (8, 3), (9, 3), (10, 3)], skin)
    px(s, 5, 3, BLACK)
    px(s, 8, 3, BLACK)
    draw_pixels(s, [(1, 4), (2, 4)], hair)
    draw_pixels(s, [(3, 4), (4, 4)], skin)
    draw_pixels(s, [(5, 4), (6, 4), (7, 4)], hair)
    draw_pixels(s, [(8, 4), (9, 4), (10, 4)], skin)
    draw_pixels(s, [(3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5)], skin)
    draw_pixels(s, [(4, 6), (5, 6), (6, 6), (8, 6)], shirt)
    draw_pixels(s, [(7, 6)], overall)
    draw_pixels(s, [(3, 7)], skin)
    draw_pixels(s, [(4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7)], shirt)
    draw_pixels(s, [(10, 7)], skin)
    draw_pixels(s, [(4, 8), (5, 8)], shirt)
    draw_pixels(s, [(6, 8), (7, 8)], overall)
    draw_pixels(s, [(8, 8), (9, 8)], shirt)
    draw_pixels(s, [(4, 9), (6, 9), (7, 9), (9, 9)], overall)
    px(s, 5, 9, YELLOW)
    px(s, 8, 9, YELLOW)
    draw_pixels(s, [(4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10)], overall)
    if frame == 0:
        draw_pixels(s, [(3, 11), (4, 11), (5, 11), (8, 11), (9, 11), (10, 11)], overall)
        draw_pixels(s, [(3, 12), (4, 12), (5, 12), (8, 12), (9, 12), (10, 12)], overall)
        draw_pixels(s, [(2, 13), (3, 13), (4, 13), (9, 13), (10, 13), (11, 13)], SHOE_BROWN)
    else:
        draw_pixels(s, [(3, 11), (4, 11), (5, 11), (9, 11), (10, 11), (11, 11)], overall)
        draw_pixels(s, [(2, 12), (3, 12), (4, 12), (10, 12), (11, 12), (12, 12)], overall)
        draw_pixels(s, [(1, 13), (2, 13), (3, 13), (10, 13), (11, 13), (12, 13)], SHOE_BROWN)
    scaled = pygame.transform.scale(s, (TILE, TILE))
    if not facing_right:
        scaled = pygame.transform.flip(scaled, True, False)
    return scaled


def create_fire_mario_big(facing_right=True, frame=0):
    s = make_surface(16, 32)
    hat = WHITE
    shirt = WHITE
    overall = RED
    skin = SKIN
    hair = DARK_BROWN
    draw_pixels(s, [(x, 1) for x in range(4, 9)], hat)
    draw_pixels(s, [(x, 2) for x in range(2, 13)], hat)
    draw_pixels(s, [(x, 3) for x in range(2, 14)], hat)
    draw_pixels(s, [(2, 4), (3, 4), (4, 4)], hair)
    draw_pixels(s, [(5, 4), (6, 4), (7, 4), (8, 4), (9, 4)], skin)
    draw_pixels(s, [(10, 4)], hair)
    draw_pixels(s, [(1, 5), (2, 5)], hair)
    draw_pixels(s, [(3, 5), (4, 5), (5, 5), (6, 5)], skin)
    draw_pixels(s, [(7, 5)], hair)
    draw_pixels(s, [(8, 5), (9, 5), (10, 5), (11, 5)], skin)
    px(s, 5, 5, BLACK)
    px(s, 5, 6, BLACK)
    px(s, 9, 5, BLACK)
    px(s, 9, 6, BLACK)
    draw_pixels(s, [(1, 6), (2, 6)], hair)
    draw_pixels(s, [(3, 6), (4, 6)], skin)
    draw_pixels(s, [(5, 6), (6, 6), (7, 6), (8, 6)], hair)
    draw_pixels(s, [(9, 6), (10, 6), (11, 6)], skin)
    draw_pixels(s, [(x, 7) for x in range(3, 12)], skin)
    draw_pixels(s, [(6, 8), (7, 8), (8, 8), (9, 8)], hair)
    draw_pixels(s, [(x, 9) for x in range(4, 11)], skin)
    for yy in range(10, 14):
        draw_pixels(s, [(x, yy) for x in range(3, 11)], shirt)
    draw_pixels(s, [(1, 11), (2, 11), (1, 12), (2, 12)], skin)
    draw_pixels(s, [(11, 11), (12, 11), (11, 12), (12, 12)], skin)
    for yy in range(14, 22):
        draw_pixels(s, [(x, yy) for x in range(3, 11)], overall)
    px(s, 5, 15, YELLOW)
    px(s, 8, 15, YELLOW)
    px(s, 5, 16, YELLOW)
    px(s, 8, 16, YELLOW)
    for yy in range(14, 17):
        px(s, 4, yy, shirt)
        px(s, 9, yy, shirt)
    if frame == 0:
        for yy in range(22, 27):
            draw_pixels(s, [(3, yy), (4, yy), (5, yy)], overall)
            draw_pixels(s, [(8, yy), (9, yy), (10, yy)], overall)
        draw_pixels(s, [(2, 27), (3, 27), (4, 27), (5, 27)], SHOE_BROWN)
        draw_pixels(s, [(8, 27), (9, 27), (10, 27), (11, 27)], SHOE_BROWN)
        draw_pixels(s, [(2, 28), (3, 28), (4, 28), (5, 28)], SHOE_BROWN)
        draw_pixels(s, [(8, 28), (9, 28), (10, 28), (11, 28)], SHOE_BROWN)
    else:
        for yy in range(22, 26):
            draw_pixels(s, [(2, yy), (3, yy), (4, yy)], overall)
            draw_pixels(s, [(9, yy), (10, yy), (11, yy)], overall)
        draw_pixels(s, [(1, 27), (2, 27), (3, 27), (4, 27)], SHOE_BROWN)
        draw_pixels(s, [(9, 27), (10, 27), (11, 27), (12, 27)], SHOE_BROWN)
        draw_pixels(s, [(1, 28), (2, 28), (3, 28), (4, 28)], SHOE_BROWN)
        draw_pixels(s, [(9, 28), (10, 28), (11, 28), (12, 28)], SHOE_BROWN)
    scaled = pygame.transform.scale(s, (TILE, TILE * 2))
    if not facing_right:
        scaled = pygame.transform.flip(scaled, True, False)
    return scaled


def create_flower():
    s = make_surface(16, 16)
    draw_pixels(s, [(7, y) for y in range(8, 15)], GREEN)
    draw_pixels(s, [(8, y) for y in range(8, 15)], GREEN)
    draw_pixels(s, [(5, 10), (6, 10), (9, 11), (10, 11)], GREEN)
    for angle in range(0, 360, 45):
        px_x = 7 + int(4 * math.cos(math.radians(angle)))
        px_y = 4 + int(4 * math.sin(math.radians(angle)))
        draw_pixels(s, [(px_x, px_y), (px_x + 1, px_y), (px_x, px_y + 1)], ORANGE)
    for angle in range(22, 360, 45):
        px_x = 7 + int(3 * math.cos(math.radians(angle)))
        px_y = 4 + int(3 * math.sin(math.radians(angle)))
        px(s, px_x, px_y, RED)
    draw_pixels(s, [(7, 3), (8, 3), (7, 4), (8, 4)], YELLOW)
    return pygame.transform.scale(s, (TILE - 4, TILE - 4))


def create_fireball():
    s = make_surface(10, 10)
    pygame.draw.circle(s, ORANGE, (5, 5), 5)
    pygame.draw.circle(s, YELLOW, (5, 5), 3)
    pygame.draw.circle(s, WHITE, (4, 3), 1)
    return s


def create_piranha_plant(open_mouth=True):
    s = make_surface(16, 24)
    draw_pixels(s, [(x, y) for x in range(6, 10) for y in range(10, 24)], GREEN)
    draw_pixels(s, [(x, y) for x in range(5, 11) for y in range(10, 12)], GREEN)
    head_color = (200, 30, 30)
    dark_head = (150, 10, 10)
    draw_pixels(s, [(x, y) for x in range(2, 14) for y in range(0, 10)], head_color)
    draw_pixels(s, [(x, y) for x in range(3, 13) for y in range(1, 4)], dark_head)
    draw_pixels(s, [(4, 2), (5, 2), (4, 3), (5, 3)], WHITE)
    draw_pixels(s, [(10, 2), (11, 2), (10, 3), (11, 3)], WHITE)
    if open_mouth:
        draw_pixels(s, [(x, 5) for x in range(3, 13)], BLACK)
        for xx in [4, 6, 8, 10]:
            px(s, xx, 4, WHITE)
            px(s, xx, 6, WHITE)
    else:
        draw_pixels(s, [(x, 6) for x in range(3, 13)], dark_head)
    px(s, 5, 1, WHITE)
    px(s, 10, 1, WHITE)
    px(s, 5, 2, BLACK)
    px(s, 10, 2, BLACK)
    return pygame.transform.scale(s, (TILE, int(TILE * 1.5)))


# =============================================================================
# SON
# =============================================================================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False

    def load(self):
        sound_files = {
            "jump": "small_jump.ogg",
            "stomp": "stomp.ogg",
            "coin": "coin.ogg",
            "powerup": "powerup.ogg",
            "powerup_appears": "powerup_appears.ogg",
            "death": "death.wav",
            "bump": "bump.ogg",
            "brick_bump": "brick-bump.ogg",
            "kick": "kick.ogg",
            "pipe": "pipe.ogg",
        }
        for name, filename in sound_files.items():
            path = os.path.join(ASSET_DIR, filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(0.3)

        # Musique de fond
        music_path = os.path.join(ASSET_DIR, "main_theme.ogg")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.2)
                pygame.mixer.music.play(-1)
                self.music_playing = True
            except Exception:
                pass

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def stop_music(self):
        if self.music_playing:
            pygame.mixer.music.stop()


# =============================================================================
# CLASSES DU JEU
# =============================================================================

class Camera:
    def __init__(self):
        self.x = 0.0

    def update(self, target_x, level_width, dt):
        target_cx = target_x - SCREEN_W // 3
        self.x += (target_cx - self.x) * 8 * dt
        self.x = max(0, min(self.x, level_width - SCREEN_W))


class BrickDebris:
    def __init__(self, x, y):
        self.particles = []
        for dx, dy in [(-2, -6), (2, -6), (-3, -3), (3, -3)]:
            self.particles.append([x + dx * 4, y, dx * 40, dy * 60])
        self.timer = 0.6
        self.image = None

    def set_image(self, tile_sprites):
        if tile_sprites and "bricks" in tile_sprites:
            self.image = pygame.transform.scale(tile_sprites["bricks"], (8, 8))

    def update(self, dt):
        self.timer -= dt
        for p in self.particles:
            p[3] += GRAVITY * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
        return self.timer > 0

    def draw(self, screen, cam_x):
        for p in self.particles:
            sx, sy = int(p[0] - cam_x), int(p[1])
            if self.image:
                screen.blit(self.image, (sx, sy))
            else:
                pygame.draw.rect(screen, BROWN, (sx, sy, 8, 8))


class Fireball:
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.vx = 350 * direction
        self.vy = -80
        self.alive = True
        self.image = create_fireball()
        self.rect = pygame.Rect(x - 5, y - 5, 10, 10)
        self.bounces = 0

    def update(self, dt, solids):
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.y = s.top - 5
                    self.vy = -200
                    self.bounces += 1
                    if self.bounces > 3:
                        self.alive = False
                    break
        if self.y > SCREEN_H + 50 or self.x < -50 or self.x > 10000:
            self.alive = False

    def draw(self, screen, cam_x):
        screen.blit(self.image, (int(self.x - cam_x) - 5, int(self.y) - 5))


class Item:
    def __init__(self, x, y, item_type, image):
        self.x, self.y = x, y
        self.target_y = y - TILE
        self.item_type = item_type
        self.vx = 60 if item_type == "mushroom" else 0
        self.vy = 0
        self.alive = True
        self.emerging = True
        self.image = image
        self.w, self.h = self.image.get_size()

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt, solids):
        if self.emerging:
            self.y -= 80 * dt
            if self.y <= self.target_y:
                self.y = self.target_y
                self.emerging = False
            return
        if self.item_type == "mushroom":
            self.vy += GRAVITY * dt
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL
            self.x += self.vx * dt
            self.y += self.vy * dt
            r = self.rect
            for s in solids:
                if r.colliderect(s):
                    if self.vy > 0 and r.bottom > s.top and r.top < s.top:
                        self.y = s.top - self.h
                        self.vy = 0
                    if self.vx > 0 and r.right > s.left and r.left < s.left:
                        self.vx = -self.vx
                    elif self.vx < 0 and r.left < s.right and r.right > s.right:
                        self.vx = -self.vx
        if self.y > SCREEN_H + 100:
            self.alive = False

    def draw(self, screen, cam_x):
        if self.alive:
            screen.blit(self.image, (int(self.x - cam_x), int(self.y)))


class PiranhaPlant:
    def __init__(self, x, y_pipe_top):
        self.x = x
        self.base_y = y_pipe_top
        self.y = self.base_y
        self.max_rise = TILE * 1.5
        self.phase = 0.0
        self.speed = 1.2
        self.frames = [create_piranha_plant(True), create_piranha_plant(False)]
        self.w = TILE
        self.h = int(TILE * 1.5)

    @property
    def rect(self):
        visible_h = max(0, self.base_y - self.y)
        if visible_h < 5:
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(int(self.x), int(self.y), self.w, int(visible_h))

    def update(self, dt):
        self.phase += self.speed * dt
        cycle = math.sin(self.phase)
        self.y = self.base_y - (cycle * self.max_rise if cycle > 0 else 0)

    def draw(self, screen, cam_x):
        visible_h = self.base_y - self.y
        if visible_h < 3:
            return
        fidx = 0 if math.sin(self.phase * 3) > 0 else 1
        img = self.frames[fidx]
        sx = int(self.x - cam_x)
        clip_rect = pygame.Rect(0, int(self.h - visible_h), self.w, int(visible_h))
        clipped = img.subsurface(clip_rect)
        screen.blit(clipped, (sx, int(self.y)))


class Enemy:
    def __init__(self, x, y, goomba_sprites=None):
        self.x, self.y = x, y
        self.vx, self.vy = -60, 0
        self.alive = True
        self.squished = False
        self.squish_timer = 0
        self.goomba_sprites = goomba_sprites
        self.anim_timer = 0
        self.anim_idx = 0
        self.w, self.h = TILE, TILE

    @property
    def rect(self):
        if self.squished:
            return pygame.Rect(int(self.x), int(self.y) + self.h - TILE // 4, self.w, TILE // 4)
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt, solids):
        if self.squished:
            self.squish_timer -= dt
            if self.squish_timer <= 0:
                self.alive = False
            return
        self.vy += GRAVITY * dt
        if self.vy > MAX_FALL:
            self.vy = MAX_FALL
        self.x += self.vx * dt
        self.y += self.vy * dt
        r = self.rect
        for s in solids:
            if r.colliderect(s):
                if self.vy > 0 and r.bottom > s.top and r.top < s.top:
                    self.y = s.top - self.h
                    self.vy = 0
                elif self.vx > 0 and r.right > s.left and r.left < s.left:
                    self.vx = -abs(self.vx)
                elif self.vx < 0 and r.left < s.right and r.right > s.right:
                    self.vx = abs(self.vx)
        self.anim_timer += dt
        if self.anim_timer > 0.25:
            self.anim_timer = 0
            self.anim_idx = (self.anim_idx + 1) % 2
        if self.y > SCREEN_H + 100:
            self.alive = False

    def stomp(self):
        self.squished = True
        self.squish_timer = 0.4
        self.vx = 0

    def draw(self, screen, cam_x):
        sx = int(self.x - cam_x)
        gs = self.goomba_sprites
        if gs:
            if self.squished:
                screen.blit(gs["flat"], (sx, int(self.y) + self.h - TILE))
            else:
                key = "walk1" if self.anim_idx == 0 else "walk2"
                screen.blit(gs[key], (sx, int(self.y)))
        else:
            color = BROWN if not self.squished else DARK_BROWN
            pygame.draw.rect(screen, color, (sx, int(self.y), TILE, TILE))


class QuestionBlock:
    def __init__(self, x, y, content="mushroom", tile_sprites=None):
        self.x, self.y = x, y
        self.content = content
        self.used = False
        self.bump_offset = 0
        self.bump_vel = 0
        self.frame = 0
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.tile_sprites = tile_sprites

    def hit(self, mushroom_img, flower_img, sound_mgr):
        if self.used:
            return None
        self.used = True
        self.bump_vel = -200
        if self.content == "empty":
            if sound_mgr:
                sound_mgr.play("bump")
            return None
        if sound_mgr:
            sound_mgr.play("powerup_appears")
        img = mushroom_img if self.content == "mushroom" else flower_img
        return Item(self.x + 4, self.y, self.content, img)

    def update(self, dt):
        self.frame += 1
        if self.bump_vel != 0:
            self.bump_offset += self.bump_vel * dt
            self.bump_vel += 600 * dt
            if self.bump_offset >= 0:
                self.bump_offset = 0
                self.bump_vel = 0
        self.rect.y = int(self.y + self.bump_offset)

    def draw(self, screen, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y + self.bump_offset)
        ts = self.tile_sprites
        if ts:
            if self.used:
                screen.blit(ts["empty"], (sx, sy))
            else:
                idx = (self.frame // 10) % 3
                keys = ["qblock1", "qblock2", "qblock3"]
                screen.blit(ts[keys[idx]], (sx, sy))
        else:
            color = (90, 70, 40) if self.used else (200, 150, 0)
            pygame.draw.rect(screen, color, (sx, sy, TILE, TILE))


class Brick:
    def __init__(self, x, y, tile_sprites=None):
        self.x, self.y = x, y
        self.alive = True
        self.bump_offset = 0
        self.bump_vel = 0
        self.tile_sprites = tile_sprites
        self.rect = pygame.Rect(x, y, TILE, TILE)

    def hit(self, player_is_big, sound_mgr):
        if player_is_big:
            self.alive = False
            if sound_mgr:
                sound_mgr.play("brick_bump")
            return True
        else:
            self.bump_vel = -150
            if sound_mgr:
                sound_mgr.play("bump")
            return False

    def update(self, dt):
        if self.bump_vel != 0:
            self.bump_offset += self.bump_vel * dt
            self.bump_vel += 600 * dt
            if self.bump_offset >= 0:
                self.bump_offset = 0
                self.bump_vel = 0
        self.rect.y = int(self.y + self.bump_offset)

    def draw(self, screen, cam_x):
        if not self.alive:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y + self.bump_offset)
        if self.tile_sprites and "bricks" in self.tile_sprites:
            screen.blit(self.tile_sprites["bricks"], (sx, sy))
        else:
            pygame.draw.rect(screen, BROWN, (sx, sy, TILE, TILE))


class Pipe:
    def __init__(self, x, y, height_tiles=2, has_piranha=False, tile_sprites=None):
        self.x, self.y = x, y
        self.w = TILE * 2
        self.h = height_tiles * TILE
        self.rects = [pygame.Rect(x, y, TILE * 2, height_tiles * TILE)]
        self.tile_sprites = tile_sprites
        self.height_tiles = height_tiles
        self.piranha = None
        if has_piranha:
            self.piranha = PiranhaPlant(x + TILE // 2, y)

    def update(self, dt):
        if self.piranha:
            self.piranha.update(dt)

    def draw(self, screen, cam_x):
        sx = int(self.x - cam_x)
        if self.piranha:
            self.piranha.draw(screen, cam_x)
        ts = self.tile_sprites
        if ts and "pipeL" in ts:
            screen.blit(ts["pipeL"], (sx, self.y))
            screen.blit(ts["pipeR"], (sx + TILE, self.y))
            for i in range(1, self.height_tiles):
                screen.blit(ts["pipe2L"], (sx, self.y + i * TILE))
                screen.blit(ts["pipe2R"], (sx + TILE, self.y + i * TILE))
        else:
            pygame.draw.rect(screen, PIPE_GREEN, (sx, self.y, TILE * 2, TILE))
            pygame.draw.rect(screen, PIPE_GREEN_LIGHT, (sx + 4, self.y, 12, TILE))
            for i in range(1, self.height_tiles):
                pygame.draw.rect(screen, PIPE_GREEN, (sx + 4, self.y + i * TILE, TILE * 2 - 8, TILE))


class Player:
    def __init__(self, x, y, mario_sprites, fire_sprites, sound_mgr):
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = False
        self.facing_right = True
        self.state = STATE_SMALL
        self.alive = True
        self.walk_frame = 0
        self.frame_timer = 0.0
        self.invincible = 0.0
        self.speed = 200
        self.jumping = False
        self.stored_mushroom = 0
        self.mario_sprites = mario_sprites
        self.fire_sprites = fire_sprites
        self.sound = sound_mgr

    @property
    def width(self):
        return TILE

    @property
    def height(self):
        return TILE if self.state == STATE_SMALL else TILE * 2

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_sprite(self):
        d = "R" if self.facing_right else "L"
        frames = ["idle", "run1", "run2", "run3"]
        f_name = frames[int(self.walk_frame) % 4] if self.on_ground else "jump"

        if self.state == STATE_FIRE:
            fs = self.fire_sprites
            sz = "big"
            key = f"{sz}_{d}_{f_name}"
            if key in fs:
                return fs[key]
            return fs.get(f"{sz}_{d}_idle", list(fs.values())[0])

        ms = self.mario_sprites
        sz = "big" if self.state >= STATE_BIG else "small"
        key = f"{sz}_{d}_{f_name}"
        if key in ms:
            return ms[key]
        return ms.get(f"{sz}_{d}_idle", list(ms.values())[0])

    def update(self, dt, keys, solids, q_blocks, bricks, enemies, items,
               fireballs, piranhas, debris_list, mushroom_img, flower_img):
        if not self.alive:
            return

        if self.invincible > 0:
            self.invincible -= dt

        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing_right = True
        else:
            self.vx *= 0.8
            if abs(self.vx) < 5:
                self.vx = 0

        if keys[pygame.K_SPACE]:
            if self.on_ground and not self.jumping:
                if self.state == STATE_SMALL:
                    self.vy = JUMP_FORCE_SMALL
                else:
                    speed_ratio = min(abs(self.vx) / self.speed, 1.0)
                    self.vy = JUMP_FORCE_BIG_STAND + (JUMP_FORCE_BIG_RUN - JUMP_FORCE_BIG_STAND) * speed_ratio
                self.on_ground = False
                self.jumping = True
                if self.sound:
                    self.sound.play("jump")
        else:
            self.jumping = False
            if self.vy < JUMP_CUT:
                self.vy = JUMP_CUT

        # Gravite seulement si pas au sol (evite la vibration)
        if not self.on_ground:
            self.vy += GRAVITY * dt
            if self.vy > MAX_FALL:
                self.vy = MAX_FALL
        else:
            # Petite force vers le bas pour coller au sol
            self.vy = 1

        brick_rects = [b.rect for b in bricks if b.alive]
        qb_rects = [qb.rect for qb in q_blocks]
        all_solids = solids + brick_rects + qb_rects

        self.x += self.vx * dt
        r = self.rect
        for s in all_solids:
            if r.colliderect(s):
                if self.vx > 0:
                    r.right = s.left
                elif self.vx < 0:
                    r.left = s.right
                self.x = r.x
                self.vx = 0

        self.y += self.vy * dt
        r = self.rect
        self.on_ground = False

        for s in solids:
            if r.colliderect(s):
                if self.vy > 0 and r.bottom > s.top:
                    r.bottom = s.top
                    self.y = r.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and r.top < s.bottom:
                    r.top = s.bottom
                    self.y = r.y
                    self.vy = 0

        r = self.rect
        for qb in q_blocks:
            if r.colliderect(qb.rect):
                if self.vy > 0 and r.bottom > qb.rect.top and (r.bottom - qb.rect.top) < 20:
                    r.bottom = qb.rect.top
                    self.y = r.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and r.top < qb.rect.bottom:
                    r.top = qb.rect.bottom
                    self.y = r.y
                    self.vy = 0
                    item = qb.hit(mushroom_img, flower_img, self.sound)
                    if item:
                        items.append(item)

        r = self.rect
        for brick in bricks:
            if not brick.alive:
                continue
            if r.colliderect(brick.rect):
                if self.vy > 0 and r.bottom > brick.rect.top and (r.bottom - brick.rect.top) < 20:
                    r.bottom = brick.rect.top
                    self.y = r.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and r.top < brick.rect.bottom:
                    r.top = brick.rect.bottom
                    self.y = r.y
                    self.vy = 0
                    broken = brick.hit(self.state >= STATE_BIG, self.sound)
                    if broken:
                        d = BrickDebris(brick.x + TILE // 2, brick.y)
                        debris_list.append(d)

        if abs(self.vx) > 10 and self.on_ground:
            self.frame_timer += dt
            if self.frame_timer > 0.1:
                self.frame_timer = 0
                self.walk_frame += 1
        elif self.on_ground:
            self.walk_frame = 0

        r = self.rect
        for e in enemies:
            if not e.alive or e.squished:
                continue
            er = e.rect
            if r.colliderect(er):
                if self.vy > 0 and r.bottom - er.top < er.height * 0.5:
                    e.stomp()
                    self.vy = -280
                    self.y = er.top - self.height
                    if self.sound:
                        self.sound.play("stomp")
                else:
                    self.take_hit()

        r = self.rect
        for p in piranhas:
            if p and r.colliderect(p.rect):
                self.take_hit()

        r = self.rect
        for item in items:
            if not item.alive or item.emerging:
                continue
            if r.colliderect(item.rect):
                item.alive = False
                if self.sound:
                    self.sound.play("powerup")
                if item.item_type == "mushroom":
                    if self.state == STATE_SMALL:
                        self.grow(STATE_BIG)
                    else:
                        self.stored_mushroom += 1
                elif item.item_type == "flower":
                    if self.state == STATE_SMALL:
                        self.grow(STATE_BIG)
                    self.grow(STATE_FIRE)

        if self.y > SCREEN_H + 50:
            self.alive = False
            if self.sound:
                self.sound.play("death")
                self.sound.stop_music()

    def take_hit(self):
        if self.invincible > 0:
            return
        if self.sound:
            self.sound.play("pipe")
        if self.state == STATE_FIRE:
            self.state = STATE_BIG
            self.invincible = 2.0
        elif self.state == STATE_BIG:
            self.shrink()
            self.invincible = 2.0
            if self.stored_mushroom > 0:
                self.stored_mushroom -= 1
                self.grow(STATE_BIG)
        else:
            if self.stored_mushroom > 0:
                self.stored_mushroom -= 1
                self.grow(STATE_BIG)
                self.invincible = 2.0
            else:
                self.alive = False
                if self.sound:
                    self.sound.play("death")
                    self.sound.stop_music()

    def grow(self, new_state):
        old_h = self.height
        self.state = new_state
        self.y -= (self.height - old_h)

    def shrink(self):
        old_h = self.height
        self.state = STATE_SMALL
        self.y += (old_h - self.height)

    def shoot(self, fireballs):
        if self.state == STATE_FIRE:
            d = 1 if self.facing_right else -1
            fireballs.append(Fireball(self.x + (self.width if d > 0 else -5),
                                      self.y + self.height // 2, d))

    def draw(self, screen, cam_x):
        if not self.alive:
            return
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return
        screen.blit(self.get_sprite(), (int(self.x - cam_x), int(self.y)))


# =============================================================================
# PARALLAXE
# =============================================================================
class ParallaxBG:
    def __init__(self, level_w, tile_sprites=None):
        self.level_w = level_w
        self.tile_sprites = tile_sprites
        self._generate()

    def _generate(self):
        self.sky = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(107 * (1 - t) + 50 * t)
            g = int(145 * (1 - t) + 80 * t)
            b = int(255 * (1 - t) + 140 * t)
            pygame.draw.line(self.sky, (r, g, b), (0, y), (SCREEN_W, y))
        rng = random.Random(42)
        total_w = self.level_w + SCREEN_W
        self.clouds = [(rng.randint(0, total_w), rng.randint(30, 120),
                        rng.randint(70, 150), rng.randint(25, 50)) for _ in range(18)]
        rng2 = random.Random(77)
        self.mountains = [(i * 120, SCREEN_H - 140 - rng2.randint(40, 140), 120)
                          for i in range(total_w // 120 + 2)]
        rng3 = random.Random(33)
        self.hills = [(i * 90, rng3.randint(40, 90)) for i in range(total_w // 90 + 2)]
        rng4 = random.Random(55)
        self.bushes = [(rng4.randint(0, total_w), rng4.randint(0, 1)) for _ in range(25)]

    def draw(self, screen, cam_x):
        screen.blit(self.sky, (0, 0))
        ts = self.tile_sprites

        # Nuages NES (speed 0.1)
        for cx, cy, cw, ch in self.clouds:
            sx = (cx - cam_x * 0.1) % (self.level_w + SCREEN_W) - SCREEN_W // 2
            if ts and "cloud1_1" in ts:
                screen.blit(ts["cloud1_1"], (int(sx), cy))
                screen.blit(ts["cloud1_2"], (int(sx) + TILE, cy))
                screen.blit(ts["cloud1_3"], (int(sx) + TILE * 2, cy))
            else:
                pygame.draw.ellipse(screen, (235, 240, 255), (int(sx), cy, cw, ch))

        # Montagnes (speed 0.2)
        for mx, my, mw in self.mountains:
            sx = mx - cam_x * 0.2
            if sx + mw < -50 or sx > SCREEN_W + 50:
                continue
            pts = [(int(sx), SCREEN_H - 60), (int(sx + mw // 2), int(my)), (int(sx + mw), SCREEN_H - 60)]
            pygame.draw.polygon(screen, (80, 100, 140), pts)

        # Collines (speed 0.4)
        for hx, hh in self.hills:
            sx = hx - cam_x * 0.4
            if sx + 90 < -20 or sx > SCREEN_W + 20:
                continue
            pygame.draw.ellipse(screen, (50, 150, 50), (int(sx), SCREEN_H - 60 - hh, 90, hh * 2))

        # Buissons NES (speed 0.6)
        for bx, btype in self.bushes:
            sx = bx - cam_x * 0.6
            if sx < -TILE * 3 or sx > SCREEN_W + TILE:
                continue
            by = SCREEN_H - 60 - TILE
            if ts and "bush_1" in ts:
                screen.blit(ts["bush_1"], (int(sx), by))
                screen.blit(ts["bush_2"], (int(sx) + TILE, by))
                screen.blit(ts["bush_3"], (int(sx) + TILE * 2, by))
            else:
                pygame.draw.ellipse(screen, (30, 120, 30), (int(sx), by, 80, 30))


# =============================================================================
# NIVEAU
# =============================================================================
def create_level(tile_sprites, goomba_sprites):
    level_map = [
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        "...........................................................................................",
        ".............B?BVF?B....................B?B.........?..............B?B?B....................",
        "...........................................................................................",
        "..........E.............E......E...........E........E..........E.....E..........E..........",
        "...........................................................................................",
        "GGGGGGGGGGGGGGGGGGGGGGGGGGGG......GGGGGGGGGGGGGGggGGGGGGGGGGGGGGGGGGGG....GGGGGGGGGGGGGGG",
        "DDDDDDDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDddDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDD",
        "DDDDDDDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDddDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDD",
        "DDDDDDDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDddDDDDDDDDDDDDDDDDDDDDDD....DDDDDDDDDDDDDDD",
    ]

    solids = []
    q_blocks = []
    bricks = []
    enemies = []
    pipes = []
    tiles_render = []

    ts = tile_sprites
    ground_img = ts["ground"] if ts and "ground" in ts else None
    dirt_img = ts.get("empty") if ts else None
    sky_img = ts.get("sky") if ts else None

    for row_i, row in enumerate(level_map):
        for col_i, cell in enumerate(row):
            x, y = col_i * TILE, row_i * TILE
            if cell == 'G':
                solids.append(pygame.Rect(x, y, TILE, TILE))
                if ground_img:
                    tiles_render.append((ground_img, x, y))
            elif cell == 'D' or cell == 'd':
                solids.append(pygame.Rect(x, y, TILE, TILE))
                if dirt_img:
                    tiles_render.append((dirt_img, x, y))
            elif cell == 'g':
                solids.append(pygame.Rect(x, y, TILE, TILE))
                if ground_img:
                    tiles_render.append((ground_img, x, y))
            elif cell == 'B':
                bricks.append(Brick(x, y, ts))
            elif cell == '?':
                q_blocks.append(QuestionBlock(x, y, "mushroom", ts))
            elif cell == 'F':
                q_blocks.append(QuestionBlock(x, y, "flower", ts))
            elif cell == 'V':
                q_blocks.append(QuestionBlock(x, y, "empty", ts))
            elif cell == 'E':
                enemies.append(Enemy(x, row_i * TILE - TILE, goomba_sprites))

    ground_row = 15
    pipe_defs = [(20, 2, False), (42, 3, True), (60, 2, True)]
    for col, h_tiles, has_piranha in pipe_defs:
        px_x = col * TILE
        px_y = (ground_row - h_tiles) * TILE
        pipes.append(Pipe(px_x, px_y, h_tiles, has_piranha, ts))

    spawn_x = 3 * TILE
    spawn_y = 14 * TILE
    level_w = len(level_map[0]) * TILE
    return solids, q_blocks, bricks, enemies, pipes, tiles_render, spawn_x, spawn_y, level_w


# =============================================================================
# JEU PRINCIPAL
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Mario Parallaxe - Prog Multimedia")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 16, bold=True)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)
        self.running = True
        self.game_over = False

        # Charger sprites
        self.loader = SpriteLoader()
        self.loader.load()

        self.tile_sprites = self.loader.get_tile_sprites() if self.loader.loaded else None
        self.mario_sprites = self.loader.get_mario_sprites() if self.loader.loaded else {}
        self.goomba_sprites = self.loader.get_goomba_sprites() if self.loader.loaded else None

        # Sprites Fire Mario - NES si disponible, sinon codes
        if self.loader.loaded:
            self.fire_sprites = self.loader.get_fire_mario_sprites()
        else:
            self.fire_sprites = {}
            for right in [True, False]:
                d = "R" if right else "L"
                for f, name in enumerate(["idle", "run1", "run2", "run3"]):
                    self.fire_sprites[f"big_{d}_{name}"] = create_fire_mario_big(right, f % 2)
                    self.fire_sprites[f"small_{d}_{name}"] = create_fire_mario_small(right, f % 2)
                self.fire_sprites[f"big_{d}_jump"] = create_fire_mario_big(right, 0)
                self.fire_sprites[f"small_{d}_jump"] = create_fire_mario_small(right, 0)

        # Images items
        if self.loader.loaded:
            self.mushroom_img = self.loader.get_mushroom_sprite()
        else:
            self.mushroom_img = pygame.Surface((TILE, TILE))
            self.mushroom_img.fill(RED)
        self.flower_img = create_flower()

        # Sons
        self.sound = SoundManager()
        self.sound.load()

        # Niveau
        (self.solids, self.q_blocks, self.bricks, self.enemies,
         self.pipes, self.tiles, spawn_x, spawn_y, self.level_w) = \
            create_level(self.tile_sprites, self.goomba_sprites)

        self.player = Player(spawn_x, spawn_y, self.mario_sprites,
                             self.fire_sprites, self.sound)
        self.camera = Camera()
        self.parallax = ParallaxBG(self.level_w, self.tile_sprites)
        self.items = []
        self.fireballs = []
        self.debris = []

    def restart(self):
        self.__init__()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and self.game_over:
                    self.restart()
                elif event.key == pygame.K_f:
                    self.player.shoot(self.fireballs)

    def update(self):
        if self.game_over:
            return
        dt = min(self.clock.get_time() / 1000.0, 0.05)
        keys = pygame.key.get_pressed()

        pipe_solids = []
        piranhas = []
        for pipe in self.pipes:
            pipe_solids.extend(pipe.rects)
            if pipe.piranha:
                piranhas.append(pipe.piranha)

        all_solids = self.solids + pipe_solids

        self.player.update(dt, keys, all_solids, self.q_blocks, self.bricks,
                           self.enemies, self.items, self.fireballs,
                           piranhas, self.debris, self.mushroom_img, self.flower_img)

        if not self.player.alive:
            self.game_over = True
            return

        for qb in self.q_blocks:
            qb.update(dt)
        for b in self.bricks:
            if b.alive:
                b.update(dt)
        for e in self.enemies:
            if e.alive:
                e.update(dt, all_solids)
        for pipe in self.pipes:
            pipe.update(dt)
        for item in self.items:
            if item.alive:
                item.update(dt, all_solids)
        self.items = [i for i in self.items if i.alive]

        for fb in self.fireballs:
            if fb.alive:
                fb.update(dt, all_solids)
                for e in self.enemies:
                    if e.alive and not e.squished and fb.rect.colliderect(e.rect):
                        e.alive = False
                        fb.alive = False
        self.fireballs = [f for f in self.fireballs if f.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.debris = [d for d in self.debris if d.update(dt)]
        self.camera.update(self.player.x, self.level_w, dt)

    def draw(self):
        cam_x = self.camera.x
        self.parallax.draw(self.screen, cam_x)

        for img, tx, ty in self.tiles:
            sx = tx - cam_x
            if -TILE < sx < SCREEN_W + TILE:
                self.screen.blit(img, (int(sx), ty))

        for pipe in self.pipes:
            if -TILE * 2 < pipe.x - cam_x < SCREEN_W + TILE * 2:
                pipe.draw(self.screen, cam_x)

        for b in self.bricks:
            if b.alive:
                b.draw(self.screen, cam_x)
        for qb in self.q_blocks:
            qb.draw(self.screen, cam_x)
        for d in self.debris:
            d.draw(self.screen, cam_x)
        for item in self.items:
            item.draw(self.screen, cam_x)
        for e in self.enemies:
            e.draw(self.screen, cam_x)
        for fb in self.fireballs:
            fb.draw(self.screen, cam_x)

        self.player.draw(self.screen, cam_x)

        # HUD
        states = {STATE_SMALL: "Petit", STATE_BIG: "Grand", STATE_FIRE: "Feu"}
        reserve = f"  Reserve: {self.player.stored_mushroom}" if self.player.stored_mushroom > 0 else ""
        hud = f"Mario: {states[self.player.state]}{reserve}  |  Fleches  Espace  F:feu"
        self.screen.blit(self.font.render(hud, True, WHITE), (10, 8))

        parallax_info = "Parallaxe: Ciel(0)  Nuages(0.1)  Montagnes(0.2)  Collines(0.4)  Buissons(0.6)  Sol(1.0)"
        self.screen.blit(self.font.render(parallax_info, True, (200, 200, 200)), (10, SCREEN_H - 22))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            go = self.big_font.render("GAME OVER", True, RED)
            self.screen.blit(go, go.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 25)))
            sub = self.font.render("Appuie sur ESPACE pour recommencer", True, WHITE)
            self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 25)))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
    print("Jeu termine.")
