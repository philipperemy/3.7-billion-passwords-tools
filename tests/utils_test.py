import unittest

from breach.utils import RingDictionary


class UtilsTest(unittest.TestCase):

    def test_ring_dictionary_1(self):
        rd = RingDictionary(max_num_keys=3)
        rd['a'] = 2
        self.assertListEqual(sorted(rd.keys()), ['a'])
        self.assertListEqual(sorted(rd.k), ['a'])
        rd['b'] = 2
        self.assertListEqual(sorted(rd.keys()), ['a', 'b'])
        self.assertListEqual(sorted(rd.k), ['a', 'b'])
        rd['c'] = 2
        self.assertListEqual(sorted(rd.keys()), ['a', 'b', 'c'])
        self.assertListEqual(sorted(rd.k), ['a', 'b', 'c'])
        rd['d'] = 2
        self.assertListEqual(sorted(rd.keys()), ['b', 'c', 'd'])
        self.assertListEqual(sorted(rd.k), ['b', 'c', 'd'])

        rd = RingDictionary(max_num_keys=1)
        rd['c'] = 1
        rd['c'] = 2
        rd['c'] = 3
        self.assertListEqual(sorted(rd.keys()), ['c'])
        self.assertListEqual(sorted(rd.k), ['c'])

        rd['d'] = 3
        self.assertListEqual(sorted(rd.keys()), ['d'])
        self.assertListEqual(sorted(rd.k), ['d'])


if __name__ == '__main__':
    unittest.main()
