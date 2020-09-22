from unittest import TestCase

from veniq.baselines.semi.benefits import _LCOM2


class BenefitTest(TestCase):
    dict_semantic = {3: ['length', 'rcs'],
                4: ['length', 'i', 'rcs'],
                5: [],
                6: ['rcs', 'i'],
                7: ['rcs', 'rec', 'i', 'grabRes'],
                9: ['rcs', 'rec', 'i', 'grabNonFileSetRes'],
                11: ['length', 'rec', 'j'],
                12: ['rec', 'j', 'getName', 'replace'],
                13: ['rcs', 'i'],
                14: ['rcs', 'i'],
                15: ['afs', 'equals', 'getFullpath', 'getProj'],
                16: ['name.afs', 'getProj', 'getFullpath'],
                17: ['afs', 'equals', 'getProj', 'getPref'],
                18: ['afs', 'getPref', 'getProj'],
                19: ['pr', 'endsWith'],
                20: ['pr'],
                22: ['name', 'pr'],
                25: ['MANIFEST_NAME', 'name', 'equalsIgnoreCase'],
                26: ['j', 'manifests', 'rec', 'i'],
                30: ['manifests', 'i'],
                31: ['manifests', 'i'],
                34: ['manifests']
                }

    def test_1(self):
        example_1 = (3, 14)
        example_2 = (15, 18)
        original_value = _LCOM2(self.dict_semantic)
        opportunity_value_1 = _LCOM2(self.dict_semantic, example_1, 'opportunity')
        original_after_ref_value_1 = _LCOM2(self.dict_semantic, example_1, 'after_ref')
        self.assertEqual(original_value > opportunity_value_1, True)
        self.assertEqual(original_value > original_after_ref_value_1, True)

        self.assertEqual(original_value > opportunity_value_1, True)
