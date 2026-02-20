from dataclasses import dataclass
from typing import List

from cifconv.point import Point


@dataclass
class Wire:
    uuid: str
    points: List[Point]
