import array
import colorsys
import math
import os

import pygame

from game.hanoi_game import HanoiGame

ASSETS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))

# Sprites de disco, de menor a mayor. El arte original mide 1024x1024 con
# relleno transparente; cada píxel "real" ocupa 16x16, así que se reduce a su
# rejilla nativa antes de recolorear y escalar (pixel art nítido).
DISK_ASSETS = (
    "Pequeño pequeño disco naranja.png",
    "Pequeño disco naranja .png",
    "Pequeño mediano disco naranja .png",
    "Mediano disco naranja .png",
    "Grande mediano disco naranja.png",
    "Grande disco naranja.png",
    "Muy grande disco naranja.png",
    "Enorme disco naranja.png",
)
DISK_ASSET_PIXEL = 16


def load_image(name):
    path = os.path.join(ASSETS_DIR, name)
    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


def load_native_sprite(name, pixel=DISK_ASSET_PIXEL):
    """Carga un PNG, recorta el relleno y lo reduce a su rejilla de píxeles."""
    image = load_image(name)
    if image is None:
        return None
    rect = image.get_bounding_rect()
    if rect.w <= 0 or rect.h <= 0:
        return None
    cropped = image.subsurface(rect).copy()
    width = max(1, rect.w // pixel)
    height = max(1, rect.h // pixel)
    return pygame.transform.scale(cropped, (width, height))


def hue_shift(color, degrees):
    """Gira el tono conservando saturación y brillo (mantiene el sombreado)."""
    r, g, b = color[:3]
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360.0) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    alpha = color[3] if len(color) > 3 else 255
    return (int(round(r * 255)), int(round(g * 255)),
            int(round(b * 255)), alpha)


def tint_surface(surface, degrees):
    """Recolorea un sprite nativo píxel a píxel (solo la paleta de color)."""
    if degrees == 0:
        return surface.copy()
    out = surface.copy()
    cache = {}
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            color = surface.get_at((x, y))
            if color.a == 0 or color.r == color.g == color.b:
                continue
            key = (color.r, color.g, color.b)
            if key not in cache:
                cache[key] = hue_shift(color, degrees)
            out.set_at((x, y), cache[key])
    return out


def format_time(seconds):
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


class HanoiGUI:
    WIDTH = 960
    HEIGHT = 640
    FPS = 60

    COLOR_BG = (45, 25, 95)
    COLOR_BASE = (139, 90, 43)
    COLOR_POLE = (160, 110, 60)
    COLOR_TEXT = (255, 249, 240)
    COLOR_TEXT_SOFT = (200, 185, 225)
    COLOR_TEXT_MUTED = (150, 135, 180)
    COLOR_DISK_BORDER = (16, 10, 24)
    COLOR_SELECTION = (255, 220, 60)

    # Tono por tamaño: dorado -> naranja -> rojo -> magenta (tema del fondo).
    DISK_TINTS = (26, 18, 10, 2, -6, -14, -22, -30, -38, -46)
    DISK_COLORS = [
        (255, 190, 60),
        (255, 170, 30),
        (255, 143, 0),
        (250, 115, 15),
        (240, 80, 30),
        (225, 50, 45),
        (205, 35, 70),
        (180, 30, 85),
        (155, 28, 95),
        (130, 30, 100),
    ]

    NUM_TOWERS = 3

    # HUD superior
    HUD_RECT = pygame.Rect(8, 8, 944, 88)
    HUD_BOTTOM = 96

    # Escenario
    PLATFORM_X = 30
    PLATFORM_Y = 476
    PLATFORM_TOP_H = 24
    BASE_Y = 500
    POLE_HEIGHT = 370
    POLE_WIDTH = 18
    POLE_CAP_H = 5

    DISK_STEP = 26
    DISK_MIN_W = 140
    DISK_MAX_W = 250

    ERROR_SECONDS = 3
    TIME_WARNING_SECONDS = 10
    HINT_SECONDS = 4
    AUTO_SOLVE_INTERVAL_MS = 400

    # Animación del disco: sube, se desplaza y baja. ANIM_MS = 0 la desactiva.
    ANIM_MS = 300
    ANIM_UP = 0.30
    ANIM_DOWN = 0.30
    ANIM_LIFT_MARGIN = 30

    COLOR_PANEL = (24, 14, 52)
    COLOR_PANEL_SHADOW = (10, 6, 20)
    COLOR_BUTTON = (92, 58, 28)
    COLOR_BUTTON_LIGHT = (150, 98, 46)
    COLOR_BUTTON_HOVER = (139, 90, 43)
    COLOR_ERROR = (255, 90, 90)
    COLOR_WIN = (255, 220, 60)
    COLOR_LOSE = (255, 120, 100)
    COLOR_BUTTON_DISABLED = (60, 48, 70)
    COLOR_TEXT_DISABLED = (150, 140, 160)
    COLOR_HINT = (90, 230, 130)

    # Barra inferior (sobre la madera de la base)
    BTN_MENU = pygame.Rect(40, 552, 100, 54)
    BTN_RETRY = pygame.Rect(150, 552, 100, 54)
    BTN_HISTORY = pygame.Rect(440, 552, 130, 54)
    BTN_UNDO = pygame.Rect(580, 552, 140, 54)
    BTN_HINT = pygame.Rect(730, 552, 90, 54)
    BTN_SOLVE = pygame.Rect(830, 552, 120, 54)

    # Menú
    MENU_PANEL = pygame.Rect(180, 50, 600, 510)
    BTN_MINUS = pygame.Rect(330, 200, 64, 64)
    BTN_PLUS = pygame.Rect(566, 200, 64, 64)
    BTN_MODE_PREV = pygame.Rect(350, 292, 40, 40)
    BTN_MODE_NEXT = pygame.Rect(570, 292, 40, 40)
    BTN_START_PREV = pygame.Rect(350, 344, 40, 40)
    BTN_START_NEXT = pygame.Rect(570, 344, 40, 40)
    BTN_START = pygame.Rect(380, 418, 200, 64)
    BTN_WIN_RETRY = pygame.Rect(290, 380, 180, 56)
    BTN_WIN_MENU = pygame.Rect(490, 380, 180, 56)

    HISTORY_PANEL = pygame.Rect(632, 104, 312, 236)
    HISTORY_ROWS = 8
    HISTORY_ROW_H = 22

    TOWER_KEYS = {
        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
        pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2,
    }

    SHORTCUTS = (
        ("1  2  3", "Elegir torre (origen y destino)"),
        ("U / Ctrl+Z", "Deshacer (5 s)"),
        ("H", "Pista"),
        ("X", "Resolver automáticamente"),
        ("L", "Mostrar / ocultar historial"),
        ("N", "Puzzle nuevo (mismos ajustes)"),
        ("R", "Reintentar el mismo puzzle"),
        ("M", "Activar / silenciar sonido"),
        ("Esc", "Volver al menú"),
        ("F1", "Esta ayuda"),
    )

    MODE_LABELS = {
        HanoiGame.MODE_NORMAL: "NORMAL",
        HanoiGame.MODE_PERFECT: "PERFECTO",
        HanoiGame.MODE_TIMED: "CONTRARRELOJ",
    }

    START_LABELS = {
        HanoiGame.START_STANDARD: "CLÁSICO",
        HanoiGame.START_MIXED: "MIXTO",
    }

    def __init__(self, num_disks=3, show_menu=True):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Torre de Hanói · Retro Pixel")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.game = HanoiGame(num_disks)

        self.font = pygame.font.SysFont("consolas", 11, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 9, bold=True)
        self.font_mid = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_hud = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_big = pygame.font.SysFont("consolas", 24, bold=True)

        self.img_background = load_image("background.png")
        self.img_base = load_image("base.png")
        self.img_pole_wood = load_image("pole_wood.png")
        self.img_pole_steel = load_image("pole_steel.png")
        self.img_pole_wood = self._scale_pole(self.img_pole_wood)
        self.img_pole_steel = self._scale_pole(self.img_pole_steel)

        self.disk_sprites = []
        for name in DISK_ASSETS:
            sprite = load_native_sprite(name)
            if sprite is not None:
                self.disk_sprites.append(sprite)

        self._disk_cache = {}
        self._tint_cache = {}
        self._text_cache = {}
        self._base_shadow = None

        self.selected_tower = None
        self.error_message = ""
        self.error_until = 0

        self.hint = None
        self.hint_until = 0
        self.auto_solving = False
        self.auto_next = 0

        self.show_history = False
        self.history_scroll = 0
        self._history_seen = 0
        self.show_help = False

        self.anim = None
        self._anim_seen = 0
        self._anim_last = None

        self.sound_enabled = True
        self._end_sound_done = False
        self._init_sounds()

        self.state = "menu" if show_menu else "playing"
        self.menu_disks = num_disks
        self.menu_mode = HanoiGame.MODE_NORMAL
        self.menu_start = HanoiGame.START_STANDARD

    # ------------------------------------------------------------------
    # Assets y geometría de discos
    # ------------------------------------------------------------------
    @staticmethod
    def _scale_pole(image):
        if image is None:
            return None
        return pygame.transform.scale(
            image, (HanoiGUI.POLE_WIDTH, HanoiGUI.POLE_HEIGHT))

    def tower_center_x(self, index):
        section = self.WIDTH // self.NUM_TOWERS
        return section * index + section // 2

    def tower_rect(self, index):
        section = self.WIDTH // self.NUM_TOWERS
        top = self.HUD_BOTTOM + 8
        bottom = self.PLATFORM_Y + self.PLATFORM_TOP_H + 16
        return pygame.Rect(section * index, top, section, bottom - top)

    def disk_color(self, size):
        return self.DISK_COLORS[(size - 1) % len(self.DISK_COLORS)]

    def disk_width(self, size, num_disks=None):
        count = self.game.num_disks if num_disks is None else num_disks
        if count <= 1:
            return self.DISK_MAX_W
        step = (self.DISK_MAX_W - self.DISK_MIN_W) / (count - 1)
        return int(round(self.DISK_MIN_W + (size - 1) * step))

    def disk_sprite_index(self, size, num_disks=None):
        count = self.game.num_disks if num_disks is None else num_disks
        total = len(self.disk_sprites)
        if total == 0:
            return 0
        if count <= 1:
            return total - 1
        return int(round((size - 1) * (total - 1) / (count - 1)))

    def disk_tint(self, size, num_disks=None):
        """Reparte la paleta completa entre los discos de la partida."""
        count = self.game.num_disks if num_disks is None else num_disks
        total = len(self.DISK_TINTS)
        if count <= 1:
            return self.DISK_TINTS[total // 3]
        return self.DISK_TINTS[
            int(round((size - 1) * (total - 1) / (count - 1)))]

    def _disk_image(self, size, num_disks, width):
        index = self.disk_sprite_index(size, num_disks)
        if not self.disk_sprites:
            return self._fallback_disk(size, width)
        tint = self.disk_tint(size, num_disks)
        key = (index, tint)
        if key not in self._tint_cache:
            self._tint_cache[key] = tint_surface(
                self.disk_sprites[index], tint)
        sprite = self._tint_cache[key]
        height = max(1, int(round(sprite.get_height() * width
                                  / sprite.get_width())))
        return pygame.transform.scale(sprite, (width, height))

    def _fallback_disk(self, size, width):
        """Disco plano por si faltan los PNG (mismo aspecto retro)."""
        height = max(18, width // 5)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        base = self.disk_color(size)
        light = tuple(min(255, c + 55) for c in base)
        dark = tuple(int(c * 0.62) for c in base)
        pygame.draw.rect(surface, self.COLOR_DISK_BORDER,
                         pygame.Rect(0, 0, width, height), 3)
        pygame.draw.rect(surface, base,
                         pygame.Rect(3, 3, width - 6, height - 6))
        pygame.draw.rect(surface, light,
                         pygame.Rect(3, 3, width - 6, max(2, height // 6)))
        pygame.draw.rect(surface, dark,
                         pygame.Rect(3, height - max(3, height // 5),
                                     width - 6, max(2, height // 6)))
        return surface

    def disk_surface(self, size):
        key = (size, self.game.num_disks)
        if key not in self._disk_cache:
            self._disk_cache[key] = self._disk_image(
                size, self.game.num_disks, self.disk_width(size))
        return self._disk_cache[key]

    def disk_pos(self, tower_index, level, size):
        surface = self.disk_surface(size)
        x = self.tower_center_x(tower_index) - surface.get_width() // 2
        y = self.BASE_Y - surface.get_height() - level * self.DISK_STEP
        return x, y

    # ------------------------------------------------------------------
    # Sonido
    # ------------------------------------------------------------------
    def _init_sounds(self):
        self.sounds = {}
        self.audio_ok = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(22050, -16, 1, 512)
            init = pygame.mixer.get_init()
            if init is None:
                return
            rate, _fmt, channels = init
            self.sounds = {
                "select": self._tone(660, 50, 0.16, rate, channels),
                "move": self._tone(520, 70, 0.20, rate, channels),
                "error": self._tone(150, 120, 0.20, rate, channels),
                "undo": self._tone(360, 90, 0.18, rate, channels),
                "hint": self._tone(780, 60, 0.14, rate, channels),
                "win": self._sequence(
                    ((523, 90), (659, 90), (784, 120), (1046, 180)),
                    rate, channels),
                "lose": self._sequence(
                    ((330, 120), (247, 120), (165, 200)), rate, channels),
            }
            self.audio_ok = True
        except (pygame.error, ValueError):
            self.sounds = {}

    @staticmethod
    def _tone(freq, ms, volume, rate, channels):
        count = max(1, int(rate * ms / 1000))
        samples = array.array("h")
        fade_in = max(1, int(rate * 0.004))
        fade_out = max(1, int(rate * 0.02))
        for i in range(count):
            envelope = min(1.0, i / fade_in, (count - i) / fade_out)
            wave = 1.0 if math.sin(2 * math.pi * freq * i / rate) >= 0 else -1.0
            value = int(32767 * volume * envelope * wave)
            for _ in range(channels):
                samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    @classmethod
    def _sequence(cls, notes, rate, channels):
        samples = array.array("h")
        for freq, ms in notes:
            count = max(1, int(rate * ms / 1000))
            fade = max(1, int(rate * 0.01))
            for i in range(count):
                envelope = min(1.0, i / fade, (count - i) / fade)
                wave = 1.0 if math.sin(
                    2 * math.pi * freq * i / rate) >= 0 else -1.0
                value = int(32767 * 0.18 * envelope * wave)
                for _ in range(channels):
                    samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if not self.sound_enabled or name not in self.sounds:
            return
        try:
            self.sounds[name].play()
        except pygame.error:
            pass

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.play("select")

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key, event.mod)
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_history(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse(event.pos)

    def tower_at(self, pos):
        for index in range(self.NUM_TOWERS):
            if self.tower_rect(index).collidepoint(pos):
                return index
        return None

    def handle_click(self, pos):
        if self.game.is_over():
            return
        clicked = self.tower_at(pos)
        if clicked is None:
            self.selected_tower = None
            return
        self.select_tower(clicked)

    def select_tower(self, clicked):
        """Marca origen o destino. Lo usan el clic y las teclas 1/2/3."""
        if self.game.is_over():
            return
        self.error_message = ""
        if self.selected_tower is None:
            if not self.game.get_state()[clicked]:
                self.set_error("La torre origen está vacía.")
                return
            self.selected_tower = clicked
            self.play("select")
            return
        origin = self.selected_tower
        self.selected_tower = None
        if clicked == origin:
            return
        try:
            self.game.move(origin, clicked)
            self.clear_hint()
            self.play("move")
        except ValueError as error:
            self.set_error(str(error))

    def clear_hint(self):
        self.hint = None
        self.hint_until = 0

    def try_hint(self):
        """Resalta origen y destino del siguiente movimiento óptimo."""
        if self.game.is_over():
            return
        self.error_message = ""
        hint = self.game.use_hint()
        if hint is None:
            return
        self.hint = hint
        self.hint_until = pygame.time.get_ticks() + self.HINT_SECONDS * 1000
        self.play("hint")

    def start_auto_solve(self):
        """Resolver automáticamente: un movimiento óptimo cada intervalo."""
        if self.game.is_over() or self.game.get_hint() is None:
            return
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        self.auto_solving = True
        self.auto_next = pygame.time.get_ticks()

    def stop_auto_solve(self):
        self.auto_solving = False

    def toggle_auto_solve(self):
        if self.auto_solving:
            self.stop_auto_solve()
        else:
            self.start_auto_solve()

    def auto_solve_step(self):
        now = pygame.time.get_ticks()
        if now < self.auto_next:
            return
        try:
            self.game.auto_step()
        except ValueError as error:
            self.set_error(str(error))
            self.stop_auto_solve()
            return
        self.play("move")
        self.auto_next = now + self.AUTO_SOLVE_INTERVAL_MS
        if self.game.is_over():
            self.stop_auto_solve()

    def try_undo(self):
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        try:
            self.game.undo()
            self.play("undo")
        except ValueError as error:
            self.set_error(str(error))

    def toggle_history(self):
        self.show_history = not self.show_history
        self.history_scroll = 0

    def scroll_history(self, delta):
        """Rueda del ratón: delta > 0 sube hacia los movimientos antiguos."""
        if self.state != "playing" or not self.show_history:
            return
        max_scroll = max(0, self.game.get_history_len() - self.HISTORY_ROWS)
        self.history_scroll = max(
            0, min(max_scroll, self.history_scroll + delta))

    def close_overlays(self):
        self.show_help = False
        self.history_scroll = 0
        self.reset_animation()

    def _ticks(self):
        return pygame.time.get_ticks()

    @staticmethod
    def ease(u):
        return u * u * (3 - 2 * u)

    def animating(self):
        return self.anim is not None

    def end_panel_visible(self):
        """El panel de fin espera a que termine la animación del último disco."""
        return self.game.is_over() and not self.animating()

    def reset_animation(self):
        """Corta la animación y sincroniza con el historial actual (sin animar)."""
        self.anim = None
        history = self.game.get_history()
        self._anim_seen = len(history)
        self._anim_last = history[-1] if history else None

    def start_animation(self, disk, src, dst):
        """Anima `disk` de la torre src a la dst. El estado lógico ya cambió:
        el disco está en la cima de dst y ya no está en src."""
        state = self.game.get_state()
        if not state[dst] or state[dst][-1] != disk:
            self.anim = None
            return
        x0, y0 = self.disk_pos(src, len(state[src]), disk)
        x1, y1 = self.disk_pos(dst, len(state[dst]) - 1, disk)
        self.anim = {
            "disk": disk, "src": src, "dst": dst, "start": self._ticks(),
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "lift": min(y0, y1) - self.ANIM_LIFT_MARGIN,
        }

    def update_animation(self):
        """Detecta un movimiento (+1 en el historial) o un deshacer (-1) y lo
        anima. Cualquier otro cambio (reset, partida nueva) no se anima."""
        history = self.game.get_history()
        size = len(history)
        delta = size - self._anim_seen
        if delta == 1 and self.ANIM_MS > 0:
            _n, origin, dest, disk, _t = history[-1]
            self.start_animation(disk, origin, dest)
        elif delta == -1 and self.ANIM_MS > 0 and self._anim_last:
            _n, origin, dest, disk, _t = self._anim_last
            self.start_animation(disk, dest, origin)
        elif delta != 0:
            self.anim = None
        self._anim_seen = size
        self._anim_last = history[-1] if history else None
        if self.anim and self._ticks() - self.anim["start"] >= self.ANIM_MS:
            self.anim = None

    def anim_progress(self):
        if not self.anim:
            return 1.0
        elapsed = self._ticks() - self.anim["start"]
        return max(0.0, min(1.0, elapsed / self.ANIM_MS))

    def anim_position(self, t):
        """(x, y) del disco en vuelo para t en [0, 1]: sube, cruza y baja."""
        a = self.anim
        up_end = self.ANIM_UP
        down_start = 1.0 - self.ANIM_DOWN
        if t < up_end:
            u = self.ease(t / up_end)
            return a["x0"], a["y0"] + (a["lift"] - a["y0"]) * u
        if t < down_start:
            u = self.ease((t - up_end) / (down_start - up_end))
            return a["x0"] + (a["x1"] - a["x0"]) * u, a["lift"]
        u = self.ease((t - down_start) / self.ANIM_DOWN)
        return a["x1"], a["lift"] + (a["y1"] - a["lift"]) * u

    def new_puzzle(self):
        """N: puzzle nuevo con los mismos discos, modo e inicio."""
        self.start_game(self.game.num_disks, self.game.get_mode(),
                        self.game.get_start())

    def update(self):
        if self.state == "playing":
            self.game.update_time()
            self.update_animation()
            size = self.game.get_history_len()
            if size != self._history_seen:
                self._history_seen = size
                self.history_scroll = 0
            if self.game.is_over():
                self.selected_tower = None
                self.show_help = False
                self.stop_auto_solve()
                self.clear_hint()
                if not self._end_sound_done:
                    self._end_sound_done = True
                    self.play("lose" if self.game.is_lost() else "win")
            elif self.auto_solving:
                self.auto_solve_step()
            if self.hint and pygame.time.get_ticks() > self.hint_until:
                self.clear_hint()

    def set_error(self, message):
        self.error_message = message
        self.error_until = pygame.time.get_ticks() + self.ERROR_SECONDS * 1000
        self.play("error")

    def change_menu_mode(self, delta):
        modes = list(HanoiGame.MODES)
        idx = modes.index(self.menu_mode)
        self.menu_mode = modes[(idx + delta) % len(modes)]

    def change_menu_start(self, delta):
        starts = list(HanoiGame.STARTS)
        idx = starts.index(self.menu_start)
        self.menu_start = starts[(idx + delta) % len(starts)]

    def start_game(self, num_disks, mode=None, start=None):
        if mode is None:
            mode = self.menu_mode
        if start is None:
            start = self.menu_start
        self.game = HanoiGame(num_disks, mode=mode, start=start)
        self.menu_disks = num_disks
        self.menu_mode = mode
        self.menu_start = start
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        self.stop_auto_solve()
        self.close_overlays()
        self._end_sound_done = False
        self.state = "playing"

    def restart_game(self):
        """RETRY: repite la misma partida (mismo estado inicial, aunque sea mixto)."""
        self.game.reset()
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        self.stop_auto_solve()
        self.close_overlays()
        self._end_sound_done = False
        self.state = "playing"

    def go_to_menu(self):
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        self.stop_auto_solve()
        self.close_overlays()
        self.state = "menu"

    def change_menu_disks(self, delta):
        value = self.menu_disks + delta
        self.menu_disks = max(HanoiGame.MIN_DISKS,
                              min(HanoiGame.MAX_DISKS, value))

    def handle_key(self, key, mod=0):
        if self.state == "menu":
            if key == pygame.K_ESCAPE:
                self.running = False
            else:
                self.handle_menu_key(key)
        elif self.auto_solving:
            # cualquier tecla cancela el auto-resolver (Esc no sale al menú)
            self.stop_auto_solve()
        elif self.show_help:
            # cualquier tecla cierra la ayuda sin ejecutar su acción
            self.show_help = False
        elif key == pygame.K_ESCAPE:
            self.go_to_menu()
        elif key == pygame.K_r:
            self.restart_game()
        elif self.game.is_over():
            # el resto de atajos se ignoran al terminar la partida
            return
        elif key in self.TOWER_KEYS:
            self.select_tower(self.TOWER_KEYS[key])
        elif key == pygame.K_u or (
                key == pygame.K_z and mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
            self.try_undo()
        elif key == pygame.K_h:
            self.try_hint()
        elif key == pygame.K_x:
            self.start_auto_solve()
        elif key == pygame.K_l:
            self.toggle_history()
        elif key == pygame.K_n:
            self.new_puzzle()
        elif key == pygame.K_m:
            self.toggle_sound()
        elif key == pygame.K_F1:
            self.selected_tower = None
            self.show_help = True

    def handle_menu_key(self, key):
        if key in (pygame.K_UP, pygame.K_RIGHT):
            self.change_menu_disks(1)
        elif key in (pygame.K_DOWN, pygame.K_LEFT):
            self.change_menu_disks(-1)
        elif key == pygame.K_a:
            self.change_menu_mode(-1)
        elif key == pygame.K_d:
            self.change_menu_mode(1)
        elif key == pygame.K_w:
            self.change_menu_start(-1)
        elif key == pygame.K_s:
            self.change_menu_start(1)
        elif key == pygame.K_m:
            self.toggle_sound()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_game(self.menu_disks, self.menu_mode)

    def handle_mouse(self, pos):
        if self.state == "menu":
            if self.BTN_MINUS.collidepoint(pos):
                self.change_menu_disks(-1)
            elif self.BTN_PLUS.collidepoint(pos):
                self.change_menu_disks(1)
            elif self.BTN_MODE_PREV.collidepoint(pos):
                self.change_menu_mode(-1)
            elif self.BTN_MODE_NEXT.collidepoint(pos):
                self.change_menu_mode(1)
            elif self.BTN_START_PREV.collidepoint(pos):
                self.change_menu_start(-1)
            elif self.BTN_START_NEXT.collidepoint(pos):
                self.change_menu_start(1)
            elif self.BTN_START.collidepoint(pos):
                self.start_game(self.menu_disks, self.menu_mode)
            return

        if self.game.is_over():
            if self.animating():
                return
            if self.BTN_WIN_RETRY.collidepoint(pos):
                self.restart_game()
            elif self.BTN_WIN_MENU.collidepoint(pos):
                self.go_to_menu()
            return

        if self.auto_solving:
            # cualquier clic cancela el auto-resolver
            self.stop_auto_solve()
            return

        if self.show_help:
            self.show_help = False
            return

        if self.BTN_MENU.collidepoint(pos):
            self.go_to_menu()
        elif self.BTN_RETRY.collidepoint(pos):
            self.restart_game()
        elif self.BTN_HISTORY.collidepoint(pos):
            self.toggle_history()
        elif self.BTN_UNDO.collidepoint(pos):
            self.try_undo()
        elif self.BTN_HINT.collidepoint(pos):
            self.try_hint()
        elif self.BTN_SOLVE.collidepoint(pos):
            self.start_auto_solve()
        else:
            self.handle_click(pos)

    # ------------------------------------------------------------------
    # Dibujo: utilidades
    # ------------------------------------------------------------------
    def _text_image(self, text, font, color, scale=2, shadow=True):
        key = (text, font, color, scale, shadow)
        cached = self._text_cache.get(key)
        if cached is not None:
            return cached
        base = font.render(text, False, color)
        image = pygame.transform.scale(
            base, (base.get_width() * scale, base.get_height() * scale))
        if shadow:
            shade = font.render(text, False, self.COLOR_PANEL_SHADOW)
            shade = pygame.transform.scale(
                shade, (shade.get_width() * scale, shade.get_height() * scale))
            out = pygame.Surface(
                (image.get_width() + scale, image.get_height() + scale),
                pygame.SRCALPHA)
            out.blit(shade, (scale, scale))
            out.blit(image, (0, 0))
            image = out
        if len(self._text_cache) > 512:
            self._text_cache.clear()
        self._text_cache[key] = image
        return image

    def draw_text(self, text, font, color, center=None, topleft=None,
                  scale=2, shadow=True):
        image = self._text_image(text, font, color, scale, shadow)
        rect = image.get_rect()
        if center is not None:
            rect.center = center
        else:
            rect.topleft = topleft
        self.screen.blit(image, rect)
        return rect

    def draw_panel(self, rect, border=None, fill=None, width=3):
        border = self.COLOR_SELECTION if border is None else border
        fill = self.COLOR_PANEL if fill is None else fill
        pygame.draw.rect(self.screen, self.COLOR_PANEL_SHADOW,
                         rect.move(4, 4))
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, border, rect, width)

    def draw_button(self, rect, label, font=None, disabled=False):
        font = font or self.font
        if disabled:
            pygame.draw.rect(self.screen, self.COLOR_BUTTON_DISABLED, rect)
            pygame.draw.rect(self.screen, self.COLOR_DISK_BORDER, rect, 3)
            self.draw_text(label, font, self.COLOR_TEXT_DISABLED,
                           center=rect.center, shadow=False)
            return
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, self.COLOR_PANEL_SHADOW,
                         pygame.Rect(rect.x + 3, rect.y + 3,
                                     rect.width, rect.height))
        pygame.draw.rect(
            self.screen,
            self.COLOR_BUTTON_HOVER if hover else self.COLOR_BUTTON, rect)
        pygame.draw.rect(self.screen, self.COLOR_BUTTON_LIGHT,
                         pygame.Rect(rect.x + 3, rect.y + 3,
                                     rect.width - 6, 5))
        pygame.draw.rect(self.screen, self.COLOR_DISK_BORDER, rect, 3)
        if hover:
            pygame.draw.rect(self.screen, self.COLOR_SELECTION, rect, 3)
        if label:
            self.draw_text(label, font, self.COLOR_TEXT,
                           center=rect.center, shadow=False)

    def draw_disabled_button(self, rect, label, font=None):
        self.draw_button(rect, label, font, disabled=True)

    def draw_arrow_button(self, rect, direction):
        """Botón con una flecha de píxeles (evita glifos raros de la fuente)."""
        self.draw_button(rect, "", self.font_small)
        cx, cy = rect.center
        if direction < 0:
            points = [(cx + 6, cy - 8), (cx + 6, cy + 8), (cx - 6, cy)]
        else:
            points = [(cx - 6, cy - 8), (cx - 6, cy + 8), (cx + 6, cy)]
        pygame.draw.polygon(self.screen, self.COLOR_TEXT, points)

    # ------------------------------------------------------------------
    # Dibujo: HUD y paneles
    # ------------------------------------------------------------------
    def draw_hud(self):
        self.draw_panel(self.HUD_RECT)

        self.draw_text("TORRE DE HANÓI", self.font_title, self.COLOR_WIN,
                       topleft=(24, 10))
        start_label = self.START_LABELS.get(
            self.game.get_start(), self.game.get_start().upper())
        self.draw_text(f"INICIO: {start_label}", self.font_small,
                       self.COLOR_TEXT_SOFT, topleft=(26, 60), shadow=False)
        self.draw_text("F1 ATAJOS", self.font_small, self.COLOR_TEXT_MUTED,
                       topleft=(214, 60), shadow=False)

        for x in (330, 500, 600, 800):
            pygame.draw.line(self.screen, (70, 45, 110),
                             (x, 18), (x, 86), 2)

        mode_label = self.MODE_LABELS.get(
            self.game.get_mode(), self.game.get_mode().upper())
        self.draw_hud_card(342, "MODO", mode_label, self.font_small,
                           value_y=48)

        self.draw_hud_card(512, "DISCOS", str(self.game.num_disks),
                           self.font_hud)

        self.draw_hud_card(
            612, "MOVS / MÍN",
            f"{self.game.get_moves()} / {self.game.get_min_moves()}",
            self.font_mid)

        if self.game.get_mode() == HanoiGame.MODE_TIMED:
            left = self.game.get_time_left()
            color = (self.COLOR_ERROR
                     if left <= self.TIME_WARNING_SECONDS else self.COLOR_TEXT)
            self.draw_hud_card(812, "RESTA",
                               format_time(math.ceil(left)), self.font_hud,
                               color)
        else:
            self.draw_hud_card(812, "TIEMPO",
                               format_time(self.game.get_elapsed()),
                               self.font_hud)

        self.draw_bottom_bar()

    def draw_hud_card(self, x, label, value, font, color=None, value_y=38):
        self.draw_text(label, self.font_small, self.COLOR_TEXT_MUTED,
                       topleft=(x, 14), shadow=False)
        self.draw_text(value, font, color or self.COLOR_TEXT,
                       topleft=(x, value_y))

    def draw_bottom_bar(self):
        self.draw_button(self.BTN_MENU, "MENÚ", self.font_small)
        self.draw_button(self.BTN_RETRY, "RETRY", self.font_small)
        self.draw_button(self.BTN_HISTORY, "HISTORIAL", self.font_small)
        self.draw_undo_button()
        self.draw_assist_buttons()

    def draw_assist_buttons(self):
        if self.auto_solving:
            self.draw_disabled_button(self.BTN_HINT, "PISTA", self.font_small)
            self.draw_button(self.BTN_SOLVE, "PARAR", self.font_small)
        else:
            self.draw_button(self.BTN_HINT, "PISTA", self.font_small)
            self.draw_button(self.BTN_SOLVE, "RESOLVER", self.font_small)

    def draw_undo_button(self):
        left = 0 if self.auto_solving else self.game.get_undo_time_left()
        if left > 0:
            self.draw_button(self.BTN_UNDO,
                             f"DESHACER {math.ceil(left)}s",
                             self.font_small)
            fraction = left / HanoiGame.UNDO_WINDOW
            bar = pygame.Rect(self.BTN_UNDO.x + 10,
                              self.BTN_UNDO.bottom - 11,
                              int((self.BTN_UNDO.width - 20) * fraction), 5)
            pygame.draw.rect(self.screen, self.COLOR_SELECTION, bar)
        else:
            self.draw_button(self.BTN_UNDO, "DESHACER",
                             self.font_small, disabled=True)

    def draw_history(self):
        if not self.show_history:
            return
        history = self.game.get_history()
        total = len(history)
        panel = self.HISTORY_PANEL
        self.draw_panel(panel)
        self.draw_text(f"HISTORIAL ({total}) [L]", self.font_small,
                       self.COLOR_SELECTION, topleft=(panel.x + 12, panel.y + 8),
                       shadow=False)
        top = panel.y + 34
        if total == 0:
            self.draw_text("Sin movimientos", self.font_small,
                           self.COLOR_TEXT_DISABLED,
                           topleft=(panel.x + 12, top), shadow=False)
            return
        end = total - self.history_scroll
        start = max(0, end - self.HISTORY_ROWS)
        for row, entry in enumerate(history[start:end]):
            number, origin, destination, disk, _elapsed = entry
            color = (self.COLOR_SELECTION
                     if start + row == total - 1 else self.COLOR_TEXT)
            text = f"{number:>3}. {origin + 1}->{destination + 1} (disco {disk})"
            self.draw_text(text, self.font_small, color,
                           topleft=(panel.x + 12, top + row * self.HISTORY_ROW_H),
                           shadow=False)
        if total > self.HISTORY_ROWS:
            track = pygame.Rect(panel.right - 14, top,
                                6, self.HISTORY_ROWS * self.HISTORY_ROW_H - 4)
            pygame.draw.rect(self.screen, self.COLOR_BUTTON_DISABLED, track)
            thumb_h = max(14, track.height * self.HISTORY_ROWS // total)
            max_scroll = total - self.HISTORY_ROWS
            fraction = 1 - self.history_scroll / max_scroll
            thumb_y = track.y + int((track.height - thumb_h) * fraction)
            pygame.draw.rect(self.screen, self.COLOR_SELECTION,
                             pygame.Rect(track.x, thumb_y,
                                         track.width, thumb_h))

    def draw_help(self):
        if not self.show_help:
            return
        veil = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.screen.blit(veil, (0, 0))

        key_w = max(self.font_small.size(k)[0] for k, _ in self.SHORTCUTS) * 2
        desc_w = max(self.font_small.size(d)[0] for _, d in self.SHORTCUTS) * 2
        row_h = 30
        width = 40 + key_w + 40 + desc_w + 40
        height = 76 + len(self.SHORTCUTS) * row_h + 44
        panel = pygame.Rect(0, 0, width, height)
        panel.center = (self.WIDTH // 2, self.HEIGHT // 2)
        self.draw_panel(panel, width=4)
        self.draw_text("ATAJOS DE TECLADO", self.font_mid, self.COLOR_WIN,
                       center=(panel.centerx, panel.y + 38))
        for row, (keys, action) in enumerate(self.SHORTCUTS):
            y = panel.y + 76 + row * row_h
            self.draw_text(keys, self.font_small, self.COLOR_SELECTION,
                           topleft=(panel.x + 40, y), shadow=False)
            self.draw_text(action, self.font_small, self.COLOR_TEXT,
                           topleft=(panel.x + 40 + key_w + 40, y),
                           shadow=False)
        self.draw_text("Cualquier tecla o clic cierra la ayuda",
                       self.font_small, self.COLOR_TEXT_MUTED,
                       center=(panel.centerx, panel.bottom - 26),
                       shadow=False)

    def draw_hint(self):
        if not self.hint:
            return
        origin, destination = self.hint
        for index, label in ((origin, "ORIGEN"), (destination, "DESTINO")):
            rect = self.tower_rect(index).inflate(-14, -12)
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            glow.fill((90, 230, 130, 24))
            self.screen.blit(glow, rect.topleft)
            pygame.draw.rect(self.screen, self.COLOR_HINT, rect, 3)
            self.draw_text(label, self.font_small, self.COLOR_HINT,
                           center=(rect.centerx, rect.top + 14),
                           shadow=False)

    def draw_selection(self):
        if self.selected_tower is None:
            return
        rect = self.tower_rect(self.selected_tower).inflate(-14, -12)
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        glow.fill((255, 220, 60, 28))
        self.screen.blit(glow, rect.topleft)
        pygame.draw.rect(self.screen, self.COLOR_SELECTION, rect, 3)
        cx = rect.centerx
        pygame.draw.polygon(self.screen, self.COLOR_SELECTION,
                            [(cx - 12, rect.top + 4), (cx + 12, rect.top + 4),
                             (cx, rect.top + 20)])

    def draw_error(self):
        if not self.error_message:
            return
        if pygame.time.get_ticks() > self.error_until:
            self.error_message = ""
            return
        image = self._text_image(
            self.error_message, self.font_small, self.COLOR_ERROR)
        box = image.get_rect(center=(self.WIDTH // 2, 116)).inflate(32, 22)
        self.draw_panel(box, border=self.COLOR_ERROR)
        self.screen.blit(image, image.get_rect(center=box.center))

    def draw_end_panel(self):
        veil = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.screen.blit(veil, (0, 0))

        panel = pygame.Rect(240, 120, 480, 340)
        moves = self.game.get_moves()
        minimum = self.game.get_min_moves()
        elapsed = self.game.get_elapsed()
        cx = self.WIDTH // 2

        if self.game.is_lost():
            border_color = self.COLOR_LOSE
            title = "PERDISTE"
            title_color = self.COLOR_LOSE
            if self.game.is_timed_out():
                note = "Se acabó el tiempo"
            else:
                note = "Superaste el mínimo de movimientos"
        else:
            border_color = self.COLOR_WIN
            title = "¡GANASTE!"
            title_color = self.COLOR_WIN
            if self.game.was_auto_solved():
                title = "RESUELTO"
                note = "Resuelto automáticamente"
            else:
                if moves == minimum:
                    note = "¡Partida perfecta!"
                else:
                    note = f"Te pasaste por {moves - minimum} movimientos"
                hints = self.game.get_hints_used()
                if hints:
                    note += f" · Pistas: {hints}"

        self.draw_panel(panel, border=border_color, width=4)
        self.draw_text(title, self.font_big, title_color, center=(cx, 168))
        self.draw_text(f"Movimientos: {moves}", self.font_mid,
                       self.COLOR_TEXT, center=(cx, 238))
        self.draw_text(f"Mínimo: {minimum}", self.font_mid,
                       self.COLOR_TEXT, center=(cx, 274))
        self.draw_text(f"Tiempo: {format_time(elapsed)}", self.font_mid,
                       self.COLOR_TEXT, center=(cx, 310))
        self.draw_text(note, self.font_small, title_color,
                       center=(cx, 346), shadow=False)
        self.draw_button(self.BTN_WIN_RETRY, "RETRY", self.font_mid)
        self.draw_button(self.BTN_WIN_MENU, "MENÚ", self.font_mid)

    def draw_menu(self):
        self.draw_background()
        self.draw_base()
        self.draw_poles()

        self.draw_panel(self.MENU_PANEL, width=4)
        cx = self.WIDTH // 2
        self.draw_text("TORRE DE HANÓI", self.font_big, self.COLOR_WIN,
                       center=(cx, 102))
        self.draw_text("RETRO PIXEL EDITION", self.font_small,
                       self.COLOR_TEXT_SOFT, center=(cx, 136), shadow=False)

        self.draw_text("DISCOS", self.font_mid, self.COLOR_TEXT,
                       center=(cx, 172))
        self.draw_button(self.BTN_MINUS, "-", self.font_big)
        self.draw_button(self.BTN_PLUS, "+", self.font_big)
        self.draw_text(str(self.menu_disks), self.font_big, self.COLOR_TEXT,
                       center=(cx, 232))

        self.draw_text("MODO", self.font_small, self.COLOR_TEXT_MUTED,
                       topleft=(240, 300), shadow=False)
        self.draw_arrow_button(self.BTN_MODE_PREV, -1)
        self.draw_arrow_button(self.BTN_MODE_NEXT, 1)
        mode_label = self.MODE_LABELS.get(
            self.menu_mode, self.menu_mode.upper())
        self.draw_text(mode_label, self.font_small, self.COLOR_TEXT,
                       center=(cx, 312), shadow=False)

        self.draw_text("INICIO", self.font_small, self.COLOR_TEXT_MUTED,
                       topleft=(240, 352), shadow=False)
        self.draw_arrow_button(self.BTN_START_PREV, -1)
        self.draw_arrow_button(self.BTN_START_NEXT, 1)
        start_label = self.START_LABELS.get(
            self.menu_start, self.menu_start.upper())
        self.draw_text(start_label, self.font_small, self.COLOR_TEXT,
                       center=(cx, 364), shadow=False)

        hint = "A/D modo  W/S inicio  <-/-> discos"
        if self.menu_mode == HanoiGame.MODE_TIMED:
            if self.menu_start == HanoiGame.START_STANDARD:
                limit = HanoiGame.time_limit_for(self.menu_disks)
                hint = f"Límite {format_time(limit)}  " + hint
            else:
                hint = "Límite según el inicio  " + hint
        self.draw_text(hint, self.font_small, self.COLOR_TEXT_MUTED,
                       center=(cx, 396), shadow=False)

        self.draw_button(self.BTN_START, "START", self.font_big)

        self.draw_menu_preview()
        sound = "ON" if self.sound_enabled else "OFF"
        self.draw_text(f"Enter: empezar  Esc: salir  M: sonido {sound}",
                       self.font_small, self.COLOR_TEXT_SOFT,
                       center=(cx, 542), shadow=False)

    def draw_menu_preview(self):
        count = self.menu_disks
        width = 36
        gap = 6
        total = count * width + (count - 1) * gap
        x = self.WIDTH // 2 - total // 2
        for size in range(1, count + 1):
            image = self._disk_image(size, count, width)
            self.screen.blit(image, (x, 492))
            x += width + gap

    def draw_background(self):
        if self.img_background:
            self.screen.blit(self.img_background, (0, 0))
        else:
            self.screen.fill(self.COLOR_BG)

    def draw_base(self):
        if self.img_base:
            self.screen.blit(self.img_base, (self.PLATFORM_X, self.PLATFORM_Y))
        else:
            pygame.draw.rect(self.screen, self.COLOR_BASE,
                             pygame.Rect(30, 476, 900, 152))
            pygame.draw.rect(self.screen, self.COLOR_BUTTON_LIGHT,
                             pygame.Rect(30, 476, 900, 24))

        if self._base_shadow is None:
            shadow = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            for i in range(self.NUM_TOWERS):
                cx = self.tower_center_x(i)
                pygame.draw.ellipse(shadow, (30, 16, 20, 70),
                                    (cx - 130, self.BASE_Y - 14, 260, 14))
            self._base_shadow = shadow
        self.screen.blit(self._base_shadow, (0, 0))

    def draw_tower_numbers(self):
        for i in range(self.NUM_TOWERS):
            self.draw_text(str(i + 1), self.font_small, self.COLOR_TEXT_SOFT,
                           center=(self.tower_center_x(i), 532))

    def draw_poles(self):
        for i in range(self.NUM_TOWERS):
            image = (self.img_pole_steel if i == self.NUM_TOWERS - 1
                     else self.img_pole_wood)
            if image:
                x = self.tower_center_x(i) - image.get_width() // 2
                y = self.BASE_Y - image.get_height()
                self.screen.blit(image, (x, y))
                cap = ((220, 230, 235) if i == self.NUM_TOWERS - 1
                       else (255, 220, 160))
                pygame.draw.rect(self.screen, cap,
                                 pygame.Rect(x, y, image.get_width(),
                                             self.POLE_CAP_H))
            else:
                x = self.tower_center_x(i) - self.POLE_WIDTH // 2
                pole = pygame.Rect(x, self.BASE_Y - self.POLE_HEIGHT,
                                   self.POLE_WIDTH, self.POLE_HEIGHT)
                pygame.draw.rect(self.screen, self.COLOR_POLE, pole)

    def draw_disks(self):
        flying = self.anim["dst"] if self.anim else None
        for tower_index, tower in enumerate(self.game.get_state()):
            for level, size in enumerate(tower):
                if tower_index == flying and level == len(tower) - 1:
                    continue  # este disco se dibuja en vuelo (draw_moving_disk)
                self.screen.blit(self.disk_surface(size),
                                 self.disk_pos(tower_index, level, size))

    def draw_moving_disk(self):
        if not self.anim:
            return
        x, y = self.anim_position(self.anim_progress())
        self.screen.blit(self.disk_surface(self.anim["disk"]),
                         (int(round(x)), int(round(y))))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_background()
            self.draw_base()
            self.draw_tower_numbers()
            self.draw_poles()
            self.draw_disks()
            self.draw_selection()
            self.draw_hint()
            self.draw_hud()
            self.draw_history()
            self.draw_moving_disk()
            self.draw_error()
            self.draw_help()
            if self.end_panel_visible():
                self.draw_end_panel()
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(self.FPS)
        finally:
            pygame.quit()


def main():
    gui = HanoiGUI(num_disks=3)
    gui.run()


if __name__ == "__main__":
    main()
