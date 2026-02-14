from dataclasses import dataclass

from cifconv.pin import Pin


@dataclass
class Symbol:
    name: str
    type: str | None
    ref: str
    pins: list[Pin]
    package: str | None
    description: str | None = None
