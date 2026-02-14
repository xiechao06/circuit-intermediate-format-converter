from typing import cast

from loguru import logger

from cifconv.expr import AtomExpr, Expr, ListExpr
from cifconv.pin import Pin, PinType
from cifconv.schema import Schema
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance


def expect_list(expr: Expr, first_token_value: str) -> list[Expr]:
    msg = f"Expected a list starting with '{first_token_value}' at line {expr.line}, column {expr.col}, but got {expr}"
    if not isinstance(expr, ListExpr) or len(expr.sub_exprs) == 0:
        raise ValueError(msg)
    first_token = expr.sub_exprs[0]
    if (
        not isinstance(first_token, AtomExpr)
        or first_token.value.type != first_token.value.type.IDENT
        or first_token.value.value != first_token_value
    ):
        raise ValueError(msg)
    return expr.sub_exprs[1:]


def eat_header(expr: Expr) -> list[Expr]:
    """
    处理[Header Section](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/index.html#_header_section).

    这部分没有需要提确的信息， 只是保证格式正确。
    """
    return expect_list(expr, "kicad_sch")


def expect_number(expr: Expr) -> float:
    if not isinstance(expr, AtomExpr) or expr.value.type != expr.value.type.NUMBER:
        raise ValueError(
            f"Error: Expected a number atom at line {expr.line}, column {expr.col}, but got {expr}"
        )
    return float(expr.value.value)


def expect_str(expr: Expr) -> str:
    if not isinstance(expr, AtomExpr) or expr.value.type != expr.value.type.STRING:
        msg = f"Error: Expected a string atom at line {expr.line}, column {expr.col}, but got {expr}"
        raise ValueError(msg)
    return expr.value.value


def expect_ident(expr: Expr) -> str:
    if not isinstance(expr, AtomExpr) or expr.value.type != expr.value.type.IDENT:
        raise ValueError(
            f"Error: Expected a ident atom at line {expr.line}, column {expr.col}, but got {expr}"
        )
    return expr.value.value


def process_symbol(symbol_expr: ListExpr):
    sub_exprs = expect_list(symbol_expr, "symbol")
    id = expect_str(sub_exprs[0])
    logger.debug(f"Processing symbol with id: {id}")
    type_: str | None = None
    if ":" in id:
        type_, _ = id.split(":", 1)

    ref = ""
    footprint: str | None = None
    pins: list[Pin] = []
    description: str | None = None
    for sub_expr in sub_exprs[1:]:
        if is_list(sub_expr, "property"):
            # extract property
            property_sub_exprs = expect_list(sub_expr, "property")
            property_key = expect_str(property_sub_exprs[0])
            property_value = expect_str(property_sub_exprs[1])
            if property_key == "Reference":
                ref = property_value
            elif property_key == "Footprint":
                footprint = property_value
            elif property_key == "Description":
                description = property_value
        if is_list(sub_expr, "symbol"):
            assert isinstance(sub_expr, ListExpr)
            ident_name = expect_str(sub_expr.sub_exprs[1])
            pins.extend(collect_pins(ident_name, sub_expr))

    return Symbol(
        lib_id=id,
        type=type_,
        ref=ref,
        pins=pins,
        package=footprint,
        description=description,
    )


def process_pin(ident_name: str, pin_expr: ListExpr) -> Pin:
    sub_exprs = expect_list(pin_expr, "pin")
    type_: str = expect_ident(sub_exprs[0])
    name: str | None = None
    id: str = ""
    rel_x: float | None = None
    rel_y: float | None = None
    rotation: float = 0
    for sub_expr in sub_exprs[1:]:
        if is_list(sub_expr, "name"):
            assert isinstance(sub_expr, ListExpr)
            name = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "number"):
            assert isinstance(sub_expr, ListExpr)
            id = ident_name + ":" + expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            rel_x = expect_number(sub_expr.sub_exprs[1])
            rel_y = expect_number(sub_expr.sub_exprs[2])
            rotation = (
                expect_number(sub_expr.sub_exprs[3])
                if len(sub_expr.sub_exprs) > 3
                else 0
            )
    assert name is not None, f"Pin in ident {ident_name} is missing name"
    assert rel_x is not None, (
        f"Pin {name} in ident {ident_name} is missing attribute 'at'"
    )
    assert rel_y is not None, (
        f"Pin {name} in ident {ident_name} is missing attribute 'at'"
    )
    return Pin(
        id=id,
        name=name,
        type=cast(PinType, type_),
        rel_x=rel_x,
        rel_y=rel_y,
        rotation=rotation,
    )


def collect_pins(ident_name: str, expr: ListExpr) -> list[Pin]:
    pins: list[Pin] = []
    for sub_expr in expr.sub_exprs:
        if is_list(sub_expr, "pin"):
            assert isinstance(sub_expr, ListExpr)
            pin = process_pin(ident_name=ident_name, pin_expr=sub_expr)
            pins.append(pin)
    return pins


def is_list(expr: Expr, first_token_value: str) -> bool:
    """Return True if expr is a non-empty ListExpr whose first element is an AtomExpr
    containing a Token whose value matches first_token_value; otherwise False."""
    if not isinstance(expr, ListExpr) or len(expr.sub_exprs) == 0:
        return False
    first_token = expr.sub_exprs[0]
    return (
        isinstance(first_token, AtomExpr)
        and first_token.value.type == first_token.value.type.IDENT
        and first_token.value.value == first_token_value
    )


def process_symbol_instance(symbol_instance_expr: ListExpr) -> SymbolInstance:
    sub_exprs = expect_list(symbol_instance_expr, "symbol")

    lib_id = ""
    uuid = ""
    designator = ""
    x: float | None = None
    y: float | None = None
    rotation: float = 0
    attributes: dict[str, str] = {}
    for sub_expr in sub_exprs:
        if is_list(sub_expr, "lib_id"):
            assert isinstance(sub_expr, ListExpr)
            lib_id = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "property"):
            assert isinstance(sub_expr, ListExpr)
            property_key = expect_str(sub_expr.sub_exprs[1])
            property_value = expect_str(sub_expr.sub_exprs[2])
            if property_key == "Reference":
                designator = property_value
            attributes[property_key] = property_value
        elif is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            x = expect_number(sub_expr.sub_exprs[1])
            y = expect_number(sub_expr.sub_exprs[2])
            if len(sub_expr.sub_exprs) > 3:
                rotation = expect_number(sub_expr.sub_exprs[3])
    if uuid == "":
        raise ValueError("Symbol instance is missing uuid")
    if lib_id == "":
        raise ValueError("Symbol instance is missing lib_id")
    if designator == "":
        raise ValueError("Symbol instance is missing Reference property")
    if x is None or y is None:
        raise ValueError("Symbol instance is missing at property")

    return SymbolInstance(
        uuid=uuid,
        lib_id=lib_id,
        designator=designator,
        x=x,
        y=y,
        rotation=rotation,
        attributes=attributes,
    )


def cifconv_eval(expr: Expr | None):
    schema = Schema(symbols=[], instances=[])
    if expr is None:
        return schema
    for expr in eat_header(expr):
        if is_list(expr, "lib_symbols"):
            ident_exprs = expect_list(expr, "lib_symbols")
            for ident_expr in ident_exprs:
                assert isinstance(ident_expr, ListExpr)
                schema.symbols.append(process_symbol(ident_expr))
        elif is_list(expr, "symbol"):
            assert isinstance(expr, ListExpr)
            schema.instances.append(process_symbol_instance(expr))

    return schema
