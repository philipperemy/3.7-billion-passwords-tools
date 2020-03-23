import unittest

from breach.query import mask_pass, mask_pass_justin_rule


class ParserTest(unittest.TestCase):

    def test_mask_password(self):
        self.assertEqual('123456**654321', mask_pass('12345688654321', num_asterisks=2))
        self.assertEqual('123456***54321', mask_pass('12345688654321', num_asterisks=3))
        self.assertEqual('12345****54321', mask_pass('12345688654321', num_asterisks=4))
        self.assertEqual('12**********21', mask_pass('12345688654321', num_asterisks=10))
        self.assertEqual('1************1', mask_pass('12345688654321', num_asterisks=12))
        self.assertEqual('**************', mask_pass('12345688654321', num_asterisks=14))
        self.assertEqual('**************', mask_pass('12345688654321', num_asterisks=18))
        self.assertEqual('**************', mask_pass('12345688654321', num_asterisks=99))
        self.assertEqual('1234568*654321', mask_pass('12345688654321', num_asterisks=1))
        self.assertEqual('12345688654321', mask_pass('12345688654321', num_asterisks=0))

    def test_mask_password_justin(self):
        expected = 'il**********m'
        initial = 'iloveicecream'
        assert len(expected) == len(initial)
        self.assertEqual(expected, mask_pass_justin_rule(initial, num_asterisks=-1))

        expected = 'm****n'
        initial = 'martin'
        assert len(expected) == len(initial)
        self.assertEqual(expected, mask_pass_justin_rule(initial, num_asterisks=-1))


if __name__ == '__main__':
    unittest.main()
