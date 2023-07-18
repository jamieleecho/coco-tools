import os
import filecmp
import pkg_resources
import sys
import subprocess
import tempfile
import unittest

import coco.pixtopgm
from coco import __version__
from coco.util import iotostr

from .util import unix_only


class TestPixToPGM(unittest.TestCase):
    USAGE_REGEX = r"\[-h\] \[--version\] image.pix \[image.pgm\]"
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.pix\s*input PIX image file\s*"
        r"image.pgm\s*output PGM image file"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    def setUp(self):
        self.outfile = tempfile.NamedTemporaryFile(
            "w", suffix=".pgm", delete=False
        )

    def tearDown(self):
        if not self.outfile.closed:
            self.outfile.close()
        os.remove(self.outfile.name)

    def test_converts_pix_to_pgm(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/sue.pix"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/sue.pgm"
        )
        self.outfile.close()
        coco.pixtopgm.start([infilename, self.outfile.name])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_too_many_arguments(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/sue.pix"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/pixtopgm.py",
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
            r"pixtopgm.py: error: unrecognized arguments: baz",
        )

    @unix_only
    def test_converts_pix_to_pgm_via_stdout(self):
        infile = pkg_resources.resource_filename(__name__, "fixtures/sue.pix")
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/sue.pgm"
        )
        subprocess.check_call(
            [sys.executable, "coco/pixtopgm.py", infile],
            env={"PYTHONPATH": "."},
            stdout=self.outfile,
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_help(self):
        output = subprocess.check_output(
            [sys.executable, "coco/pixtopgm.py", "-h"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), "Convert RS-DOS PIX images to PGM")
        self.assertRegex(iotostr(output), self.VERSION_REGEX)
        self.assertRegex(iotostr(output), self.USAGE_REGEX)
        self.assertRegex(iotostr(output), self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(iotostr(output), self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self):
        output = subprocess.check_output(
            [sys.executable, "coco/pixtopgm.py", "--version"],
            env={"PYTHONPATH": "."},
            stderr=subprocess.STDOUT,
        )
        self.assertRegex(iotostr(output), self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            infile = pkg_resources.resource_filename(
                __name__, "fixtures/sue.pix"
            )
            subprocess.check_output(
                [sys.executable, "coco/pixtopgm.py", infile, "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"pixtopgm.py: error: unrecognized arguments: --oops",
        )
