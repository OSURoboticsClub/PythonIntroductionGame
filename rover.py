from coordinate import Coordinate
from math import isfinite
from threading import RLock


class Rover:
    SIZE = 5
    RADIUS = SIZE // 2

    _x_acceleration: float
    _y_acceleration: float

    def __init__(self, x_acceleration: float = 0, y_acceleration: float = 0,
                 x: float = 3, y: float = 3):
        self.__state_lock = RLock()
        self.__max_acceleration = 3.0
        self.__current_x_speed = 0.0
        self.__current_y_speed = 0.0
        if not (isfinite(float(x)) and isfinite(float(y))):
            raise ValueError("position must be finite")
        self.__position = Coordinate(float(x), float(y))
        self.set_acceleration(x_acceleration, y_acceleration)

    @property
    def position(self) -> Coordinate:
        """Return an immutable snapshot of the continuous position."""
        from protected_coordinate import ProtectedCoordinate
        with self.__state_lock:
            return ProtectedCoordinate(self.__position.x, self.__position.y)

    @property
    def x_acceleration(self) -> float:
        with self.__state_lock:
            return self._x_acceleration

    @x_acceleration.setter
    def x_acceleration(self, value: float) -> None:
        self.set_acceleration(value, self._y_acceleration)

    @property
    def y_acceleration(self) -> float:
        with self.__state_lock:
            return self._y_acceleration

    @y_acceleration.setter
    def y_acceleration(self, value: float) -> None:
        self.set_acceleration(self._x_acceleration, value)

    @property
    def visible_position(self) -> tuple[int, int]:
        with self.__state_lock:
            return round(self.__position.x), round(self.__position.y)

    @property
    def x_speed(self) -> float:
        with self.__state_lock:
            return self.__current_x_speed

    @property
    def y_speed(self) -> float:
        with self.__state_lock:
            return self.__current_y_speed

    @property
    def current_speed(self) -> float:
        with self.__state_lock:
            return (self.__current_x_speed ** 2 +
                    self.__current_y_speed ** 2) ** 0.5

    def set_acceleration(self, x: float, y: float) -> None:
        x, y = float(x), float(y)
        if not (isfinite(x) and isfinite(y)):
            raise ValueError("acceleration must be finite")
        with self.__state_lock:
            self._x_acceleration = max(-self.__max_acceleration,
                                       min(self.__max_acceleration, x))
            self._y_acceleration = max(-self.__max_acceleration,
                                       min(self.__max_acceleration, y))

    def _advance(self, seconds: float) -> None:
        """Advance the physics simulation. Intended for the game engine only."""
        seconds = float(seconds)
        if not isfinite(seconds) or seconds < 0:
            raise ValueError("seconds must be a finite, non-negative number")
        with self.__state_lock:
            self.__current_x_speed += self._x_acceleration * seconds
            self.__current_y_speed += self._y_acceleration * seconds
            self.__position.x += self.__current_x_speed * seconds
            self.__position.y += self.__current_y_speed * seconds

    def _stop(self) -> None:
        """Stop the rover immediately. Intended for the game engine only."""
        with self.__state_lock:
            self.__current_x_speed = 0.0
            self.__current_y_speed = 0.0
