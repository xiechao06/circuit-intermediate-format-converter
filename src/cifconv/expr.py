from abc import ABC, abstractmethod
from dataclasses import dataclass

from cifconv.cifconv_token import Token


class Expr(ABC):
    @property
    @abstractmethod
    def line(self) -> int:
        pass

    @property
    @abstractmethod
    def col(self) -> int:
        pass


@dataclass
class ListExpr(Expr):
    sub_exprs: list["Expr"]

    @property
    def line(self) -> int:
        if len(self.sub_exprs) == 0:
            return 0
        return self.sub_exprs[0].line

    @property
    def col(self) -> int:
        if len(self.sub_exprs) == 0:
            return 0
        return self.sub_exprs[0].col


@dataclass
class AtomExpr(Expr):
    value: Token

    @property
    def line(self) -> int:
        return self.value.line

    @property
    def col(self) -> int:
        return self.value.col


@dataclass
class RParenExpr(Expr):
    value: Token

    @property
    def line(self) -> int:
        return self.value.line

    @property
    def col(self) -> int:
        return self.value.col
