from dataclasses import dataclass


@dataclass
class SymbolInst:
    uuid: str
    ref: str
    symbol_ref: str
    x: float
    y: float
    rotation: float = 0
    description: str | None = None
