"""Pruebas del Punto 3.8: tema visual con sprites de disco.

Ejecutar desde la raíz del proyecto:  python -m unittest tests.test_tema -v
"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pygame
    from ui.gui import DISK_ASSETS, HanoiGUI, hue_shift, tint_surface
except ImportError:
    pygame = None


@unittest.skipIf(pygame is None, "pygame no está instalado")
class SpritesTest(unittest.TestCase):
    def setUp(self):
        self.gui = HanoiGUI(num_disks=10, show_menu=False)

    def tearDown(self):
        pygame.quit()

    def test_se_cargan_los_ocho_sprites(self):
        self.assertEqual(len(self.gui.disk_sprites), len(DISK_ASSETS))
        for sprite in self.gui.disk_sprites:
            # ya están en su rejilla nativa, no en los 1024x1024 originales
            self.assertLess(sprite.get_width(), 60)
            self.assertLess(sprite.get_height(), 45)
            self.assertGreater(sprite.get_width(), 20)
            self.assertGreater(sprite.get_height(), 15)

    def test_anchos_proporcionales_al_tamano(self):
        widths = [self.gui.disk_width(size) for size in range(1, 11)]
        self.assertEqual(widths[0], self.gui.DISK_MIN_W)
        self.assertEqual(widths[-1], self.gui.DISK_MAX_W)
        self.assertEqual(widths, sorted(widths))
        self.assertEqual(len(set(widths)), len(widths))

    def test_paleta_repartida_entre_los_discos(self):
        for count in (2, 3, 5, 10):
            tints = [self.gui.disk_tint(size, count)
                     for size in range(1, count + 1)]
            self.assertEqual(len(set(tints)), count)
        self.assertEqual(self.gui.disk_tint(1, 10), self.gui.DISK_TINTS[0])
        self.assertEqual(self.gui.disk_tint(10, 10), self.gui.DISK_TINTS[-1])

    def test_disk_surface_usa_el_sprite_y_la_cache(self):
        surface = self.gui.disk_surface(1)
        self.assertIs(surface, self.gui.disk_surface(1))
        self.assertEqual(surface.get_width(), self.gui.disk_width(1))
        # el sprite se aplana lo justo para que el apilado respire
        self.assertGreater(surface.get_height(), self.gui.DISK_STEP)
        self.assertLess(surface.get_height(), surface.get_width() / 2)

    def test_ranura_del_palo_en_los_sprites(self):
        for sprite in self.gui.disk_sprites:
            width, height = sprite.get_size()
            left = width // 2 - 2
            hole_y = max(1, int(round(height * 0.32)))
            for y in range(hole_y + 1):
                for x in range(left, left + 4):
                    self.assertEqual(sprite.get_at((x, y)).a, 0)
            # los píxeles a los lados de la ranura siguen opacos
            self.assertEqual(sprite.get_at((left - 1, hole_y)).a, 255)
            self.assertEqual(sprite.get_at((left + 4, hole_y)).a, 255)

    def test_el_apilado_de_diez_cabe_bajo_el_palo(self):
        gui = HanoiGUI(num_disks=10, show_menu=False)
        try:
            top_y = gui.disk_pos(0, 9, 1)[1]
            pole_top = gui.BASE_Y - gui.POLE_HEIGHT
            self.assertGreaterEqual(top_y, pole_top)
            self.assertGreaterEqual(top_y, gui.HUD_RECT.bottom)
            # el palo asoma por encima del último disco
            self.assertGreater(top_y, pole_top)
        finally:
            pygame.quit()

    def test_apilado_con_el_paso_nuevo(self):
        x0, y0 = self.gui.disk_pos(0, 0, 10)
        x1, y1 = self.gui.disk_pos(0, 1, 10)
        self.assertEqual(x0, x1)
        self.assertEqual(y0 - y1, self.gui.DISK_STEP)
        self.assertEqual(
            x0 + self.gui.disk_surface(10).get_width() // 2,
            self.gui.tower_center_x(0))

    def test_tintado_conserva_transparencia_y_cambia_color(self):
        sprite = self.gui.disk_sprites[0]
        tinted = tint_surface(sprite, 60)
        transparent_before = 0
        changed = 0
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                before = sprite.get_at((x, y))
                after = tinted.get_at((x, y))
                if before.a == 0:
                    transparent_before += 1
                    self.assertEqual(after.a, 0)
                elif before.r != before.g or before.g != before.b:
                    if (before.r, before.g, before.b) != (
                            after.r, after.g, after.b):
                        changed += 1
        self.assertGreater(transparent_before, 0)
        self.assertGreater(changed, 0)
        self.assertEqual(hue_shift((255, 143, 0), 0), (255, 143, 0, 255))

    def test_hud_y_torres_no_se_pisan(self):
        self.assertGreater(self.gui.tower_rect(0).top,
                           self.gui.HUD_RECT.bottom)
        self.assertLessEqual(self.gui.tower_rect(2).right, self.gui.WIDTH)
        self.assertGreaterEqual(self.gui.tower_rect(0).left, 0)

    def test_botones_inferiores_sin_solapes(self):
        rects = (self.gui.BTN_MENU, self.gui.BTN_RETRY, self.gui.BTN_HISTORY,
                 self.gui.BTN_UNDO, self.gui.BTN_HINT, self.gui.BTN_SOLVE)
        for i, rect in enumerate(rects):
            self.assertGreaterEqual(rect.left, 0)
            self.assertLessEqual(rect.right, self.gui.WIDTH)
            for other in rects[i + 1:]:
                self.assertFalse(rect.colliderect(other))


@unittest.skipIf(pygame is None, "pygame no está instalado")
class PantallasTest(unittest.TestCase):
    def setUp(self):
        self.gui = HanoiGUI(num_disks=6, show_menu=False)

    def tearDown(self):
        pygame.quit()

    def test_menú_clickable_cambia_modo_e_inicio(self):
        gui = HanoiGUI(num_disks=4, show_menu=True)
        try:
            gui.handle_mouse(gui.BTN_MODE_NEXT.center)
            self.assertEqual(gui.menu_mode, "perfect")
            gui.handle_mouse(gui.BTN_MODE_PREV.center)
            self.assertEqual(gui.menu_mode, "normal")
            gui.handle_mouse(gui.BTN_START_NEXT.center)
            self.assertEqual(gui.menu_start, "mixed")
            gui.handle_mouse(gui.BTN_START_PREV.center)
            self.assertEqual(gui.menu_start, "standard")
            gui.handle_mouse(gui.BTN_PLUS.center)
            self.assertEqual(gui.menu_disks, 5)
            gui.handle_mouse(gui.BTN_MINUS.center)
            self.assertEqual(gui.menu_disks, 4)
        finally:
            pygame.quit()

    def test_m_silencia_sonido(self):
        self.assertTrue(self.gui.sound_enabled)
        self.gui.handle_key(pygame.K_m)
        self.assertFalse(self.gui.sound_enabled)
        self.gui.handle_key(pygame.K_m)
        self.assertTrue(self.gui.sound_enabled)

    def test_mientras_la_ayuda_esta_abierta_m_no_cambia_el_sonido(self):
        self.gui.handle_key(pygame.K_F1)
        self.assertTrue(self.gui.show_help)
        self.gui.handle_key(pygame.K_m)
        self.assertFalse(self.gui.show_help)
        self.assertTrue(self.gui.sound_enabled)

    def test_dibujo_de_todas_las_pantallas(self):
        self.gui.draw()
        self.gui.handle_key(pygame.K_l)
        self.gui.draw()
        self.gui.handle_key(pygame.K_F1)
        self.gui.draw()
        self.gui.show_help = False
        self.gui.set_error("Error de prueba")
        self.gui.draw()
        while not self.gui.game.is_over():
            self.gui.game.auto_step()
        self.gui.anim = None
        self.gui.draw()
        self.gui.state = "menu"
        self.gui.draw()

    def test_preview_del_menu_con_todos_los_discos(self):
        gui = HanoiGUI(num_disks=10, show_menu=True)
        try:
            gui.draw()
            self.assertEqual(len(gui.disk_sprites), len(DISK_ASSETS))
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
