#!/usr/bin/env python3
""" "
Tokenizer for the KiCad schematic format. This is a simple implementation that can be improved with more features and error handling.
"""

from sys import stdin

from cifconv.cifconv_token import Token, TokenType


def kicad_sch_tokenize(input_data: str):
    """Tokenize a KiCad schematic source string into a stream of tokens.

    The tokenizer yields Token instances with type, value, column, and line
    information. It recognizes parentheses, quoted strings (with basic escape
    handling), numbers (including negative and decimal forms), and symbols, while
    skipping whitespace and tracking line/column positions.
    """
    i = 0
    line = 1
    col = 1
    while i < len(input_data):
        c = input_data[i]
        if c == "\n":
            line += 1
            col = 1
            i += 1
            continue
        elif c.isspace():
            col += 1
            i += 1
            continue
        elif c == "(":
            yield Token(TokenType.LPAREN, c, col, line)
            col += 1
            i += 1
        elif c == ")":
            yield Token(TokenType.RPAREN, c, col, line)
            col += 1
            i += 1
        elif c == '"':
            start = i + 1
            i += 1
            while i < len(input_data) and input_data[i] != '"':
                if input_data[i] == "\\" and i + 1 < len(input_data):
                    i += 2  # Skip escaped character
                else:
                    i += 1
            yield Token(TokenType.STRING, input_data[start:i], col, line)
            i += 1  # Skip closing quote
            col += i - start + 1
        elif c.isdigit() or (
            c == "-" and i + 1 < len(input_data) and input_data[i + 1].isdigit()
        ):
            start = i
            if c == "-":
                i += 1
            while i < len(input_data) and (
                input_data[i].isdigit() or input_data[i] == "."
            ):
                i += 1
            yield Token(TokenType.NUMBER, input_data[start:i], col, line)
            col += i - start
        else:
            start = i
            while (
                i < len(input_data)
                and not input_data[i].isspace()
                and input_data[i] not in '()"'
            ):
                i += 1
            yield Token(TokenType.SYMBOL, input_data[start:i], col, line)
            col += i - start


if __name__ == "__main__":
    input_data = stdin.read()
    for token in kicad_sch_tokenize(input_data):
        print(token)
