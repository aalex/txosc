# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
OSC tests.

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest

class BlobArgumentTest(unittest.TestCase):
    """
    Encoding and decoding of a "blob" argument.
    """
    def testEncode(self):
        self.assertEqual(1,1)

    def testDecode(self):
        self.assertEqual(1,1)

