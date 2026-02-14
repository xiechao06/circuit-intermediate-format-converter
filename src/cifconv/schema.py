from cifconv.bus import Bus
from cifconv.junction import Junction
from cifconv.label import Label
from cifconv.noconnect import NoConnect
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance
from cifconv.wire import Wire


class Schema:
    symbols: list[Symbol] = []
    instances: list[SymbolInstance] = []
    wires: list[Wire] = []
    buses: list[Bus] = []
    labels: list[Label] = []
    junctions: list[Junction] = []
    noconnects: list[NoConnect] = []
