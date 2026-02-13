from dataclasses import dataclass

from cifconv.symbol import Symbol


@dataclass
class Schema:
    symbols: list[Symbol]
