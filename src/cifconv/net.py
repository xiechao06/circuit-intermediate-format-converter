from dataclasses import dataclass
from typing import TYPE_CHECKING

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.point import Point
from cifconv.wire import Wire

if TYPE_CHECKING:
    from cifconv.pin_instance import PinInstance
    from cifconv.symbol_instance import SymbolInstance


@dataclass
class Net:
    """Represents a net in a KiCad schematic, which is a collection of electrically connected elements."""

    uuid: str
    name: str
    wires: list[Wire]
    buses: list[Bus]
    bus_entries: list[BusEntry]
    points: list[Point] | None = None
    connected_pins: list[tuple["SymbolInstance", "PinInstance"]] | None = None
