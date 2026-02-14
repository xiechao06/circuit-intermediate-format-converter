from dataclasses import dataclass


@dataclass
class SymbolInstance:
    uuid: str
    lib_id: str
    designator: str
    x: float
    y: float
    rotation: float = 0
    attributes: dict[str, str] | None = None
    description: str | None = None
