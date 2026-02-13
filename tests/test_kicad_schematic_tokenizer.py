from cifconv.cifconv_token import Token, TokenType
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize


def test_lparen():
    input_data = "("
    tokens = list(kicad_sch_tokenize(input_data))
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.LPAREN, "(", 1, 1)


def test_rparen():
    input_data = ")"
    tokens = list(kicad_sch_tokenize(input_data))
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.RPAREN, ")", 1, 1)


def test_string():
    input_data = '"Hello, World!"'
    tokens = list(kicad_sch_tokenize(input_data))
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.STRING, "Hello, World!", 1, 1)


def test_number():
    input_data = "123.45"
    tokens = list(kicad_sch_tokenize(input_data))
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.NUMBER, "123.45", 1, 1)


def test_symbol():
    input_data = "symbol_name"
    tokens = list(kicad_sch_tokenize(input_data))
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.SYMBOL, "symbol_name", 1, 1)


def test_complex_input():
    input_data = "\n".join(
        [
            "(symbol",
            '    "R"',
            '    (lib_id "Device:R")',
            "    (at 0 0)",
            "    (unit 1)",
            ")",
        ]
    )

    tokens = list(kicad_sch_tokenize(input_data))
    expected_tokens = [
        Token(TokenType.LPAREN, "(", 1, 1),
        Token(TokenType.SYMBOL, "symbol", 2, 1),
        Token(TokenType.STRING, "R", 5, 2),
        Token(TokenType.LPAREN, "(", 5, 3),
        Token(TokenType.SYMBOL, "lib_id", 6, 3),
        Token(TokenType.STRING, "Device:R", 13, 3),
        Token(TokenType.RPAREN, ")", 23, 3),
        Token(TokenType.LPAREN, "(", 5, 4),
        Token(TokenType.SYMBOL, "at", 6, 4),
        Token(TokenType.NUMBER, "0", 9, 4),
        Token(TokenType.NUMBER, "0", 11, 4),
        Token(TokenType.RPAREN, ")", 12, 4),
        Token(TokenType.LPAREN, "(", 5, 5),
        Token(TokenType.SYMBOL, "unit", 6, 5),
        Token(TokenType.NUMBER, "1", 11, 5),
        Token(TokenType.RPAREN, ")", 12, 5),
        Token(TokenType.RPAREN, ")", 1, 6),
    ]
    assert tokens == expected_tokens
