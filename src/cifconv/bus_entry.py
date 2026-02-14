from dataclasses import dataclass


@dataclass
class BusEntry:
    """Represents a bus entry in a KiCad schematic."""
    
    x: float
    y: float
    size_x: float
    size_y: float
    uuid: str
    
    @property
    def start_point(self):
        """Get the start point of the bus entry (at position)."""
        return (self.x, self.y)
    
    @property
    def end_point(self):
        """Get the end point of the bus entry (position + size)."""
        return (self.x + self.size_x, self.y + self.size_y)