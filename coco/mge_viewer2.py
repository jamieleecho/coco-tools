#!/usr/bin/env python3
# encoding: utf-8
# mge_viewer2 - viewer for mge (Color Max 3) files
# Original program "mge_viewer2"
#   Copyright (c) 2022 by  R. Allen Murphey
#
# View ColorMax 3 MGE files
# See: https://pythonguides.com/python-read-a-binary-file/
# See: https://code.activestate.com/recipes/579048-python-mandelbrot-fractal-with-tkinter/ # noqa


import argparse
import sys
from tkinter import Tk, Canvas, PhotoImage, NW

from coco import __version__
from coco.util import stdiotobuffer


# Color Computer 3 RGB Palette in Photoimage color format
RGB = [
    "#000000",  # Black
    "#000055",  # Dark Blue
    "#005500",  # Dark Green
    "#005555",  # Dark Cyan
    "#550000",  # Dark Red
    "#550055",  # Dark Magenta
    "#555500",  # Brown
    "#555555",  # Dark Grey
    "#0000AA",  # Medium Blue
    "#0000FF",  # Bright Blue
    "#0055AA",  # Light Blue/Cyan
    "#0055FF",  # Light Blue
    "#5500AA",  # Indigo***
    "#5500FF",  # Medium Blue/Purple
    "#5555AA",  # Medium Sky Blue
    "#5555FF",  # Medium Peacock
    "#00AA00",  # Medium Green
    "#00AA55",  # Medium Green/Cyan
    "#00FF00",  # Bright Green
    "#00FF55",  # Medium Yellow/Green
    "#55AA00",  # Light Yellow/Green
    "#55AA55",  # Light Green/Cyan
    "#55FF00",  # Bright Yellow/Green
    "#55FF55",  # Light Green
    "#00AAAA",  # Pale Green/Cyan
    "#55FFFF",  # Peacock
    "#00FFAA",  # Light Green/Cyan
    "#00FFFF",  # Bright Cyan
    "#55AAAA",  # Light Peacock
    "#55AAFF",  # Pale Peacock
    "#55FFAA",  # Pale Green/Cyan
    "#55FFFF",  # Light Cyan
    "#AA0000",  # Medium Red
    "#AA0055",  # Medium Red/Magenta
    "#AA5500",  # Yellow/Orange
    "#AA5555",  # Light Red
    "#FF0000",  # Bright Red
    "#FF0055",  # Light Red/Magenta
    "#FF5500",  # Orange
    "#FF5555",  # Pale Red/Magenta
    "#AA00AA",  # Medium Blue/Magenta
    "#AA00FF",  # Blue/Purple
    "#AA55AA",  # Light Magenta
    "#AA55FF",  # Purple
    "#FF00AA",  # Light Purple
    "#FF00FF",  # Bright Magenta
    "#FF55AA",  # Pale Blue/Magenta
    "#FF55FF",  # Pale Purple
    "#AAAA00",  # Medium Yellow
    "#AAAA55",  # Light Yellow
    "#AAFF00",  # Light Yellow/Green
    "#AAFF55",  # Pale Yellow/Green
    "#FFAA00",  # Light Yellow/Orange
    "#FFAA55",  # Medium Yellow
    "#FFFF00",  # Bright Yellow
    "#FFFF55",  # Pale Yellow
    "#AAAAAA",  # Light Grey
    "#AAAAFF",  # Pale Blue
    "#AAFFAA",  # Pale Cyan
    "#AAFFFF",  # Pale Blue/Cyan
    "#FFAAAA",  # Pale Red
    "#FFAAFF",  # Pale Magenta
    "#FFFFAA",  # Very Pale Yellow
    "#FFFFFF",  # White
]

