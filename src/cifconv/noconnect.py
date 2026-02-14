from dataclasses import dataclass


@dataclass
class NoConnect:
    """Represents a no-connect marker in a KiCad schematic."""
    
    x: float
    y: float
    uuid: str