from pathlib import Path
from unittest import TestCase

from veniq.dataset_mining.create_dataset_json import find_lines
from veniq.dataset_mining.code_similarity import is_similar_functions


class TestFunctionsForMining(TestCase):
    current_directory = Path(__file__).absolute().parent

    def test_is_similar(self):
        is_similar = is_similar_functions(
            str(Path(self.current_directory, 'before/EduStepicConnector.java')),
            str(Path(self.current_directory, 'after/EduStepicConnector.java')),
            [142, 153],
            [159, 171]
        )
        self.assertEqual(is_similar, True)

    def test_is_not_similar(self):
        # real EM, but too many changes
        is_similar = is_similar_functions(
            str(Path(self.current_directory, 'before/FixedMembershipToken.java')),
            str(Path(self.current_directory, 'after/FixedMembershipToken.java')),
            [55, 88],
            [73, 82]
        )
        self.assertEqual(is_similar, False)

    def test_find_lines_second_line_with_gap(self):
        d = [{
            "startLine": 1,
            "endLine": 1},
            {
                "startLine": 3,
                "endLine": 5,
            }]

        lst = find_lines(d)
        self.assertEqual(lst, ((1, 1), (3, 5)))

    def test_find_lines_second_line_no_gap(self):
        d = [{
            "startLine": 1,
            "endLine": 1
        },
            {
                "startLine": 2,
                "endLine": 5,
            }]
        lst = find_lines(d)
        self.assertEqual(lst, ((1, 5), ))

    def test_find_lines_repetitions(self):
        d = [{
            "startLine": 1,
            "endLine": 4
            },
            {
                "endLine": 2,
                "startLine": 2,
            },
            {
                "startLine": 3,
                "endLine": 3},
            {

                "startLine": 6,
                "endLine": 10,
            },
            {
                "startLine": 9,
                "endLine": 9},
            {
                "endLine": 10,
                "startLine": 10,
            }
        ]
        lst = find_lines(d)
        self.assertEqual(lst, ((1, 4), (6, 10)))

    def test_find_lines_last_wit_gap(self):
        d = [{
            "startLine": 1,
            "endLine": 4
            },
            {

                "startLine": 6,
                "endLine": 10,
            },
            {
                "startLine": 15,
                "endLine": 15
            }
        ]
        lst = find_lines(d)
        self.assertEqual(lst, ((1, 4), (6, 10), (15, 15)))

    def test_large(self):
        d = [
            {
                "startLine": 327,
                "endLine": 327
            },
            {
                "startLine": 328,
                "endLine": 328
            },
            {
                "startLine": 331,
                "endLine": 331
            },
            {
                "startLine": 334,
                "endLine": 334
            },
            {
                "startLine": 336,
                "endLine": 336
            },
            {
                "startLine": 338,
                "endLine": 338
            },
            {
                "startLine": 340,
                "endLine": 340
            },
            {
                "startLine": 343,
                "endLine": 343
            },
            {
                "startLine": 346,
                "endLine": 346
            },
            {
                "startLine": 347,
                "endLine": 347
            },
            {
                "startLine": 349,
                "endLine": 349
            },
            {
                "startLine": 355,
                "endLine": 355
            },
            {
                "startLine": 358,
                "endLine": 358
            },
            {
                "startLine": 360,
                "endLine": 360
            },
            {
                "startLine": 362,
                "endLine": 362
            },
            {
                "startLine": 367,
                "endLine": 367
            },
            {
                "startLine": 380,
                "endLine": 380
            },
            {
                "startLine": 382,
                "endLine": 382
            },
            {
                "startLine": 387,
                "endLine": 387
            },
            {
                "startLine": 409,
                "endLine": 409
            },
            {
                "startLine": 394,
                "endLine": 394
            },
            {
                "startLine": 395,
                "endLine": 395
            },
            {
                "startLine": 397,
                "endLine": 397
            },
            {
                "startLine": 399,
                "endLine": 399
            },
            {
                "startLine": 390,
                "endLine": 390
            },
            {
                "startLine": 339,
                "endLine": 341
            },
            {
                "startLine": 339,
                "endLine": 341
            },
            {
                "startLine": 337,
                "endLine": 342
            },
            {
                "startLine": 337,
                "endLine": 342
            },
            {
                "startLine": 359,
                "endLine": 361
            },
            {
                "startLine": 359,
                "endLine": 361
            },
            {
                "startLine": 356,
                "endLine": 364
            },
            {
                "startLine": 357,
                "endLine": 363
            },
            {
                "startLine": 357,
                "endLine": 363
            },
            {
                "startLine": 356,
                "endLine": 364
            },
            {
                "startLine": 366,
                "endLine": 368
            },
            {
                "startLine": 366,
                "endLine": 368
            },
            {
                "startLine": 350,
                "endLine": 370
            },
            {
                "startLine": 352,
                "endLine": 369
            },
            {
                "startLine": 352,
                "endLine": 369
            },
            {
                "startLine": 350,
                "endLine": 370
            },
            {
                "startLine": 408,
                "endLine": 410
            },
            {
                "startLine": 324,
                "endLine": 411
            },
            {
                "startLine": 396,
                "endLine": 398
            },
            {
                "startLine": 398,
                "endLine": 400
            },
            {
                "startLine": 396,
                "endLine": 400
            },
            {
                "startLine": 383,
                "endLine": 404
            },
            {
                "startLine": 386,
                "endLine": 401
            },
            {
                "startLine": 384,
                "endLine": 403
            },
            {
                "startLine": 384,
                "endLine": 403
            },
            {
                "startLine": 386,
                "endLine": 401
            },
            {
                "startLine": 383,
                "endLine": 404
            },
            {
                "startLine": 388,
                "endLine": 392
            },
            {
                "startLine": 408,
                "endLine": 410
            },
            {
                "startLine": 389,
                "endLine": 391
            }
        ]
        lst = find_lines(d)
        self.assertEqual(lst, ((324, 411), ))
