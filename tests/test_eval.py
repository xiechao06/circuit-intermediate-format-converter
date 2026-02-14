import pytest

from cifconv.cifconv_eval import (
    expect_ident,
    expect_list,
    expect_number,
    expect_str,
    is_list,
    process_pin,
    process_symbol,
)
from cifconv.expr import ListExpr
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize
from cifconv.read_expr import read_expr


def test_is_list():
    input_data = "(a b c)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    assert is_list(expr, "a")


def test_expect_number():
    input_data = "123.45"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    assert expect_number(expr) == 123.45  # noqa: F821


def test_expect_number_invalid():
    input_data = '"not a number"'
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a number atom"):
        expect_number(expr)

    input_data = "(foo 1 2)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a number atom"):
        expect_number(expr)


def test_expect_str():
    input_data = '"Hello, World!"'
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    assert expect_str(expr) == "Hello, World!"  # noqa: F821

    input_data = "123.45"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a string atom"):
        expect_str(expr)

    input_data = "(foo bar)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a string atom"):
        expect_str(expr)


def test_expect_ident():
    input_data = "ident_name"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    assert expect_ident(expr) == "ident_name"  # noqa: F821

    input_data = '"not a ident"'
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a ident atom"):
        expect_ident(expr)

    input_data = "(foo bar)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a ident atom"):
        expect_ident(expr)


def test_expect_list():
    input_data = "(kicad_sch foo bar)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    sub_exprs = expect_list(expr, "kicad_sch")  # noqa: F821
    assert len(sub_exprs) == 2
    assert expect_ident(sub_exprs[0]) == "foo"
    assert expect_ident(sub_exprs[1]) == "bar"

    input_data = '"not a list"'
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a list"):
        expect_list(expr, "kicad_sch")

    input_data = "(wrong_type foo bar)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    with pytest.raises(ValueError, match="Expected a list starting with 'kicad_sch'"):
        expect_list(expr, "kicad_sch")


def test_process_pin():
    input_data = """
(pin bidirectional line
    (at -22.86 10.16 0)
    (length 3.81)
    (name "DAT2"
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (number "1"
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
)
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    pin = process_pin("test_ident", expr)
    assert pin.name == "DAT2"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 10.16
    assert pin.rotation == 0
    assert pin.id == "test_ident:1"


def test_process_symbol():
    input_data = """
(symbol "Connector:Micro_SD_Card_Det1"
            (property "Reference" "J"
                (at -16.51 17.78 0)
                (effects
                    (font
                        (size 1.27 1.27)
                    )
                )
            )
            (property "Footprint" "footprint"
                (at 52.07 17.78 0)
                (effects
                    (font
                        (size 1.27 1.27)
                    )
                    (hide yes)
                )
            )
            (property "Description" "Micro SD Card Socket with one card detection pin"
                (at 0 0 0)
                (effects
                    (font
                        (size 1.27 1.27)
                    )
                    (hide yes)
                )
            )
            (symbol "Micro_SD_Card_Det1_1_1"
                (pin bidirectional line
                    (at -22.86 10.16 0)
                    (length 3.81)
                    (name "DAT2"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "1"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin passive line
                    (at 20.32 -12.7 180)
                    (length 3.81)
                    (name "SHIELD"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "10"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin bidirectional line
                    (at -22.86 7.62 0)
                    (length 3.81)
                    (name "DAT3/CD"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "2"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin input line
                    (at -22.86 5.08 0)
                    (length 3.81)
                    (name "CMD"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "3"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin power_in line
                    (at -22.86 2.54 0)
                    (length 3.81)
                    (name "VDD"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "4"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin input line
                    (at -22.86 0 0)
                    (length 3.81)
                    (name "CLK"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "5"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin power_in line
                    (at -22.86 -2.54 0)
                    (length 3.81)
                    (name "VSS"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "6"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin bidirectional line
                    (at -22.86 -5.08 0)
                    (length 3.81)
                    (name "DAT0"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "7"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin bidirectional line
                    (at -22.86 -7.62 0)
                    (length 3.81)
                    (name "DAT1"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "8"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
                (pin passive line
                    (at -22.86 -12.7 0)
                    (length 3.81)
                    (name "DET"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                    (number "9"
                        (effects
                            (font
                                (size 1.27 1.27)
                            )
                        )
                    )
                )
            )
        )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    symbol = process_symbol(expr)
    assert symbol.name == "Micro_SD_Card_Det1"
    assert symbol.type == "Connector"
    assert symbol.ref == "J"
    assert symbol.package == "footprint"
    assert symbol.description == "Micro SD Card Socket with one card detection pin"
    assert len(symbol.pins) == 10
    pin = symbol.pins[0]
    assert pin.name == "DAT2"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 10.16
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:1"

    pin = symbol.pins[1]
    assert pin.name == "SHIELD"
    assert pin.type == "passive"
    assert pin.rel_x == 20.32
    assert pin.rel_y == -12.7
    assert pin.rotation == 180
    assert pin.id == "Micro_SD_Card_Det1_1_1:10"

    pin = symbol.pins[2]
    assert pin.name == "DAT3/CD"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 7.62
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:2"

    pin = symbol.pins[3]
    assert pin.name == "CMD"
    assert pin.type == "input"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 5.08
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:3"

    pin = symbol.pins[4]
    assert pin.name == "VDD"
    assert pin.type == "power_in"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 2.54
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:4"

    pin = symbol.pins[5]
    assert pin.name == "CLK"
    assert pin.type == "input"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 0
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:5"

    pin = symbol.pins[6]
    assert pin.name == "VSS"
    assert pin.type == "power_in"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -2.54
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:6"

    pin = symbol.pins[7]
    assert pin.name == "DAT0"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -5.08
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:7"

    pin = symbol.pins[8]
    assert pin.name == "DAT1"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -7.62
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:8"

    pin = symbol.pins[9]
    assert pin.name == "DET"
    assert pin.type == "passive"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -12.7
    assert pin.rotation == 0
    assert pin.id == "Micro_SD_Card_Det1_1_1:9"
