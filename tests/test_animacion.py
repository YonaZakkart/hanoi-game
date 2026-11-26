"""Pruebas del Punto 3.7: animación del movimiento de discos (solo GUI).

Ejecutar desde la raíz del proyecto:  python -m unittest tests.test_animacion -v
"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pygame
    from ui.gui import HanoiGUI
except ImportError:
    pygame = None


@unittest.skipIf(pygame is None, "pygame no está instalado")
class AnimacionTest(unittest.TestCase):
    def setUp(self):
        self.now = 10_000
        self.gui = HanoiGUI(num_disks=3, show_menu=False)
        self.gui._ticks = lambda: self.now

    def tearDown(self):
        pygame.quit()

    def move(self, a, b):
        self.gui.select_tower(a)
        self.gui.select_tower(b)
        self.gui.update()

    def test_sin_animacion_al_empezar(self):
        self.gui.update()
        self.assertFalse(self.gui.animating())

    def test_un_movimiento_inicia_la_animacion(self):
        self.move(0, 2)
        anim = self.gui.anim
        self.assertIsNotNone(anim)
        self.assertEqual((anim["disk"], anim["src"], anim["dst"]), (1, 0, 2))

    def test_termina_tras_anim_ms(self):
        self.move(0, 2)
        self.now += self.gui.ANIM_MS - 1
        self.gui.update()
        self.assertTrue(self.gui.animating())
        self.now += 1
        self.gui.update()
        self.assertFalse(self.gui.animating())

    def test_extremos_y_altura_de_la_trayectoria(self):
        self.move(0, 2)
        a = self.gui.anim
        self.assertEqual(self.gui.anim_position(0.0), (a["x0"], a["y0"]))
        x, y = self.gui.anim_position(1.0)
        self.assertAlmostEqual(x, a["x1"])
        self.assertAlmostEqual(y, a["y1"])
        # a mitad de camino va a la altura de elevación, entre las dos torres
        x, y = self.gui.anim_position(0.5)
        self.assertEqual(y, a["lift"])
        self.assertTrue(min(a["x0"], a["x1"]) < x < max(a["x0"], a["x1"]))
        # nunca baja del punto de salida ni del de llegada hacia abajo de la pista
        for i in range(101):
            _, y = self.gui.anim_position(i / 100)
            self.assertGreaterEqual(y, a["lift"])
            self.assertLessEqual(y, max(a["y0"], a["y1"]))

    def test_la_elevacion_libera_la_punta_del_palo(self):
        self.move(0, 2)
        pole_top = self.gui.BASE_Y - self.gui.POLE_HEIGHT
        disk_h = self.gui.DISK_UNITS_H * self.gui.PIXEL
        self.assertLessEqual(self.gui.anim["lift"] + disk_h, pole_top)

    def test_disco_en_vuelo_no_se_dibuja_en_su_torre(self):
        self.move(0, 2)
        blits = []
        real = self.gui.screen
        self.gui.screen = _Spy(real, blits)
        self.gui.draw_disks()
        self.gui.screen = real
        # 3 discos en total, uno en vuelo -> solo 2 dibujados
        self.assertEqual(len(blits), 2)

    def test_deshacer_anima_en_sentido_contrario(self):
        self.move(0, 2)
        self.now += self.gui.ANIM_MS
        self.gui.update()
        self.gui.try_undo()
        self.gui.update()
        anim = self.gui.anim
        self.assertIsNotNone(anim)
        self.assertEqual((anim["disk"], anim["src"], anim["dst"]), (1, 2, 0))
        self.assertEqual(self.gui.game.get_state()[0], [3, 2, 1])

    def test_varios_cambios_a_la_vez_no_se_animan(self):
        for _ in range(3):
            self.gui.game.auto_step()
        self.gui.update()
        self.assertFalse(self.gui.animating())

    def test_movimiento_nuevo_reemplaza_la_animacion(self):
        self.move(0, 2)
        self.now += 100
        self.move(0, 1)
        self.assertEqual((self.gui.anim["disk"], self.gui.anim["dst"]), (2, 1))
        self.assertEqual(self.gui.anim["start"], self.now)

    def test_auto_resolver_anima_cada_paso(self):
        self.gui.game.auto_step()
        self.gui.update()
        self.assertTrue(self.gui.animating())
        self.assertLess(self.gui.ANIM_MS, self.gui.AUTO_SOLVE_INTERVAL_MS)

    def test_reiniciar_no_deja_animacion_ni_falsa_animacion(self):
        self.move(0, 2)
        self.gui.restart_game()
        self.assertFalse(self.gui.animating())
        self.gui.update()
        self.assertFalse(self.gui.animating())

    def test_partida_nueva_y_menu_cortan_la_animacion(self):
        self.move(0, 2)
        self.gui.new_puzzle()
        self.gui.update()
        self.assertFalse(self.gui.animating())
        self.move(0, 2)
        self.gui.go_to_menu()
        self.assertFalse(self.gui.animating())
        self.gui.start_game(3)
        self.gui.update()
        self.assertFalse(self.gui.animating())

    def test_anim_ms_cero_desactiva(self):
        self.gui.ANIM_MS = 0
        self.move(0, 2)
        self.assertFalse(self.gui.animating())

    def test_panel_final_espera_a_la_ultima_animacion(self):
        game = self.gui.game
        while len(game.get_solution()) > 1:
            game.auto_step()
        self.gui.update()
        self.gui.game.auto_step()           # último movimiento
        self.gui.update()
        self.assertTrue(game.is_over())
        self.assertTrue(self.gui.animating())
        self.assertFalse(self.gui.end_panel_visible())
        # los botones del panel no responden mientras tanto
        self.gui.handle_mouse(self.gui.BTN_WIN_RETRY.center)
        self.assertTrue(game.is_over())
        self.now += self.gui.ANIM_MS
        self.gui.update()
        self.assertTrue(self.gui.end_panel_visible())

    def test_dibujo_en_todas_las_fases(self):
        self.gui.handle_key(pygame.K_l)
        self.move(0, 2)
        for ms in (0, 50, 90, 150, 210, 270, 299):
            self.now = self.gui.anim["start"] + ms if self.gui.anim else self.now
            self.gui.draw()

    def test_mixto_y_diez_discos(self):
        self.gui.start_game(10, start="mixed")
        self.gui._ticks = lambda: self.now
        self.gui.game.auto_step()
        self.gui.update()
        self.assertTrue(self.gui.animating())
        for i in range(0, 101, 10):
            self.gui.anim_position(i / 100)
        self.gui.draw()


class _Spy:
    """Cuenta los blits sin dibujar de verdad."""
    def __init__(self, real, log):
        self._real, self._log = real, log

    def blit(self, surface, pos, *a, **k):
        self._log.append(pos)

    def __getattr__(self, name):
        return getattr(self._real, name)


if __name__ == "__main__":
    unittest.main()