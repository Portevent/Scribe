from enum import Enum


class Role(Enum):
    """What an argument of a command represents"""
    X = "x"  # x coordinate (absolute or relative depending on the command case)
    Y = "y"  # y coordinate
    RX = "rx"  # arc x radius
    RY = "ry"  # arc y radius
    ANGLE = "angle"  # arc x-axis rotation, in degrees
    FLAG = "flag"  # arc large-arc / sweep flag (0 or 1)


_X, _Y = Role.X, Role.Y

# Argument roles of each command (lowercase key, valid for both cases)
ROLES: dict[str, tuple[Role, ...]] = {
    'm': (_X, _Y),
    'l': (_X, _Y),
    'h': (_X,),
    'v': (_Y,),
    'c': (_X, _Y, _X, _Y, _X, _Y),
    's': (_X, _Y, _X, _Y),
    'q': (_X, _Y, _X, _Y),
    't': (_X, _Y),
    'a': (Role.RX, Role.RY, Role.ANGLE, Role.FLAG, Role.FLAG, _X, _Y),
    'z': (),
}
