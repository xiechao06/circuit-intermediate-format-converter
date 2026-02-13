from cifconv.cifconv_eval import is_list
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize
from cifconv.read_expr import read_expr


def test_is_list():
    input_data = "(a b c)"
    tokens = list(kicad_sch_tokenize(input_data))
    expr = read_expr(t for t in tokens)
    assert expr is not None
    assert is_list(expr, "a")
