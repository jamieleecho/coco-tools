#!/usr/bin/env python
# decb_to_b09 - Convert a Color BASIC programs to a BASIC09 programs
#   Copyright (c) 2023 by Jamie Cho
#
# reads decb text files and converts to BASIC09 text files

import argparse
import os
import sys

from coco import __version__
from coco.b09.compiler import convert_file, parse_fixed_array_size
from coco.b09.errors import ParseError

DESCRIPTION = """Convert a Color BASIC program to a BASIC09 program
Copyright (c) 2023 by Jamie Cho
Version: {}""".format(__version__)


def _fixed_array_size(spec: str) -> tuple[str, tuple[int | None, ...]]:
    try:
        return parse_fixed_array_size(spec)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def main():
    try:
        start(sys.argv[1:])
    except ParseError as error:
        sys.exit(f"decb-to-b09: error: {error}")


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_decb_text_program_file",
        metavar="program.bas",
        type=argparse.FileType("r"),
        help="input DECB text program file",
    )
    parser.add_argument(
        "output_b09_text_program_file",
        metavar="program.b09",
        type=argparse.FileType("w"),
        help="output BASIC09 text program file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
    )
    parser.add_argument(
        "-l",
        "--filter-unused-linenum",
        action="store_true",
        help="Filter out line numbers not referenced by the program",
    )
    parser.add_argument(
        "-z",
        "--dont-initialize-vars",
        action="store_true",
        help="Don't pre-initialize all variables",
    )
    parser.add_argument(
        "-s",
        "--default-string-storage",
        type=int,
        default=32,
        help="Bytes to allocate for each string",
    )
    parser.add_argument(
        "-D",
        "--dont-output-dependencies",
        action="store_true",
        help="Don't output required dependencies",
    )
    parser.add_argument(
        "-w",
        "--dont-run-width-32",
        action="store_true",
        help="if set don't run the default width 32",
    )
    parser.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help=(
            "Skip the _ecb_start call so the program runs on a "
            "typical console. _ecb_start programs the CoCo palette, "
            "switches to 32 columns and sets the cursor color, none "
            "of which apply to an ordinary terminal."
        ),
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        help="Optional compiler configuration file",
        required=False,
    )
    parser.add_argument(
        "--list-integer-candidates",
        action="store_true",
        help=(
            "Instead of compiling, write a sorted list of variables "
            "that could be stored as BASIC09 integers, one per line. "
            "Array variables are written with a trailing '()'."
        ),
    )
    parser.add_argument(
        "-O",
        "--optimize",
        action="store_true",
        help=(
            "Enable real-to-integer optimization: variables and "
            "arrays that are only ever assigned integer values in "
            "the range [-32768, 32767] are declared as BASIC09 "
            "INTEGER instead of the default REAL."
        ),
    )
    parser.add_argument(
        "--basic09-for-loops",
        action="store_true",
        help=(
            "Emit FOR loops with BASIC09's semantics, which skip the "
            "body when the start is already past the limit. By "
            "default loops keep Color BASIC's semantics and run the "
            "body at least once."
        ),
    )
    parser.add_argument(
        "--exact-powers",
        action="store_true",
        help=(
            "Compute X^Y exactly when Y is a whole number. Like Color "
            "BASIC's, BASIC09's ^ is slightly off even for small "
            "integers (2^7 is 128.0000002), which breaks programs "
            "that compare powers of 2 for equality."
        ),
    )
    parser.add_argument(
        "--fix-array-size",
        action="append",
        default=[],
        type=_fixed_array_size,
        metavar="A(n,n)",
        help=(
            "Give the array A a fixed size, with the largest subscript "
            "n in each dimension, or * to keep the bound the program "
            "DIMs it with. BASIC09 arrays have a fixed size, so this "
            "is needed for arrays DIMmed with a bound that is not a "
            "constant, such as DIM A(N). Repeat for each array: "
            '--fix-array-size "A(3,3)" --fix-array-size "B$(3,*)".'
        ),
    )
    parser.add_argument(
        "--no-optimize",
        type=str,
        default="",
        metavar="A,B,C",
        help=(
            "Comma-separated list of variables to exclude from the "
            "real-to-integer optimization. Use plain names for "
            "scalars (e.g., A) and a trailing '()' for arrays "
            "(e.g., Y()). Has no effect unless -O is also set."
        ),
    )

    args = parser.parse_args(argv)
    # The procedure name comes from the input file name, which stdin
    # does not have -- its .name is "<stdin>". Leave it empty there so
    # the compiler falls back to its default procedure name.
    input_file = args.input_decb_text_program_file
    procname = (
        ""
        if input_file is sys.stdin
        else os.path.splitext(os.path.basename(input_file.name))[0]
    )

    # Close the files even when the conversion fails, or Windows cannot
    # delete the output file that argparse already created.
    with args.input_decb_text_program_file, args.output_b09_text_program_file:
        fixed_array_sizes: dict[str, tuple[int | None, ...]] = {}
        for name, bounds in args.fix_array_size:
            if fixed_array_sizes.setdefault(name, bounds) != bounds:
                parser.error(f"--fix-array-size gives {name} more than one size")

        no_optimize_vars = {
            name.strip() for name in args.no_optimize.split(",") if name.strip()
        }

        convert_file(
            args.input_decb_text_program_file,
            args.output_b09_text_program_file,
            basic09_for_loops=args.basic09_for_loops,
            config_file=args.config_file,
            default_width32=not args.dont_run_width_32,
            default_str_storage=args.default_string_storage,
            exact_powers=args.exact_powers,
            filter_unused_linenum=args.filter_unused_linenum,
            fixed_array_sizes=fixed_array_sizes,
            initialize_vars=not args.dont_initialize_vars,
            list_integer_candidates=args.list_integer_candidates,
            no_optimize_vars=no_optimize_vars,
            optimize=args.optimize,
            output_dependencies=not args.dont_output_dependencies,
            procname=procname,
            terminal=args.terminal,
        )


if __name__ == "__main__":
    main()
