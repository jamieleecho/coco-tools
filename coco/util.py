import argparse
import codecs
import sys


if sys.version_info < (3,):

    def iotostr(x):
        return x

    def strtoio(x):
        return x

    def stdiotobuffer(x):
        return x

    def iotobytes(x):
        return bytes(x)


else:

    def iotostr(x):
        return codecs.decode(x, encoding="latin1")

    def strtoio(x):
        return codecs.encode(x, encoding="latin1")

    def stdiotobuffer(x):
        return x.buffer

    def iotobytes(x):
        return x


def check_positive(value):
    """Argparse validator for integers > 0"""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def check_zero_or_positive(value):
    """Argparse validator for integers >= 0"""
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid int value >= 0" % value)
    return ivalue


def getbit(c, ii):
    """
    Similar to Ruby's bit manipulation, returns the iith bit of c.
    c - an integer
    ii - bit to probe
    returns 1 if bit ii in c is 1 and o otherwise
    """
    return 1 if (c & (1 << ii)) else 0


def pack(a):
    """
    Similar to Ruby's array pack('ccc'), returns a character
    packed representation of a
    a - array of integers
    return - string of equivalent ASCII chars.
    """
    return (
        "".join("{}".format(chr(x)) for x in a)
        if sys.version_info < (3,)
        else iotostr(bytes(a))
    )
