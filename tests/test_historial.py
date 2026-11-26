"""Pruebas del Punto 3.6: historial de movimientos y atajos de teclado.

Ejecutar desde la raíz del proyecto:  python -m unittest tests.test_historial -v
"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.hanoi_game import HanoiGame

try:
    import pygame
    from ui.gui import HanoiGUI
except ImportError:  # sin pygame solo se prueba la lógica
    pygame = None


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class HistorialLogicaTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.game = HanoiGame(3, clock=self.clock)

    def test_empieza_vacio(self):
        self.assertEqual(self.game.get_history(), [])
        self.assertEqual(self.game.get_history_len(), 0)

    def test_registra_cada_movimiento(self):
        self.game.move(0, 2)
        self.clock.advance(2)
        self.game.move(0, 1)
        history = self.game.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0][:4], (1, 0, 2, 1))   # n, origen, destino, disco
        self.assertEqual(history[1][:4], (2, 0, 1, 2))
        self.assertAlmostEqual(history[0][4], 0.0)
        self.assertAlmostEqual(history[1][4], 2.0)

    def test_movimiento_invalido_no_se_registra(self):
        self.game.move(0, 2)
        with self.assertRaises(ValueError):
            self.game.move(0, 2)   # disco 2 sobre disco 1
        self.assertEqual(self.game.get_history_len(), 1)

    def test_deshacer_quita_la_ultima_entrada(self):
        self.game.move(0, 2)
        self.game.move(0, 1)
        self.game.undo()
        history = self.game.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][0], 1)
        self.assertEqual(self.game.get_moves(), 1)

    def test_deshacer_y_mover_mantiene_numeracion(self):
        self.game.move(0, 2)
        self.game.undo()
        self.game.move(0, 1)
        history = self.game.get_history()
        self.assertEqual([h[0] for h in history], [1])
        self.assertEqual(history[0][1:4], (0, 1, 1))

    def test_reset_vacia_el_historial(self):
        self.game.move(0, 2)
        self.game.reset()
        self.assertEqual(self.game.get_history(), [])

    def test_auto_step_registra(self):
        for _ in range(3):
            self.game.auto_step()
        self.assertEqual(self.game.get_history_len(), 3)
        self.assertEqual([h[0] for h in self.game.get_history()], [1, 2, 3])

    def test_solucion_completa_registra_el_minimo(self):
        while not self.game.is_over():
            self.game.auto_step()
        self.assertEqual(self.game.get_history_len(), self.game.get_min_moves())
        self.assertEqual(self.game.get_history_len(), self.game.get_moves())

    def test_get_history_devuelve_copia(self):
        self.game.move(0, 2)
        copy = self.game.get_history()
        copy.clear()
        copy.append("basura")
        self.assertEqual(self.game.get_history_len(), 1)
        self.assertEqual(self.game.get_history()[0][0], 1)

    def test_historial_con_inicio_mixto_y_perfecto(self):
        game = HanoiGame(4, mode=HanoiGame.MODE_PERFECT, clock=self.clock,
                         start=HanoiGame.START_MIXED, seed=3)
        game.auto_step()
        self.assertEqual(game.get_history_len(), 1)
        game.undo()
        self.assertEqual(game.get_history_len(), 0)


@unittest.skipIf(pygame is None, "pygame no está instalado")
class AtajosGUITest(unittest.TestCase):
    def setUp(self):
        self.gui = HanoiGUI(num_disks=3, show_menu=False)

    def tearDown(self):
        pygame.quit()

    def press(self, key, mod=0):
        self.gui.handle_key(key, mod)

    def test_teclas_123_mueven_un_disco(self):
        self.press(pygame.K_1)
        self.assertEqual(self.gui.selected_tower, 0)
        self.press(pygame.K_3)
        self.assertIsNone(self.gui.selected_tower)
        self.assertEqual(self.gui.game.get_moves(), 1)
        self.assertEqual(self.gui.game.get_state()[2], [1])

    def test_teclado_numerico(self):
        self.press(pygame.K_KP1)
        self.press(pygame.K_KP2)
        self.assertEqual(self.gui.game.get_state()[1], [1])

    def test_misma_torre_cancela_seleccion(self):
        self.press(pygame.K_1)
        self.press(pygame.K_1)
        self.assertIsNone(self.gui.selected_tower)
        self.assertEqual(self.gui.game.get_moves(), 0)

    def test_origen_vacio_muestra_error(self):
        self.press(pygame.K_2)
        self.assertIsNone(self.gui.selected_tower)
        self.assertTrue(self.gui.error_message)

    def test_movimiento_ilegal_muestra_error(self):
        self.press(pygame.K_1); self.press(pygame.K_3)
        self.press(pygame.K_1); self.press(pygame.K_3)
        self.assertEqual(self.gui.game.get_moves(), 1)
        self.assertTrue(self.gui.error_message)

    def test_clic_y_teclado_comparten_flujo(self):
        pos = self.gui.tower_rect(0).center
        self.gui.handle_click(pos)
        self.assertEqual(self.gui.selected_tower, 0)
        self.press(pygame.K_2)
        self.assertEqual(self.gui.game.get_state()[1], [1])

    def test_u_deshace(self):
        self.press(pygame.K_1); self.press(pygame.K_2)
        self.press(pygame.K_u)
        self.assertEqual(self.gui.game.get_moves(), 0)
        self.assertEqual(self.gui.game.get_history_len(), 0)

    def test_ctrl_z_deshace_y_z_solo_no(self):
        self.press(pygame.K_1); self.press(pygame.K_2)
        self.press(pygame.K_z)
        self.assertEqual(self.gui.game.get_moves(), 1)
        self.press(pygame.K_z, pygame.KMOD_CTRL)
        self.assertEqual(self.gui.game.get_moves(), 0)

    def test_ctrl_z_por_eventos_reales(self):
        self.press(pygame.K_1); self.press(pygame.K_2)
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_LCTRL))
        self.gui.handle_events()
        self.assertEqual(self.gui.game.get_moves(), 0)

    def test_l_muestra_y_oculta_historial(self):
        self.assertFalse(self.gui.show_history)
        self.press(pygame.K_l)
        self.assertTrue(self.gui.show_history)
        self.press(pygame.K_l)
        self.assertFalse(self.gui.show_history)

    def test_rueda_solo_con_panel_visible_y_con_limites(self):
        gui = HanoiGUI(num_disks=5, show_menu=False)
        for _ in range(12):
            gui.game.auto_step()
        gui.scroll_history(3)
        self.assertEqual(gui.history_scroll, 0)       # panel oculto
        gui.handle_key(pygame.K_l)
        gui.scroll_history(3)
        self.assertEqual(gui.history_scroll, 3)
        gui.scroll_history(100)
        self.assertEqual(gui.history_scroll, 12 - gui.HISTORY_ROWS)
        gui.scroll_history(-100)
        self.assertEqual(gui.history_scroll, 0)

    def test_rueda_por_evento_real(self):
        gui = HanoiGUI(num_disks=5, show_menu=False)
        for _ in range(10):
            gui.game.auto_step()
        gui.handle_key(pygame.K_l)
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=2))
        gui.handle_events()
        self.assertEqual(gui.history_scroll, 2)

    def test_movimiento_nuevo_vuelve_al_final(self):
        gui = HanoiGUI(num_disks=5, show_menu=False)
        for _ in range(10):
            gui.game.auto_step()
        gui.handle_key(pygame.K_l)
        gui.update()
        gui.scroll_history(2)
        gui.game.auto_step()
        gui.update()
        self.assertEqual(gui.history_scroll, 0)

    def test_n_crea_puzzle_nuevo_con_mismos_ajustes(self):
        gui = HanoiGUI(num_disks=3, show_menu=False)
        gui.start_game(4, HanoiGame.MODE_PERFECT, HanoiGame.START_MIXED)
        gui.handle_key(pygame.K_1)
        gui.game.auto_step()
        gui.handle_key(pygame.K_n)
        self.assertEqual(gui.game.num_disks, 4)
        self.assertEqual(gui.game.get_mode(), HanoiGame.MODE_PERFECT)
        self.assertEqual(gui.game.get_start(), HanoiGame.START_MIXED)
        self.assertEqual(gui.game.get_moves(), 0)
        self.assertEqual(gui.game.get_history_len(), 0)

    def test_r_vacia_historial(self):
        self.press(pygame.K_1); self.press(pygame.K_2)
        self.press(pygame.K_r)
        self.assertEqual(self.gui.game.get_history_len(), 0)

    def test_f1_abre_y_cualquier_tecla_cierra_sin_accion(self):
        self.press(pygame.K_F1)
        self.assertTrue(self.gui.show_help)
        self.press(pygame.K_1)
        self.assertFalse(self.gui.show_help)
        self.assertIsNone(self.gui.selected_tower)

    def test_esc_cierra_ayuda_sin_ir_al_menu(self):
        self.press(pygame.K_F1)
        self.press(pygame.K_ESCAPE)
        self.assertFalse(self.gui.show_help)
        self.assertEqual(self.gui.state, "playing")

    def test_clic_cierra_ayuda(self):
        self.press(pygame.K_F1)
        self.gui.handle_mouse(self.gui.tower_rect(0).center)
        self.assertFalse(self.gui.show_help)
        self.assertIsNone(self.gui.selected_tower)

    def test_auto_resolver_cancela_sin_ejecutar_atajo(self):
        self.gui.start_auto_solve()
        self.assertTrue(self.gui.auto_solving)
        self.press(pygame.K_l)
        self.assertFalse(self.gui.auto_solving)
        self.assertFalse(self.gui.show_history)

    def test_atajos_ignorados_en_el_menu(self):
        gui = HanoiGUI(num_disks=3, show_menu=True)
        for key in (pygame.K_1, pygame.K_u, pygame.K_l, pygame.K_n, pygame.K_F1):
            gui.handle_key(key)
        self.assertEqual(gui.state, "menu")
        self.assertFalse(gui.show_history)
        self.assertFalse(gui.show_help)
        self.assertEqual(gui.game.get_moves(), 0)

    def test_atajos_ignorados_al_terminar(self):
        while not self.gui.game.is_over():
            self.gui.game.auto_step()
        moves = self.gui.game.get_moves()
        for key in (pygame.K_1, pygame.K_u, pygame.K_l, pygame.K_n, pygame.K_F1):
            self.gui.handle_key(key)
        self.assertEqual(self.gui.game.get_moves(), moves)
        self.assertFalse(self.gui.show_history)
        self.assertFalse(self.gui.show_help)

    def test_atajos_previos_siguen_funcionando(self):
        self.press(pygame.K_h)
        self.assertIsNotNone(self.gui.hint)
        self.press(pygame.K_x)
        self.assertTrue(self.gui.auto_solving)
        self.press(pygame.K_x)               # cancela
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.gui.state, "menu")

    def test_dibujo_con_paneles_no_falla(self):
        gui = HanoiGUI(num_disks=6, show_menu=False)
        gui.draw()
        gui.handle_key(pygame.K_l); gui.draw()           # historial vacío
        for _ in range(9):
            gui.game.auto_step()
        gui.update(); gui.draw()                          # con filas y barra
        gui.scroll_history(2); gui.draw()
        gui.handle_key(pygame.K_F1); gui.draw()           # ayuda


if __name__ == "__main__":
    unittest.main()