from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """Represents a point in 2D space with x and y coordinates."""

    x: float
    y: float
