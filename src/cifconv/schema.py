from cifconv.bus import Bus
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance
from cifconv.wire import Wire


class Schema:
    symbols: list[Symbol] = []
    instances: list[SymbolInstance] = []
    wires: list[Wire] = []
    buses: list[Bus] = []
