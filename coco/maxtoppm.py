#!/usr/bin/env python
# encoding: utf-8
# maxtoppm - decoder for max and art graphics formats
# Original program "maxtoppm" written in Ruby
#   Copyright (c) 2018 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads max art files and converts to ppm

import argparse
import os
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


PIXEL_MODE_BW = 0
PIXEL_MODE_BR = 1
PIXEL_MODE_RB = 2
PIXEL_MODE_BR2 = 3
PIXEL_MODE_RB2 = 4
PIXEL_MODE_BR3 = 5
PIXEL_MODE_RB3 = 6
PIXEL_MODE_S10 = 7
PIXEL_MODE_S11 = 8


def convert(
    input_image_stream,
    output_image_stream,
    arte,
    newsroom,
    cols,
    rows,
    skip,
    ignore_header_errors,
):
    def clip(v):
        return 255 if v > 255 else (0 if v < 0 else v)

    # imitate +I and -I colours using Coco palette
    br2 = [pack(x) for x in [[0, 0, 0], [255, 85, 0], [0, 170, 255], [255, 255, 255]]]
    # take names "blue" and "red" too literally like many "patched for Coco3"
    # programs
    br3 = [pack(x) for x in [[0, 0, 0], [255, 0, 0], [0, 0, 255], [255, 255, 255]]]
    # probably not exact...
    semig = [
        pack(x)
        for x in [
            [0, 0, 0],
            [0, 255, 0],
            [255, 255, 0],
            [0, 0, 255],
            [255, 0, 0],
            [255, 255, 255],
            [0, 211, 170],
            [204, 0, 255],
            [255, 128, 0],
        ]
    ]

    f = input_image_stream
    out = output_image_stream

    if skip:
        f.read(skip)

    if newsroom:
        head = iotostr(f.read(2))
        cols = ord(head[0]) * 8
        rows = ord(head[1])
    else:
        head = iotostr(f.read(5))
        if ord(head[0]) != 0:
            sys.stderr.write("bad first byte in header\n")
            if not ignore_header_errors:
                return False
        if not rows:
            size = ord(head[1]) * 256 + ord(head[2])
            rows = 8 * size // cols
            if cols * rows // 8 != size:
                sys.stderr.write(
                    "data length {} in header would be closest to {}x{} but "
                    "that would be {} bytes\n".format(
                        size, cols, rows, cols * rows // 8
                    )
                )
                if not ignore_header_errors:
                    return False

    out.write(strtoio("P6\n{} {}\n255\n".format(cols, rows)))
    for jj in range(rows):
        row = iotostr(f.read(cols >> 3))
        oy = r2 = g2 = b2 = 0
        for vv in row:
            v = ord(vv)
            if arte == PIXEL_MODE_BW:
                for k in range(8):
                    out.write(strtoio(br2[getbit(v, 7 - k) * 3]))
            elif (arte == PIXEL_MODE_BR) or (arte == PIXEL_MODE_RB):
                x = -100 if arte == PIXEL_MODE_BR else 100
                # this is using the exact YIQ-to-RGB formula, but the rest is
                # just trial-and-error of what looks ok, without actually using
                # the spec of NTSC and/or VDG/GIME.  more pixel options could
                # be added to allow variants on : brightness/contrast ;
                # saturation ; double-resolution for greater detail in
                # emulation ; different smoothing and horiz phase ; and
                # replacing ±I colours by ±V colours (green-purple of PAL and
                # of SECAM).
                for k in range(8):
                    ny = getbit(v, 7 - k) * 255
                    y = (oy + ny + (ny >> 2)) >> 1
                    i = (x * (y - oy)) >> 7
                    r = clip(int((y + 0.9563 * i)))
                    g = clip(int((y - 0.2721 * i)))
                    b = clip(int((y - 1.1070 * i)))
                    out.write(
                        strtoio(pack([(r + r2) >> 1, (g + g2) >> 1, (b + b2) >> 1]))
                    )
                    oy = ny
                    x = -x
                    r2 = r
                    g2 = g
                    b2 = b
            elif arte == PIXEL_MODE_BR2:
                for k in range(4):
                    out.write(
                        strtoio(
                            br2[getbit(v, 7 - k - k) * 2 + getbit(v, 6 - k - k)] * 2
                        )
                    )
            elif arte == PIXEL_MODE_RB2:
                for k in range(4):
                    out.write(
                        strtoio(
                            br2[getbit(v, 7 - k - k) + getbit(v, 6 - k - k) * 2] * 2
                        )
                    )
            elif arte == PIXEL_MODE_BR3:
                for k in range(4):
                    out.write(
                        strtoio(
                            br3[getbit(v, 7 - k - k) * 2 + getbit(v, 6 - k - k)] * 2
                        )
                    )
            elif arte == PIXEL_MODE_RB3:
                for k in range(4):
                    out.write(
                        strtoio(
                            br3[getbit(v, 7 - k - k) + getbit(v, 6 - k - k) * 2] * 2
                        )
                    )
            elif arte == PIXEL_MODE_S10:
                for k in range(4):
                    out.write(
                        strtoio(
                            semig[1 + getbit(v, 7 - k - k) + getbit(v, 6 - k - k) * 2]
                            * 2
                        )
                    )
            elif arte == PIXEL_MODE_S11:
                for k in range(4):
                    out.write(
                        strtoio(
                            semig[5 + getbit(v, 7 - k - k) + getbit(v, 6 - k - k) * 2]
                            * 2
                        )
                    )
    return True


