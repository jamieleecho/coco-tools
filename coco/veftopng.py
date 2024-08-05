#!/usr/bin/env python
#
# veftopng.py: Convert OS-9 VEF images to PNG
# Copyright (c) 2018  Travis Poppe <tlp@lickwid.net>
# Copyright (c) 2020  Jamie Cho
#
# Version 2020.03.28
#
# Requires: PyPNG, Pillow (pip install pypng, pip install pillow)

# Usage: veftopng.py image.vef image.png

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse
import png
import sys

from PIL import Image
from coco import __version__
from coco.util import iotobytes


def unsquash(data, count, orig_len):
    """Decompress squashed VEF data."""

    decomp_data = []

    i = 0
    while i < count:
        count_byte = data[i]
        i += 1
        # If high bit is set, we remove it (-128) and repeat the next byte that
        # many times.
        if count_byte > 128:
            count_byte -= 128
            while count_byte > 0:
                decomp_data.append(data[i])
                count_byte -= 1
            i += 1
        # Otherwise insert next count_byte number of bytes as-is.
        else:
            j = 0
            while j < count_byte:
                decomp_data.append(data[i])
                i += 1
                j += 1

    # Only return orig_len bytes; some VEFs are broken and have more,
    # corrupting the image.
    return decomp_data[0:orig_len]


DESCRIPTION = """Convert OS-9 VEF images to PNG
Copyright (c) 2018-2020  Travis Poppe <tlp@lickwid.net>
Copyright (c) 2020  Jamie Cho
Version: {}""".format(__version__)


def main():
    start(sys.argv[1:])


