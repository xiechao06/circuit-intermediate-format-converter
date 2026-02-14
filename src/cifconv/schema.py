from dataclasses import dataclass

from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance


@dataclass
class Schema:
    symbols: list[Symbol]
    instances: list[SymbolInstance]
