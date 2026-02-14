from dataclasses import dataclass


@dataclass
class Label:
    text: str
    x: float
    y: float
    rotation: float
    uuid: str
