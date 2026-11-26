import math
import os
import pygame
from game.hanoi_game import HanoiGame

ASSETS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))


def load_image(name):
    path = os.path.join(ASSETS_DIR, name)
    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


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
    COLOR_TEXT = (255, 255, 255)
    COLOR_DISK_BORDER = (16, 10, 24)
    COLOR_SELECTION = (255, 220, 60)

    DISK_COLORS = [
        (231, 76, 60),
        (230, 126, 34),
        (241, 196, 15),
        (46, 204, 113),
        (26, 188, 156),
        (52, 152, 219),
        (155, 89, 182),
        (233, 30, 99),
        (121, 85, 72),
        (149, 165, 166),
    ]

    PIXEL = 4

    NUM_TOWERS = 3
    PLATFORM_X = 30
    PLATFORM_Y = 468
    PLATFORM_TOP_H = 40
    BASE_Y = 492
    POLE_HEIGHT = 300
    POLE_WIDTH = 24

    DISK_UNITS_H = 7
    DISK_UNITS_MIN = 12
    DISK_UNITS_MAX = 56

    ERROR_SECONDS = 3
    TIME_WARNING_SECONDS = 10
    HINT_SECONDS = 4
    AUTO_SOLVE_INTERVAL_MS = 400

    # Animación del disco: sube, se desplaza y baja. ANIM_MS = 0 la desactiva.
    ANIM_MS = 300
    ANIM_UP = 0.30
    ANIM_DOWN = 0.30
    ANIM_LIFT_MARGIN = 4

    COLOR_PANEL = (24, 14, 52)
    COLOR_BUTTON = (92, 58, 28)
    COLOR_BUTTON_HOVER = (139, 90, 43)
    COLOR_ERROR = (255, 90, 90)
    COLOR_WIN = (255, 220, 60)
    COLOR_LOSE = (255, 120, 100)
    COLOR_BUTTON_DISABLED = (60, 48, 70)
    COLOR_TEXT_DISABLED = (150, 140, 160)
    COLOR_HINT = (90, 230, 130)

    BTN_MENU = pygame.Rect(70, 540, 200, 52)
    BTN_RETRY = pygame.Rect(380, 540, 200, 52)
    BTN_MINUS = pygame.Rect(300, 270, 64, 64)
    BTN_PLUS = pygame.Rect(596, 270, 64, 64)
    BTN_START = pygame.Rect(380, 430, 200, 64)
    BTN_WIN_RETRY = pygame.Rect(290, 380, 180, 56)
    BTN_WIN_MENU = pygame.Rect(490, 380, 180, 56)
    BTN_UNDO = pygame.Rect(750, 54, 180, 44)
    BTN_HINT = pygame.Rect(750, 104, 180, 34)
    BTN_SOLVE = pygame.Rect(750, 144, 180, 34)

    HISTORY_PANEL = pygame.Rect(320, 6, 300, 180)
    HISTORY_ROWS = 6
    HISTORY_ROW_H = 24

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
        pygame.init()
        pygame.display.set_caption("Torre de Hanói")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.game = HanoiGame(num_disks)
        self.font = pygame.font.SysFont("consolas", 28)
        self.font_big = pygame.font.SysFont("consolas", 52, bold=True)
        self.font_mid = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 20, bold=True)

        self.img_background = load_image("background.png")
        self.img_base = load_image("base.png")
        self.img_pole_wood = load_image("pole_wood.png")
        self.img_pole_steel = load_image("pole_steel.png")

        self._disk_cache = {}

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

        self.state = "menu" if show_menu else "playing"
        self.menu_disks = num_disks
        self.menu_mode = HanoiGame.MODE_NORMAL
        self.menu_start = HanoiGame.START_STANDARD

    def tower_center_x(self, index):
        section = self.WIDTH // self.NUM_TOWERS
        return section * index + section // 2

    def tower_rect(self, index):
        section = self.WIDTH // self.NUM_TOWERS
        top = self.BASE_Y - self.POLE_HEIGHT
        bottom = self.PLATFORM_Y + self.PLATFORM_TOP_H
        return pygame.Rect(section * index, top, section, bottom - top)

    def disk_color(self, size):
        return self.DISK_COLORS[(size - 1) % len(self.DISK_COLORS)]

    def disk_units(self, size):
        biggest = self.game.num_disks
        if biggest <= 1:
            return self.DISK_UNITS_MAX
        step = (self.DISK_UNITS_MAX - self.DISK_UNITS_MIN) / (biggest - 1)
        units = self.DISK_UNITS_MIN + (size - 1) * step
        return int(round(units / 2) * 2)

    def disk_surface(self, size):
        key = (size, self.game.num_disks)
        if key not in self._disk_cache:
            self._disk_cache[key] = self._build_disk(size)
        return self._disk_cache[key]

    def _build_disk(self, size):
        units = self.disk_units(size)
        h = self.DISK_UNITS_H
        base = self.disk_color(size)
        light = tuple(min(255, c + 55) for c in base)
        dark = tuple(int(c * 0.62) for c in base)

        small = pygame.Surface((units, h), pygame.SRCALPHA)
        for y in range(h):
            for x in range(units):
                edge_x = x in (0, units - 1)
                edge_y = y in (0, h - 1)
                if edge_x and edge_y:
                    continue
                if edge_x or edge_y:
                    color = self.COLOR_DISK_BORDER
                elif y == 1:
                    color = light
                elif y >= h - 2:
                    color = dark
                else:
                    color = base
                small.set_at((x, y), color)
        return pygame.transform.scale(
            small, (units * self.PIXEL, h * self.PIXEL))

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
            return
        origin = self.selected_tower
        self.selected_tower = None
        if clicked == origin:
            return
        try:
            self.game.move(origin, clicked)
            self.clear_hint()
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
        self.auto_next = now + self.AUTO_SOLVE_INTERVAL_MS
        if self.game.is_over():
            self.stop_auto_solve()

    def try_undo(self):
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        try:
            self.game.undo()
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

    def disk_pos(self, tower_index, level, size):
        surface = self.disk_surface(size)
        disk_h = self.DISK_UNITS_H * self.PIXEL
        step = (self.DISK_UNITS_H - 1) * self.PIXEL
        x = self.tower_center_x(tower_index) - surface.get_width() // 2
        y = self.BASE_Y - disk_h - level * step
        return x, y

    def start_animation(self, disk, src, dst):
        """Anima `disk` de la torre src a la dst. El estado lógico ya cambió:
        el disco está en la cima de dst y ya no está en src."""
        state = self.game.get_state()
        if not state[dst] or state[dst][-1] != disk:
            self.anim = None
            return
        x0, y0 = self.disk_pos(src, len(state[src]), disk)
        x1, y1 = self.disk_pos(dst, len(state[dst]) - 1, disk)
        lift = (self.BASE_Y - self.POLE_HEIGHT
                - self.DISK_UNITS_H * self.PIXEL - self.ANIM_LIFT_MARGIN)
        self.anim = {
            "disk": disk, "src": src, "dst": dst, "start": self._ticks(),
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "lift": min(lift, y0, y1),
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
            elif self.auto_solving:
                self.auto_solve_step()
            if self.hint and pygame.time.get_ticks() > self.hint_until:
                self.clear_hint()

    def set_error(self, message):
        self.error_message = message
        self.error_until = pygame.time.get_ticks() + self.ERROR_SECONDS * 1000

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
        self.state = "playing"

    def restart_game(self):
        """RETRY: repite la misma partida (mismo estado inicial, aunque sea mixto)."""
        self.game.reset()
        self.selected_tower = None
        self.error_message = ""
        self.clear_hint()
        self.stop_auto_solve()
        self.close_overlays()
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
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_game(self.menu_disks, self.menu_mode)

    def handle_mouse(self, pos):
        if self.state == "menu":
            if self.BTN_MINUS.collidepoint(pos):
                self.change_menu_disks(-1)
            elif self.BTN_PLUS.collidepoint(pos):
                self.change_menu_disks(1)
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
        elif self.BTN_UNDO.collidepoint(pos):
            self.try_undo()
        elif self.BTN_HINT.collidepoint(pos):
            self.try_hint()
        elif self.BTN_SOLVE.collidepoint(pos):
            self.start_auto_solve()
        else:
            self.handle_click(pos)

    def draw_text(self, text, font, color, center=None, topleft=None):
        image = font.render(text, True, color)
        outline = font.render(text, True, self.COLOR_DISK_BORDER)
        rect = image.get_rect()
        if center is not None:
            rect.center = center
        else:
            rect.topleft = topleft
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            self.screen.blit(outline, rect.move(dx, dy))
        self.screen.blit(image, rect)

    def draw_button(self, rect, label, font=None):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        color = self.COLOR_BUTTON_HOVER if hover else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, color, rect)
        border = self.COLOR_SELECTION if hover else self.COLOR_DISK_BORDER
        pygame.draw.rect(self.screen, border, rect, 4)
        self.draw_text(label, font or self.font_mid, self.COLOR_TEXT,
                       center=rect.center)

    def draw_timer(self):
        if self.game.get_mode() == HanoiGame.MODE_TIMED:
            left = self.game.get_time_left()
            color = self.COLOR_TEXT
            if left <= self.TIME_WARNING_SECONDS:
                color = self.COLOR_ERROR
            label = f"RESTA: {format_time(math.ceil(left))}"
        else:
            color = self.COLOR_TEXT
            label = f"TIEMPO: {format_time(self.game.get_elapsed())}"
        self.draw_text(label, self.font_mid, color, topleft=(24, 130))

    def draw_hud(self):
        self.draw_button(self.BTN_MENU, "MENU")
        self.draw_button(self.BTN_RETRY, "RETRY")
        self.draw_text(f"MOVES: {self.game.get_moves()}", self.font_mid,
                       self.COLOR_TEXT, center=(790, 566))
        self.draw_text(f"MIN: {self.game.get_min_moves()}", self.font_mid,
                       self.COLOR_TEXT, topleft=(24, 20))
        self.draw_text(f"DISCOS: {self.game.num_disks}", self.font_small,
                       self.COLOR_TEXT, topleft=(24, 62))
        mode_label = self.MODE_LABELS.get(
            self.game.get_mode(), self.game.get_mode().upper())
        self.draw_text(f"MODO: {mode_label}", self.font_small,
                       self.COLOR_TEXT, topleft=(24, 96))
        self.draw_timer()
        start_label = self.START_LABELS.get(
            self.game.get_start(), self.game.get_start().upper())
        self.draw_text(f"INICIO: {start_label}", self.font_small,
                       self.COLOR_TEXT, topleft=(24, 168))
        self.draw_text("Esc: menú | R: reintentar", self.font_small,
                       self.COLOR_TEXT, center=(self.WIDTH - 170, 18))
        self.draw_text("F1: atajos | L: historial", self.font_small,
                       self.COLOR_TEXT, center=(self.WIDTH - 170, 38))
        self.draw_undo_button()
        self.draw_assist_buttons()

    def draw_history(self):
        if not self.show_history:
            return
        history = self.game.get_history()
        total = len(history)
        panel = self.HISTORY_PANEL
        pygame.draw.rect(self.screen, self.COLOR_PANEL, panel)
        pygame.draw.rect(self.screen, self.COLOR_SELECTION, panel, 3)
        self.draw_text(f"HISTORIAL ({total}) [L]", self.font_small,
                       self.COLOR_SELECTION, topleft=(panel.x + 12, panel.y + 6))
        top = panel.y + 34
        if total == 0:
            self.draw_text("Sin movimientos", self.font_small,
                           self.COLOR_TEXT_DISABLED, topleft=(panel.x + 12, top))
            return
        end = total - self.history_scroll
        start = max(0, end - self.HISTORY_ROWS)
        for row, entry in enumerate(history[start:end]):
            number, origin, destination, disk, _elapsed = entry
            color = self.COLOR_SELECTION if start + row == total - 1 else self.COLOR_TEXT
            text = f"{number:>3}. {origin + 1}->{destination + 1} (disco {disk})"
            self.draw_text(text, self.font_small, color,
                           topleft=(panel.x + 12, top + row * self.HISTORY_ROW_H))
        if total > self.HISTORY_ROWS:
            track = pygame.Rect(panel.right - 14, top,
                                6, self.HISTORY_ROWS * self.HISTORY_ROW_H - 4)
            pygame.draw.rect(self.screen, self.COLOR_BUTTON_DISABLED, track)
            thumb_h = max(14, track.height * self.HISTORY_ROWS // total)
            max_scroll = total - self.HISTORY_ROWS
            fraction = 1 - self.history_scroll / max_scroll
            thumb_y = track.y + int((track.height - thumb_h) * fraction)
            pygame.draw.rect(self.screen, self.COLOR_SELECTION,
                             pygame.Rect(track.x, thumb_y, track.width, thumb_h))

    def draw_help(self):
        if not self.show_help:
            return
        veil = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        self.screen.blit(veil, (0, 0))

        key_w = max(self.font_small.size(k)[0] for k, _ in self.SHORTCUTS)
        desc_w = max(self.font_small.size(d)[0] for _, d in self.SHORTCUTS)
        row_h = 30
        width = 30 + key_w + 30 + desc_w + 30
        height = 70 + len(self.SHORTCUTS) * row_h + 40
        panel = pygame.Rect(0, 0, width, height)
        panel.center = (self.WIDTH // 2, self.HEIGHT // 2)
        pygame.draw.rect(self.screen, self.COLOR_PANEL, panel)
        pygame.draw.rect(self.screen, self.COLOR_SELECTION, panel, 4)
        self.draw_text("ATAJOS DE TECLADO", self.font_mid, self.COLOR_WIN,
                       center=(panel.centerx, panel.y + 36))
        for row, (keys, action) in enumerate(self.SHORTCUTS):
            y = panel.y + 70 + row * row_h
            self.draw_text(keys, self.font_small, self.COLOR_SELECTION,
                           topleft=(panel.x + 30, y))
            self.draw_text(action, self.font_small, self.COLOR_TEXT,
                           topleft=(panel.x + 30 + key_w + 30, y))
        self.draw_text("Cualquier tecla o clic cierra la ayuda",
                       self.font_small, self.COLOR_TEXT_DISABLED,
                       center=(panel.centerx, panel.bottom - 24))

    def draw_disabled_button(self, rect, label, font=None):
        pygame.draw.rect(self.screen, self.COLOR_BUTTON_DISABLED, rect)
        pygame.draw.rect(self.screen, self.COLOR_DISK_BORDER, rect, 4)
        self.draw_text(label, font or self.font_small,
                       self.COLOR_TEXT_DISABLED, center=rect.center)

    def draw_assist_buttons(self):
        if self.auto_solving:
            self.draw_disabled_button(self.BTN_HINT, "PISTA (H)")
            self.draw_button(self.BTN_SOLVE, "PARAR (clic)", self.font_small)
        else:
            self.draw_button(self.BTN_HINT, "PISTA (H)", self.font_small)
            self.draw_button(self.BTN_SOLVE, "RESOLVER (X)", self.font_small)

    def draw_hint(self):
        if not self.hint:
            return
        origin, destination = self.hint
        for index, label in ((origin, "ORIGEN"), (destination, "DESTINO")):
            rect = self.tower_rect(index)
            pygame.draw.rect(self.screen, self.COLOR_HINT,
                             rect.inflate(-10, -10), 4)
            self.draw_text(label, self.font_small, self.COLOR_HINT,
                           center=(rect.centerx, rect.top + 20))

    def draw_undo_button(self):
        rect = self.BTN_UNDO
        left = 0 if self.auto_solving else self.game.get_undo_time_left()
        if left > 0:
            self.draw_button(rect, f"DESHACER ({math.ceil(left)}s)",
                             self.font_small)
            fraction = left / HanoiGame.UNDO_WINDOW
            bar = pygame.Rect(rect.x + 10, rect.bottom - 12,
                              int((rect.width - 20) * fraction), 6)
            pygame.draw.rect(self.screen, self.COLOR_SELECTION, bar)
        else:
            pygame.draw.rect(self.screen, self.COLOR_BUTTON_DISABLED, rect)
            pygame.draw.rect(self.screen, self.COLOR_DISK_BORDER, rect, 4)
            self.draw_text("DESHACER", self.font_small,
                           self.COLOR_TEXT_DISABLED, center=rect.center)

    def draw_error(self):
        if not self.error_message:
            return
        if pygame.time.get_ticks() > self.error_until:
            self.error_message = ""
            return
        text = self.font_small.render(
            self.error_message, True, self.COLOR_ERROR)
        box = text.get_rect(center=(self.WIDTH // 2, 112)).inflate(40, 20)
        pygame.draw.rect(self.screen, self.COLOR_PANEL, box)
        pygame.draw.rect(self.screen, self.COLOR_ERROR, box, 3)
        self.screen.blit(text, text.get_rect(center=box.center))

    def draw_end_panel(self):
        veil = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        self.screen.blit(veil, (0, 0))

        panel = pygame.Rect(240, 130, 480, 330)
        pygame.draw.rect(self.screen, self.COLOR_PANEL, panel)

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

        pygame.draw.rect(self.screen, border_color, panel, 4)
        self.draw_text(title, self.font_big, title_color, center=(cx, 180))
        self.draw_text(f"Movimientos: {moves}", self.font_mid, self.COLOR_TEXT,
                       center=(cx, 240))
        self.draw_text(f"Mínimo: {minimum}", self.font_mid, self.COLOR_TEXT,
                       center=(cx, 277))
        self.draw_text(f"Tiempo: {format_time(elapsed)}", self.font_mid,
                       self.COLOR_TEXT, center=(cx, 314))
        self.draw_text(note, self.font_small, title_color, center=(cx, 352))
        self.draw_button(self.BTN_WIN_RETRY, "RETRY")
        self.draw_button(self.BTN_WIN_MENU, "MENU")

    def draw_menu(self):
        self.draw_background()
        self.draw_base()
        self.draw_poles()

        panel = pygame.Rect(180, 60, 600, 460)
        pygame.draw.rect(self.screen, self.COLOR_PANEL, panel)
        pygame.draw.rect(self.screen, self.COLOR_SELECTION, panel, 4)

        cx = self.WIDTH // 2
        self.draw_text("TORRE DE HANÓI", self.font_big, self.COLOR_WIN,
                       center=(cx, 110))

        self.draw_text("Número de discos", self.font_mid, self.COLOR_TEXT,
                       center=(cx, 190))
        self.draw_button(self.BTN_MINUS, "-")
        self.draw_button(self.BTN_PLUS, "+")
        self.draw_text(str(self.menu_disks), self.font_big, self.COLOR_TEXT,
                       center=(cx, 302))

        mode_label = self.MODE_LABELS.get(
            self.menu_mode, self.menu_mode.upper())
        mode_text = f"MODO: {mode_label}"
        if self.menu_mode == HanoiGame.MODE_TIMED:
            if self.menu_start == HanoiGame.START_STANDARD:
                limit = HanoiGame.time_limit_for(self.menu_disks)
                mode_text = f"MODO: {mode_label} ({format_time(limit)})"
            else:
                # con inicio mixto el límite depende del estado que salga
                mode_text = f"MODO: {mode_label} (según inicio)"
        self.draw_text(mode_text, self.font, self.COLOR_TEXT,
                       center=(cx, 350))
        start_label = self.START_LABELS.get(
            self.menu_start, self.menu_start.upper())
        self.draw_text(f"INICIO: {start_label}", self.font, self.COLOR_TEXT,
                       center=(cx, 380))
        self.draw_text("A/D: modo | W/S: inicio", self.font_small,
                       self.COLOR_TEXT, center=(cx, 408))

        self.draw_button(self.BTN_START, "START")
        self.draw_text(
            "Flechas: discos | Enter: empezar | Esc: salir",
            self.font_small, self.COLOR_TEXT, center=(cx, 500))

    def draw_background(self):
        if self.img_background:
            self.screen.blit(self.img_background, (0, 0))
        else:
            self.screen.fill(self.COLOR_BG)

    def draw_base(self):
        if self.img_base:
            self.screen.blit(self.img_base, (self.PLATFORM_X, self.PLATFORM_Y))
            return
        for i in range(self.NUM_TOWERS):
            x = self.tower_center_x(i) - 140
            pygame.draw.rect(self.screen, self.COLOR_BASE,
                             pygame.Rect(x, self.BASE_Y, 280, 24))

    def draw_poles(self):
        for i in range(self.NUM_TOWERS):
            image = self.img_pole_steel if i == self.NUM_TOWERS - 1 else self.img_pole_wood
            if image:
                x = self.tower_center_x(i) - image.get_width() // 2
                y = self.BASE_Y - image.get_height()
                self.screen.blit(image, (x, y))
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

    def draw_selection(self):
        if self.selected_tower is None:
            return
        rect = self.tower_rect(self.selected_tower)
        pygame.draw.rect(self.screen, self.COLOR_SELECTION, rect, 4)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_background()
            self.draw_base()
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