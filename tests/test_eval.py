import pytest

from cifconv.cifconv_eval import (
    expect_ident,
    expect_list,
    expect_number,
    expect_str,
    is_list,
)
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
