import unittest

from veniq.baselines.semi.overlap import is_overlap


class TestOverlap(unittest.TestCase):
    def test_zero_overlap(self):
        res = is_overlap((1, 5), (7, 10))
        self.assertEqual(res, False)

    def test_full_overlap(self):
        res = is_overlap((1, 7), (4, 7))
        self.assertEqual(res, True)

    def test_partial_overlap(self):
        res = is_overlap((1, 5), (3, 6))
        self.assertEqual(res, True)

    def test_partial_overlap_with_miv_overlap_false(self):
        res = is_overlap((1, 12), (12, 22))
        self.assertEqual(res, True)
