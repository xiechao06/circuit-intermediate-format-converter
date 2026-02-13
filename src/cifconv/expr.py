import enum
from dataclasses import dataclass

from cifconv.cifconv_token import Token


class ExprType(enum.Enum):
    ATOM = enum.auto()
    LIST = enum.auto()
    RPAREN = enum.auto()


@dataclass
class Expr:
    type: ExprType
    line: int
    col: int


@dataclass
class ListExpr(Expr):
    sub_exprs: list["Expr"]


@dataclass
class AtomExpr(Expr):
    value: Token


@dataclass
class RParenExpr(Expr):
    value: Token
