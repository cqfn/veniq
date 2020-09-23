from unittest import TestCase

from veniq.baselines.semi.group_and_rank import (
    in_same_group,
    group_and_rank_in_groups,
    output_best_opportunities)


class GroupAndRankTest(TestCase):
    opport_0 = (3, 5)
    opport_1 = (2, 32)
    opport_2 = (2, 34)
    opport_3 = (33, 50)
    opport_4 = (35, 50)
    opport_5 = (55, 65)
    opportunities = [opport_0, opport_1, opport_2,
                     opport_3, opport_4, opport_5]

    def test_in_same_group_1(self):
        self.assertTrue(in_same_group(self.opport_1, self.opport_2))

    def test_in_same_group_2(self):
        self.assertTrue(in_same_group(self.opport_3, self.opport_4))

    def test_not_in_same_group(self):
        self.assertFalse(in_same_group(self.opport_0, self.opport_5))

    def test_diff_in_size(self):
        self.assertFalse(in_same_group(self.opport_0, self.opport_1))

    def test_not_overlap(self):
        self.assertFalse(in_same_group(self.opport_2, self.opport_3))

    def test_not_overlap_custom(self):
        self.assertTrue(
            in_same_group(self.opport_3, self.opport_4)
        )
        self.assertFalse(
            in_same_group(self.opport_3, self.opport_4,
                          min_overlap=0.9)
        )

    def test_group_and_rank_in_groups(self):
        expect_primary = [self.opport_0, self.opport_1,
                          self.opport_3, self.opport_5]

        self.assertEqual(
            set(group_and_rank_in_groups(self.opportunities)),
            set(expect_primary))

    def test_group_and_rank_in_groups_custom_overlap(self):
        expect_primary = [self.opport_0, self.opport_1,
                          self.opport_3, self.opport_4, self.opport_5]

        self.assertEqual(
            set(group_and_rank_in_groups(
                self.opportunities,
                min_overlap=0.9)),
            set(expect_primary)
        )

    def test_output_best_opportunities(self):
        expect_list = [self.opport_0, self.opport_1,
                       self.opport_3, self.opport_5]
        self.assertEqual(
            output_best_opportunities(self.opportunities),
            expect_list
        )

    def test_output_best_opportunities_top1(self):
        expect_list = [self.opport_0]
        self.assertEqual(
            output_best_opportunities(self.opportunities, top_k=1),
            expect_list
        )

    def test_output_best_opportunities_custom_overlap_top4(self):
        expect_list = [self.opport_0, self.opport_1,
                       self.opport_3, self.opport_4]
        self.assertEqual(
            output_best_opportunities(
                self.opportunities,
                top_k=4,
                min_overlap=0.9
            ),
            expect_list
        )
