"""
This is where all of your code to control the rover and make it to the end of
the map! You are allowed to only control the acceleration of the rover,
though you are welcome to access any information about the field, and there is
exposed information as follows that you can use to manipulate the simulation.

In order to win the game, your rover needs to contact the middle tile of the
endpoint and have a speed below 1 m/s in order to win. If you are too fast,
you will not win until you slow down.

Additionally, if you contact any tile that contains an obstacle (not just the
middle of it), you will lose the game. Similarly, if you leave the game
boundary you will lose (though you are still able to contact the exact boundary
despite also being denoted with hashtags).

Below are the few things that you might need to solve the problem as well as
other miscellaneous information you are able to access. Your solution cannot
use anything that uses a private variable or method, which you can identify by
seeing if there's an underscore in front of it (so the method _foo() and
parameter x._foo both are private, and you cannot access it). However, you can
look through the other files if you are confused on how something works.

The ``field`` variable is the Field object created for the current game.
The rover can be accessed as ``field.rover``.

Field information:

- ``field.seed``: the integer seed used to generate this field.

- ``field.rover_location``: the rover's continuous position. It is a
  read-only coordinate; use ``field.rover_location.x`` and
  ``field.rover_location.y``.

- ``field.visible_rover_location``: the rover's current grid cell as an
  ``(x, y)`` tuple of integers. Note this is different from the actual rover
  position, since this is just where you can see the rover. For your precise
  position, defer to field.rover_location.

- ``field.endpoint``: the read-only center coordinate of the endpoint. Access
  its components with ``field.endpoint.x`` and ``field.endpoint.y``.

- ``field.obstacles``: a tuple of read-only center coordinates, one for each
  obstacle. For example, ``[(obstacle.x, obstacle.y) for obstacle in
  field.obstacles]``.

- ``field.map``: a copy of the 2D map, indexed as ``field.map[y][x]``. The
  symbols are ``.`` for open space, ``#`` for the boundary, ``X`` for an
  obstacle, ``E`` for the endpoint, and ``R`` for the rover. The rover and
  endpoint/obstacle symbols represent their visible square footprints.
  Note that coordinates are indexed starting from the top left (meaning that is
  (0,0), and then the other coordinates are increasing going down or right).

- ``field.get_cell(x, y)``: the symbol at one grid coordinate. Coordinates
  outside the field return ``#``.

- ``field.status``: ``"playing"``, ``"won"``, or ``"lost"``.

- ``field.elapsed_time``: elapsed simulation time in seconds.

- ``field.tick_speed``: the duration of one simulation tick in seconds.

- ``field.current_speed``: the rover's speed (the magnitude of its velocity).
    Note that in order to win, you need to score

- ``field.simulation_running``: whether the background simulation is active.
- ``field.render()``: the current map formatted as a printable multi-line
  string.

Rover information (through ``field.rover``):
- ``rover.position``: the same continuous, read-only position coordinate as
  ``field.rover_location``.
- ``rover.visible_position``: the current visible grid cell as an ``(x, y)``
  tuple.
- ``rover.x_speed`` and ``rover.y_speed``: velocity components.
- ``rover.current_speed``: velocity magnitude.
- ``rover.x_acceleration`` and ``rover.y_acceleration``: current acceleration
  components.

Controlling acceleration:
- Return ``(x_acceleration, y_acceleration)`` from a controller passed to
  ``field.run(controller)``. Returning ``None`` means ``(0, 0)``. This is an
  alternative to starting the background simulation manually.
- You may also call ``field.rover.set_acceleration(x, y)`` or assign to
  ``field.rover.x_acceleration`` and ``field.rover.y_acceleration`` while the
  background simulation is running. Acceleration is clamped to the range
  ``-3.0`` through ``3.0`` on each axis - this means that if you enter an
  integer too high or too low, it will automatically set it to the maximum
  acceleration otherwise.

The simulation runs in a background thread after ``field.start_simulation()``.
It can be stopped with ``field.stop_simulation()`` or waited on with
``field.wait_for_simulation(timeout)``.

As a warning, the values above can change while your code is running, so read
them when needed.
"""

# Import statements to allow for getting code from other code modules - you do
# not necessarily need to use all of these, but they are here if needed.
from coordinate import Coordinate
from protected_coordinate import ProtectedCoordinate
from field import Field
from rover import Rover


def main() -> None:
    # This is a prompt for getting a fixed seed to run the simulation on.
    # When you run the program, you will be given this prompt, and you should
    # insert any number to get a seed to generate a map.

    try:
        seed_text = input("Seed (blank for random): ").strip()
        seed = int(seed_text) if seed_text else None
    except EOFError:
        seed = None
    except ValueError:
        print("The seed must be an integer.")
        return

    # Create the game field and start the simulation.
    # This runs on a different thread, which is why the simulation is running
    # even while your code will continue to run.
    field = Field(seed)
    field.start_simulation()

    # Your code goes here!
    # Limit this code to 3 lines of code in this function for set-seed, for
    # random seed limit this to 10 lines of code. To get around this
    # restriction, make functions to do the tasks instead!


# This is the file entry point. When this file is run, the main function
# will run.
if __name__ == "__main__":
    main()
