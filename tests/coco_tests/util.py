import platform
import pytest

from PIL import Image
import imagehash


unix_only = pytest.mark.skipif(
    platform.system() == "Windows", reason="This test does not work in Windows"
)


# From google ai
def compare_images_imagehash(
    image_path1: str, image_path2: str, hash_size: int = 8, similarity_cutoff: int = 5
) -> bool:
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)

    hash1 = imagehash.average_hash(img1, hash_size)
    hash2 = imagehash.average_hash(img2, hash_size)

    return (hash1 - hash2) < similarity_cutoff
