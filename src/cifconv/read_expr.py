from typing import Generator

from cifconv.cifconv_token import Token
from cifconv.expr import AtomExpr, Expr, ListExpr, RParenExpr
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize


def read_expr(tokens: Generator[Token, None, None]) -> Expr | None:
    """Parse a token stream into an expression tree.

    Consumes tokens from the provided generator to build either an AtomExpr,
    a ListExpr for parenthesized lists, or an RParenExpr sentinel. Raises
    ValueError if the input ends unexpectedly inside a list.

    Args:
        tokens: Generator of Token objects to parse.

    Returns:
        Parsed Expr instance, or None if the token stream is exhausted.

    Raises:
        ValueError: If a list begins with '(' and the input ends before its
            matching ')'.
    """
    for token in tokens:
        if token.type == token.type.LPAREN:
            expr_list: list[Expr] = []
            while True:
                sub_expr = read_expr(tokens)
                if sub_expr is None:
                    raise ValueError(
                        f"Unexpected end of input while parsing list starting at line {token.line}, column {token.col}"
                    )
                    break
                if isinstance(sub_expr, RParenExpr):
                    break
                expr_list.append(sub_expr)
            return ListExpr(sub_exprs=expr_list)
        elif token.type == token.type.RPAREN:
            return RParenExpr(token)
        else:
            return AtomExpr(token)


if __name__ == "__main__":
    input_data = """(ident "R" (lib_id "Device:R") (at 0 0) (unit 1)
  (property "Reference" "R1" (id 0) (at 0 0) (layer "F.SilkS"))
  (property "Value" "10k" (id 1) (at 0 0) (layer "F.SilkS"))
  (property "Footprint" "Resistor_SMD:R_0805" (id 2) (at 0 0) (layer "F.SilkS"))
    (pin "1" (at -0.5 0) (length 1) (type passive))
    (pin "2" (at 0.5 0) (length 1) (type passive))
)"""
    expr = read_expr(kicad_sch_tokenize(input_data))
    print(expr)
