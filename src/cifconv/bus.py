from dataclasses import dataclass
from typing import List
from cifconv.point import Point


@dataclass
class Bus:
    uuid: str
    points: List[Point]
