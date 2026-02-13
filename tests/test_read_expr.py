from build.lib.cifconv.read_expr import read_expr
from cifconv.cifconv_token import Token, TokenType
from cifconv.expr import AtomExpr, ListExpr, RParenExpr


def test_rparen():
    tokens = [Token(TokenType.RPAREN, ")", 1, 1)]
    expr = read_expr((t for t in tokens))
    assert isinstance(expr, RParenExpr)
    assert expr.value == tokens[0]


def test_atom():
    tokens = [Token(TokenType.SYMBOL, "symbol_name", 1, 1)]
    expr = read_expr((t for t in tokens))
    assert isinstance(expr, AtomExpr)
    assert expr.value == tokens[0]


def test_list():
    tokens = [
        Token(TokenType.LPAREN, "(", 1, 1),
        Token(TokenType.SYMBOL, "symbol_name", 1, 2),
        Token(TokenType.RPAREN, ")", 1, 3),
    ]
    expr = read_expr((t for t in tokens))
    assert isinstance(expr, ListExpr)
    assert len(expr.sub_exprs) == 1
    assert isinstance(expr.sub_exprs[0], AtomExpr)
    assert expr.sub_exprs[0].value == tokens[1]


def test_nested_list():
    # (outer (inner 1 2 3))
    tokens = [
        Token(TokenType.LPAREN, "(", 1, 1),
        Token(TokenType.SYMBOL, "outer", 1, 2),
        Token(TokenType.LPAREN, "(", 1, 3),
        Token(TokenType.SYMBOL, "inner", 1, 4),
        Token(TokenType.NUMBER, "1", 1, 5),
        Token(TokenType.NUMBER, "2", 1, 6),
        Token(TokenType.NUMBER, "3", 1, 7),
        Token(TokenType.RPAREN, ")", 1, 8),
        Token(TokenType.RPAREN, ")", 1, 9),
    ]
    expr = read_expr((t for t in tokens))
    assert isinstance(expr, ListExpr)
    assert len(expr.sub_exprs) == 2
    assert isinstance(expr.sub_exprs[0], AtomExpr)
    assert expr.sub_exprs[0].value == tokens[1]
    assert isinstance(expr.sub_exprs[1], ListExpr)
    assert len(expr.sub_exprs[1].sub_exprs) == 4
    assert isinstance(expr.sub_exprs[1].sub_exprs[0], AtomExpr)
    assert expr.sub_exprs[1].sub_exprs[0].value == tokens[3]
    assert isinstance(expr.sub_exprs[1].sub_exprs[1], AtomExpr)
    assert expr.sub_exprs[1].sub_exprs[1].value == tokens[4]
    assert isinstance(expr.sub_exprs[1].sub_exprs[2], AtomExpr)
    assert expr.sub_exprs[1].sub_exprs[2].value == tokens[5]
    assert isinstance(expr.sub_exprs[1].sub_exprs[3], AtomExpr)
    assert expr.sub_exprs[1].sub_exprs[3].value == tokens[6]
