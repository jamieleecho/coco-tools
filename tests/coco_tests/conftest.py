from pathlib import Path
from typing import Mapping, Tuple

import pytest

from coco.png_utilities import (
    LCHEntry,
    PaletteEntry,
    _convert_png_2d_array_to_2d_palette_indices,
    _load_png_image_as_2darray,
    _parse_input_palette,
    _rgb_palette_to_lch_palette,
    _truncate_palette_to_bits_per_pixel,
)


@pytest.fixture(scope="module")
def fixtures_path() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def images_path(fixtures_path: Path) -> Path:
    """Return the path to the images directory."""
    return fixtures_path / "images"


@pytest.fixture(scope="module")
def xmastree_image_path(images_path: Path) -> Path:
    """Return the path to the xmastree images directory."""
    return images_path / "xmastree.png"


@pytest.fixture(scope="module")
def palettes_path(fixtures_path: Path) -> Path:
    """Return the path to the palettes directory."""
    return fixtures_path / "palettes"


@pytest.fixture(scope="module")
def default_palette_path(palettes_path: Path) -> Path:
    """Return the path to the default palette file."""
    return palettes_path / "default-palette.txt"


@pytest.fixture(scope="module")
def default_palette(default_palette_path: Path) -> Mapping[int, PaletteEntry]:
    """Return the default palette as a mapping from index to PaletteEntry."""
    return _parse_input_palette(palette_path=str(default_palette_path))


@pytest.fixture(scope="module")
def truncated_palette(
    default_palette: Mapping[int, PaletteEntry],
) -> Mapping[int, PaletteEntry]:
    """Return the truncated palette to the given bits per pixel."""
    return _truncate_palette_to_bits_per_pixel(
        rgb_palette=default_palette,
        bits_per_pixel=2,
    )


@pytest.fixture(scope="module")
def default_lch_palette(
    truncated_palette: Mapping[int, PaletteEntry],
) -> Mapping[int, LCHEntry]:
    """Return the default palette converted to LCHEntry."""
    return _rgb_palette_to_lch_palette(rgb_palette=truncated_palette)


@pytest.fixture(scope="module")
def xmastree_image(
    xmastree_image_path: Path,
    truncated_palette: Mapping[int, PaletteEntry],
) -> list[list[Tuple[int, int, int, int]]]:
    """Return the xmastree image as a 2D array of palette indices."""
    return _load_png_image_as_2darray(image_path=str(xmastree_image_path))


@pytest.fixture(scope="module")
def xmastree_indexed_image(
    xmastree_image: list[list[Tuple[int, int, int, int]]],
    default_lch_palette: Mapping[int, LCHEntry],
) -> list[list[int]]:
    """Return the xmastree image as a 2D array of palette indices."""
    return _convert_png_2d_array_to_2d_palette_indices(
        png_2d_array=xmastree_image,
        lch_palette=default_lch_palette,
    )


@pytest.fixture(scope="module")
def xmastree_icon_path(
    images_path: Path,
) -> Path:
    """Return the path to the xmastree image."""
    return images_path / "icon.xmt"


@pytest.fixture(scope="module")
def branch_image_path(images_path: Path) -> Path:
    """Return the path to the xmastree images directory."""
    return images_path / "branch.png"


@pytest.fixture(scope="module")
def xmas_palette_path(palettes_path: Path) -> Path:
    """Return the path to the default palette file."""
    return palettes_path / "xmas-palette.txt"


@pytest.fixture(scope="module")
def coco_branch_image_path(images_path: Path) -> Path:
    """Return the path to the xmastree images directory."""
    return images_path / "branch.png"
