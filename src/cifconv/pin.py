from dataclasses import dataclass
from typing import Literal

PinType = Literal[
    "input",
    "output",
    "bidirectional",
    "tri_state",
    "passive",
    "free",
    "unspecified",
    "power_in",
    "power_out",
    "open_collector",
    "open_emitter",
    "no_connect",
]


@dataclass
class Pin:
    number: str
    name: str
    # see https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_ident_pin
    type: PinType | None
    rel_x: float
    rel_y: float
    rotation: float = 0
