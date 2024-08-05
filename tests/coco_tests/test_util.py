import argparse
import unittest
import sys

from coco.util import (
    check_positive,
    check_zero_or_positive,
    getbit,
    iotobytes,
    iotostr,
    pack,
    stdiotobuffer,
    strtoio,
)


class TestUtil(unittest.TestCase):
    if sys.version_info < (3,):

        def test_iotostr(self) -> None:
            self.assertEqual("abc", iotostr("abc"))

        def test_strtoio(self) -> None:
            self.assertEqual("abc", strtoio("abc"))

        def test_stdiotobuffer(self) -> None:
            self.assertEqual(sys.stdin, stdiotobuffer(sys.stdin))
            self.assertEqual(sys.stdout, stdiotobuffer(sys.stdout))

        def test_iotobytes(self) -> None:
            self.assertEqual(b"123", iotobytes("123"))

    else:

        def test_iotostr(self) -> None:
            self.assertEqual("abc", iotostr(b"abc"))

        def test_strtoio(self) -> None:
            self.assertEqual(b"abc", strtoio("abc"))

        def test_stdiotobuffer(self) -> None:
            self.assertEqual(sys.stdin.buffer, stdiotobuffer(sys.stdin))
            self.assertEqual(sys.stdout.buffer, stdiotobuffer(sys.stdout))

        def test_iotobytes(self) -> None:
            self.assertEqual(b"123", iotobytes(b"123"))

    def test_check_positive(self) -> None:
        self.assertEqual(3, check_positive(3))
        with self.assertRaises(argparse.ArgumentTypeError):
            check_positive(0)
        with self.assertRaises(argparse.ArgumentTypeError):
            check_positive(-1)
        self.assertEqual(3, check_positive(3.9))

    def test_check_zero_or_positive(self) -> None:
        self.assertEqual(3, check_zero_or_positive(3))
        self.assertEqual(0, check_zero_or_positive(0))
        with self.assertRaises(argparse.ArgumentTypeError):
            check_positive(0)
        self.assertEqual(3, check_positive(3.9))

    def test_getbit(self) -> None:
        self.assertEqual(getbit(33, 0), 1)
        self.assertEqual(getbit(32, 0), 0)
        self.assertEqual(getbit(128, 7), 1)
        self.assertEqual(getbit(128, 0), 0)

    def test_pack(self) -> None:
        self.assertEqual(pack([65, 66, 255, 0]), "AB\xff\x00")
