"""Pruebas del Punto 3.5 (pistas y resolver automáticamente).

Ejecutar desde la raíz del proyecto:  python tests/test_pistas.py
(también funciona con pytest). La GUI se prueba en modo headless.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from game.hanoi_game import HanoiGame  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def raises(exc, fn, *args):
    try:
        fn(*args)
    except exc:
        return True
    return False


# ---------------------------------------------------------------- lógica
def test_hint_is_first_optimal_move_and_pure():
    g = HanoiGame(3)
    assert g.get_hint() == g.get_optimal_moves()[0] == (0, 2)
    assert g.get_hint() == (0, 2)            # no consume nada
    assert g.get_moves() == 0 and g.hints_used == 0
    assert g._start_time is None             # no arranca el cronómetro


def test_hint_counts_only_with_use_hint():
    g = HanoiGame(3)
    g.use_hint()
    g.use_hint()
    assert g.get_hints_used() == 2 and g.is_assisted() and not g.was_auto_solved()


def test_hint_after_wrong_move_and_after_undo():
    clock = FakeClock()
    g = HanoiGame(3, clock=clock)
    g.move(0, 1)                             # movimiento no óptimo
    hint = g.get_hint()
    assert g.is_valid_move(*hint)
    assert len(g.get_solution()) == len(g.get_optimal_moves())
    g.undo()
    assert g.get_hint() == (0, 2)


def test_following_hints_solves_optimally_all_sizes_and_starts():
    for n in range(1, 8):
        for start, seed in ((HanoiGame.START_STANDARD, None),
                            (HanoiGame.START_MIXED, 1),
                            (HanoiGame.START_MIXED, 7)):
            if n == 1 and start == HanoiGame.START_MIXED:
                continue
            g = HanoiGame(n, start=start, seed=seed, clock=FakeClock())
            minimum = g.get_min_moves()
            while g.get_hint() is not None:
                g.move(*g.use_hint())
            assert g.is_finished() and g.get_moves() == minimum, (n, start, seed)
            assert g.get_hint() is None and g.get_solution() == []


def test_auto_step_solves_and_marks_assisted():
    g = HanoiGame(4, clock=FakeClock())
    steps = 0
    while not g.is_over():
        g.auto_step()
        steps += 1
    assert steps == 15 == g.get_moves() and g.is_finished()
    assert g.was_auto_solved() and g.is_assisted()
    assert raises(ValueError, g.auto_step)   # nada pendiente


def test_auto_step_from_mixed_state():
    g = HanoiGame(5, start=HanoiGame.START_MIXED, seed=3, clock=FakeClock())
    minimum = g.get_min_moves()
    while not g.is_over():
        g.auto_step()
    assert g.get_moves() == minimum and g.is_finished()


def test_reset_clears_assistance():
    g = HanoiGame(3, clock=FakeClock())
    g.use_hint()
    g.auto_step()
    g.reset()
    assert g.hints_used == 0 and not g.auto_solved and not g.is_assisted()
    assert g.get_hint() == (0, 2)


def test_hint_none_when_over():
    g = HanoiGame(1, clock=FakeClock())
    g.move(0, 2)
    assert g.get_hint() is None and g.use_hint() is None and g.hints_used == 0


def test_perfect_mode_hints_never_lose():
    g = HanoiGame(4, mode=HanoiGame.MODE_PERFECT, clock=FakeClock())
    while g.get_hint() is not None:
        g.move(*g.use_hint())
    assert g.is_finished() and not g.is_lost()


def test_timed_mode_clock_runs_and_timeout_stops_hints():
    clock = FakeClock()
    g = HanoiGame(3, mode=HanoiGame.MODE_TIMED, clock=clock)   # límite 20 s
    g.get_hint()
    clock.advance(100)                       # pedir pista no arranca el reloj
    assert g.get_time_left() == 20
    g.auto_step()                            # arranca con el primer movimiento
    clock.advance(25)
    assert g.get_hint() is None              # tiempo agotado
    assert g.is_timed_out()
    assert raises(ValueError, g.auto_step)


def test_undo_after_auto_step_within_window():
    clock = FakeClock()
    g = HanoiGame(3, clock=clock)
    g.auto_step()
    assert g.can_undo()
    g.undo()
    assert g.get_moves() == 0


# ------------------------------------------------------------------- GUI
def make_gui(**kw):
    import pygame
    from ui.gui import HanoiGUI
    gui = HanoiGUI(show_menu=False, **kw)
    ticks = {"now": 0}
    pygame.time.get_ticks = lambda: ticks["now"]
    return gui, ticks, pygame


def test_gui_hint_button_and_key_and_expiry():
    gui, ticks, pg = make_gui(num_disks=3)
    gui.handle_mouse(gui.BTN_HINT.center)
    assert gui.hint == (0, 2) and gui.game.get_hints_used() == 1
    gui.draw()
    ticks["now"] += 1000 * gui.HINT_SECONDS + 1
    gui.update()
    assert gui.hint is None
    gui.handle_key(pg.K_h)
    assert gui.hint == (0, 2) and gui.game.get_hints_used() == 2
    # al mover con clics la pista se quita
    gui.handle_click(gui.tower_rect(0).center)
    gui.handle_click(gui.tower_rect(2).center)
    assert gui.hint is None and gui.game.get_moves() == 1
    gui.draw()
    pg.quit()


def test_gui_hint_cleared_by_undo_restart_menu():
    gui, ticks, pg = make_gui(num_disks=3)
    gui.handle_click(gui.tower_rect(0).center)
    gui.handle_click(gui.tower_rect(1).center)
    gui.try_hint()
    gui.try_undo()
    assert gui.hint is None
    gui.try_hint()
    gui.handle_key(pg.K_r)
    assert gui.hint is None and gui.game.get_hints_used() == 0
    gui.try_hint()
    gui.handle_key(pg.K_ESCAPE)
    assert gui.hint is None and gui.state == "menu"
    pg.quit()


def test_gui_auto_solve_full_run_and_panel():
    gui, ticks, pg = make_gui(num_disks=3)
    gui.handle_key(pg.K_x)
    assert gui.auto_solving
    for _ in range(200):
        gui.update()
        gui.draw()
        ticks["now"] += gui.AUTO_SOLVE_INTERVAL_MS
        if gui.game.is_over():
            break
    gui.update()
    assert gui.game.is_finished() and gui.game.get_moves() == 7
    assert gui.game.was_auto_solved() and not gui.auto_solving
    gui.draw()                               # panel "RESUELTO"
    pg.quit()


def test_gui_auto_solve_respects_interval():
    gui, ticks, pg = make_gui(num_disks=4)
    gui.handle_mouse(gui.BTN_SOLVE.center)
    gui.update()
    assert gui.game.get_moves() == 1         # primer paso inmediato
    ticks["now"] += gui.AUTO_SOLVE_INTERVAL_MS - 1
    gui.update()
    assert gui.game.get_moves() == 1
    ticks["now"] += 1
    gui.update()
    assert gui.game.get_moves() == 2
    pg.quit()


def test_gui_click_and_keys_cancel_auto_solve():
    gui, ticks, pg = make_gui(num_disks=4)
    gui.handle_key(pg.K_x)
    gui.update()
    gui.handle_mouse(gui.tower_rect(1).center)      # clic cancela y se consume
    assert not gui.auto_solving and gui.selected_tower is None
    moves = gui.game.get_moves()
    ticks["now"] += 5000
    gui.update()
    assert gui.game.get_moves() == moves
    gui.handle_key(pg.K_x)
    assert gui.auto_solving
    gui.handle_key(pg.K_ESCAPE)                     # Esc cancela, NO va al menú
    assert not gui.auto_solving and gui.state == "playing"
    # deshacer deshabilitado mientras resuelve; hint/undo tras cancelar funcionan
    gui.handle_key(pg.K_h)
    assert gui.hint is not None
    gui.draw()
    pg.quit()


def test_gui_auto_solve_stops_on_timeout_and_shows_error():
    gui, ticks, pg = make_gui(num_disks=3)
    clock = FakeClock()
    gui.game = HanoiGame(3, mode=HanoiGame.MODE_TIMED, clock=clock)
    gui.handle_key(pg.K_x)
    gui.update()                                    # primer movimiento
    clock.advance(30)                               # se acaba el tiempo
    ticks["now"] += 1000
    gui.update()
    assert gui.game.is_timed_out() and not gui.auto_solving
    gui.draw()
    pg.quit()


def test_gui_hint_solve_ignored_when_over_and_in_menu():
    gui, ticks, pg = make_gui(num_disks=1)
    gui.handle_click(gui.tower_rect(0).center)
    gui.handle_click(gui.tower_rect(2).center)
    assert gui.game.is_finished()
    gui.handle_key(pg.K_h)
    gui.handle_key(pg.K_x)
    gui.handle_mouse(gui.BTN_HINT.center)
    assert gui.hint is None and not gui.auto_solving
    assert gui.game.get_hints_used() == 0
    gui.handle_key(pg.K_ESCAPE)
    assert gui.state == "menu"
    gui.handle_key(pg.K_h)                           # en el menú no pasa nada
    gui.handle_key(pg.K_x)
    assert gui.hint is None and not gui.auto_solving
    pg.quit()


def test_gui_win_panel_with_hints_note():
    gui, ticks, pg = make_gui(num_disks=2)
    while not gui.game.is_over():
        gui.try_hint()
        gui.game.move(*gui.hint)
        gui.clear_hint()
    assert gui.game.get_hints_used() == 3 and not gui.game.was_auto_solved()
    gui.draw()
    pg.quit()


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("OK  ", name)
    print(f"\n{len(tests)} pruebas pasaron.")