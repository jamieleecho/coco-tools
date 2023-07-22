# coco-tools

This is a simple collection of tools to assist with developing software for
the [TRS-80 Color Computer](https://en.wikipedia.org/wiki/TRS-80_Color_Computer).

## Installation

```
# To install via pip
pip install coco-tools

# To install from source
git clone https://github.com/jamieleecho/coco-tools.git
cd coco-tools
python3 setup.py
```

## Tools

### [decb-to-b09](README.decb-to-b09.md)

```
usage: decb-to-b09 [-h] [--version] [-l] [-z] program.bas program.b09

Convert a Color BASIC program to a BASIC09 program
Copyright (c) 2023 by Jamie Cho
Version: 0.7

positional arguments:
  program.bas           input DECB text program file
  program.b09           output BASIC09 text program file

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -l, --filter-unused-linenum
                        Filter out line numbers not referenced by the program
  -z, --dont-initialize-vars
                        Don't pre-initialize all variables
```

### cm3toppm

```
usage: cm3toppm [-h] [--version] [image.cm3] [image.ppm]

Convert RS-DOS CM3 images to PPM
Copyright (c) 2017 by Mathieu Bouchard
Copyright (c) 2018-2020 by Jamie Cho
Version: 0.6

positional arguments:
  image.cm3   input CM3 image file
  image.ppm   output PPM image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### hrstoppm

```
usage: hrstoppm [-h] [-w width] [-r height] [-s bytes] [--version]
                [image.hrs] [image.ppm]

Convert RS-DOS HRS images to PPM
Copyright (c) 2018 by Mathieu Bouchard
Copyright (c) 2018-2020 by Jamie Cho
Version: 0.6

positional arguments:
  image.hrs   input HRS image file
  image.ppm   output PPM image file

options:
  -h, --help  show this help message and exit
  -w width    choose different width (this does not assume bigger pixels)
  -r height   choose height not computed from header divided by width
  -s bytes    skip some number of bytes
  --version   show program's version number and exit
```

### maxtoppm

```
usage: maxtoppm [-h] [--version]
                [-br | -rb | -br2 | -rb2 | -br3 | -rb3 | -s10 | -s11] [-i]
                [-w width] [-r height] [-s bytes] [-newsroom]
                [image] [image.ppm]

Convert RS-DOS MAX and ART images to PPM
Copyright (c) 2018 by Mathieu Bouchard
Copyright (c) 2018-2020 by Mathieu Bouchard, Jamie Cho
Version: 0.6

positional arguments:
  image       input image file
  image.ppm   output PPM image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit

pixel mode:
  Default pixel mode is no artifact (PMODE 4 on monitor). The 6 other modes:

  -br         PMODE 4 artifacts, cyan-blue first
  -rb         PMODE 4 artifacts, orange-red first
  -br2        PMODE 3 Coco 3 cyan-blue first
  -rb2        PMODE 3 Coco 3 orange-red first
  -br3        PMODE 3 Coco 3 primary, blue first
  -rb3        PMODE 3 Coco 3 primary, red first
  -s10        PMODE 3 SCREEN 1,0
  -s11        PMODE 3 SCREEN 1,1

Format and size options::
  Default file format is CocoMax 1/2's .MAX, which is also Graphicom's
  .PIC and SAVEM of 4 or 8 pages of PMODE 3/4.
  Also works with any other height of SAVEM (including fractional pages).

  -i          ignore header errors (but read header anyway)
  -w width    choose different width (this does not assume bigger pixels)
  -r height   choose height not computed from header divided by width
  -s bytes    skip header and assume it has the specified length
  -newsroom   read Coco Newsroom / The Newspaper .ART header instead
```

### mgetoppm

```
usage: mgetoppm [-h] [--version] [image.mge] [image.ppm]

Convert RS-DOS MGE images to PPM
Copyright (c) 2017 by Mathieu Bouchard
Copyright (c) 2018-2020 by Jamie Cho
Version: 0.6

positional arguments:
  image.mge   input MGE image file
  image.ppm   output PPM image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### mge_viewer2

```
usage: mge_viewer2 [-h] [--version] [image.mge]

View ColorMax 3 MGE files
Copyright (c) 2022 by R. Allen Murphey
Version: 0.6

positional arguments:
  image.mge   input MGE image file

optional arguments:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### pixtopgm

```
usage: pixtopgm [-h] [--version] image.pix [image.pgm]

Convert RS-DOS PIX images to PGM
Copyright (c) 2018-2020 by Mathieu Bouchard, Jamie Cho
Version: 0.6

positional arguments:
  image.pix   input PIX image file
  image.pgm   output PGM image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### rattoppm

```
usage: rattoppm [-h] [--version] [image.rat] [image.ppm]

Convert RS-DOS RAT images to PPM
Copyright (c) 2018-2020 by Mathieu Bouchard, Jamie Cho
Version: 0.6

positional arguments:
  image.rat   input RAT image file
  image.ppm   output PPM image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

### veftopng

```
usage: veftopng [-h] [--version] image.vef image.png

Convert OS-9 VEF images to PNG
Copyright (c) 2018-2020  Travis Poppe <tlp@lickwid.net>
Copyright (c) 2020  Jamie Cho
Version: 0.6

positional arguments:
  image.vef   input VEF image file
  image.png   output PNG image file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

## Developing and Testing

```
# Build the docker image
docker-compose build test

# Run tests using the source on the docker image
docker-compose run test

# Run tests using the source on the host computer
docker-compose run testv
```
