"""
This is where all of your code to control the rover and make it to the end of
the map! You are allowed to only control the acceleration of the rover,
though you are welcome to access any information about the field, and there is
exposed information as follows that you can use to manipulate the simulation.

Information you have access to (and how to access):
Rover position: Get it from rover.position. It will return




Additionally, you also have some starter code to start up the simulation,
but in order to control the rover you will have to create your own control
functions to do so.
"""
# Import statements to allow for getting code from other code modules.
from coordinate import Coordinate
from protected_coordinate import ProtectedCoordinate
from field import Field
from rover import Rover
from threading import Thread

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