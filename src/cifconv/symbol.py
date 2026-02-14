from dataclasses import dataclass

from cifconv.pin import Pin


@dataclass
class Symbol:
    lib_id: str
    type: str | None
    ref: str
    pins: list[Pin]
    package: str | None
    description: str | None = None
