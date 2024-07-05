#!/usr/bin/env python
# cm3toppm - decoder for cm3 (CoCoMax 3) format
# Original program "cm3toppm" written in Ruby
#   Copyright (c) 2017 by Mathieu Bouchard
# Translation to Python code:
#   Copyright (c) 2018-2020 by Jamie Cho
#
# reads cm3 files and converts to ppm

import argparse
import sys

from coco import __version__
from coco.util import getbit, iotostr, pack, stdiotobuffer, strtoio


def convert(input_image_stream, output_image_stream):
    def debug(x):
        sys.stderr.write("{}\n".format(x))

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

    # Read basic structure
    #   - is is a 192 or 384 row image?
    #   - motifs - patterns used for filling shapes stored in the image file
    f = input_image_stream
    cols = 320
    pictyp = ord(iotostr(f.read(1)))
    rows = (getbit(pictyp, 7) + 1) * 192
    sans_motifs = getbit(pictyp, 0) != 0
    debug("{}x{}, 16 couleurs, sans_motifs={}".format(cols, rows, sans_motifs))

    # Get palette information
    palette = [ord(iotostr(f.read(1))) for ii in range(16)]
    anirat = ord(iotostr(f.read(1)))
    cycrat = ord(iotostr(f.read(1)))
    cm3cyc = [ord(iotostr(f.read(1))) for ii in range(8)]
    aniflg = ord(iotostr(f.read(1))) & 0x80 != 0
    cycflg = ord(iotostr(f.read(1))) & 0x80 != 0
    debug("palette={}".format(palette))
    debug(
        "cm3cyc={} cycrat={} cycflg={} anirat={} aniflg={}".format(
            cm3cyc, cycrat, cycflg, anirat, aniflg
        )
    )
    if not sans_motifs:
        iotostr(f.read(243))
    linbuf = [0] * 160
    buff1 = [0] * 20
    buff2 = []

    # Start outputting image
    out = output_image_stream
    out.write(strtoio("P6\n{} {}\n255\n".format(cols, rows)))

    for ii in range(getbit(pictyp, 7) + 1):
        lines = ord(iotostr(f.read(1)))
        for jj in range(lines):
            u = 0
            y = 0
            bitu = 7
            bity = 7
            x = 0
            a = None
            contr = ord(iotostr(f.read(1)))
            if contr < 128:
                for kk in range(20):
                    buff1[kk] = ord(iotostr(f.read(1)))
                buff2 = []
                for kk in range(contr):
                    buff2.append(ord(iotostr(f.read(1))))
            for kk in range(160):
                if contr >= 128:
                    a = ord(iotostr(f.read(1)))
                else:
                    cc = getbit(buff1[u], bitu)
                    bitu = bitu - 1
                    if bitu < 0:
                        bitu = 7
                        u = u + 1
                    if cc == 0:
                        a = linbuf[(x - 1) % 160]
                    else:
                        cc = getbit(buff2[y], bity)
                        bity = bity - 1
                        if bity < 0:
                            bity = 7
                            y = y + 1
                        a = linbuf[x] if cc == 0 else ord(iotostr(f.read(1)))
                linbuf[x] = a
                dump(a >> 4)
                dump(a & 15)
                x = x + 1

    # Look for extra junk at the end of the file
    extra = 0
    while iotostr(f.read(1)) != "":
        extra = extra + 1
        pass
    if extra > 0:
        debug("{} octets de trop".format(extra))


DESCRIPTION = """Convert RS-DOS CM3 images to PPM
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
        metavar="image.cm3",
        type=argparse.FileType("rb"),
        nargs="?",
        default=stdiotobuffer(sys.stdin),
        help="input CM3 image file",
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
