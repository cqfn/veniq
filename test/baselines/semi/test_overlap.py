# The MIT License (MIT)
#
# Copyright (c) 2020 Veniq
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import unittest

from veniq.baselines.semi.overlap import is_overlap


class TestOverlap(unittest.TestCase):
    def test_zero_overlap(self):
        res = is_overlap([1, 5], [7, 10])
        self.assertEqual(res, False)

    def test_full_overlap(self):
        res = is_overlap([1, 7], [4, 7])
        self.assertEqual(res, True)

    def test_partial_overlap(self):
        res = is_overlap([1, 5], [3, 6])
        self.assertEqual(res, True)

    def test_partial_overlap_with_miv_overlap_false(self):
        res = is_overlap([1, 12], [12, 22])
        self.assertEqual(res, False)