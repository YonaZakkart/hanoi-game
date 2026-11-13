import math
import time

from models.tower import Tower


class HanoiGame:
    NUM_TOWERS = 3
    MIN_DISKS = 1
    MAX_DISKS = 10

    MODE_NORMAL = "normal"
    MODE_PERFECT = "perfect"
    MODE_TIMED = "timed"
    MODES = (MODE_NORMAL, MODE_PERFECT, MODE_TIMED)

    SECONDS_PER_MOVE = 1.5
    MIN_TIME_LIMIT = 20

    UNDO_WINDOW = 5

    def __init__(self, num_disks, mode=MODE_NORMAL, clock=time.monotonic):
        if not isinstance(num_disks, int) or isinstance(num_disks, bool):
            raise ValueError("El número de discos debe ser un entero.")
        if num_disks < self.MIN_DISKS or num_disks > self.MAX_DISKS:
            raise ValueError(
                f"El número de discos debe estar entre {self.MIN_DISKS} y {self.MAX_DISKS}."
            )
        if mode not in self.MODES:
            raise ValueError(
                f"Modo inválido. Debe ser uno de: {', '.join(self.MODES)}."
            )
        self.num_disks = num_disks
        self.mode = mode
        self.min_moves = 2 ** num_disks - 1
        self._clock = clock
        if mode == self.MODE_TIMED:
            self.time_limit = self.time_limit_for(num_disks)
        else:
            self.time_limit = None
        self.towers = []
        self.moves = 0
        self.lost = False
        self.timed_out = False
        self._start_time = None
        self._end_time = None
        self._last_move = None
        self.reset()

    @classmethod
    def time_limit_for(cls, num_disks):
        minimum = 2 ** num_disks - 1
        return max(cls.MIN_TIME_LIMIT, int(math.ceil(minimum * cls.SECONDS_PER_MOVE)))

    def reset(self):
        self.towers = [Tower() for _ in range(self.NUM_TOWERS)]
        for disk in range(self.num_disks, 0, -1):
            self.towers[0].push(disk)
        self.moves = 0
        self.lost = False
        self.timed_out = False
        self._start_time = None
        self._end_time = None
        self._last_move = None

    def _validate_index(self, index):
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError("La torre debe indicarse con un número entero.")
        if index < 0 or index >= self.NUM_TOWERS:
            raise ValueError(
                f"Torre inválida. Debe estar entre 1 y {self.NUM_TOWERS}."
            )

    def is_valid_move(self, from_tower, to_tower):
        try:
            self._validate_index(from_tower)
            self._validate_index(to_tower)
        except ValueError:
            return False
        if from_tower == to_tower:
            return False
        origin = self.towers[from_tower]
        destination = self.towers[to_tower]
        if origin.is_empty():
            return False
        if destination.is_empty():
            return True
        return origin.peek() < destination.peek()

    def update_time(self):
        if self.mode != self.MODE_TIMED:
            return
        if self._start_time is None or self._end_time is not None:
            return
        if self.get_elapsed() >= self.time_limit:
            self.timed_out = True
            self._end_time = self._start_time + self.time_limit

    def get_elapsed(self):
        if self._start_time is None:
            return 0.0
        if self._end_time is not None:
            end = self._end_time
        else:
            end = self._clock()
        return max(0.0, end - self._start_time)

    def get_time_left(self):
        if self.time_limit is None:
            return None
        return max(0.0, self.time_limit - self.get_elapsed())

    def get_time_limit(self):
        return self.time_limit

    def move(self, from_tower, to_tower):
        self.update_time()
        if self.timed_out:
            raise ValueError("Se acabó el tiempo.")
        if self.lost:
            raise ValueError("La partida ya está perdida.")
        self._validate_index(from_tower)
        self._validate_index(to_tower)
        if from_tower == to_tower:
            raise ValueError(
                "La torre origen y la torre destino deben ser distintas.")
        origin = self.towers[from_tower]
        destination = self.towers[to_tower]
        if origin.is_empty():
            raise ValueError("La torre origen está vacía.")
        if not destination.is_empty() and origin.peek() > destination.peek():
            raise ValueError(
                "No se puede colocar un disco grande sobre uno más pequeño.")
        if self._start_time is None:
            self._start_time = self._clock()
        disk = origin.pop()
        destination.push(disk)
        self.moves += 1
        self._last_move = (from_tower, to_tower, self._clock())

        if self.mode == self.MODE_PERFECT and self.moves > self.min_moves:
            self.lost = True

        if self._end_time is None:
            if self.lost or self.towers[2].size() == self.num_disks:
                self._end_time = self._clock()

        return disk

    def can_undo(self):
        self.update_time()
        if self._last_move is None or self.is_over():
            return False
        return self._clock() - self._last_move[2] <= self.UNDO_WINDOW

    def get_undo_time_left(self):
        if not self.can_undo():
            return 0.0
        elapsed = self._clock() - self._last_move[2]
        return max(0.0, self.UNDO_WINDOW - elapsed)

    def undo(self):
        self.update_time()
        if self.is_over():
            raise ValueError("No se puede deshacer: la partida ya terminó.")
        if self._last_move is None:
            raise ValueError("No hay ningún movimiento para deshacer.")
        from_tower, to_tower, when = self._last_move
        if self._clock() - when > self.UNDO_WINDOW:
            raise ValueError(
                f"Ya no se puede deshacer (límite de {self.UNDO_WINDOW} segundos).")
        disk = self.towers[to_tower].pop()
        self.towers[from_tower].push(disk)
        self.moves -= 1
        self._last_move = None
        if self.moves == 0:
            self._start_time = None
        return disk

    def is_finished(self):
        if self.mode == self.MODE_PERFECT:
            return self.towers[2].size() == self.num_disks and not self.lost
        return self.towers[2].size() == self.num_disks

    def is_won(self):
        return self.is_finished()

    def is_lost(self):
        return self.lost or self.timed_out

    def is_timed_out(self):
        return self.timed_out

    def is_over(self):
        return self.is_finished() or self.is_lost()

    def get_mode(self):
        return self.mode

    def get_state(self):
        return [tower.get_disks() for tower in self.towers]

    def get_towers(self):
        return self.get_state()

    def get_moves(self):
        return self.moves

    def get_min_moves(self):
        return self.min_moves