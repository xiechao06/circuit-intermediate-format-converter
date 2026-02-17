from dataclasses import dataclass

from cifconv.point import Point


@dataclass
class BusEntry:
    """Represents a bus entry in a KiCad schematic."""

    x: float
    y: float
    size_x: float
    size_y: float
    uuid: str

    @property
    def start_point(self) -> Point:
        """Get the start point of the bus entry (at position)."""
        return Point(self.x, self.y)

    @property
    def end_point(self) -> Point:
        """Get the end point of the bus entry (position + size)."""
        return Point(self.x + self.size_x, self.y + self.size_y)
