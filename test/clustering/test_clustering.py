# flake8: noqa
from unittest import TestCase
from collections import OrderedDict
from veniq.baselines.semi.clustering import SEMI


class ClusteringTestCase(TestCase):
      example = OrderedDict([
             (2, []),
             (3, ['manifests', 'rcs', 'length']),
             (4, ['rcs', 'length', 'i']),
             (5, ['rec']),
             (6, ['rcs', 'i']),
             (7, ['rcs', 'i', 'rec', 'grabRes']),
             # (8, ['rcs', 'i']),
             (8, []),
             (9, ['rcs', 'i', 'rec', 'grabNonFileSetRes']),
             (10, []),
             (11, ['length', 'rec', 'j']),
             (12, ['rec', 'j', 'name', 'getName', 'replace']),
             (13, ['rcs', 'i']),
             (14, ['rcs', 'i', 'afs']),
             (15, ['rcs', 'afs', 'equals', 'getFullpath', 'getProj']),
             (16, ['name', 'afs', 'getFullpath', 'getProj']),
             (17, ['afs', 'equals', 'getProj', 'getPref']),
             (18, ['afs', 'getProj', 'getPref', 'pr']),
             (19, ['pr', 'endsWith']),
             (20,['pr']),
             (21,[]),
             (22,['name', 'pr']),
             (23,[]),
             (24,[]),
             (25,['name', 'equalsIgnoreCase']),
             (26, ['manifests', 'rec', 'j', 'i']),
             (27,[]),
             (28,[]),
             (29,[]),
             (30, ['manifests', 'i']),
             (31, ['manifests', 'i']),
             (32,[]),
             (33,[]),
             (34, ['manifests']),
            ]
           )

      def test_article(self):
            self.assertEqual(SEMI(self.example),
            [[3, 12], [13, 22], [30, 31]], 'Error on STEP 1')

