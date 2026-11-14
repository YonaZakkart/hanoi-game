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

    COLOR_PANEL = (24, 14, 52)
    COLOR_BUTTON = (92, 58, 28)
    COLOR_BUTTON_HOVER = (139, 90, 43)
    COLOR_ERROR = (255, 90, 90)
    COLOR_WIN = (255, 220, 60)
    COLOR_LOSE = (255, 120, 100)
    COLOR_BUTTON_DISABLED = (60, 48, 70)
    COLOR_TEXT_DISABLED = (150, 140, 160)

    BTN_MENU = pygame.Rect(70, 540, 200, 52)
    BTN_RETRY = pygame.Rect(380, 540, 200, 52)
    BTN_MINUS = pygame.Rect(300, 270, 64, 64)
    BTN_PLUS = pygame.Rect(596, 270, 64, 64)
    BTN_START = pygame.Rect(380, 430, 200, 64)
    BTN_WIN_RETRY = pygame.Rect(290, 380, 180, 56)
    BTN_WIN_MENU = pygame.Rect(490, 380, 180, 56)
    BTN_UNDO = pygame.Rect(750, 54, 180, 44)

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
                self.handle_key(event.key)
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
        except ValueError as error:
            self.set_error(str(error))

    def try_undo(self):
        self.selected_tower = None
        self.error_message = ""
        try:
            self.game.undo()
        except ValueError as error:
            self.set_error(str(error))

    def update(self):
        if self.state == "playing":
            self.game.update_time()
            if self.game.is_over():
                self.selected_tower = None

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
        self.state = "playing"

    def restart_game(self):
        """RETRY: repite la misma partida (mismo estado inicial, aunque sea mixto)."""
        self.game.reset()
        self.selected_tower = None
        self.error_message = ""
        self.state = "playing"

    def go_to_menu(self):
        self.selected_tower = None
        self.error_message = ""
        self.state = "menu"

    def change_menu_disks(self, delta):
        value = self.menu_disks + delta
        self.menu_disks = max(HanoiGame.MIN_DISKS,
                              min(HanoiGame.MAX_DISKS, value))

    def handle_key(self, key):
        if self.state == "menu":
            if key == pygame.K_ESCAPE:
                self.running = False
            else:
                self.handle_menu_key(key)
        elif key == pygame.K_ESCAPE:
            self.go_to_menu()
        elif key == pygame.K_r:
            self.restart_game()

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
            if self.BTN_WIN_RETRY.collidepoint(pos):
                self.restart_game()
            elif self.BTN_WIN_MENU.collidepoint(pos):
                self.go_to_menu()
            return

        if self.BTN_MENU.collidepoint(pos):
            self.go_to_menu()
        elif self.BTN_RETRY.collidepoint(pos):
            self.restart_game()
        elif self.BTN_UNDO.collidepoint(pos):
            self.try_undo()
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
                       self.COLOR_TEXT, center=(self.WIDTH - 170, 34))
        self.draw_undo_button()

    def draw_undo_button(self):
        rect = self.BTN_UNDO
        left = self.game.get_undo_time_left()
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
            if moves == minimum:
                note = "¡Partida perfecta!"
            else:
                note = f"Te pasaste por {moves - minimum} movimientos"

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
        disk_h = self.DISK_UNITS_H * self.PIXEL
        step = (self.DISK_UNITS_H - 1) * self.PIXEL
        for tower_index, tower in enumerate(self.game.get_state()):
            center_x = self.tower_center_x(tower_index)
            for level, size in enumerate(tower):
                surface = self.disk_surface(size)
                x = center_x - surface.get_width() // 2
                y = self.BASE_Y - disk_h - level * step
                self.screen.blit(surface, (x, y))

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
            self.draw_hud()
            self.draw_error()
            if self.game.is_over():
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