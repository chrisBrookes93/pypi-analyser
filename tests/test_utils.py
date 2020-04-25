import unittest


class TestUtils(unittest.TestCase):

    def test_order_dict_by_key_name(self):
        input = {'a': 1, 'c': 3, 'b': 2, 'z': 4}
        #result =