def start(argv):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_image",
        metavar="image.vef",
        type=str,
        help="input VEF image file",
    )
    parser.add_argument(
        "output_image",
        metavar="image.png",
        type=str,
        help="output PNG image file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
    )
    args = parser.parse_args(argv)

    with open(args.input_image, "rb") as file:
        data = bytearray(iotobytes(file.read()))
        if not data:
            sys.exit("File is empty.")

    # CoCo 3 64-color palette (RGB)
    coco3_rgb = [
        (0x00, 0x00, 0x00),  # 0 black
        (0x00, 0x00, 0x55),  # 1 dark blue
        (0x00, 0x55, 0x00),  # 2 dark green
        (0x00, 0x55, 0x55),  # 3 dark cyan
        (0x55, 0x00, 0x00),  # 4 dark red
        (0x55, 0x00, 0x55),  # 5 dark magenta
        (0x55, 0x55, 0x00),  # 6 brown
        (0x55, 0x55, 0x55),  # 7 dark grey
        (0x00, 0x00, 0xAA),  # 8 medium blue
        (0x00, 0x00, 0xFF),  # 9 bright blue
        (0x00, 0x55, 0xAA),  # 10 light blue/cyan
        (0x00, 0x55, 0xFF),  # 11 light blue
        (0x55, 0x00, 0xAA),  # 12 indigo
        (0x55, 0x00, 0xFF),  # 13 medium blue/purple
        (0x55, 0x55, 0xAA),  # 14 medium sky blue
        (0x55, 0x55, 0xFF),  # 15 medium peacock
        (0x00, 0xAA, 0x00),  # 16 medium green
        (0x00, 0xAA, 0x55),  # 17 medium green/cyan
        (0x00, 0xFF, 0x00),  # 18 bright green
        (0x00, 0xFF, 0x55),  # 19 medium yellow/green
        (0x55, 0xAA, 0x00),  # 20 light yellow/green
        (0x55, 0xAA, 0x55),  # 21 light green/cyan
        (0x55, 0xFF, 0x00),  # 22 bright yellow/green
        (0x55, 0xFF, 0x55),  # 23 light green
        (0x00, 0xAA, 0xAA),  # 24 pale green/cyan
        (0x00, 0xAA, 0xFF),  # 25 peacock
        (0x00, 0xFF, 0xAA),  # 26 light green/cyan
        (0x00, 0xFF, 0xFF),  # 27 bright cyan
        (0x55, 0xAA, 0xAA),  # 28 light peacock
        (0x55, 0xAA, 0xFF),  # 29 pale peacock
        (0x55, 0xFF, 0xAA),  # 30 pale green/cyan
        (0x55, 0xFF, 0xFF),  # 31 light cyan
        (0xAA, 0x00, 0x00),  # 32 medium red
        (0xAA, 0x00, 0x55),  # 33 medium red/magenta
        (0xAA, 0x55, 0x00),  # 34 yellow/orange
        (0xAA, 0x55, 0x55),  # 35 light red
        (0xFF, 0x00, 0x00),  # 36 bright red
        (0xFF, 0x00, 0x55),  # 37 light red/magenta
        (0xFF, 0x55, 0x00),  # 38 orange
        (0xFF, 0x55, 0x55),  # 39 pale red/magenta
        (0xAA, 0x00, 0xAA),  # 40 medium blue/magenta
        (0xAA, 0x00, 0xFF),  # 41 blue/purple
        (0xAA, 0x55, 0xAA),  # 42 light magenta
        (0xAA, 0x55, 0xFF),  # 43 purple
        (0xFF, 0x00, 0xAA),  # 44 light purple
        (0xFF, 0x00, 0xFF),  # 45 bright magenta
        (0xFF, 0x55, 0xAA),  # 46 pale blue/magenta
        (0xFF, 0x55, 0xFF),  # 47 pale purple
        (0xAA, 0xAA, 0x00),  # 48 medium yellow
        (0xAA, 0xAA, 0x55),  # 49 light yellow
        (0xAA, 0xFF, 0x00),  # 50 light yellow/green
        (0xAA, 0xFF, 0x55),  # 51 pale yellow/green
        (0xFF, 0xAA, 0x00),  # 52 light yellow/orange
        (0xFF, 0xAA, 0x55),  # 53 medium yellow
        (0xFF, 0xFF, 0x00),  # 54 bright yellow
        (0xFF, 0xFF, 0x55),  # 55 pale yellow
        (0xAA, 0xAA, 0xAA),  # 56 light grey
        (0xAA, 0xAA, 0xFF),  # 57 pale blue
        (0xAA, 0xFF, 0xAA),  # 58 pale cyan
        (0xAA, 0xFF, 0xFF),  # 59 pale blue/cyan
        (0xFF, 0xAA, 0xAA),  # 60 pale red
        (0xFF, 0xAA, 0xFF),  # 61 pale magenta
        (0xFF, 0xFF, 0xAA),  # 62 very pale yellow
        (0xFF, 0xFF, 0xFF),  # 63 white
    ]

    # 320x200x16 (Screen Type 8)
    if data[1] == 0:
        width = 320
        height = 200
        colors = 16
        orig_len = 80
        veftype = 8
    # 640x200x4 (Screen Type 7)
    elif data[1] == 1:
        width = 640
        height = 200
        colors = 4
        orig_len = 80
        veftype = 7
    # 320x200x4 (Screen Type 6)
    elif data[1] == 3:
        width = 320
        height = 200
        colors = 4
        orig_len = 40
        veftype = 6
    # 640x200x2 (Screen Type 5)
    elif data[1] == 4:
        width = 640
        height = 200
        colors = 2
        orig_len = 40
        veftype = 5
    else:
        veftype = 0

    if not veftype:
        sys.exit("Illegal file format.")
    else:
        print(args.output_image, ": ", width, "x", height, "x", colors, sep="")

    # Grab VEF palette
    pal = data[2:18]

    image_data = []

    # Unsquash compressed VEFs
    if data[0] == 128:
        print("Detected squashed VEF. Decompressing...")

        # Our image data starts at byte 18, which is also the first count byte
        # of 400. It describes how many bytes follow to unsquash for each loop.
        count_byte = 18

        i = 0
        while i < 400:
            count = data[count_byte]
            last_count = count_byte + 1
            count_byte = count_byte + count + 1

            image_data += unsquash(data[last_count:count_byte], count, orig_len)

            i += 1
    else:
        image_data = data[18:]

    bitmap = []
    for byte in image_data:
        if veftype == 8:
            # Each byte contains two pixels (one for each nibble.) Split out
            # the nibbles and set two pixels for each byte. A pixel is an
            # integer from 0-15 referencing an entry in the 64 color palette.
            bitmap.append(pal[byte >> 4])
            bitmap.append(pal[byte & 0x0F])

        if veftype == 7 or veftype == 6:
            # Each byte contains four pixels. A pixel is an integer from 0-3
            # referencing an entry in the 64 color palette.
            bitmap.append(pal[byte >> 6])
            bitmap.append(pal[(byte & 0b00110000) >> 4])
            bitmap.append(pal[(byte & 0b00001100) >> 2])
            bitmap.append(pal[byte & 0b00000011])

    with open(args.output_image, "wb") as file:
        w = png.Writer(width, height, palette=coco3_rgb, bitdepth=8)
        w.write_array(file, bitmap)

    # Resize 640x200 images so they are the correct aspect ratio.
    if width == 640:
        print("Resizing image to 640x{}...".format(height * 2))
        png_file = Image.open(args.output_image)
        png_file = png_file.resize((640, height * 2))
        png_file.save(args.output_image)
        png_file.close()


if __name__ == "__main__":
    main()
