import math
from typing import cast

from loguru import logger

from cifconv.bus import Bus
from cifconv.bus_entry import BusEntry
from cifconv.expr import AtomExpr, Expr, ListExpr
from cifconv.junction import Junction
from cifconv.label import Label
from cifconv.no_connect import NoConnect
from cifconv.pin import Pin, PinType
from cifconv.pin_instance import PinInstance
from cifconv.point import Point
from cifconv.schema import Schema
from cifconv.symbol import Symbol
from cifconv.symbol_instance import SymbolInstance
from cifconv.wire import Wire


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
            symbol_name = expect_str(sub_expr.sub_exprs[1])
            pins.extend(collect_pins(symbol_name, sub_expr))

    return Symbol(
        lib_id=id,
        type=type_,
        ref=ref,
        pins=pins,
        package=footprint,
        description=description,
    )


def process_pin(symbol_name: str, pin_expr: ListExpr) -> Pin:
    sub_exprs = expect_list(pin_expr, "pin")
    type_: str = expect_ident(sub_exprs[0])
    name: str | None = None
    number: str = ""
    rel_x: float | None = None
    rel_y: float | None = None
    rotation: float = 0
    for sub_expr in sub_exprs[1:]:
        if is_list(sub_expr, "name"):
            assert isinstance(sub_expr, ListExpr)
            name = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "number"):
            assert isinstance(sub_expr, ListExpr)
            number = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "at"):
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
        number=number,
        name=name,
        type=cast(PinType, type_),
        rel_x=rel_x,
        rel_y=rel_y,
        rotation=rotation,
    )


def collect_pins(symbol_name: str, expr: ListExpr) -> list[Pin]:
    pins: list[Pin] = []
    for sub_expr in expr.sub_exprs:
        if is_list(sub_expr, "pin"):
            assert isinstance(sub_expr, ListExpr)
            pin = process_pin(symbol_name=symbol_name, pin_expr=sub_expr)
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


def process_symbol_instance(
    symbol_instance_expr: ListExpr, schema: Schema
) -> SymbolInstance:
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

    pin_instances: list[PinInstance] = []
    symbol_def = schema.symbols.get(lib_id)
    if symbol_def is not None:
        for pin in symbol_def.pins:
            rad = math.radians(rotation)
            abs_x = x + pin.rel_x * math.cos(rad) - pin.rel_y * math.sin(rad)
            abs_y = y + pin.rel_x * math.sin(rad) + pin.rel_y * math.cos(rad)
            abs_rotation = (pin.rotation + rotation) % 360
            pin_instances.append(
                PinInstance(
                    number=pin.number,
                    name=pin.name,
                    type=pin.type,
                    x=abs_x,
                    y=abs_y,
                    rotation=abs_rotation,
                )
            )

    return SymbolInstance(
        uuid=uuid,
        lib_id=lib_id,
        designator=designator,
        x=x,
        y=y,
        rotation=rotation,
        attributes=attributes,
        pin_instances=pin_instances if pin_instances else None,
    )


def process_wire(wire_expr: ListExpr):
    """
    Process a wire expression and extract its properties.

    This function parses a wire expression to extract the UUID and list of points
    that define the wire's path. It validates that the wire has a UUID and at least
    2 points (to form at least 1 segment).

    Args:
        wire_expr (ListExpr): A list expression representing a wire with the structure:
            (wire (uuid <uuid-string>) (pts (pt <x1> <y1>) (pt <x2> <y2>) ...))

    Returns:
        Wire: A Wire object containing:
            - uuid (str): The unique identifier of the wire
            - points (list[Point]): A list of Point objects defining the wire's path
              defining the wire's path
            - connected_pins (list): An empty list (to be populated later)

    Raises:
        ValueError: If the wire is missing a UUID or has fewer than 2 points
        AssertionError: If the expression structure is malformed or contains
            unexpected data types
    """
    sub_exprs = expect_list(wire_expr, "wire")
    uuid = ""
    points: list[Point] = []
    for sub_expr in sub_exprs:
        if is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "pts"):
            assert isinstance(sub_expr, ListExpr)
            for pt_expr in sub_expr.sub_exprs[1:]:
                assert isinstance(pt_expr, ListExpr)
                x = expect_number(pt_expr.sub_exprs[1])
                y = expect_number(pt_expr.sub_exprs[2])
                points.append(Point(x, y))
    if uuid == "":
        raise ValueError("Wire is missing uuid")
    if len(points) < 2:
        raise ValueError("Wire must have at least 2 segments")
    return Wire(uuid=uuid, points=points, connected_pins=[])


