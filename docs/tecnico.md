# Documentación Técnica

Resumen de las estructuras y funciones principales del proyecto (v1 consola y v2 GUI).

## Arquitectura

Tres capas con responsabilidades separadas:

```
main.py ──► ui/console_ui.py   (mostrar y leer, modo --console)
   ├────► ui/gui.py           (GUI Pygame, modo por defecto)
   │   └──► utils/helpers.py   (validar entradas)
   └──────► game/hanoi_game.py (reglas y estado) ──► models/tower.py (pila)
```

- **models**: estructura de datos.
- **game**: reglas del juego, sin `print` ni `input`.
- **ui**: solo muestra información y lee la entrada; no conoce las reglas.
- **main / utils**: integran todo y validan formato de entradas.

Esta separación permitió añadir la GUI (v2) sin tocar `game` ni `models`.

## models/tower.py — `Tower`

Pila (LIFO) de enteros; cada entero es el tamaño de un disco. La base está en el índice 0 y la cima al final.

| Método | Descripción |
|--------|-------------|
| `push(disk)` | Apila un disco. `ValueError` si es mayor que el de la cima. |
| `pop()` | Quita y devuelve el disco de la cima. `IndexError` si está vacía. |
| `peek()` | Devuelve la cima sin quitarla. `IndexError` si está vacía. |
| `is_empty()` | `True` si no hay discos. |
| `size()` | Cantidad de discos. |
| `get_disks()` | Copia de la lista de discos (base → cima). |

## game/hanoi_game.py — `HanoiGame`

Constantes: `NUM_TOWERS = 3`, `MIN_DISKS = 1`, `MAX_DISKS = 10`.

`HanoiGame(num_disks)` valida que sea un entero entre 1 y 10 (`ValueError` si no) y coloca todos los discos en la torre 0, con el más grande abajo.

| Método | Descripción |
|--------|-------------|
| `move(from_tower, to_tower)` | Mueve el disco de la cima. Devuelve el disco movido y suma 1 al contador. Lanza `ValueError` si la torre es inválida, origen = destino, el origen está vacío o se pone un disco grande sobre uno pequeño. |
| `is_valid_move(from_tower, to_tower)` | `True`/`False` sin modificar el estado ni lanzar excepciones. |
| `is_finished()` | `True` cuando todos los discos están en la torre 3 (índice 2). |
| `get_state()` | Lista de 3 listas con los discos de cada torre (base → cima). |
| `get_moves()` | Movimientos realizados. |
| `get_min_moves()` | Mínimo teórico: 2ⁿ − 1. |
| `reset()` | Reinicia torres y contador. |

Alias: `is_won()` = `is_finished()`, `get_towers()` = `get_state()`.

Las torres se indexan 0-2 internamente.

## ui/console_ui.py

| Función | Descripción |
|---------|-------------|
| `render_towers(towers, num_disks=None)` | Dibuja las 3 torres con discos proporcionales. Recibe `game.get_state()`. |
| `ask_move()` | Pide origen y destino. Acepta `1 3`, `1,3`, `1-3`, `1>3` y `13`. Devuelve `(origen, destino)` en base 0, o `None` si el usuario sale (`q`, `salir`, Ctrl+C/Ctrl+D). Solo valida el formato. |
| `show_message(message)` | Mensaje informativo. |
| `show_error(message)` | Error con prefijo `[!]`. |
| `show_victory(moves, min_moves)` | Pantalla de victoria; avisa si fue partida perfecta. |

Convención: el usuario ve torres 1-3; el resto del código usa índices 0-2.

## utils/helpers.py

| Función | Descripción |
|---------|-------------|
| `calculate_min_moves(num_disks)` | Devuelve 2ⁿ − 1. |
| `parse_num_disks(text)` | Convierte texto a entero y valida el rango. `ValueError` con mensaje claro si no es válido. |
| `ask_num_disks()` | Pide el número de discos hasta recibir uno válido. `None` si el usuario sale. |
| `ask_yes_no(question)` | Pregunta sí/no (`s`, `si`, `sí`, `y`, `yes` / `n`, `no`). `False` si se cierra la entrada. |

## main.py

- `play(game)`: bucle de una partida en consola. Muestra el tablero y los contadores, pide el movimiento y captura el `ValueError` de `game.move()` para mostrarlo con `show_error`. Devuelve `True` si se ganó, `False` si el usuario salió.
- `run_console()`: flujo de consola (v1): pide el número de discos, juega y pregunta si se quiere repetir.
- `run_gui()`: abre `HanoiGUI()` (arranca en el menú). El import de `ui.gui` es diferido: si falta `pygame`, imprime cómo instalarlo y devuelve 1; la consola no se ve afectada.
- `main(argv=None)`: lee `--console`; sin la opción lanza la GUI. Su valor de retorno es el código de salida.

Ejecución: `python main.py` (GUI) o `python main.py --console`.

## Flujo de un turno

1. `render_towers(game.get_state(), ...)` y se muestran movimientos y mínimo.
2. `ask_move()` devuelve `(origen, destino)` o `None`.
3. `game.move(origen, destino)`. Si falla, `show_error`.
4. Si `game.is_finished()`, se muestra `show_victory`.

## Criterios de aceptación del MVP

- [x] Tower como pila con validación de tamaño
- [x] Inicialización con N discos (1-10)
- [x] Movimiento con validación de todas las reglas
- [x] Detección de victoria
- [x] Contador de movimientos y mínimo teórico (2ⁿ − 1)
- [x] Render claro de las 3 torres
- [x] Mensajes de error y de victoria
- [x] Entrada de origen y destino
- [x] Flujo principal con validación del número de discos
- [x] Lógica de juego independiente de la interfaz

## ui/gui.py — `HanoiGUI` (v2)

