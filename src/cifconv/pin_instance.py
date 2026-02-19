from dataclasses import dataclass

from cifconv.pin import PinType


@dataclass
class PinInstance:
    number: str
    name: str
    type: PinType | None
    x: float
    y: float
    rotation: float