def process_bus(bus_expr: ListExpr):
    """
    Process a bus expression and create a Bus object.

    Extracts UUID and points from a bus list expression and validates that
    the bus has a UUID and at least 2 points (segments).

    Args:
        bus_expr (ListExpr): A list expression containing bus data with 'uuid'
                           and 'pts' sub-expressions.

    Returns:
        Bus: A Bus object with the extracted UUID, points, and an empty list
              of connected pins.

    Raises:
        ValueError: If the bus is missing a UUID or has fewer than 2 points.
        AssertionError: If sub-expressions are not of the expected type (ListExpr).

    Note: Buses share the same structure as wires, but they may be treated differently
      in later processing stages based on their intended use in the circuit design.
    """
    sub_exprs = expect_list(bus_expr, "bus")
    uuid = ""
    points: list[Point] = []
    for sub_expr in sub_exprs:
        if is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])
        elif is_list(sub_expr, "pts"):
            assert isinstance(sub_expr, ListExpr)
            for pt_expr in sub_expr.sub_exprs[1:]:
                assert isinstance(pt_expr, ListExpr)
                x = expect_number(pt_expr.sub_exprs[1])
                y = expect_number(pt_expr.sub_exprs[2])
                points.append(Point(x, y))
    if uuid == "":
        raise ValueError("Bus is missing uuid")
    if len(points) < 2:
        raise ValueError("Bus must have at least 2 segments")
    return Bus(uuid=uuid, points=points, connected_pins=[])


def process_label(label_expr: ListExpr) -> Label:
    """
    Process a local label expression.

    Parses a label expression per the KiCad schematic file format:
        (label "TEXT" (at X Y ROT) (effects ...) (uuid "..."))

    Args:
        label_expr: A list expression representing a label.

    Returns:
        Label: A Label object with text, position, rotation, and uuid.

    Raises:
        ValueError: If the label is missing text, position, or uuid.
    """
    sub_exprs = expect_list(label_expr, "label")
    text = expect_str(sub_exprs[0])
    uuid = ""
    x: float | None = None
    y: float | None = None
    rotation: float = 0
    for sub_expr in sub_exprs[1:]:
        if is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            x = expect_number(sub_expr.sub_exprs[1])
            y = expect_number(sub_expr.sub_exprs[2])
            if len(sub_expr.sub_exprs) > 3:
                rotation = expect_number(sub_expr.sub_exprs[3])
        elif is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])
    if uuid == "":
        raise ValueError("Label is missing uuid")
    if x is None or y is None:
        raise ValueError("Label is missing position (at)")
    return Label(text=text, x=x, y=y, rotation=rotation, uuid=uuid)


def process_junction(junction_expr: ListExpr) -> Junction:
    """
    Process a junction expression.

    Parses a junction expression per the KiCad schematic file format:
        (junction (at X Y) (diameter DIA) (color R G B A) (uuid "..."))

    Args:
        junction_expr: A list expression representing a junction.

    Returns:
        Junction: A Junction object with position and uuid.

    Raises:
        ValueError: If the junction is missing position or uuid.
    """
    sub_exprs = expect_list(junction_expr, "junction")
    uuid = ""
    x: float | None = None
    y: float | None = None

    for sub_expr in sub_exprs:
        if is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            x = expect_number(sub_expr.sub_exprs[1])
            y = expect_number(sub_expr.sub_exprs[2])
        elif is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])

    if uuid == "":
        raise ValueError("Junction is missing uuid")
    if x is None or y is None:
        raise ValueError("Junction is missing position (at)")

    return Junction(x=x, y=y, uuid=uuid)


