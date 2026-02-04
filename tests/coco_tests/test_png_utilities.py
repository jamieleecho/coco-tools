import filecmp
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping, Tuple

import pytest
from PIL import Image

from coco.png_utilities import (
    ENV_FILE_REGEX,
    PALET_FILE_PERMISSIVE_REGEX,
    PALET_FILE_REGEX,
    LCHEntry,
    PaletteEntry,
    _create_mvicon_arg_parser,
    _parse_input_palette,
    _rgb_palette_to_lch_palette,
    _truncate_palette_to_bits_per_pixel,
    _write_mvicon_file,
    convert_png_to_os9_image,
    png_to_coco_png,
    png_to_mvicon,
    png_to_os9_image,
)


def test_ENV_FILE_REGEX_invalid_line() -> None:
    invalid_line = "INVALID LINE"
    match = ENV_FILE_REGEX.match(invalid_line)
    assert match is None


@pytest.mark.parametrize(
    "test_line",
    [
        ("VAR=VALUE",),
        (" VAR = VALUE "),
        (""),
        ("   "),
        ("* this is a comment"),
        (" * "),
    ],
)
def test_ENV_FILE_REGEX_valid_line(
    test_line: str,
) -> None:
    valid_line = " VAR = VALUE"
    match = ENV_FILE_REGEX.match(valid_line)
    assert match is not None


@pytest.mark.parametrize(
    "test_line",
    [
        "PALET2=1,2,3",
        "  PALET2 = 1 , 2 , 3 ",
        "PALET16=0,0,0",
        "PALET0=3,3,3",
        "PALET=hello world",
    ],
)
def test_PALET_FILE_PERMISSIVE_REGEX_valid_line(
    test_line: str,
) -> None:
    match = PALET_FILE_PERMISSIVE_REGEX.match(test_line)
    assert match is not None


@pytest.mark.parametrize(
    "test_line",
    [
        "TEST=2",
        "*comment=ignore",
    ],
)
def test_PALET_FILE_PERMISSIVE_REGEX_invalid_line(test_line: str) -> None:
    match = PALET_FILE_PERMISSIVE_REGEX.match(test_line)
    assert match is None


@pytest.mark.parametrize(
    "test_line,expected_index,expected_red,expected_green,expected_blue",
    [
        ("PALET5=2,1,0", 5, 2, 1, 0),
        ("  PALET0 = 2 , 1 , 0 ", 0, 2, 1, 0),
        ("  PALET15 = 2 , 1 , 3 ", 15, 2, 1, 3),
        ("  PALET17 = 9 , 1 , 3 ", 17, 9, 1, 3),
        ("  PALET123 = 8, 1 , 3 ", 123, 8, 1, 3),
    ],
)
def test_PALET_FILE_REGEX_valid_line(
    test_line: str,
    expected_index: int,
    expected_red: int,
    expected_green: int,
    expected_blue: int,
) -> None:
    match = PALET_FILE_REGEX.match(test_line)
    assert match is not None


@pytest.mark.parametrize(
    "test_line",
    [
        "PALET9=21,1,0",
        "PALET2=1,1,20",
        "PALET4=1,21,0",
    ],
)
def test_PALET_FILE_REGEX_invalid_line(
    test_line: str,
) -> None:
    match = PALET_FILE_REGEX.match(test_line)
    assert match is None


@pytest.mark.parametrize(
    "entry,expected_lch_entry",
    [
        (PaletteEntry(r=0, g=0, b=0), LCHEntry(luminence=0.0, chroma=0.0, hue=360.0)),
        (
            PaletteEntry(r=3, g=3, b=3),
            LCHEntry(
                luminence=99.99998453333127,
                chroma=0.00857377398931557,
                hue=266.9285772201555,
            ),
        ),
        (
            PaletteEntry(r=3, g=0, b=0),
            LCHEntry(
                luminence=53.23896002513146,
                chroma=104.5490632458832,
                hue=39.998956384033,
            ),
        ),
    ],
)
def test_LCHEntry_from_palette_entry(
    entry: PaletteEntry,
    expected_lch_entry: LCHEntry,
) -> None:
    lch_entry = LCHEntry.from_palette_entry(palette_entry=entry)
    assert lch_entry == expected_lch_entry


@pytest.mark.parametrize(
    "red,green,blue,expected_lch_entry",
    [
        (0, 0, 0, LCHEntry(luminence=0.0, chroma=0.0, hue=360.0)),
        (
            255,
            255,
            255,
            LCHEntry(
                luminence=99.99998453333127,
                chroma=0.00857377398931557,
                hue=266.9285772201555,
            ),
        ),
        (
            255,
            0,
            0,
            LCHEntry(
                luminence=53.23896002513146,
                chroma=104.5490632458832,
                hue=39.998956384033,
            ),
        ),
    ],
)
def test_LCHEntry_from_rgb_entry(
    red: int,
    green: int,
    blue: int,
    expected_lch_entry: LCHEntry,
) -> None:
    lch_entry = LCHEntry.from_rgb(r=red, g=green, b=blue)
    assert lch_entry == expected_lch_entry


