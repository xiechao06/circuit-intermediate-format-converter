import pytest

from cifconv.cifconv_eval import (
    expect_ident,
    expect_list,
    expect_number,
    expect_str,
    is_list,
    process_bus_entry,
    process_junction,
    process_label,
    process_no_connect,
    process_pin,
    process_symbol,
    process_symbol_instance,
    process_wire,
)
from cifconv.expr import ListExpr
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize
from cifconv.label import Label
from cifconv.point import Point
from cifconv.read_expr import read_expr
from cifconv.wire import Wire


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
    assert pin.number == "1"


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
    assert symbol.lib_id == "Connector:Micro_SD_Card_Det1"
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
    assert pin.number == "1"

    pin = symbol.pins[1]
    assert pin.name == "SHIELD"
    assert pin.type == "passive"
    assert pin.rel_x == 20.32
    assert pin.rel_y == -12.7
    assert pin.rotation == 180
    assert pin.number == "10"

    pin = symbol.pins[2]
    assert pin.name == "DAT3/CD"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 7.62
    assert pin.rotation == 0
    assert pin.number == "2"

    pin = symbol.pins[3]
    assert pin.name == "CMD"
    assert pin.type == "input"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 5.08
    assert pin.rotation == 0
    assert pin.number == "3"

    pin = symbol.pins[4]
    assert pin.name == "VDD"
    assert pin.type == "power_in"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 2.54
    assert pin.rotation == 0
    assert pin.number == "4"

    pin = symbol.pins[5]
    assert pin.name == "CLK"
    assert pin.type == "input"
    assert pin.rel_x == -22.86
    assert pin.rel_y == 0
    assert pin.rotation == 0
    assert pin.number == "5"

    pin = symbol.pins[6]
    assert pin.name == "VSS"
    assert pin.type == "power_in"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -2.54
    assert pin.rotation == 0
    assert pin.number == "6"

    pin = symbol.pins[7]
    assert pin.name == "DAT0"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -5.08
    assert pin.rotation == 0
    assert pin.number == "7"

    pin = symbol.pins[8]
    assert pin.name == "DAT1"
    assert pin.type == "bidirectional"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -7.62
    assert pin.rotation == 0
    assert pin.number == "8"

    pin = symbol.pins[9]
    assert pin.name == "DET"
    assert pin.type == "passive"
    assert pin.rel_x == -22.86
    assert pin.rel_y == -12.7
    assert pin.rotation == 0
    assert pin.number == "9"


def test_process_symbol_instance():
    input_data = """
(symbol
    (lib_id "Connector_Generic:Conn_01x09")
    (at 66.04 93.98 270)
    (unit 1)
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (fields_autoplaced yes)
    (uuid "02450218-5adf-4bf1-8fee-f81b71280256")
    (property "Reference" "J3"
        (at 66.04 97.79 90)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (property "Value" "Conn_01x09"
        (at 66.04 100.33 90)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
    )
    (property "Footprint" "Connector_FFC-FPC:TE_0-1734839-9_1x09-1MP_P0.5mm_Horizontal"
        (at 66.04 93.98 0)
        (effects
            (font
                (size 1.27 1.27)
            )
            (hide yes)
        )
    )
    (property "Datasheet" "~"
        (at 66.04 93.98 0)
        (effects
            (font
                (size 1.27 1.27)
            )
            (hide yes)
        )
    )
    (property "Description" "Generic connector, single row, 01x09, script generated (kicad-library-utils/schlib/autogen/connector/)"
        (at 66.04 93.98 0)
        (effects
            (font
                (size 1.27 1.27)
            )
            (hide yes)
        )
    )
    (pin "4"
        (uuid "2ccd2220-9a06-47c9-90c3-970ab2dac82f")
    )
    (pin "5"
        (uuid "52a1baa9-650d-49f0-9836-4155733d74d1")
    )
    (pin "6"
        (uuid "94b1007a-5641-43c9-b1e3-bad870f511c9")
    )
    (pin "7"
        (uuid "3606f00d-7456-4608-b27e-c3d17bd862b0")
    )
    (pin "8"
        (uuid "6dfac76a-7962-421d-a69b-ebfe93098606")
    )
    (pin "9"
        (uuid "1722b38f-529f-4909-a0c9-598ba8991645")
    )
    (pin "1"
        (uuid "894003e2-065f-43d9-a3ec-023da06229d9")
    )
    (pin "2"
        (uuid "90faf26b-71a8-4153-afe7-a07c38f822ed")
    )
    (pin "3"
        (uuid "9432e83a-d69b-466f-99f6-7821a304bfb5")
    )
    (instances
        (project ""
            (path "/6bdfbe6c-bf58-4ff9-82c4-7d07673f6195"
                (reference "J3")
                (unit 1)
            )
        )
    )
)
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    from cifconv.schema import Schema

    schema = Schema()
    symbol_instance = process_symbol_instance(expr, schema)

    assert symbol_instance.uuid == "02450218-5adf-4bf1-8fee-f81b71280256"
    assert symbol_instance.lib_id == "Connector_Generic:Conn_01x09"
    assert symbol_instance.designator == "J3"

    assert symbol_instance.x == 66.04
    assert symbol_instance.y == 93.98
    assert symbol_instance.rotation == 270
    assert symbol_instance.attributes is not None
    assert (
        symbol_instance.attributes["Description"]
        == "Generic connector, single row, 01x09, script generated (kicad-library-utils/schlib/autogen/connector/)"
    )
    assert (
        symbol_instance.attributes["Footprint"]
        == "Connector_FFC-FPC:TE_0-1734839-9_1x09-1MP_P0.5mm_Horizontal"
    )
    assert symbol_instance.attributes["Value"] == "Conn_01x09"
    assert symbol_instance.attributes["Reference"] == "J3"
    assert symbol_instance.attributes["Datasheet"] == "~"


def test_process_wire():
    from cifconv.point import Point

    input_data = """
    (wire
        (pts
            (xy 69.85 115.57) (xy 69.85 130.81)
        )
        (stroke
            (width 0)
            (type default)
        )
        (uuid "05c18f37-f35e-48ba-868c-337da2308d7c")
    )
