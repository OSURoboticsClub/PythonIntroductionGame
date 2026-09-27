"""Manual terminal preview for the rover game.

Arrow keys or WASD set a sustained maximum acceleration:
left/right = x acceleration, up/down = y acceleration.
Press Space to coast (zero acceleration) and q to quit.
"""

import select
import sys
import termios
import time
import tty

from field import Field


MAX_ACCELERATION = 3.0
LINE_MODE_TICKS = 20


def read_key() -> str | None:
    """Read one key without waiting, translating arrow escape sequences."""
    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return None
    first = sys.stdin.read(1)
    if first != "\x1b":
        return first
    sequence = sys.stdin.read(2)
    return {
        "[A": "up",
        "[B": "down",
        "[C": "right",
        "[D": "left",
    }.get(sequence)


def command_for_key(key: str | None) -> tuple[float, float] | None:
    """Translate an arrow/WASD key into a rover command."""
    if key == "q":
        return None
    if key in ("left", "a"):
        return -MAX_ACCELERATION, 0
    if key in ("right", "d"):
        return MAX_ACCELERATION, 0
    if key in ("up", "w"):
        return 0, -MAX_ACCELERATION
    if key in ("down", "s"):
        return 0, MAX_ACCELERATION
    return 0, 0


def manual_controller(field: Field) -> tuple[float, float] | None:
    key = read_key()
    if key is None:
        # Raw terminal input reports only key presses, not key releases.  Keep
        # applying the selected acceleration until another direction or Space
        # is pressed; otherwise a key would accelerate for just one 0.05s tick.
        return field.rover.x_acceleration, field.rover.y_acceleration
    return command_for_key(key)


def line_controller(field: Field) -> tuple[float, float] | None:
    """IDE-console fallback for streams that do not support raw arrow keys."""
    try:
        key = input("Command [W/A/S/D, Enter=coast, Q=quit]: ").strip().lower()
    except EOFError:
        return None
    return command_for_key(key[:1] if key else None)


def _draw(field: Field, clear: bool) -> None:
    prefix = "\033[H\033[J" if clear else ""
    print(prefix + field.render())
    rover = field.rover
    print("Arrow keys/WASD set acceleration | Space coasts | q quits")
    print("Axes: +x=right, +y=down")
    print(f"velocity:     x={rover.x_speed:+.2f}  y={rover.y_speed:+.2f} units/s  "
          f"speed={field.current_speed:.2f} units/s")
    print(f"acceleration: x={rover.x_acceleration:+.2f}  "
          f"y={rover.y_acceleration:+.2f} units/s^2")
    print(f"seed={field.seed} elapsed={field.elapsed_time:.2f}s status={field.status}")


def main() -> None:
    try:
        seed_text = input("Seed (blank for random): ").strip()
        seed = int(seed_text) if seed_text else None
    except EOFError:
        seed = None
    except ValueError:
        print("The seed must be an integer.")
        return
    field = Field(seed=seed)

    # PyCharm's ordinary Run console is not a real terminal, so termios cannot
    # read arrow keys there.  Offer a line-based WASD mode instead of crashing
    # with "Inappropriate ioctl for device".
    if not sys.stdin.isatty():
        print("Raw arrow-key input is unavailable; using line-based WASD controls.")
        _draw(field, clear=False)
        while field.status == "playing":
            command = line_controller(field)
            if command is None:
                print("Game exited by player.")
                return
            for _ in range(LINE_MODE_TICKS):
                field._tick(*command)
                if field.status != "playing":
                    break
            _draw(field, clear=False)
        print(f"Game ended: {field.status}")
        return

    old_settings = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        _draw(field, clear=True)
        while field.status == "playing":
            command = manual_controller(field)
            if command is None:
                print("Game exited by player.")
                return
            field._tick(*command)
            _draw(field, clear=True)
            time.sleep(field.tick_speed)
        print(f"Game ended: {field.status}")
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()
