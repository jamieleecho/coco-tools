import filecmp
import importlib.resources as pkg_resources
import os
import subprocess
import sys
import tempfile
import unittest

import coco.cm3toppm
from coco import __version__
from coco.util import iotostr

from .util import unix_only


class TestCM3ToPPM(unittest.TestCase):
    USAGE_REGEX = r"\[-h\] \[--version\] \[image.cm3\] \[image.ppm\]"
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.cm3\s*input CM3 image file"
        r"\s*image.ppm\s*output PPM image file"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    def setUp(self):
        self.outfile = tempfile.NamedTemporaryFile("w", suffix=".ppm", delete=False)

    def tearDown(self):
        if not self.outfile.closed:
            self.outfile.close()
        os.remove(self.outfile.name)

    def test_converts_cm3_to_ppm(self) -> None:
        infilename = pkg_resources.files(__package__) / "fixtures/clip1.cm3"
        comparefilename = pkg_resources.files(__package__) / "fixtures/clip1.ppm"
        self.outfile.close()
        with infilename as infile_path, comparefilename as compare_path:
            coco.cm3toppm.start([str(infile_path), self.outfile.name])
            self.assertTrue(filecmp.cmp(self.outfile.name, str(compare_path)))

    @unix_only
    def test_too_many_arguments(self) -> None:
        infilename = pkg_resources.files(__package__) / "fixtures/clip1.cm3"
        with infilename as infile_path:
            with self.assertRaises(subprocess.CalledProcessError) as context:
                subprocess.check_output(
                    [
                        sys.executable,
                        "coco/cm3toppm.py",
                        infile_path,
                        self.outfile.name,
                        "baz",
                    ],
                    env={"PYTHONPATH": "."},
                    stderr=subprocess.STDOUT,
                )
            self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
            self.assertRegex(
                iotostr(context.exception.output),
                r"cm3toppm.py: error: unrecognized arguments: baz",
            )

    @unix_only
    def test_converts_cm3_to_ppm_via_stdio(self) -> None:
        infile = (pkg_resources.files(__package__) / "fixtures/clip1.cm3").open("rb")
        with pkg_resources.files(__package__) / "fixtures/clip1.ppm" as comparefilename:
            read, write = os.pipe()
            os.write(write, infile.read())
            os.close(write)
            subprocess.check_call(
                [sys.executable, "coco/cm3toppm.py"],
                env={"PYTHONPATH": "."},
                stdin=read,
                stdout=self.outfile,
            )
            self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_converts_cm3_to_ppm_via_stdin(self) -> None:
        infilename = pkg_resources.files(__package__) / "fixtures/clip1.cm3"
        comparefilename = pkg_resources.files(__package__) / "fixtures/clip1.ppm"
        with infilename as infile_path, comparefilename as comparefile_path:
            subprocess.check_call(
                [sys.executable, "coco/cm3toppm.py", infile_path],
                env={"PYTHONPATH": "."},
                stdout=self.outfile,
            )
            self.assertTrue(filecmp.cmp(self.outfile.name, comparefile_path))

    @unix_only
    def test_help(self) -> None:
        output = subprocess.check_output(
            [sys.executable, "coco/cm3toppm.py", "-h"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), "Convert RS-DOS CM3 images to PPM")
        self.assertRegex(iotostr(output), self.VERSION_REGEX)
        self.assertRegex(iotostr(output), self.USAGE_REGEX)
        self.assertRegex(iotostr(output), self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(iotostr(output), self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self) -> None:
        output = subprocess.check_output(
            [sys.executable, "coco/cm3toppm.py", "--version"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/cm3toppm.py", "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"cm3toppm.py: error: unrecognized arguments: --oops",
        )
