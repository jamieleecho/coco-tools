import os
import filecmp
import pkg_resources
import subprocess
import sys
import tempfile
import unittest

import coco.rattoppm
from .util import unix_only
from coco import __version__
from coco.util import iotostr


class TestRatToPPM(unittest.TestCase):
    USAGE_REGEX = r"\[-h\] \[--version\] \[image.rat\] \[image.ppm\]"
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.rat\s*input RAT image file\s*"
        r"image.ppm\s*output PPM image file"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    def setUp(self):
        self.outfile = tempfile.NamedTemporaryFile(
            "w", suffix=".ppm", delete=False
        )

    def tearDown(self):
        if not self.outfile.closed:
            self.outfile.close()
        os.remove(self.outfile.name)

    def test_converts_rat_to_ppm(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.rat"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.ppm"
        )
        self.outfile.close()
        coco.rattoppm.start([infilename, self.outfile.name])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_too_many_arguments(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.rat"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/rattoppm.py",
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
            r"rattoppm.py: error: unrecognized arguments: baz",
        )

    @unix_only
    def test_converts_rat_to_ppm_via_stdio(self):
        infile = pkg_resources.resource_stream(
            __name__, "fixtures/watrfall.rat"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.ppm"
        )
        read, write = os.pipe()
        os.write(write, infile.read())
        os.close(write)
        subprocess.check_call(
            [sys.executable, "coco/rattoppm.py"],
            env={"PYTHONPATH": "."},
            stdin=read,
            stdout=self.outfile,
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_converts_rat_to_ppm_via_stdin(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.rat"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/watrfall.ppm"
        )
        subprocess.check_call(
            [sys.executable, "coco/rattoppm.py", infilename],
            env={"PYTHONPATH": "."},
            stdout=self.outfile,
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_help(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/rattoppm.py", "-h"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, "Convert RS-DOS RAT images to PPM")
        self.assertRegex(output, self.VERSION_REGEX)
        self.assertRegex(output, self.USAGE_REGEX)
        self.assertRegex(output, self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(output, self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/rattoppm.py", "--version"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/rattoppm.py", "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"rattoppm.py: error: unrecognized arguments: --oops",
        )
