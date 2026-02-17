from dataclasses import dataclass
from typing import List
from cifconv.point import Point


@dataclass
class Bus:
    uuid: str
    points: List[Point]  # list of Point objects for the bus segments
    connected_pins: list[
        tuple[str, str]
    ]  # list of ref and pin name, e.g. [("U1", "1"), ("R2", "2")]