"""

    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    wire = process_wire(expr)

    assert wire.uuid == "05c18f37-f35e-48ba-868c-337da2308d7c"
    assert len(wire.points) == 2
    assert wire.points[0] == Point(69.85, 115.57)
    assert wire.points[1] == Point(69.85, 130.81)


def test_process_label():
    input_data = """
    (label "SD_D1"
        (at 100.5 50.25 0)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
        (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    label = process_label(expr)

    assert label.text == "SD_D1"
    assert label.x == 100.5
    assert label.y == 50.25
    assert label.rotation == 0
    assert label.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def test_process_label_with_rotation():
    input_data = """
    (label "CLK"
        (at 200 150 90)
        (effects
            (font
                (size 1.27 1.27)
            )
        )
        (uuid "11111111-2222-3333-4444-555555555555")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    label = process_label(expr)

    assert label.text == "CLK"
    assert label.x == 200
    assert label.y == 150
    assert label.rotation == 90
    assert label.uuid == "11111111-2222-3333-4444-555555555555"


def test_process_label_missing_uuid():
    input_data = """
    (label "NET"
        (at 10 20 0)
        (effects (font (size 1.27 1.27)))
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="Label is missing uuid"):
        process_label(expr)


def test_process_label_missing_at():
    input_data = """
    (label "NET"
        (effects (font (size 1.27 1.27)))
        (uuid "aaa-bbb")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="Label is missing position"):
        process_label(expr)


def test_process_junction():
    input_data = """
    (junction
        (at 100.5 50.25)
        (diameter 0)
        (color 0 0 0 0)
        (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    junction = process_junction(expr)

    assert junction.x == 100.5
    assert junction.y == 50.25
    assert junction.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def test_process_junction_without_optional_fields():
    input_data = """
    (junction
        (at 200 150)
        (uuid "11111111-2222-3333-4444-555555555555")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    junction = process_junction(expr)

    assert junction.x == 200
    assert junction.y == 150
    assert junction.uuid == "11111111-2222-3333-4444-555555555555"


def test_process_junction_missing_uuid():
    input_data = """
    (junction
        (at 10 20)
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="Junction is missing uuid"):
        process_junction(expr)


def test_process_junction_missing_at():
    input_data = """
    (junction
        (uuid "aaa-bbb")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="Junction is missing position"):
        process_junction(expr)


def test_process_no_connect():
    input_data = """
    (no_connect
        (at 100.5 50.25)
        (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    no_connect = process_no_connect(expr)

    assert no_connect.x == 100.5
    assert no_connect.y == 50.25
    assert no_connect.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def test_process_no_connect_missing_uuid():
    input_data = """
    (no_connect
        (at 10 20)
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="NoConnect is missing uuid"):
        process_no_connect(expr)


def test_process_no_connect_missing_at():
    input_data = """
    (no_connect
        (uuid "aaa-bbb")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="NoConnect is missing position"):
        process_no_connect(expr)


def test_process_bus_entry():
    input_data = """
    (bus_entry
        (at 100.5 50.25)
        (size 5.0 3.0)
        (stroke (width 0.1524) (type solid) (color 0 0 0 0))
        (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    bus_entry = process_bus_entry(expr)

    assert bus_entry.x == 100.5
    assert bus_entry.y == 50.25
    assert bus_entry.size_x == 5.0
    assert bus_entry.size_y == 3.0
    assert bus_entry.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    # Test getter properties
    assert bus_entry.start_point == Point(100.5, 50.25)
    assert bus_entry.end_point == Point(105.5, 53.25)


def test_process_bus_entry_without_size():
    input_data = """
    (bus_entry
        (at 200 150)
        (uuid "11111111-2222-3333-4444-555555555555")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    bus_entry = process_bus_entry(expr)

    assert bus_entry.x == 200
    assert bus_entry.y == 150
    assert bus_entry.size_x == 0  # Default value
    assert bus_entry.size_y == 0  # Default value
    assert bus_entry.uuid == "11111111-2222-3333-4444-555555555555"

    # Test getter properties with default size
    assert bus_entry.start_point == Point(200, 150)
    assert bus_entry.end_point == Point(200, 150)  # Same as start when size is 0


def test_process_bus_entry_missing_uuid():
    input_data = """
    (bus_entry
        (at 10 20)
        (size 5 3)
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="BusEntry is missing uuid"):
        process_bus_entry(expr)


def test_process_bus_entry_missing_at():
    input_data = """
    (bus_entry
        (size 5 3)
        (uuid "aaa-bbb")
    )
"""
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    with pytest.raises(ValueError, match="BusEntry is missing position"):
        process_bus_entry(expr)


def test_schema_nets_property():
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a simple schema with a wire and a label
    schema = Schema()

    # Add a wire
    wire = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    schema.wires[wire.uuid] = wire

    # Add a label at the same position as the wire
    label = Label(text="VCC", x=0, y=0, rotation=0, uuid="label-uuid-1")
    schema.labels.append(label)

    # The net should be named after the label
    nets = schema.nets
    assert len(nets) >= 1  # There should be at least one net
    assert any(
        net.name == "VCC" for net in nets
    )  # At least one net should be named VCC


def test_schema_nets_property_unnamed_net():
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with a wire but no label
    schema = Schema()

    # Add a wire
    wire = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    schema.wires[wire.uuid] = wire

    # The net should be named with the default naming scheme
    nets = schema.nets
    # Since there's only one net and it has no label, it should be named "net_0"
    assert any(net.name.startswith("net_") for net in nets)


def test_schema_nets_property_multiple_connected_elements():
    from cifconv.junction import Junction
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with multiple connected elements
    schema = Schema()

    # Add two wires that connect at a point
    wire1 = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    wire2 = Wire(
        uuid="wire-uuid-2", points=[Point(10, 0), Point(20, 0)], connected_pins=[]
    )
    schema.wires[wire1.uuid] = wire1
    schema.wires[wire2.uuid] = wire2

    # Add a junction at the connection point
    junction = Junction(x=10, y=0, uuid="junction-uuid-1")
    schema.junctions[junction.uuid] = junction

    # Add a label at the connection point
    label = Label(text="SIGNAL_A", x=10, y=0, rotation=0, uuid="label-uuid-1")
    schema.labels.append(label)

    # The connected components should form one net named after the label
    nets = schema.nets
    assert any(net.name == "SIGNAL_A" for net in nets)
    assert len(nets) == 1  # Only one net should be formed


def test_schema_nets_with_bus_and_bus_entry():
    from cifconv.bus import Bus
    from cifconv.bus_entry import BusEntry
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with a bus, bus entry, and wire
    schema = Schema()

    # Add a bus
    bus = Bus(uuid="bus-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[])
    schema.buses[bus.uuid] = bus

    # Add a bus entry that connects to the bus
    bus_entry = BusEntry(x=10, y=0, size_x=0, size_y=5, uuid="bus-entry-uuid-1")
    schema.bus_entries[bus_entry.uuid] = bus_entry

    # Add a wire that connects to the end of the bus entry
    wire = Wire(
        uuid="wire-uuid-1", points=[Point(10, 5), Point(20, 5)], connected_pins=[]
    )
    schema.wires[wire.uuid] = wire

    # Add a label at the connection point
    label = Label(text="BUS_SIGNAL", x=10, y=0, rotation=0, uuid="label-uuid-1")
    schema.labels.append(label)

    # The connected components should form one net named after the label
    nets = schema.nets
    assert len(nets) == 1  # Only one net should be formed
    assert nets[0].name == "BUS_SIGNAL"  # Named after the label
    assert len(nets[0].buses) == 1  # Should contain the bus
    assert len(nets[0].bus_entries) == 1  # Should contain the bus entry
    assert len(nets[0].wires) == 1  # Should contain the wire


def test_schema_nets_with_multiple_buses_connected_via_junction():
    from cifconv.bus import Bus
    from cifconv.junction import Junction
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema

    # Create a schema with multiple buses connected via a junction
    schema = Schema()

    # Add first bus
    bus1 = Bus(uuid="bus-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[])
    schema.buses[bus1.uuid] = bus1

    # Add second bus
    bus2 = Bus(
        uuid="bus-uuid-2", points=[Point(10, 0), Point(20, 0)], connected_pins=[]
    )
    schema.buses[bus2.uuid] = bus2

    # Add a junction at the connection point
    junction = Junction(x=10, y=0, uuid="junction-uuid-1")
    schema.junctions[junction.uuid] = junction

    # Add a label at the connection point
    label = Label(text="MULTI_BUS_NET", x=10, y=0, rotation=0, uuid="label-uuid-1")
    schema.labels.append(label)

    # The connected buses should form one net named after the label
    nets = schema.nets
    assert len(nets) == 1  # Only one net should be formed
    assert nets[0].name == "MULTI_BUS_NET"  # Named after the label
    assert len(nets[0].buses) == 2  # Should contain both buses
    assert len(nets[0].junctions) == 1  # Should contain the junction


def test_schema_nets_multiple_separate_networks():
    from cifconv.bus import Bus
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with multiple separate networks
    schema = Schema()

    # Network 1: A wire with a label
    wire1 = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    schema.wires[wire1.uuid] = wire1
    label1 = Label(text="NET_A", x=0, y=0, rotation=0, uuid="label-uuid-1")
    schema.labels.append(label1)

    # Network 2: A bus with a label (separate from Network 1)
    bus1 = Bus(
        uuid="bus-uuid-1", points=[Point(20, 20), Point(30, 20)], connected_pins=[]
    )
    schema.buses[bus1.uuid] = bus1
    label2 = Label(text="NET_B", x=20, y=20, rotation=0, uuid="label-uuid-2")
    schema.labels.append(label2)

    # Network 3: A wire without a label (should get auto-generated name)
    wire2 = Wire(
        uuid="wire-uuid-2", points=[Point(40, 40), Point(50, 40)], connected_pins=[]
    )
    schema.wires[wire2.uuid] = wire2

    # There should be 3 separate nets
    nets = schema.nets
    assert len(nets) == 3

    # Check that labeled nets have correct names
    net_names = [net.name for net in nets]
    assert "NET_A" in net_names
    assert "NET_B" in net_names

    # Check that there's a net with an auto-generated name
    auto_named_nets = [net for net in nets if net.name.startswith("net_")]
    assert len(auto_named_nets) == 1


def test_schema_nets_multiple_connected_components():
    from cifconv.bus_entry import BusEntry
    from cifconv.junction import Junction
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with multiple connected components
    schema = Schema()

    # Component 1: Two wires connected by a junction with a label
    wire1 = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    wire2 = Wire(
        uuid="wire-uuid-2", points=[Point(10, 0), Point(20, 0)], connected_pins=[]
    )
    junction1 = Junction(x=10, y=0, uuid="junction-uuid-1")
    label1 = Label(text="POWER_RAIL", x=10, y=0, rotation=0, uuid="label-uuid-1")

    schema.wires[wire1.uuid] = wire1
    schema.wires[wire2.uuid] = wire2
    schema.junctions[junction1.uuid] = junction1
    schema.labels.append(label1)

    # Component 2: A bus entry and wire with a different label
    bus_entry = BusEntry(x=30, y=30, size_x=0, size_y=5, uuid="bus-entry-uuid-1")
    wire3 = Wire(
        uuid="wire-uuid-3", points=[Point(30, 35), Point(40, 35)], connected_pins=[]
    )
    label2 = Label(text="DATA_LINE", x=30, y=30, rotation=0, uuid="label-uuid-2")

    schema.bus_entries[bus_entry.uuid] = bus_entry
    schema.wires[wire3.uuid] = wire3
    schema.labels.append(label2)

    # Component 3: Unconnected wire without a label
    wire4 = Wire(
        uuid="wire-uuid-4", points=[Point(50, 50), Point(60, 50)], connected_pins=[]
    )
    schema.wires[wire4.uuid] = wire4

    # There should be 3 separate nets
    nets = schema.nets
    assert len(nets) == 3

    # Check that each net has the expected name
    net_names = [net.name for net in nets]
    assert "POWER_RAIL" in net_names
    assert "DATA_LINE" in net_names

    # Check that there's one auto-named net
    auto_named_nets = [net for net in nets if net.name.startswith("net_")]
    assert len(auto_named_nets) == 1

    # Verify that elements are properly grouped in their respective nets
    power_net = next(net for net in nets if net.name == "POWER_RAIL")
    assert len(power_net.wires) == 2
    assert len(power_net.junctions) == 1

    data_net = next(net for net in nets if net.name == "DATA_LINE")
    assert len(data_net.bus_entries) == 1
    assert len(data_net.wires) == 1

    auto_net = next(net for net in nets if net.name.startswith("net_"))
    assert len(auto_net.wires) == 1


def test_schema_nets_labels_on_wire_points():
    from cifconv.label import Label
    from cifconv.point import Point
    from cifconv.schema import Schema
    from cifconv.wire import Wire

    # Create a schema with wires and labels positioned on wire points
    schema = Schema()

    # Wire 1: from (0, 0) to (10, 0)
    wire1 = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )
    schema.wires[wire1.uuid] = wire1

    # Wire 2: from (20, 0) to (30, 0)
    wire2 = Wire(
        uuid="wire-uuid-2", points=[Point(20, 0), Point(30, 0)], connected_pins=[]
    )
    schema.wires[wire2.uuid] = wire2

    # Labels positioned on wire points (endpoints)
    label1 = Label(text="NET1", x=0, y=0, rotation=0, uuid="label-1")
    label2 = Label(text="NET2", x=20, y=0, rotation=0, uuid="label-2")
    schema.labels.append(label1)
    schema.labels.append(label2)

    # There should be 2 separate nets
    nets = schema.nets
    assert len(nets) == 2

    net_names = [net.name for net in nets]
    assert "NET1" in net_names
    assert "NET2" in net_names


def test_pin_instance_creation():
    from cifconv.pin_instance import PinInstance

    pin_instance = PinInstance(
        number="1",
        name="VCC",
        type="power_in",
        x=100.0,
        y=50.0,
        rotation=90.0,
    )

    assert pin_instance.number == "1"
    assert pin_instance.name == "VCC"
    assert pin_instance.type == "power_in"
    assert pin_instance.x == 100.0
    assert pin_instance.y == 50.0
    assert pin_instance.rotation == 90.0


def test_pin_instance_with_none_type():
    from cifconv.pin_instance import PinInstance

    pin_instance = PinInstance(
        number="2",
        name="GND",
        type=None,
        x=0.0,
        y=0.0,
        rotation=0.0,
    )

    assert pin_instance.number == "2"
    assert pin_instance.name == "GND"
    assert pin_instance.type is None
    assert pin_instance.x == 0.0
    assert pin_instance.y == 0.0
    assert pin_instance.rotation == 0.0


def test_symbol_instance_with_pin_instances():
    from cifconv.pin_instance import PinInstance
    from cifconv.symbol_instance import SymbolInstance

    pin_instances = [
        PinInstance(
            number="1", name="VCC", type="power_in", x=10.0, y=20.0, rotation=0.0
        ),
        PinInstance(
            number="2", name="GND", type="power_in", x=10.0, y=30.0, rotation=0.0
        ),
        PinInstance(
            number="3", name="OUT", type="output", x=20.0, y=25.0, rotation=180.0
        ),
    ]

    symbol_instance = SymbolInstance(
        uuid="test-uuid-123",
        lib_id="Device:R",
        designator="R1",
        x=50.0,
        y=50.0,
        rotation=90.0,
        attributes={"Value": "10k"},
        pin_instances=pin_instances,
    )

    assert symbol_instance.uuid == "test-uuid-123"
    assert symbol_instance.lib_id == "Device:R"
    assert symbol_instance.designator == "R1"
    assert symbol_instance.x == 50.0
    assert symbol_instance.y == 50.0
    assert symbol_instance.rotation == 90.0
    assert symbol_instance.pin_instances is not None
    assert len(symbol_instance.pin_instances) == 3
    assert symbol_instance.pin_instances[0].name == "VCC"
    assert symbol_instance.pin_instances[1].name == "GND"
    assert symbol_instance.pin_instances[2].name == "OUT"


def test_symbol_instance_without_pin_instances():
    from cifconv.symbol_instance import SymbolInstance

    symbol_instance = SymbolInstance(
        uuid="test-uuid-456",
        lib_id="Device:C",
        designator="C1",
        x=100.0,
        y=100.0,
        rotation=0.0,
    )

    assert symbol_instance.pin_instances is None


def test_net_with_points():
    from cifconv.net import Net

    wire = Wire(
        uuid="wire-uuid-1",
        points=[Point(0, 0), Point(10, 0), Point(10, 10)],
        connected_pins=[],
    )

    net = Net(
        name="TEST_NET",
        wires=[wire],
        buses=[],
        junctions=[],
        bus_entries=[],
        points=[Point(0, 0), Point(10, 0), Point(10, 10)],
    )

    assert net.name == "TEST_NET"
    assert net.points is not None
    assert len(net.points) == 3
    assert Point(0, 0) in net.points
    assert Point(10, 0) in net.points
    assert Point(10, 10) in net.points


def test_net_with_connected_pins():
    from cifconv.net import Net
    from cifconv.pin_instance import PinInstance
    from cifconv.symbol_instance import SymbolInstance

    wire = Wire(
        uuid="wire-uuid-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[]
    )

    pin1 = PinInstance(
        number="1", name="OUT", type="output", x=0.0, y=0.0, rotation=0.0
    )
    pin2 = PinInstance(
        number="2", name="IN", type="input", x=10.0, y=0.0, rotation=180.0
    )

    instance1 = SymbolInstance(
        uuid="inst-uuid-1",
        lib_id="Device:R",
        designator="R1",
        x=0.0,
        y=0.0,
        pin_instances=[pin1],
    )
    instance2 = SymbolInstance(
        uuid="inst-uuid-2",
        lib_id="Device:R",
        designator="R2",
        x=10.0,
        y=0.0,
        pin_instances=[pin2],
    )

    net = Net(
        name="CONNECTED_NET",
        wires=[wire],
        buses=[],
        junctions=[],
        bus_entries=[],
        points=[Point(0, 0), Point(10, 0)],
        connected_pins=[(instance1, pin1), (instance2, pin2)],
    )

    assert net.connected_pins is not None
    assert len(net.connected_pins) == 2
    assert net.connected_pins[0][0].designator == "R1"
    assert net.connected_pins[0][1].name == "OUT"
    assert net.connected_pins[1][0].designator == "R2"
    assert net.connected_pins[1][1].name == "IN"


def test_process_symbol_instance_with_symbol_definition():
    input_symbol = """
(symbol "Device:R"
    (property "Reference" "R"
        (at 0 0 0)
        (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0805"
        (at 0 0 0)
        (effects (font (size 1.27 1.27)) (hide yes))
    )
    (symbol "R_1_1"
        (pin passive line
            (at -5.08 0 0)
            (length 2.54)
            (name "1"
                (effects (font (size 1.27 1.27)))
            )
            (number "1"
                (effects (font (size 1.27 1.27)))
            )
        )
        (pin passive line
            (at 5.08 0 180)
            (length 2.54)
            (name "2"
                (effects (font (size 1.27 1.27)))
            )
            (number "2"
                (effects (font (size 1.27 1.27)))
            )
        )
    )
)
"""
    input_instance = """
(symbol
    (lib_id "Device:R")
    (at 100 50 0)
    (uuid "test-instance-uuid")
    (property "Reference" "R1"
        (at 100 50 0)
        (effects (font (size 1.27 1.27)))
    )
    (property "Value" "10k"
        (at 100 50 0)
        (effects (font (size 1.27 1.27)))
    )
)
"""
    from cifconv.schema import Schema

    schema = Schema()

    tokens = list(kicad_sch_tokenize(input_symbol))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    symbol = process_symbol(expr)
    schema.symbols[symbol.lib_id] = symbol

    tokens = list(kicad_sch_tokenize(input_instance))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    instance = process_symbol_instance(expr, schema)

    assert instance.uuid == "test-instance-uuid"
    assert instance.lib_id == "Device:R"
    assert instance.designator == "R1"
    assert instance.x == 100.0
    assert instance.y == 50.0
    assert instance.rotation == 0.0

    assert instance.pin_instances is not None
    assert len(instance.pin_instances) == 2

    pin1 = instance.pin_instances[0]
    assert pin1.number == "1"
    assert pin1.name == "1"
    assert pin1.type == "passive"
    assert pin1.x == 100.0 + (-5.08)
    assert pin1.y == 50.0 + 0.0
    assert pin1.rotation == 0.0

    pin2 = instance.pin_instances[1]
    assert pin2.number == "2"
    assert pin2.name == "2"
    assert pin2.type == "passive"
    assert pin2.x == 100.0 + 5.08
    assert pin2.y == 50.0 + 0.0
    assert pin2.rotation == 180.0


def test_process_symbol_instance_with_rotation():
    input_symbol = """
(symbol "Device:R"
    (property "Reference" "R"
        (at 0 0 0)
        (effects (font (size 1.27 1.27)))
    )
    (symbol "R_1_1"
        (pin passive line
            (at -5.08 0 0)
            (length 2.54)
            (name "1" (effects (font (size 1.27 1.27))))
            (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line
            (at 5.08 0 180)
            (length 2.54)
            (name "2" (effects (font (size 1.27 1.27))))
            (number "2" (effects (font (size 1.27 1.27))))
        )
    )
)
"""
    input_instance = """
(symbol
    (lib_id "Device:R")
    (at 100 50 90)
    (uuid "test-instance-uuid-rotated")
    (property "Reference" "R2"
        (at 100 50 0)
        (effects (font (size 1.27 1.27)))
    )
)
"""
    import math

    from cifconv.schema import Schema

    schema = Schema()

    tokens = list(kicad_sch_tokenize(input_symbol))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    symbol = process_symbol(expr)
    schema.symbols[symbol.lib_id] = symbol

    tokens = list(kicad_sch_tokenize(input_instance))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    instance = process_symbol_instance(expr, schema)

    assert instance.rotation == 90.0
    assert instance.pin_instances is not None
    assert len(instance.pin_instances) == 2

    pin1 = instance.pin_instances[0]
    rad = math.radians(90)
    expected_x1 = 100.0 + (-5.08) * math.cos(rad) - 0.0 * math.sin(rad)
    expected_y1 = 50.0 + (-5.08) * math.sin(rad) + 0.0 * math.cos(rad)
    assert abs(pin1.x - expected_x1) < 0.001
    assert abs(pin1.y - expected_y1) < 0.001
    assert pin1.rotation == 90.0

    pin2 = instance.pin_instances[1]
    expected_x2 = 100.0 + 5.08 * math.cos(rad) - 0.0 * math.sin(rad)
    expected_y2 = 50.0 + 5.08 * math.sin(rad) + 0.0 * math.cos(rad)
    assert abs(pin2.x - expected_x2) < 0.001
    assert abs(pin2.y - expected_y2) < 0.001
    assert pin2.rotation == 270.0


def test_process_symbol_instance_without_symbol_definition():
    input_instance = """
(symbol
    (lib_id "Device:Unknown")
    (at 50 50 0)
    (uuid "test-uuid-unknown")
    (property "Reference" "U1"
        (at 50 50 0)
        (effects (font (size 1.27 1.27)))
    )
)
"""
    from cifconv.schema import Schema

    schema = Schema()

    tokens = list(kicad_sch_tokenize(input_instance))
    expr = read_expr(t for t in tokens)
    assert isinstance(expr, ListExpr)
    instance = process_symbol_instance(expr, schema)

    assert instance.uuid == "test-uuid-unknown"
    assert instance.lib_id == "Device:Unknown"
    assert instance.designator == "U1"
    assert instance.pin_instances is None


def test_schema_nets_with_connected_pins():
    from cifconv.pin_instance import PinInstance
    from cifconv.schema import Schema
    from cifconv.symbol import Symbol
    from cifconv.symbol_instance import SymbolInstance

    schema = Schema()

    symbol = Symbol(
        lib_id="Device:R",
        type="Device",
        ref="R",
        pins=[],
        package=None,
        description=None,
    )
    schema.symbols["Device:R"] = symbol

    pin1 = PinInstance(number="1", name="1", type="passive", x=0.0, y=0.0, rotation=0.0)
    pin2 = PinInstance(
        number="2", name="2", type="passive", x=10.0, y=0.0, rotation=0.0
    )

    instance1 = SymbolInstance(
        uuid="inst-1",
        lib_id="Device:R",
        designator="R1",
        x=0.0,
        y=0.0,
        pin_instances=[pin1],
    )
    instance2 = SymbolInstance(
        uuid="inst-2",
        lib_id="Device:R",
        designator="R2",
        x=10.0,
        y=0.0,
        pin_instances=[pin2],
    )
    schema.instances.append(instance1)
    schema.instances.append(instance2)

    wire = Wire(uuid="wire-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[])
    schema.wires[wire.uuid] = wire

    label = Label(text="NET1", x=0, y=0, rotation=0, uuid="label-1")
    schema.labels.append(label)

    nets = schema.nets
    assert len(nets) == 1

    net = nets[0]
    assert net.name == "NET1"
    assert net.points is not None
    assert Point(0, 0) in net.points
    assert Point(10, 0) in net.points

    assert net.connected_pins is not None
    assert len(net.connected_pins) == 2

    connected_designators = {cp[0].designator for cp in net.connected_pins}
    assert "R1" in connected_designators
    assert "R2" in connected_designators


def test_schema_nets_with_no_connect():
    from cifconv.no_connect import NoConnect
    from cifconv.pin_instance import PinInstance
    from cifconv.schema import Schema
    from cifconv.symbol import Symbol
    from cifconv.symbol_instance import SymbolInstance

    schema = Schema()

    symbol = Symbol(
        lib_id="Device:R",
        type="Device",
        ref="R",
        pins=[],
        package=None,
        description=None,
    )
    schema.symbols["Device:R"] = symbol

    pin1 = PinInstance(number="1", name="1", type="passive", x=0.0, y=0.0, rotation=0.0)
    pin2 = PinInstance(
        number="2", name="2", type="passive", x=10.0, y=0.0, rotation=0.0
    )

    instance = SymbolInstance(
        uuid="inst-1",
        lib_id="Device:R",
        designator="R1",
        x=0.0,
        y=0.0,
        pin_instances=[pin1, pin2],
    )
    schema.instances.append(instance)

    wire = Wire(uuid="wire-1", points=[Point(0, 0), Point(10, 0)], connected_pins=[])
    schema.wires[wire.uuid] = wire

    no_connect = NoConnect(x=10.0, y=0.0, uuid="nc-1")
    schema.no_connects.append(no_connect)

    nets = schema.nets
    assert len(nets) == 1

    net = nets[0]
    assert net.connected_pins is not None
    assert len(net.connected_pins) == 1
    assert net.connected_pins[0][0].designator == "R1"
    assert net.connected_pins[0][1].name == "1"


def test_schema_nets_points_collection():
    from cifconv.schema import Schema

    schema = Schema()

    wire1 = Wire(
        uuid="wire-1",
        points=[Point(0, 0), Point(10, 0), Point(10, 10)],
        connected_pins=[],
    )
    wire2 = Wire(
        uuid="wire-2", points=[Point(20, 20), Point(30, 20)], connected_pins=[]
    )
    schema.wires[wire1.uuid] = wire1
    schema.wires[wire2.uuid] = wire2

    nets = schema.nets
    assert len(nets) == 2

    net1 = next(n for n in nets if Point(0, 0) in (n.points or []))
    net2 = next(n for n in nets if Point(20, 20) in (n.points or []))

    assert net1.points is not None
    assert len(net1.points) == 3
    assert Point(0, 0) in net1.points
    assert Point(10, 0) in net1.points
    assert Point(10, 10) in net1.points

    assert net2.points is not None
    assert len(net2.points) == 2
    assert Point(20, 20) in net2.points
    assert Point(30, 20) in net2.points
