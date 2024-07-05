#!/usr/bin/env python
# encoding: utf-8
# pixtopgm - decoder for pix (Digisector) 4-bit greyscale sideways images
# Original program "pixtopgm" written in Ruby
#   Copyright (c) 2018 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads pix files and converts to pgm

import argparse
import math
import os
import sys

from coco import __version__
from coco.util import iotostr, stdiotobuffer, strtoio


def convert(input_image_stream, output_image_stream):
    f = input_image_stream
    out = output_image_stream
    sz = os.path.getsize(f.name)
    side = int(math.sqrt(sz * 2))
    out.write(strtoio("P5\n{} {}\n255\n".format(side, side)))
    s = ["a"] * (sz * 2)
    for y in range(side):
        for x in range(side // 2):
            v = ord(iotostr(f.read(1)))
            s[(x + x) * side + y] = chr(255 - (v >> 4) * 17)
            s[(x + x + 1) * side + y] = chr(255 - (v & 15) * 17)
    out.write(strtoio("".join(s)))


DESCRIPTION = """Convert RS-DOS PIX images to PGM
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
        metavar="image.pix",
        type=argparse.FileType("rb"),
        help="input PIX image file",
    )
    parser.add_argument(
        "output_image",
        metavar="image.pgm",
        type=argparse.FileType("wb"),
        nargs="?",
        default=stdiotobuffer(sys.stdout),
        help="output PGM image file",
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
