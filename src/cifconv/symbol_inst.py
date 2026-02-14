from dataclasses import dataclass


@dataclass
class identInst:
    uuid: str
    ref: str
    ident_ref: str
    x: float
    y: float
    rotation: float = 0
    description: str | None = None