CMP = [
    "#000000",  # Black
    "#0E4E14",  # Dark Blue
    "#0C4512",  # Dark Green
    "#15350E",  # Dark Cyan
    "#33210A",  # Dark Red
    "#56040A",  # Dark Magenta
    "#6C010C",  # Brown
    "#760113",  # Dark Grey
    "#710C4C",  # Medium Blue
    "#5C1887",  # Bright Blue
    "#3D1FB2",  # Light Blue/Cyan
    "#1523C4",  # Light Blue
    "#012594",  # Indigo***
    "#053361",  # Medium Blue/Purple
    "#0C431D",  # Medium Sky Blue
    "#0D4D14",  # Medium Peacock
    "#323232",  # Medium Green
    "#1D9526",  # Medium Green/Cyan
    "#318D24",  # Bright Green
    "#567B20",  # Medium Yellow/Green
    "#77671C",  # Light Yellow/Green
    "#9E4D19",  # Light Green/Cyan
    "#B33718",  # Bright Yellow/Green
    "#C0274E",  # Light Green
    "#BA238F",  # Pale Green/Cyan
    "#A52BCF",  # Peacock
    "#8535F8",  # Light Green/Cyan
    "#5E3FF9",  # Bright Cyan
    "#1764E4",  # Light Peacock
    "#1077AE",  # Pale Peacock
    "#178963",  # Pale Green/Cyan
    "#19942E",  # Light Cyan
    "#747474",  # Medium Red
    "#4AD43A",  # Medium Red/Magenta
    "#66CC34",  # Yellow/Orange
    "#8EBA30",  # Light Red
    "#B3A42C",  # Bright Red
    "#DB8929",  # Light Red/Magenta
    "#F37244",  # Orange
    "#FC6184",  # Pale Red/Magenta
    "#FB58CA",  # Medium Blue/Magenta
    "#E659FA",  # Blue/Purple
    "#C660FA",  # Light Magenta
    "#9B6DFA",  # Purple
    "#519CFB",  # Light Purple
    "#3DB3F3",  # Bright Magenta
    "#34C7A3",  # Pale Blue/Magenta
    "#39D363",  # Pale Purple
    "#FDFDFE",  # Medium Yellow
    "#89E668",  # Light Yellow
    "#A1DD53",  # Light Yellow/Green
    "#BDCF4D",  # Pale Yellow/Green
    "#D7C052",  # Light Yellow/Orange
    "#F0AE69",  # Medium Yellow
    "#FD9E8E",  # Bright Yellow
    "#FD94BC",  # Pale Yellow
    "#FB8FED",  # Light Grey
    "#ED90FB",  # Pale Blue
    "#D696FB",  # Pale Cyan
    "#B7A2FB",  # Pale Blue/Cyan
    "#86C4FC",  # Pale Red
    "#79D4F0",  # Pale Magenta
    "#74E1B7",  # Very Pale Yellow
    "#FFFFFF",  # White
]


def view(mgefile):
    with mgefile:
        RESOLUTION = int.from_bytes(mgefile.read(1), "big")  # 0=320x200x16
        PALETTE = list(mgefile.read(16))  # FF60-FF6F
        MONTYPE = int.from_bytes(mgefile.read(1), "big")  # 0=RGB 1+=CMP
        COMPRESSION = int.from_bytes(
            mgefile.read(1), "big"
        )  # 0=compressed 1+=non-compressed
        TITLE = mgefile.read(30).decode(
            "ISO-8859-1"
        )  # 30-byte 0-terminated string # noqa
        CYCLEDELAY = int.from_bytes(mgefile.read(1), "big")  # 0-255 0=fast
        CYCLEPAL = int.from_bytes(
            mgefile.read(1), "big"
        )  # left nybble start right nybble end

        print("Resolution .......: " + str(RESOLUTION))
        print("Palette ..........: " + str(PALETTE))
        print("MonType ..........: " + str(MONTYPE))
        print("Compression ......: " + str(COMPRESSION))
        print("Title ............: " + str(TITLE))
        print("Cycle Delay ......: " + str(CYCLEDELAY))
        print("Cycle Palettes ...: " + str(CYCLEPAL))

        PIXELSTREAM = []
        COUNTER = 160 * 200
        while COUNTER:
            if COMPRESSION:
                v = int.from_bytes(mgefile.read(1), "big")
                upper = (v & 0xF0) >> 4
                lower = v & 0x0F
                if MONTYPE:
                    color1 = CMP[PALETTE[upper]]
                    color2 = CMP[PALETTE[lower]]
                else:
                    color1 = RGB[PALETTE[upper]]
                    color2 = RGB[PALETTE[lower]]
                PIXELSTREAM.append(color1)
                PIXELSTREAM.append(color2)
                COUNTER -= 1
            else:
                repeat = int.from_bytes(mgefile.read(1), "big")
                v = int.from_bytes(mgefile.read(1), "big")
                upper = (v & 0xF0) >> 4
                lower = v & 0x0F
                if MONTYPE:
                    color1 = CMP[PALETTE[upper]]
                    color2 = CMP[PALETTE[lower]]
                else:
                    color1 = RGB[PALETTE[upper]]
                    color2 = RGB[PALETTE[lower]]
                while repeat:
                    PIXELSTREAM.append(color1)
                    PIXELSTREAM.append(color2)
                    COUNTER -= 1
                    repeat -= 1

    # Build the output frame from the stream data
    IMAGEOUT = ""
    for y in range(0, 200):
        IMAGEOUT += "{ "
        for x in range(0, 160):
            IMAGEOUT += (
                " "
                + PIXELSTREAM[y * 320 + (x * 2)]
                + " "
                + PIXELSTREAM[y * 320 + (x * 2) + 1]
            )
        IMAGEOUT += " } "

    # Tkinter window
    WINDOW = Tk()
    WINDOW.title(TITLE)

    CANVAS = Canvas(WINDOW, width=320, height=200, bg="#000000")
    CANVAS.pack()

    IMG = PhotoImage(width=320, height=200)
    CANVAS.create_image((0, 0), image=IMG, state="normal", anchor=NW)
    IMG.put(IMAGEOUT)

    WINDOW.mainloop()


DESCRIPTION = f"""View ColorMax 3 MGE files
Copyright (c) 2022 by R. Allen Murphey
Version: {__version__}"""


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
        "--version",
        action="version",
        version="%(prog)s {}".format(__version__),
    )
    args = parser.parse_args(argv)

    view(args.input_image)


if __name__ == "__main__":
    main()
