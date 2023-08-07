#!/usr/bin/env python
# decb_to_b09 - Convert a Color BASIC programs to a BASIC09 programs
#   Copyright (c) 2023 by Jamie Cho
#
# reads decb text files and converts to BASIC09 text files

import argparse
import os
import sys

from coco import __version__
from coco import b09


DESCRIPTION = """Convert a Color BASIC program to a BASIC09 program
Copyright (c) 2023 by Jamie Cho
Version: {}""".format(
    __version__
)


def main():
    start(sys.argv[1:])


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'input_decb_text_program_file',
        metavar='program.bas',
        type=argparse.FileType('r'),
        help='input DECB text program file',
    )
    parser.add_argument(
        'output_b09_text_program_file',
        metavar='program.b09',
        type=argparse.FileType('w'),
        help="output BASIC09 text program file",
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {}'.format(__version__),
    )
    parser.add_argument(
        '-l', '--filter-unused-linenum',
        action='store_true',
        help='Filter out line numbers not referenced by the program',
    )
    parser.add_argument(
        '-z', '--dont-initialize-vars',
        action='store_true',
        help='Don\'t pre-initialize all variables',
    )
    parser.add_argument(
        '-D', '--dont-output-dependencies',
        action='store_true',
        help='Don\'t output required dependencies',
    )

    args = parser.parse_args(argv)
    procname = os.path.splitext(
        os.path.basename(args.input_decb_text_program_file.name))[0]

    b09.convert_file(args.input_decb_text_program_file,
                     args.output_b09_text_program_file,
                     procname=procname,
                     filter_unused_linenum=args.filter_unused_linenum,
                     initialize_vars=not args.dont_initialize_vars,
                     output_dependencies=not args.dont_output_dependencies)
    args.input_decb_text_program_file.close()
    args.output_b09_text_program_file.close()


if __name__ == "__main__":
    main()