import os
import filecmp
import pkg_resources
import subprocess
import sys
import tempfile
import unittest

import coco.maxtoppm
from .util import unix_only
from unittest import mock
from coco import __version__
from coco.util import iotostr


class TestMaxToPPM(unittest.TestCase):
    USAGE_REGEX = (
        r"usage: maxtoppm \[-h\] \[--version\] \[-br | -rb | -br2 | -rb2 | "
        r"-br3 | -rb3\] \[-i\]\n"
        r"\[-w width\] \[-newsroom\]"
        r"image\] \[image.ppm\]"
    )
    POSITIONAL_ARGS_REGEX = (
        r"positional arguments:\s*image\s*input image file\s*"
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
        if os.path.exists(self.outfile.name):
            os.remove(self.outfile.name)

    def test_converts_max_to_ppm(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_br(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_br.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-br"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_rb(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_br.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-br"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_br2(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_br2.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-br2"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_rb2(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_rb2.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-rb2"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_br3(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_br3.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-br3"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_rb3(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_rb3.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-rb3"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_s10(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_s10.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-s10"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_max_to_ppm_s11(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_s11.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-s11"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_specifying_width(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_rb_w128.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start(
            [infilename, self.outfile.name, "-rb", "-w", "128"]
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_specifying_height(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_r96.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-r", "96"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_skipping_bytes(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4_s7.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-s", "7"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    def test_converts_newsroom_files(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/shamrock.art"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/shamrock.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-newsroom"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @mock.patch("sys.stderr")
    def test_detects_bad_headers_1(self, mockStderr):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.bad1.max"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name])
        self.assertFalse(os.path.exists(self.outfile.name))
        mockStderr.write.assert_called_with("bad first byte in header\n")

    @mock.patch("sys.stderr")
    def test_ignores_bad_headers_1(self, mockStderr):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.bad1.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-i"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))
        mockStderr.write.assert_called_with("bad first byte in header\n")

    @mock.patch("sys.stderr")
    def test_detects_bad_headers_2(self, mockStderr):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.bad2.max"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name])
        self.assertFalse(os.path.exists(self.outfile.name))
        mockStderr.write.assert_called_with(
            "data length 6147 in header would be closest to 256x192 but "
            "that would be 6144 bytes\n"
        )

    @mock.patch("sys.stderr")
    def test_ignores_bad_headers_2(self, mockStderr):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.bad2.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        self.outfile.close()
        coco.maxtoppm.start([infilename, self.outfile.name, "-i"])
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))
        mockStderr.write.assert_called_with(
            "data length 6147 in header would be closest to 256x192 but that "
            "would be 6144 bytes\n"
        )

    @unix_only
    def test_too_many_arguments(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [
                    sys.executable,
                    "coco/maxtoppm.py",
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
            r"maxtoppm.py: error: unrecognized arguments: baz",
        )

    @unix_only
    def test_converts_max_to_ppm_via_stdio(self):
        infile = pkg_resources.resource_stream(__name__, "fixtures/eye4.max")
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        read, write = os.pipe()
        os.write(write, infile.read())
        os.close(write)
        subprocess.check_call(
            [sys.executable, "coco/maxtoppm.py"],
            env={"PYTHONPATH": "."},
            stdin=read,
            stdout=self.outfile,
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_converts_max_to_ppm_via_stdin(self):
        infilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.max"
        )
        comparefilename = pkg_resources.resource_filename(
            __name__, "fixtures/eye4.ppm"
        )
        subprocess.check_call(
            [sys.executable, "coco/maxtoppm.py", infilename],
            env={"PYTHONPATH": "."},
            stdout=self.outfile,
        )
        self.assertTrue(filecmp.cmp(self.outfile.name, comparefilename))

    @unix_only
    def test_help(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/maxtoppm.py", "-h"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, "Convert RS-DOS MAX and ART images to PPM")
        self.assertRegex(output, self.VERSION_REGEX)
        self.assertRegex(output, self.USAGE_REGEX)
        self.assertRegex(output, self.POSITIONAL_ARGS_REGEX)
        self.assertRegex(output, self.OPTIONAL_ARGS_REGEX)

    @unix_only
    def test_version(self):
        output = iotostr(
            subprocess.check_output(
                [sys.executable, "coco/maxtoppm.py", "--version"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        )
        self.assertRegex(output, self.VERSION_REGEX)

    @unix_only
    def test_unknown_argument(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/maxtoppm.py", "--oops"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"maxtoppm.py: error: unrecognized arguments: --oops",
        )

    @unix_only
    def test_conflicting_arguments(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            subprocess.check_output(
                [sys.executable, "coco/maxtoppm.py", "-br", "-rb"],
                env={"PYTHONPATH": "."},
                stderr=subprocess.STDOUT,
            )
        self.assertRegex(iotostr(context.exception.output), self.USAGE_REGEX)
        self.assertRegex(
            iotostr(context.exception.output),
            r"maxtoppm.py: error: argument -rb: not allowed with argument -br",
        )
