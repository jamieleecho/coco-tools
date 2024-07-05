#!/usr/bin/env python
# encoding: utf-8
# mgetoppm - decoder for mge (ColorMax 3) format
# Original program "mgetoppm" written in Ruby
#   Copyright (c) 2017 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads mge files and converts to ppm

import argparse
import sys

from coco import __version__
from coco.util import getbit, iotostr, pack, stdiotobuffer, strtoio


def convert(input_image_stream, output_image_stream):
    def debug(x):
        sys.stderr.write("{}\n".format(x))

    def dmp500(x):
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

    # Maps composite palette values to RGB
    c2r = [
        0,
        21,
        2,
        20,
        6,
        49,
        35,
        4,
        33,
        5,
        14,
        1,
        12,
        10,
        3,
        28,
        7,
        17,
        16,
        22,
        48,
        34,
        37,
        32,
        44,
        40,
        42,
        13,
        8,
        11,
        24,
        26,
        56,
        19,
        18,
        50,
        54,
        52,
        38,
        36,
        46,
        45,
        41,
        15,
        9,
        25,
        27,
        30,
        63,
        58,
        23,
        51,
        55,
        53,
        39,
        60,
        47,
        61,
        43,
        57,
        29,
        31,
        59,
        62,
    ]

    subtyp = 0
    cols = 320 << subtyp
    rows = 200
    a = ord(iotostr(f.read(1)))
    if a != 0:
        debug("invalid header")
        sys.exit(1)
    palette = [ord(iotostr(f.read(1))) for ii in range(16)]
    debug(palette)
    is_rgb = ord(iotostr(f.read(1))) == 0
    colorspace = "RGB" if is_rgb else "CMP"
    if not is_rgb:
        for ii in range(16):
            palette[ii] = c2r[palette[ii]]
    packed = ord(iotostr(f.read(1))) != 0
    titbuf = iotostr(f.read(30))
    i = titbuf.index("\0")
    if i:
        titbuf = titbuf[:i]
    titbuf = titbuf.rstrip()
    if subtyp == 0:

        def dump(a):
            dmp500(a >> 4)
            dmp500(a & 0x0F)

    else:

        def dump(a):
            dmp500(a >> 6)
            dmp500((a >> 4) & 3)
            dmp500((a >> 2) & 3)
            dmp500(a & 3)

    cycles = ord(iotostr(f.read(1)))
    a = ord(iotostr(f.read(1)))
    botpal = a & 0xF
    toppal = (a >> 4) & 0xF
    debug("{}x{}, 16 couleurs {}, titre «{}»".format(cols, rows, colorspace, titbuf))
    debug(
        "palette={}, cycles={}, botpal={},]\ntoppal={}".format(
            palette, cycles, botpal, toppal
        )
    )
    out.write(strtoio("P6\n{} {}\n255\n".format(cols, rows)))
    y = 160 * rows
    if not packed:
        while True:
            b = ord(iotostr(f.read(1)))
            if b == 0:
                break
            a = ord(iotostr(f.read(1)))
            for jj in range(b):
                dump(a)
                y = y - 1
                if y <= 0:
                    break
    else:
        for jj in range(y):
            dump(ord(iotostr(f.read(1))))
    # Look for extra junk at the end of the file
    extra = 0
    while f.read(1) != strtoio(""):
        extra = extra + 1
        pass
    if extra > 0:
        debug("{} octets de trop".format(extra))


DESCRIPTION = """Convert RS-DOS MGE images to PPM
Copyright (c) 2017 by Mathieu Bouchard
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
        metavar="image.mge",
        type=argparse.FileType("rb"),
        nargs="?",
        default=stdiotobuffer(sys.stdin),
        help="input MGE image file",
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
