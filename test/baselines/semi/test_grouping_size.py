from unittest import TestCase

from veniq.baselines.semi.grouping_size import is_similar_size


class SimilarSizeTest(TestCase):

    def test_is_similar_size(self):
        example_1_1 = (2, 32)
        example_1_2 = (2, 34)
        self.assertEqual(is_similar_size(example_1_1, example_1_2), True)

    def test_lower_threshold(self):
        example_1_1 = (2, 32)
        example_1_2 = (2, 34)
        max_diff = 0.05
        self.assertEqual(is_similar_size(example_1_1, example_1_2,
                         max_size_difference=max_diff),
                         False)
