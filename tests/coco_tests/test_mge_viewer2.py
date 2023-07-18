import os
import filecmp
import pkg_resources
import subprocess
import sys
import tempfile
import unittest

import coco.mge_viewer2
from .util import unix_only
from coco import __version__
from coco.util import iotostr


class TestMGE_Viewer2(unittest.TestCase):
    USAGE_REGEX = r"\[-h\] \[--version\] \[image.mge\]"
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image.mge\s*input MGE image file\s*"
    )
    OPTIONAL_ARGS_REGEX = (
        r"option.*:\s*-h, --help\s*show this help message and exit"
        r"\s*--version\s*show program\'s version number and exit"
    )
    VERSION_REGEX = r"{}".format(__version__).replace(".", "\\.")

    @unix_only
    def test_too_many_arguments(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/dragon1.mge"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/mge_viewer2.py",
                    infilename,
                    "baz",
                ],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"mge_viewer2.py: error: unrecognized arguments: baz",
        )

    @unix_only
    def test_help(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/mge_viewer2.py", "-h"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, "View ColorMax 3 MGE files")
        self.assertRegex(output, self.VERSION_REGEX)
        self.assertRegex(output, self.USAGE_REGEX)
        self.assertRegex(output, self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(output, self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/mge_viewer2.py", "--version"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/mge_viewer2.py", "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"mge_viewer2.py: error: unrecognized arguments: --oops",
        )
