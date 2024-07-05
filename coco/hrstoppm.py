#!/usr/bin/env python
# encoding: utf-8
# hrstoppm - decoder for hrs (Davinci 3) format
# Original program "hrstoppm" written in Ruby
#   Copyright (c) 2018 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads hrs files and converts to ppm

import argparse
import sys

from coco import __version__
from coco.util import (
    check_positive,
    check_zero_or_positive,
    getbit,
    iotostr,
    pack,
    stdiotobuffer,
    strtoio,
)


def convert(input_image_stream, output_image_stream, width, height, skip):
    def dump(x):
        c = palette[x]
        out.write(
            strtoio(
                pack(
                    [
                        (getbit(c, 5) * 2 + getbit(c, 2)) * 85,
                        (getbit(c, 4) * 2 + getbit(c, 1)) * 85,
                        (getbit(c, 3) * 2 + getbit(c, 0)) * 85,
                    ]
                )
            )
        )

    f = input_image_stream
    if skip:
        f.read(skip)
    out = output_image_stream
    palette = [ord(ii) for ii in iotostr(f.read(16))]
    out.write(strtoio("P6\n{} {}\n255\n".format(width, height)))
    for jj in range(height):
        for ii in range(width // 2):
            c = ord(iotostr(f.read(1)))
            dump(c >> 4)
            dump(c & 15)


DESCRIPTION = """Convert RS-DOS HRS images to PPM
Copyright (c) 2018 by Mathieu Bouchard
Copyright (c) 2018-2020 by Jamie Cho
Version: {}""".format(__version__)


def main():
    start(sys.argv[1:])


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_image",
        metavar="image.hrs",
        type=argparse.FileType("rb"),
        nargs="?",
        default=stdiotobuffer(sys.stdin),
        help="input HRS image file",
    )
    parser.add_argument(
        "output_image",
        metavar="image.ppm",
        type=argparse.FileType("wb"),
        nargs="?",
        default=stdiotobuffer(sys.stdout),
        help="output PPM image file",
    )
    parser.add_argument(
        "-w",
        dest="width",
        action="store",
        default=320,
        metavar="width",
        type=check_positive,
        help="choose different width (this does not assume bigger pixels)",
    )
    parser.add_argument(
        "-r",
        dest="rows",
        action="store",
        default=192,
        metavar="height",
        type=check_positive,
        help="choose height not computed from header divided by width",
    )
    parser.add_argument(
        "-s",
        dest="skip",
        action="store",
        default=None,
        metavar="bytes",
        type=check_zero_or_positive,
        help="skip some number of bytes",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
    )
    args = parser.parse_args(argv)

    convert(args.input_image, args.output_image, args.width, args.rows, args.skip)
    args.output_image.close()
    args.input_image.close()


if __name__ == "__main__":
    main()
