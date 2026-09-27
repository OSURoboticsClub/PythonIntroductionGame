class Coordinate:
    _x: int
    _y: int
    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

    @property
    def x(self) -> float:
        return self._x
    @x.setter
    def x(self, value: float):
        self._x = value

    @property
    def y(self) -> float:
        return self._y
    @y.setter
    def y(self, value: float):
        self._y = value

    def distance_to(self, other: "Coordinate") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"Coordinate(x={self.x}, y={self.y})"
