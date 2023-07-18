import os
import filecmp
import pkg_resources
import subprocess
import sys
import tempfile
import unittest

import coco.veftopng
from .util import unix_only
from coco import __version__
from coco.util import iotostr


class TestVEFToPNG(unittest.TestCase):
    USAGE_REGEX = r"\[-h\] \[--version\] image.vef image.png"
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.vef\s*input VEF image file\s*"
        r"image.png\s*output PNG image file"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    def setUp(self):
        self.outfile = tempfile.NamedTemporaryFile(
            "w", suffix=".png", delete=False
        )

    def tearDown(self):
        if not self.outfile.closed:
            self.outfile.close()
        os.remove(self.outfile.name)

    def test_converts_320x200x16_vef_to_png(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/trekies.vef"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/trekies.png"
        )
        self.outfile.close()
        coco.veftopng.start([infilename, self.outfile.name])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_640x200x4_vef_to_png(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/owlcasl.vef"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/owlcasl.png"
        )
        self.outfile.close()
        coco.veftopng.start([infilename, self.outfile.name])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_too_many_arguments(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/trekies.vef"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/veftopng.py",
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
            r"veftopng.py: error: unrecognized arguments: baz",
        )

    @unix_only
    def test_help(self):
        output = subprocess.check_output(
            [sys.executable, "coco/veftopng.py", "-h"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), "Convert OS-9 VEF images to PNG")
        self.assertRegex(iotostr(output), self.VERSION_REGEX)
        self.assertRegex(iotostr(output), self.USAGE_REGEX)
        self.assertRegex(iotostr(output), self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(iotostr(output), self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self):
        output = subprocess.check_output(
            [sys.executable, "coco/veftopng.py", "--version"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/trekies.vef"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/veftopng.py",
                    infilename,
                    self.outfile.name,
                    "--oops",
                ],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"veftopng.py: error: unrecognized arguments: --oops",
        )
