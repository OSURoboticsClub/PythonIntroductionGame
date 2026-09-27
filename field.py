import random
import time
from collections import deque
from math import isfinite
from threading import Event, RLock, Thread, current_thread
from typing import Optional

from coordinate import Coordinate
from protected_coordinate import ProtectedCoordinate
from rover import Rover


class Field:
    """Deterministic rover game with a simple API for student controllers."""

    ENDPOINT_SIZE = 5
    ENDPOINT_RADIUS = ENDPOINT_SIZE // 2
    OBSTACLE_SIZE = 3
    OBSTACLE_RADIUS = OBSTACLE_SIZE // 2
    # Two obstacle centers must be this far apart on at least one axis.
    # This leaves five empty cells between their 3x3 footprints.
    OBSTACLE_CENTER_CLEARANCE = OBSTACLE_SIZE + Rover.SIZE

    def __init__(self, seed: Optional[int] = None, x_size: int = 80,
                 y_size: int = 24, obstacle_count: int = 10,
                 endpoint_padding: int = 10) -> None:
        if not isinstance(x_size, int) or isinstance(x_size, bool) or x_size < 12:
            raise ValueError("x_size must be an integer of at least 12")
        if not isinstance(y_size, int) or isinstance(y_size, bool) or y_size < 7:
            raise ValueError("y_size must be an integer of at least 7")
        if (not isinstance(obstacle_count, int) or isinstance(obstacle_count, bool)
                or obstacle_count < 0):
            raise ValueError("obstacle_count must be a non-negative integer")
        if not isinstance(endpoint_padding, int) or isinstance(endpoint_padding, bool):
            raise ValueError("endpoint_padding must be an integer")
        self._x_size, self._y_size = x_size, y_size
        if endpoint_padding < 3 or endpoint_padding >= x_size // 2:
            raise ValueError("endpoint_padding must leave room on both sides of the endpoint")
        self._seed = seed if seed is not None else random.randrange(1, 2**31)
        generator = random.Random(self._seed)
        # Leave open cells between the endpoint and the right-hand border.
        self._endpoint = ProtectedCoordinate(x_size - 1 - endpoint_padding, y_size // 2)
        self._obstacle_centers = []
        self._tick_speed = 0.05
        self._elapsed_time = 0.0
        self._status = "playing"
        self.__state_lock = RLock()
        self.__simulation_stop = Event()
        self.__simulation_thread = None
        self._rover = Rover(x=Rover.RADIUS + 1, y=y_size // 2)
        # Publicly inspectable map: map[y][x].  Coordinates match the grid.
        self._map = []
        self._refresh_map()
        valid_obstacle_cells = [
            (x, y)
            for y in range(self.OBSTACLE_RADIUS + 1,
                           y_size - self.OBSTACLE_RADIUS - 1)
            for x in range(self.OBSTACLE_RADIUS + 1,
                           x_size - self.OBSTACLE_RADIUS - 1)
            if (Coordinate(x, y).distance_to(self._rover.position) > 6
                and Coordinate(x, y).distance_to(self._endpoint) > 6)
        ]
        generator.shuffle(valid_obstacle_cells)
        chosen_obstacles = []
        if obstacle_count:
            for x, y in valid_obstacle_cells:
                enough_space = all(
                    abs(x - other_x) >= self.OBSTACLE_CENTER_CLEARANCE or
                    abs(y - other_y) >= self.OBSTACLE_CENTER_CLEARANCE
                    for other_x, other_y in chosen_obstacles
                )
                if not enough_space:
                    continue
                proposed = chosen_obstacles + [(x, y)]
                if self._path_exists(proposed):
                    chosen_obstacles.append((x, y))
                    if len(chosen_obstacles) == obstacle_count:
                        break
        if len(chosen_obstacles) < obstacle_count:
            raise ValueError(
                f"obstacle_count {obstacle_count} does not fit without overlap "
                "for this field size and endpoint padding"
            )
        self._obstacle_centers = [
            ProtectedCoordinate(x, y)
            for x, y in chosen_obstacles
        ]
        self._refresh_map()

    def _path_exists(self, obstacles: list[tuple[int, int]]) -> bool:
        """Check that a 5x5 rover center can reach the endpoint center."""
        radius = Rover.RADIUS
        minimum_x, maximum_x = radius + 1, self._x_size - radius - 2
        minimum_y, maximum_y = radius + 1, self._y_size - radius - 2
        start = self._rover.visible_position
        goal = (self._endpoint.x, self._endpoint.y)
        collision_radius = radius + self.OBSTACLE_RADIUS

        def is_open(x: int, y: int) -> bool:
            if not (minimum_x <= x <= maximum_x and
                    minimum_y <= y <= maximum_y):
                return False
            return all(abs(x - obstacle_x) > collision_radius or
                       abs(y - obstacle_y) > collision_radius
                       for obstacle_x, obstacle_y in obstacles)

        if not is_open(*start) or not is_open(*goal):
            return False
        pending = deque([start])
        visited = {start}
        while pending:
            x, y = pending.popleft()
            if (x, y) == goal:
                return True
            for neighbor in ((x + 1, y), (x - 1, y),
                             (x, y + 1), (x, y - 1)):
                if neighbor not in visited and is_open(*neighbor):
                    visited.add(neighbor)
                    pending.append(neighbor)
        return False

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def rover_location(self) -> Coordinate:
        """Return the rover's continuous, floating-point position."""
        return self._rover.position

    @property
    def rover(self) -> Rover:
        """Return the rover controlled by this field."""
        return self._rover

    @property
    def visible_rover_location(self) -> tuple[int, int]:
        """Return the integer grid cell currently occupied by the rover."""
        return self._rover.visible_position

    @property
    def endpoint(self) -> ProtectedCoordinate:
        return self._endpoint

    @property
    def obstacles(self) -> tuple:
        return tuple(self._obstacle_centers)

    @property
    def status(self) -> str:
        with self.__state_lock:
            return self._status

    @property
    def tick_speed(self) -> float:
        return self._tick_speed

    @property
    def current_speed(self) -> float:
        return self._rover.current_speed

    @property
    def elapsed_time(self) -> float:
        with self.__state_lock:
            return self._elapsed_time

    @property
    def simulation_running(self) -> bool:
        """Return whether the background simulation thread is active."""
        thread = self.__simulation_thread
        return thread is not None and thread.is_alive()

    @property
    def map(self) -> list[list[str]]:
        """Return a copy of the current map, indexed as map[y][x]."""
        with self.__state_lock:
            return [row[:] for row in self._map]

    def get_cell(self, x: int, y: int) -> str:
        """Return the symbol at (x, y), or '#' when outside the field."""
        if not (0 <= x < self._x_size and 0 <= y < self._y_size):
            return '#'
        with self.__state_lock:
            return self._map[y][x]

    def _refresh_map(self) -> None:
        """Rebuild the player-visible 2D map from the current game state."""
        with self.__state_lock:
            self._map = [['.' for _ in range(self._x_size)] for _ in range(self._y_size)]
            for x in range(self._x_size):
                self._map[0][x] = self._map[-1][x] = '#'
            for y in range(self._y_size):
                self._map[y][0] = self._map[y][-1] = '#'
            for obstacle in self._obstacle_centers:
                self._draw_square(obstacle.x, obstacle.y,
                                  self.OBSTACLE_RADIUS, 'X')
            self._draw_square(self._endpoint.x, self._endpoint.y,
                              self.ENDPOINT_RADIUS, 'E')
            rx, ry = self.visible_rover_location
            self._draw_square(rx, ry, Rover.RADIUS, 'R')

    def _draw_square(self, center_x: float, center_y: float,
                     radius: int, symbol: str) -> None:
        """Draw a square footprint, clipping cells outside the visible map."""
        center_x, center_y = round(center_x), round(center_y)
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius, center_x + radius + 1):
                if 0 <= x < self._x_size and 0 <= y < self._y_size:
                    self._map[y][x] = symbol

    @staticmethod
    def _segment_intersects_box(start: Coordinate, end: Coordinate,
                                center: Coordinate, radius: float) -> bool:
        """Return whether a movement segment enters an axis-aligned square."""
        minimum_x, maximum_x = center.x - radius, center.x + radius
        minimum_y, maximum_y = center.y - radius, center.y + radius
        dx, dy = end.x - start.x, end.y - start.y
        lower, upper = 0.0, 1.0
        for origin, change, minimum, maximum in (
                (start.x, dx, minimum_x, maximum_x),
                (start.y, dy, minimum_y, maximum_y)):
            if change == 0:
                if origin < minimum or origin > maximum:
                    return False
                continue
            first = (minimum - origin) / change
            second = (maximum - origin) / change
            entry, exit_ = min(first, second), max(first, second)
            lower, upper = max(lower, entry), min(upper, exit_)
            if lower > upper:
                return False
        return True

    def _has_collided(self, previous_position: Optional[Coordinate] = None) -> bool:
        """Check collisions. Intended for the game engine only."""
        position = self._rover.position
        radius = Rover.RADIUS
        boundary = (position.x - radius <= 0 or
                    position.x + radius >= self._x_size - 1 or
                    position.y - radius <= 0 or
                    position.y + radius >= self._y_size - 1)
        if boundary:
            return True
        start = previous_position if previous_position is not None else position
        collision_radius = Rover.RADIUS + self.OBSTACLE_RADIUS
        return any(self._segment_intersects_box(start, position, obstacle,
                                                collision_radius)
                   for obstacle in self._obstacle_centers)

    def _update_rover_location(self) -> None:
        """Advance one simulation step. Intended for the game engine only."""
        if self._status != "playing":
            return
        previous_position = Coordinate(self._rover.position.x, self._rover.position.y)
        self._rover._advance(self._tick_speed)
        self._elapsed_time += self._tick_speed
        if self._has_collided(previous_position):
            self._status = "lost"
        elif (abs(self._rover.position.x - self._endpoint.x) <= self.ENDPOINT_RADIUS and
              abs(self._rover.position.y - self._endpoint.y) <= self.ENDPOINT_RADIUS and
              self._rover.current_speed < 1.0):
            self._status = "won"
        self._refresh_map()

    def _tick(self, x_acceleration: Optional[float] = None,
              y_acceleration: Optional[float] = None) -> str:
        """Run one game tick. Intended for game runners and previews only."""
        with self.__state_lock:
            if self._status != "playing":
                return self._status
            if (x_acceleration is None) != (y_acceleration is None):
                raise ValueError("both acceleration values must be provided together")
            if x_acceleration is not None:
                self._rover.set_acceleration(x_acceleration, y_acceleration)
            self._update_rover_location()
            return self._status

    def start_simulation(self) -> Thread:
        """Start automatic physics updates in a background thread."""
        with self.__state_lock:
            if self._status != "playing":
                raise RuntimeError("a finished game cannot be restarted")
            if self.simulation_running:
                return self.__simulation_thread
            self.__simulation_stop.clear()
            self.__simulation_thread = Thread(
                target=self.__simulation_loop,
                name=f"rover-simulation-{self._seed}",
                daemon=True,
            )
            self.__simulation_thread.start()
            return self.__simulation_thread

    def stop_simulation(self, timeout: Optional[float] = None) -> None:
        """Request that the background simulation stop, then wait for it."""
        self.__simulation_stop.set()
        thread = self.__simulation_thread
        if thread is not None and thread is not current_thread():
            thread.join(timeout)

    def wait_for_simulation(self, timeout: Optional[float] = None) -> bool:
        """Wait for completion; return False if the timeout expires."""
        thread = self.__simulation_thread
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def __simulation_loop(self) -> None:
        next_tick = time.monotonic()
        while not self.__simulation_stop.is_set() and self.status == "playing":
            next_tick += self._tick_speed
            delay = max(0.0, next_tick - time.monotonic())
            if self.__simulation_stop.wait(delay):
                break
            self._tick()

    def render(self) -> str:
        with self.__state_lock:
            return '\n'.join(''.join(row) for row in self._map)

    def run(self, controller, realtime: bool = True) -> str:
        """Run controller(field), where each result is (x_acceleration, y_acceleration)."""
        if self.simulation_running:
            raise RuntimeError("stop the background simulation before calling run")
        while self._status == "playing":
            command = controller(self)
            if command is None:
                x, y = 0, 0
            elif isinstance(command, (tuple, list)) and len(command) == 2:
                x, y = command
            else:
                raise TypeError("controller must return a two-item tuple/list or None")
            if not (isfinite(float(x)) and isfinite(float(y))):
                raise ValueError("controller acceleration values must be finite")
            self._tick(x, y)
            if realtime:
                print('\033[H\033[J' + self.render())
                print(f"seed={self.seed} speed={self._rover.current_speed:.2f} status={self._status}")
                time.sleep(self._tick_speed)
        return self._status
