from dataclasses import dataclass

from cifconv.point import Point


@dataclass
class PinInstance:
    """
    Pin instance.
    """

    uuid: str
    number: str
    pos: Point
