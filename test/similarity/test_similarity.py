from pathlib import Path
from unittest import TestCase

from dataset_mining.code_similarity import is_similar_functions


class TestSimilarity(TestCase):
    current_directory = Path(__file__).absolute().parent

    def test_is_similar(self):
        is_similar = is_similar_functions(
            str(Path(self.current_directory, 'before\\EduStepicConnector.java')),
            str(Path(self.current_directory, 'after\\EduStepicConnector.java')),
            [142, 153],
            [159, 171]
        )
        self.assertEqual(is_similar, True)

    def test_is_not_similar(self):
        # real EM, but too many changes
        is_similar = is_similar_functions(
            str(Path(self.current_directory, 'before\\FixedMembershipToken.java')),
            str(Path(self.current_directory, 'after\\FixedMembershipToken.java')),
            [55, 88],
            [73, 82]
        )
        self.assertEqual(is_similar, False)