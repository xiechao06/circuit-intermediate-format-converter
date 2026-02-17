from dataclasses import dataclass

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.junction import Junction
from cifconv.wire import Wire


@dataclass
class Net:
    """Represents a net in a KiCad schematic, which is a collection of electrically connected elements."""

    name: str
    wires: list[Wire]
    buses: list[Bus]
    junctions: list[Junction]
    bus_entries: list[BusEntry]
