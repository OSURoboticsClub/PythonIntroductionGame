from coordinate import Coordinate
class ProtectedCoordinate(Coordinate):

    def __init__(self, x: float, y: float):
        object.__setattr__(self, "_locked", False)
        super().__init__(x, y)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name in ("_x", "_y"):
            raise AttributeError("Coordinate positions are read-only")
        super().__setattr__(name, value)

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        raise AttributeError("Coordinate positions are read-only")
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        raise AttributeError("Coordinate positions are read-only")
