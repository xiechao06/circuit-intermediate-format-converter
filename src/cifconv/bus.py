from dataclasses import dataclass


@dataclass
class Bus:
    uuid: str
    points: list[
        tuple[float, float]
    ]  # list of (x, y) coordinates for the wire segments
    connected_pins: list[
        tuple[str, str]
    ]  # list of ref and pin name, e.g. [("U1", "1"), ("R2", "2")]
