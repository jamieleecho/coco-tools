#!/usr/bin/env python
# encoding: utf-8
# rattoppm - decoder for rat (Diecom Rat) format
# Original program "rattoppm" written in Ruby
#   Copyright (c) 2018 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads rat files and converts to ppm

import argparse
import sys

from coco import __version__
from coco.util import getbit, iotostr, pack, stdiotobuffer, strtoio


def convert(input_image_stream, output_image_stream):
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
    out = output_image_stream
    escape = ord(iotostr(f.read(1)))
    packed = ord(iotostr(f.read(1)))
    f.read(1)  # bcolor
    if packed == 0:
        raise Exception("not packed")
    palette = [ord(ii) for ii in iotostr(f.read(16))]
    out.write(strtoio("P6\n320 199\n255\n"))
    ii = 199 * 160
    while ii > 0:
        c = ord(iotostr(f.read(1)))
        if c != escape:
            repeat = 1
        else:
            repeat = ord(iotostr(f.read(1)))
            c = ord(iotostr(f.read(1)))
        for jj in range(repeat):
            ii = ii - 1
            dump(c >> 4)
            dump(c & 7)


DESCRIPTION = """Convert RS-DOS RAT images to PPM
Copyright (c) 2018-2020 by Mathieu Bouchard, Jamie Cho
Version: {}""".format(__version__)


def main():
    start(sys.argv[1:])


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_image",
        metavar="image.rat",
        type=argparse.FileType("rb"),
        nargs="?",
        default=stdiotobuffer(sys.stdin),
        help="input RAT image file",
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
        "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
    )
    args = parser.parse_args(argv)

    convert(args.input_image, args.output_image)
    args.output_image.close()
    args.input_image.close()


if __name__ == "__main__":
    main()
