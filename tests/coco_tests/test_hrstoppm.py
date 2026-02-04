import filecmp
import importlib.resources as importlib_resources
import os
import subprocess
import sys
import tempfile
import unittest

import coco.hrstoppm
from coco import __version__
from coco.util import iotostr

from .util import unix_only


class TestHRSToPPM(unittest.TestCase):
    USAGE_REGEX = (
        r"\[-h\] \[-w width\] \[-r height\] \[-s bytes\] "
        r"\[--version\]\s*\[image.hrs\] \[image.ppm\]"
    )
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.hrs\s*input HRS image file\s*"
        r"image.ppm\s*output PPM image file"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*-w width\s*choose different width \(this does not assume bigger "
        r"pixels\)"
        r"\s*-r height\s*choose height not computed from header divided by "
        r"width"
        r"\s*-s bytes\s*skip some number of bytes"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    def setUp(self):
        self.outfile = tempfile.NamedTemporaryFile("w", suffix=".ppm", delete=False)

    def tearDown(self):
        if not self.outfile.closed:
            self.outfile.close()
        os.remove(self.outfile.name)

    def test_converts_hrs_to_ppm(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa.hrs"
        ) as infilename:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa.ppm"
            ) as comparefilename:
                self.outfile.close()
                coco.hrstoppm.start([str(infilename), self.outfile.name])
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_hrs_to_ppm_with_height(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa.hrs"
        ) as infilename:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa_r97.ppm"
            ) as comparefilename:
                self.outfile.close()
                coco.hrstoppm.start(["-r", "97", str(infilename), self.outfile.name])
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_hrs_to_ppm_with_width(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa.hrs"
        ) as infilename:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa_w160.ppm"
            ) as comparefilename:
                self.outfile.close()
                coco.hrstoppm.start(["-w", "160", str(infilename), self.outfile.name])
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_skipping_bytes(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa_s7.hrs"
        ) as infilename:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa.ppm"
            ) as comparefilename:
                self.outfile.close()
                coco.hrstoppm.start(["-s", "7", str(infilename), self.outfile.name])
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_too_many_arguments(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa.hrs"
        ) as infilename:
            with self.assertRaises(subprocess.CalledProcessError) as context:
                subprocess.check_output(
                    [
                        sys.executable,
                        "coco/hrstoppm.py",
                        infilename,
                        self.outfile.name,
                        "baz",
                    ],
                    env={"PYTHONPATH": "."},
                    stderr=subprocess.STDOUT,
                )
            self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
            self.assertRegex(
                iotostr(context.exception.output),
                r"hrstoppm.py: error: unrecognized arguments: baz",
            )

    @unix_only
    def test_converts_hrs_to_ppm_via_stdio(self) -> None:
        with (importlib_resources.files(__package__) / "fixtures/monalisa.hrs").open(
            "rb"
        ) as infile:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa.ppm"
            ) as comparefilename:
                read, write = os.pipe()
                os.write(write, infile.read())
                os.close(write)
                subprocess.check_call(
                    [sys.executable, "coco/hrstoppm.py"],
                    env={"PYTHONPATH": "."},
                    stdin=read,
                    stdout=self.outfile,
                )
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_converts_hrs_to_ppm_via_stdin(self) -> None:
        with importlib_resources.as_file(
            importlib_resources.files(__package__) / "fixtures/monalisa.hrs"
        ) as infilename:
            with importlib_resources.as_file(
                importlib_resources.files(__package__) / "fixtures/monalisa.ppm"
            ) as comparefilename:
                subprocess.check_call(
                    [sys.executable, "coco/hrstoppm.py", str(infilename)],
                    env={"PYTHONPATH": "."},
                    stdout=self.outfile,
                )
                self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_help(self) -> None:
        output = subprocess.check_output(
            [sys.executable, "coco/hrstoppm.py", "-h"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), "Convert RS-DOS HRS images to PPM")
        self.assertRegex(iotostr(output), self.VERSION_REGEX)
        self.assertRegex(iotostr(output), self.USAGE_REGEX)
        self.assertRegex(iotostr(output), self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(iotostr(output), self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self) -> None:
        output = subprocess.check_output(
            [sys.executable, "coco/hrstoppm.py", "--version"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/hrstoppm.py", "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"hrstoppm.py: error: unrecognized arguments: --oops",
        )
