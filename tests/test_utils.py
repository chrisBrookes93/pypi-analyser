from collections import OrderedDict
from io import open
import os
import shutil
import tempfile
import unittest
from pypianalyser.utils import order_dict_by_key_name, read_file_lines_into_list, write_list_lines_into_file


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_filepath = os.path.join(self.temp_dir, 'test_file.txt')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_order_dict_by_key_name(self):
        input = {'a': 1, 'c': 3, 'b': 2, 'z': 4}
        result = order_dict_by_key_name(input)
        self.assertIsInstance(result, OrderedDict)

        expected_vales = [1, 2, 3, 4]
        actual_values = result.values()
        self.assertListEqual(expected_vales, actual_values)

    def test_write_list_lines_into_file(self):
        expected_value = ['A', 'B', 'C']
        write_list_lines_into_file(self.temp_filepath, expected_value)

        self.assertTrue(os.path.exists(self.temp_filepath))
        with open(self.temp_filepath, 'r', encoding='utf-8') as fp:
            actual_value = fp.read()
        actual_value = actual_value.split()
        self.assertListEqual(expected_value, actual_value)

    def test_read_file_lines_into_list(self):
        expected_value = ['A', 'B', 'C']
        with open(self.temp_filepath, 'w', encoding='utf-8') as fp:
            fp.write(u'\n'.join(expected_value))

        actual_value = read_file_lines_into_list(self.temp_filepath)
        self.assertListEqual(expected_value, actual_value)