GUI con Pygame (`pygame-ce`). Solo dibuja y lee eventos; las reglas siguen en `HanoiGame`.

`HanoiGUI(num_disks=3, show_menu=True)` crea la ventana (960x640). `run()` ejecuta el bucle (eventos → `update` → `draw`) y siempre llama a `pygame.quit()` al terminar, incluso si hay un error.

**Estados** (`self.state`):

| Estado | Qué muestra |
|--------|-------------|
| `"menu"` | Selector de discos (1-10) y botón START. |
| `"playing"` | Torres, discos, HUD, errores y, al ganar, el panel de victoria. |

**Eventos**

| Entrada | Menú | Partida |
|---------|------|---------|
| `Esc` | Cierra la app | Vuelve al menú |
| `R` | — | Reinicia con los mismos discos |
| Flechas / `Enter` | Cambian discos / empieza | — |
| `QUIT` (cerrar ventana) | Cierra la app | Cierra la app |
| Clic izquierdo | Botones -, +, START | Seleccionar torre origen y destino |

**Métodos principales**

| Grupo | Métodos |
|-------|---------|
| Eventos | `handle_events`, `handle_key`, `handle_menu_key`, `handle_mouse`, `handle_click`, `tower_at` |
| Estado | `start_game(n)`, `go_to_menu()`, `change_menu_disks(delta)`, `set_error(msg)` |
| Dibujo | `draw`, `draw_background`, `draw_base`, `draw_poles`, `draw_disks`, `draw_selection`, `draw_hint`, `draw_hud`, `draw_history`, `draw_error`, `draw_help`, `draw_end_panel`, `draw_menu`, `draw_text`, `draw_panel`, `draw_button` |
| Medidas | `tower_center_x`, `tower_rect`, `disk_width`, `disk_sprite_index`, `disk_tint`, `disk_surface`, `disk_pos` |

**Flujo de un movimiento**: primer clic en una torre con discos → `selected_tower`; segundo clic en otra torre → `game.move(origen, destino)`. Si lanza `ValueError`, se muestra con `set_error` (3 s). Si `game.is_finished()`, se dibuja el panel de victoria y los clics sobre las torres dejan de hacer algo.

Los recursos están en `assets/` (`background.png`, `base.png`, `pole_wood.png`, `pole_steel.png`). Si falta alguno, se dibuja una versión simple.

## Criterios de aceptación de v2

- [x] Ventana y bucle principal con Pygame
- [x] Torres y discos con tamaños y colores diferenciados
- [x] Selección de origen y destino con clic, con feedback visual
- [x] HUD: movimientos, mínimo, errores y victoria
- [x] Selector de número de discos
- [x] `main.py` lanza la GUI; `--console` conserva el modo v1
- [x] Cierre de ventana y `Esc` / `R` funcionan
## ui/gui.py — tema visual v3 (punto 3.8)

La GUI mantiene la separación de capas: `HanoiGame` sigue siendo la única fuente de verdad y `ui/gui.py` solo dibuja y lee eventos.

**Sprites de disco**

- Los PNG de `assets/` (ocho tamaños, de "Pequeño pequeño" a "Enorme") miden 1024x1024 con relleno transparente. `load_native_sprite()` recorta el relleno con `Surface.get_bounding_rect()` y reduce la imagen a su rejilla nativa (un píxel de arte cada 16 px) para que el escalado posterior sea nítido.
- `hue_shift()` y `tint_surface()` recolorean el sprite píxel a píxel: giran el tono conservando saturación y brillo, así que el sombreado y los bordes se mantienen. La paleta `DISK_TINTS` va de dorado a magenta y `disk_tint()` la reparte entre los discos de la partida (con 3 discos se usan dorado, naranja y magenta; con 10, los diez tonos).
- `disk_width()` interpola el ancho entre `DISK_MIN_W` (140) y `DISK_MAX_W` (250) según el número de discos; `disk_sprite_index()` elige el PNG más cercano y `_disk_image()` lo escala conservando su proporción. Las superficies se cachean por `(tamaño, num_discos)` y los sprites teñidos por `(sprite, tono)`.
- `disk_pos()` apila con `DISK_STEP = 26`: los discos isométricos se solapan lo suficiente para que 10 discos quepan bajo el palo (`POLE_HEIGHT = 370`). La animación usa la altura real del sprite y eleva el disco `ANIM_LIFT_MARGIN` por encima del apilado, no por encima del palo (los sprites son mucho más altos que los discos planos de v2).

**Distribución**

- HUD superior fijo (`HUD_RECT`): título, inicio, modo, discos, movimientos/mínimo y tiempo. Los botones de acción están en una barra inferior sobre la madera de la base.
- Menú rediseñado: selectores clicables de discos (`-`/`+`), modo y inicio (flechas), botón START y una fila de vista previa con los discos del tamaño elegido y sus colores.
- Paneles de historial (`L`), ayuda (`F1`), error y fin de partida comparten `draw_panel()` (fondo oscuro, borde de píxeles y sombra) y `draw_text()` (texto renderizado sin antialias y escalado x2 para conservar el aspecto pixel).

**Sonido**

`_init_sounds()` genera ondas cuadradas con el módulo `array` y las carga como `pygame.mixer.Sound` (no hay archivos de audio). Suenan al seleccionar, mover, deshacer, pedir pista, cometer un error y al ganar o perder. `M` activa o silencia; si el mezclador no está disponible, el juego sigue funcionando sin sonido.

**Pruebas**: `tests/test_tema.py` cubre carga y tamaño de sprites, reparto de anchos y tonos, caché, apilado, no solape de HUD/botones y el dibujo de todas las pantallas. `tests/test_animacion.py` se adaptó a la nueva altura de disco.
