from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    LPAREN = auto()
    RPAREN = auto()
    STRING = auto()
    IDENT = auto()
    NUMBER = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    col: int
    line: int