DESCRIPTION = """Convert RS-DOS MAX and ART images to PPM
Copyright (c) 2018 by Mathieu Bouchard
Copyright (c) 2018-2020 by Mathieu Bouchard, Jamie Cho
Version: {}""".format(__version__)
PIXEL_MODE_DESCRIPTION = (
    "Default pixel mode is no artifact (PMODE 4 on " "monitor). The 6 other modes:"
)
PARSER_MODE_DESCRIPTION = """Default file format is CocoMax 1/2's .MAX, which is also Graphicom's
    .PIC and SAVEM of 4 or 8 pages of PMODE 3/4.
    Also works with any other height of SAVEM (including fractional pages)."""


def main():
    start(sys.argv[1:])


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_image",
        metavar="image",
        type=argparse.FileType("rb"),
        nargs="?",
        default=stdiotobuffer(sys.stdin),
        help="input image file",
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

    pixel_mode_group = parser.add_argument_group(
        "pixel mode", description=PIXEL_MODE_DESCRIPTION
    )
    pixel_mode_parser = pixel_mode_group.add_mutually_exclusive_group()
    pixel_mode_parser.add_argument(
        "-br",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_BR,
        default=PIXEL_MODE_BW,
        help="PMODE 4 artifacts, cyan-blue first",
    )
    pixel_mode_parser.add_argument(
        "-rb",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_RB,
        default=PIXEL_MODE_BW,
        help="PMODE 4 artifacts, orange-red first",
    )
    pixel_mode_parser.add_argument(
        "-br2",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_BR2,
        default=PIXEL_MODE_BW,
        help="PMODE 3 Coco 3 cyan-blue first",
    )
    pixel_mode_parser.add_argument(
        "-rb2",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_RB2,
        default=PIXEL_MODE_BW,
        help="PMODE 3 Coco 3 orange-red first",
    )
    pixel_mode_parser.add_argument(
        "-br3",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_BR3,
        default=PIXEL_MODE_BW,
        help="PMODE 3 Coco 3 primary, blue first",
    )
    pixel_mode_parser.add_argument(
        "-rb3",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_RB3,
        default=PIXEL_MODE_BW,
        help="PMODE 3 Coco 3 primary, red first",
    )
    pixel_mode_parser.add_argument(
        "-s10",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_S10,
        default=PIXEL_MODE_BW,
        help="PMODE 3 SCREEN 1,0",
    )
    pixel_mode_parser.add_argument(
        "-s11",
        dest="pixel_mode",
        action="store_const",
        const=PIXEL_MODE_S11,
        default=PIXEL_MODE_BW,
        help="PMODE 3 SCREEN 1,1",
    )

    parser_mode_group = parser.add_argument_group(
        "Format and size options:", description=PARSER_MODE_DESCRIPTION
    )
    parser_mode_group.add_argument(
        "-i",
        dest="ignore_header_errors",
        action="store_true",
        default=False,
        help="ignore header errors (but read header anyway)",
    )
    parser_mode_group.add_argument(
        "-w",
        dest="width",
        action="store",
        default=256,
        metavar="width",
        type=check_positive,
        help="choose different width (this does not assume bigger pixels)",
    )
    parser_mode_group.add_argument(
        "-r",
        dest="rows",
        action="store",
        default=None,
        metavar="height",
        type=check_positive,
        help="choose height not computed from header divided by width",
    )
    parser_mode_group.add_argument(
        "-s",
        dest="skip",
        action="store",
        default=None,
        metavar="bytes",
        type=check_zero_or_positive,
        help="skip header and assume it has the specified length",
    )
    parser_mode_group.add_argument(
        "-newsroom",
        action="store_true",
        default=False,
        help="read Coco Newsroom / The Newspaper .ART header instead",
    )

    args = parser.parse_args(argv)

    ok = convert(
        args.input_image,
        args.output_image,
        args.pixel_mode,
        args.newsroom,
        args.width,
        args.rows,
        args.skip,
        args.ignore_header_errors,
    )
    args.output_image.close()
    args.input_image.close()
    if not ok:
        os.remove(args.output_image.name)


if __name__ == "__main__":
    main()
