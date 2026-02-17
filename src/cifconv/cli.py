import argparse
import sys

from loguru import logger

from cifconv.cifconv_eval import cifconv_eval
from cifconv.kicad_schematic_tokenizer import kicad_sch_tokenize
from cifconv.read_expr import read_expr


def setup_logger(output_dir: str, *, with_color: bool = False):
    logger.remove()
    if with_color:
        logger.add(
            sys.stderr,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<10}</level> | <level>{message}</level>",
            level="DEBUG",
        )
    else:
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<10} | {message}",
            level="DEBUG",
        )

    logger.add(
        "logs.txt",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<10} | {message}",
        rotation="10 MB",
        level="DEBUG",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Convert circuit intermediate format to target JSON format"
    )
    parser.add_argument(
        "input_file",
        help="Path to the input circuit intermediate format file, e.g., KiCad Schematic file",
    )
    args = parser.parse_args()
    setup_logger(output_dir="logs", with_color=True)
    with open(args.input_file, "r") as f:
        input_data = f.read()
        schema = cifconv_eval(read_expr(kicad_sch_tokenize(input_data)))
        print([symbol.lib_id for symbol in schema.symbols])
        # print(schema.symbols[0].pins)
        print([(inst.uuid, inst.lib_id) for inst in schema.instances])
        print([(wire.uuid, [(p.x, p.y) for p in wire.points]) for wire in schema.wires])
