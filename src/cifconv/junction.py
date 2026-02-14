from dataclasses import dataclass


@dataclass
class Junction:
    """Represents a junction in a KiCad schematic."""
    
    x: float
    y: float
    uuid: str