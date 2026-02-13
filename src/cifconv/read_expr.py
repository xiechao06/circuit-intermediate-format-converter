from os import abort
from typing import Generator

from cifconv.cifconv_token import Token
from cifconv.expr import AtomExpr, Expr, ExprType, ListExpr, RParenExpr
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize


def error(message: str):
    print(f"Error: {message}")
    abort()


def read_expr(tokens: Generator[Token, None, None]) -> Expr | None:
    for token in tokens:
        if token.type == token.type.LPAREN:
            expr_list: list[Expr] = []
            while True:
                sub_expr = read_expr(tokens)
                if sub_expr is None:
                    error(
                        f"Unexpected end of input while parsing list starting at line {token.line}, column {token.col}"
                    )
                    break
                if sub_expr.type == ExprType.RPAREN:
                    break
                expr_list.append(sub_expr)
            return ListExpr(
                ExprType.LIST, sub_exprs=expr_list, line=token.line, col=token.col
            )
        elif token.type == token.type.RPAREN:
            return RParenExpr(
                ExprType.RPAREN, value=token, line=token.line, col=token.col
            )
        else:
            return AtomExpr(ExprType.ATOM, value=token, line=token.line, col=token.col)


if __name__ == "__main__":
    input_data = """(symbol "R" (lib_id "Device:R") (at 0 0) (unit 1)
  (property "Reference" "R1" (id 0) (at 0 0) (layer "F.SilkS"))
  (property "Value" "10k" (id 1) (at 0 0) (layer "F.SilkS"))
  (property "Footprint" "Resistor_SMD:R_0805" (id 2) (at 0 0) (layer "F.SilkS"))
    (pin "1" (at -0.5 0) (length 1) (type passive))
    (pin "2" (at 0.5 0) (length 1) (type passive))
)"""
    expr = read_expr(kicad_sch_tokenize(input_data))
    print(expr)