def test_parse_input_palette(default_palette: Mapping[int, PaletteEntry]) -> None:
    assert len(default_palette) == 16
    assert default_palette[0] == PaletteEntry(r=3, g=3, b=3)
    assert default_palette[1] == PaletteEntry(r=1, g=0, b=2)
    assert default_palette[7] == PaletteEntry(r=0, g=2, b=0)
    assert default_palette[8] == PaletteEntry(r=3, g=2, b=1)
    assert default_palette[14] == PaletteEntry(r=2, g=0, b=3)
    assert default_palette[15] == PaletteEntry(r=0, g=3, b=3)


def test_parse_input_partial_palette(
    palettes_path: Path,
) -> None:
    partial_palette_path = palettes_path / "partial-palette.txt"
    palette_mapping = _parse_input_palette(palette_path=str(partial_palette_path))
    assert len(palette_mapping) == 6
    assert palette_mapping[0] == PaletteEntry(r=3, g=3, b=3)
    assert palette_mapping[4] == PaletteEntry(r=3, g=0, b=2)
    assert palette_mapping[15] == PaletteEntry(r=0, g=3, b=3)


@pytest.mark.parametrize(
    "palette_file,expected_error",
    [
        ("r-too-big-palette.txt", "PALET RGB values out of range in palette file"),
        ("g-too-big-palette.txt", "PALET RGB values out of range in palette file"),
        ("b-too-big-palette.txt", "PALET RGB values out of range in palette file"),
        ("bad-line-palette.txt", "Invalid PALET line in palette file"),
        ("duplicate-line-palette.txt", "Duplicate PALET indices found in palette file"),
        (
            "index-too-big-palette.txt",
            "PALET indices must be between 0 and 15 in palette file",
        ),
        ("invalid-line-palette.txt", "Invalid line in palette file"),
    ],
)
def test_parse_input_palette_invalid_file(
    palette_file: Path,
    expected_error: str,
    palettes_path: Path,
) -> None:
    invalid_palette_path = palettes_path / palette_file
    with pytest.raises(ValueError, match=expected_error):
        _parse_input_palette(palette_path=str(invalid_palette_path))


def test_rgb_palette_to_lch_palette(
    default_palette: Mapping[int, PaletteEntry],
) -> None:
    lch_palette = _rgb_palette_to_lch_palette(rgb_palette=default_palette)
    assert len(lch_palette) == len(default_palette)
    for index, palette_entry in default_palette.items():
        expected_lch_entry = LCHEntry.from_palette_entry(palette_entry=palette_entry)
        assert lch_palette[index] == expected_lch_entry


@pytest.mark.parametrize(
    "bits_per_pixel,expected_size,palette_file",
    [
        (1, 2, "default-palette.txt"),
        (2, 4, "default-palette.txt"),
        (4, 16, "default-palette.txt"),
        (1, 2, "partial-palette.txt"),
        (2, 4, "partial-palette.txt"),
        (4, 6, "partial-palette.txt"),
    ],
)
def test_truncate_palette_to_bits_per_pixel(
    bits_per_pixel: int,
    expected_size: int,
    palette_file: str,
    palettes_path: Path,
) -> None:
    palette_path = palettes_path / palette_file
    rgb_palette = _parse_input_palette(palette_path=str(palette_path))
    truncated_palette = _truncate_palette_to_bits_per_pixel(
        rgb_palette=rgb_palette,
        bits_per_pixel=bits_per_pixel,
    )
    assert len(truncated_palette) == expected_size
    for index in truncated_palette.keys():
        assert index < 2**bits_per_pixel
        assert rgb_palette[index] == truncated_palette[index]


def test_load_png_image_as_2darray(
    xmastree_image: list[list[Tuple[int, int, int, int]]],
) -> None:
    # spot check the image
    assert len(xmastree_image) == 24
    assert len(xmastree_image[0]) == 24
    assert xmastree_image[0][0] == (0, 0, 0, 255)
    assert xmastree_image[12][12] == (0, 143, 81, 255)
    assert xmastree_image[23][23] == (0, 0, 0, 255)


def test_convert_png_2d_array_to_2d_palette_indices(
    xmastree_indexed_image: list[list[int]],
) -> None:
    assert len(xmastree_indexed_image) == 24
    assert len(xmastree_indexed_image[0]) == 24
    assert xmastree_indexed_image[0][0] == 2
    assert xmastree_indexed_image[12][12] == 3
    assert xmastree_indexed_image[23][23] == 2