def process_no_connect(no_connect_expr: ListExpr) -> NoConnect:
    """
    Process a no_connect expression.

    Parses a no_connect expression per the KiCad schematic file format:
        (no_connect (at X Y) (uuid "..."))

    Args:
        no_connect_expr: A list expression representing a no_connect.

    Returns:
        NoConnect: A NoConnect object with position and uuid.

    Raises:
        ValueError: If the no_connect is missing position or uuid.
    """
    sub_exprs = expect_list(no_connect_expr, "no_connect")
    uuid = ""
    x: float | None = None
    y: float | None = None

    for sub_expr in sub_exprs:
        if is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            x = expect_number(sub_expr.sub_exprs[1])
            y = expect_number(sub_expr.sub_exprs[2])
        elif is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])

    if uuid == "":
        raise ValueError("NoConnect is missing uuid")
    if x is None or y is None:
        raise ValueError("NoConnect is missing position (at)")

    return NoConnect(x=x, y=y, uuid=uuid)


def process_bus_entry(bus_entry_expr: ListExpr) -> BusEntry:
    """
    Process a bus_entry expression.

    Parses a bus_entry expression per the KiCad schematic file format:
        (bus_entry (at X Y) (size X Y) (stroke ...) (uuid "..."))

    Args:
        bus_entry_expr: A list expression representing a bus_entry.

    Returns:
        BusEntry: A BusEntry object with position, size, and uuid.

    Raises:
        ValueError: If the bus_entry is missing required fields.
    """
    sub_exprs = expect_list(bus_entry_expr, "bus_entry")
    uuid = ""
    x: float | None = None
    y: float | None = None
    size_x: float = 0  # Default to 0
    size_y: float = 0  # Default to 0

    for sub_expr in sub_exprs:
        if is_list(sub_expr, "at"):
            assert isinstance(sub_expr, ListExpr)
            x = expect_number(sub_expr.sub_exprs[1])
            y = expect_number(sub_expr.sub_exprs[2])
        elif is_list(sub_expr, "size"):
            assert isinstance(sub_expr, ListExpr)
            size_x = expect_number(sub_expr.sub_exprs[1])
            size_y = expect_number(sub_expr.sub_exprs[2])
        elif is_list(sub_expr, "uuid"):
            assert isinstance(sub_expr, ListExpr)
            uuid = expect_str(sub_expr.sub_exprs[1])

    if uuid == "":
        raise ValueError("BusEntry is missing uuid")
    if x is None or y is None:
        raise ValueError("BusEntry is missing position (at)")

    return BusEntry(x=x, y=y, size_x=size_x, size_y=size_y, uuid=uuid)


def cifconv_eval(expr: Expr | None):
    schema = Schema()
    if expr is None:
        return schema
    for expr in eat_header(expr):
        if is_list(expr, "lib_symbols"):
            ident_exprs = expect_list(expr, "lib_symbols")
            for ident_expr in ident_exprs:
                assert isinstance(ident_expr, ListExpr)
                symbol = process_symbol(ident_expr)
                schema.symbols[symbol.lib_id] = symbol
        elif is_list(expr, "symbol"):
            assert isinstance(expr, ListExpr)
            schema.instances.append(process_symbol_instance(expr, schema))
        elif is_list(expr, "wire"):
            assert isinstance(expr, ListExpr)
            wire = process_wire(expr)
            schema.wires[wire.uuid] = wire
        elif is_list(expr, "bus"):
            assert isinstance(expr, ListExpr)
            bus = process_bus(expr)
            schema.buses[bus.uuid] = bus
        elif is_list(expr, "label"):
            assert isinstance(expr, ListExpr)
            schema.labels.append(process_label(expr))
        elif is_list(expr, "junction"):
            assert isinstance(expr, ListExpr)
            junction = process_junction(expr)
            schema.junctions[junction.uuid] = junction
        elif is_list(expr, "no_connect"):
            assert isinstance(expr, ListExpr)
            schema.no_connects.append(process_no_connect(expr))
        elif is_list(expr, "bus_entry"):
            assert isinstance(expr, ListExpr)
            bus_entry = process_bus_entry(expr)
            schema.bus_entries[bus_entry.uuid] = bus_entry
    return schema
