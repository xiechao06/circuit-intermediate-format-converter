from typing import cast

from loguru import logger

from cifconv.cifconv_token import Token
from cifconv.expr import AtomExpr, Expr, ListExpr
from cifconv.pin import Pin, PinType
from cifconv.schema import Schema
from cifconv.symbol import Symbol


def _check(msg: str | None):
    if msg is not None:
        raise ValueError(msg)


def should_be_list(expr: Expr, first_token_value: str):
    msg = f"Expected a list starting with '{first_token_value}' at line {expr.line}, column {expr.col}, but got {expr.type}"
    if expr.type != expr.type.LIST:
        return msg
    assert isinstance(expr, ListExpr)

    if len(expr.sub_exprs) == 0:
        return msg

    first_token = expr.sub_exprs[0]

    if first_token.type != first_token.type.ATOM:
        return msg

    assert isinstance(first_token, AtomExpr)
    assert isinstance(first_token.value, Token)

    if first_token.value.value != first_token_value:
        return msg


def extract_list_exprs(expr: Expr, first_token_value: str) -> list[Expr]:
    msg = f"Expected a list starting with '{first_token_value}' at line {expr.line}, column {expr.col}, but got {expr.type}"
    if expr.type != expr.type.LIST:
        raise ValueError(msg)
    assert isinstance(expr, ListExpr)
    if len(expr.sub_exprs) == 0:
        raise ValueError(msg)
    first_token = expr.sub_exprs[0]
    if first_token.type != first_token.type.ATOM:
        raise ValueError(msg)
    assert isinstance(first_token, AtomExpr)
    assert isinstance(first_token.value, Token)
    if first_token.value.value != first_token_value:
        raise ValueError(msg)
    return expr.sub_exprs[1:]


def eat_header(expr: Expr) -> list[Expr]:
    """
    处理[Header Section](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/index.html#_header_section).

    这部分没有需要提确的信息， 只是保证格式正确。
    """
    return extract_list_exprs(expr, "kicad_sch")


def expect_number(expr: Expr) -> float:
    if expr.type != expr.type.ATOM:
        raise ValueError(
            f"Error: Expected a number atom at line {expr.line}, column {expr.col}, but got {expr.type}"
        )
    assert isinstance(expr, AtomExpr)
    if expr.value.type != expr.value.type.NUMBER:
        raise ValueError(
            f"Expected a number token at line {expr.line}, column {expr.col}, but got {expr}"
        )
    return float(expr.value.value)


def expect_str(expr: Expr) -> str:
    if expr.type != expr.type.ATOM:
        raise ValueError(
            f"Error: Expected a string atom at line {expr.line}, column {expr.col}, but got {expr.type}"
        )
    assert isinstance(expr, AtomExpr)
    if expr.value.type != expr.value.type.STRING:
        raise ValueError(
            f"Expected a string token at line {expr.line}, column {expr.col}, but got {expr}"
        )
    return expr.value.value


def process_symbol(symbol_expr: ListExpr):
    sub_exprs = extract_list_exprs(symbol_expr, "symbol")
    id = expect_str(sub_exprs[0])
    logger.debug(f"Processing symbol with id: {id}")
    type_: str | None = None
    name: str = ""
    if ":" in id:
        type_, name = id.split(":", 1)
    else:
        name = id

    ref = ""
    footprint: str | None = None
    pins: list[Pin] = []
    for sub_expr in sub_exprs[1:]:
        if _is_list(sub_expr, "property"):
            # extract property
            property_sub_exprs = extract_list_exprs(sub_expr, "property")
            property_key = expect_str(property_sub_exprs[0])
            property_value = expect_str(property_sub_exprs[1])
            if property_key == "Reference":
                ref = property_value
            elif property_key == "Footprint":
                footprint = property_value
        if _is_list(sub_expr, "symbol"):
            assert isinstance(sub_expr, ListExpr)
            symbol_name = expect_str(sub_expr.sub_exprs[1])
            pins.extend(_collect_symbol_pins(symbol_name, sub_expr))

    return Symbol(
        name=name,
        type=type_,
        ref=ref,
        pins=pins,
        package=footprint,
    )


def expect_symbol(expr: Expr) -> str:
    if expr.type != expr.type.ATOM:
        raise ValueError(
            f"Error: Expected a symbol atom at line {expr.line}, column {expr.col}, but got {expr.type}"
        )
    assert isinstance(expr, AtomExpr)
    if expr.value.type != expr.value.type.SYMBOL:
        raise ValueError(
            f"Expected a symbol token at line {expr.line}, column {expr.col}, but got {expr}"
        )
    return expr.value.value


def _process_pin(symbol_name: str, pin_expr: ListExpr) -> Pin:
    sub_exprs = extract_list_exprs(pin_expr, "pin")
    type_: str = expect_symbol(sub_exprs[0])
    name: str | None = None
    id: str = ""
    rel_x: float | None = None
    rel_y: float | None = None
    rotation: float = 0
    for sub_expr in sub_exprs[1:]:
        if _is_list(sub_expr, "name"):
            assert isinstance(sub_expr, ListExpr)
            name = expect_str(sub_expr.sub_exprs[1])
        elif _is_list(sub_expr, "number"):
            assert isinstance(sub_expr, ListExpr)
            id = symbol_name + ":" + expect_str(sub_expr.sub_exprs[1])
        elif _is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            rel_x = expect_number(sub_expr.sub_exprs[1])
            rel_y = expect_number(sub_expr.sub_exprs[2])
            rotation = (
                expect_number(sub_expr.sub_exprs[3])
                if len(sub_expr.sub_exprs) > 3
                else 0
            )
    assert name is not None, f"Pin in symbol {symbol_name} is missing name"
    assert rel_x is not None, (
        f"Pin {name} in symbol {symbol_name} is missing attribute 'at'"
    )
    assert rel_y is not None, (
        f"Pin {name} in symbol {symbol_name} is missing attribute 'at'"
    )
    return Pin(
        id=id,
        name=name,
        type=cast(PinType, type_),
        rel_x=rel_x,
        rel_y=rel_y,
        rotation=rotation,
    )


def _collect_symbol_pins(symbol_name: str, expr: ListExpr) -> list[Pin]:
    pins: list[Pin] = []
    for sub_expr in expr.sub_exprs:
        if _is_list(sub_expr, "pin"):
            assert isinstance(sub_expr, ListExpr)
            pin = _process_pin(symbol_name=symbol_name, pin_expr=sub_expr)
            pins.append(pin)
    return pins


def _is_list(expr: Expr, first_token_value: str) -> bool:
    if expr.type != expr.type.LIST:
        return False
    assert isinstance(expr, ListExpr)
    if len(expr.sub_exprs) == 0:
        return False
    first_token = expr.sub_exprs[0]
    if first_token.type != first_token.type.ATOM:
        return False
    assert isinstance(first_token, AtomExpr)
    assert isinstance(first_token.value, Token)
    if first_token.value.value != first_token_value:
        return False
    return True


def cifconv_eval(expr: Expr | None):
    schema = Schema(symbols=[])
    if expr is None:
        return schema
    for expr in eat_header(expr):
        if _is_list(expr, "lib_symbols"):
            symbol_exprs = extract_list_exprs(expr, "lib_symbols")
            for symbol_expr in symbol_exprs:
                assert isinstance(symbol_expr, ListExpr)
                schema.symbols.append(process_symbol(symbol_expr))

    return schema