def test_write_mvicon_file(
    xmastree_indexed_image: list[list[int]],
    xmastree_icon_path: Path,
) -> None:
    with TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname) / "output.mvicon"
        _write_mvicon_file(
            output_icon_path=str(tmp_path),
            png_palette_indices_2d_array=xmastree_indexed_image,
            bits_per_pixel=2,
        )
        assert filecmp.cmp(tmp_path, xmastree_icon_path)


def test_create_arg_parser() -> None:
    parser = _create_mvicon_arg_parser()
    args = parser.parse_args(
        [
            "input_image.png",
            "input_palette.palet",
            "output_icon.mvicon",
        ]
    )
    assert args.input_png == "input_image.png"
    assert args.input_palette == "input_palette.palet"
    assert args.output_icon == "output_icon.mvicon"


def test_convert_png_to_mvicon(
    xmastree_image_path: Path,
    default_palette_path: Path,
    images_path: Path,
) -> None:
    with TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        output_icon_path = tmp_path / "output.mvicon"
        from coco.png_utilities import convert_png_to_mvicon

        convert_png_to_mvicon(
            input_png_path=str(xmastree_image_path),
            input_palette_path=str(default_palette_path),
            output_icon_path=str(output_icon_path),
            bits_per_pixel=2,
        )
        assert filecmp.cmp(output_icon_path, f"{images_path}/icon.xmt")


def test_png_to_mvicon(
    xmastree_image_path: Path,
    default_palette_path: Path,
    images_path: Path,
) -> None:
    with TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        output_icon_path = tmp_path / "output.mvicon"
        args = [
            str(xmastree_image_path),
            str(default_palette_path),
            str(output_icon_path),
        ]
        png_to_mvicon(args=args)
        assert filecmp.cmp(output_icon_path, f"{images_path}/icon.xmt")


def _are_identical(
    image1_path: str,
    image2_path: str,
) -> bool:
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)
    return image1.tobytes() == image2.tobytes()


def test_png_to_coco_png(
    branch_image_path: Path,
    xmas_palette_path: Path,
    coco_branch_image_path: Path,
) -> None:
    with TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        output_png_path = tmp_path / "output.png"
        args = [
            str(branch_image_path),
            str(xmas_palette_path),
            str(output_png_path),
            str("--bits-per-pixel=4"),
        ]
        png_to_coco_png(args=args)
        assert _are_identical(branch_image_path, coco_branch_image_path)


@pytest.mark.parametrize(
    "bits_per_pixel,create_mask,mask_index,expected_message",
    [
        (0, False, -1, r"bits_per_pixel=0 but must be in dict_keys\(\[1, 2, 4\]\)."),
        (0, True, -1, r"bits_per_pixel=0 but must be in dict_keys\(\[1, 2, 4\]\)."),
        (-1, True, -1, r"bits_per_pixel=-1 but must be in dict_keys\(\[1, 2, 4]\)."),
        (1, True, -1, r"mask_index=-1 must be >= 0."),
        (1, True, 2, r"mask_index=2 and exceeds value allowed by bits_per_pixel=1."),
        (2, True, 4, r"mask_index=4 and exceeds value allowed by bits_per_pixel=2."),
        (4, True, 16, r"mask_index=16 and exceeds value allowed by bits_per_pixel=4."),
    ],
)
def test_convert_png_to_os9_image_with_errors(
    branch_image_path: Path,
    default_palette_path: Path,
    bits_per_pixel: int,
    create_mask: bool,
    mask_index: int,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        with TemporaryDirectory() as tmpdirname:
            tmp_path = Path(tmpdirname)
            output_icon_path = tmp_path / "output.i09"
            convert_png_to_os9_image(
                input_png_path=branch_image_path,
                input_palette_path=default_palette_path,
                output_os9_image_path=output_icon_path,
                bits_per_pixel=bits_per_pixel,
                create_mask=create_mask,
                mask_index=mask_index,
            )


@pytest.mark.parametrize(
    "mask_index,expected_image",
    [
        (-1, "branch.i09"),
        (0, "branch_mask0.i09"),
        (2, "branch_mask2.i09"),
    ],
)
def test_png_to_os9_image(
    branch_image_path: Path,
    xmas_palette_path: Path,
    images_path: Path,
    mask_index: int,
    expected_image: str,
) -> None:
    with TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        output_image_path = tmp_path / expected_image
        args = [
            str(branch_image_path),
            str(xmas_palette_path),
            str(output_image_path),
            str("--bits-per-pixel=4"),
            str(f"--mask-index={mask_index}"),
        ]
        png_to_os9_image(args=args)
        assert filecmp.cmp(output_image_path, f"{images_path}/{expected_image}")
