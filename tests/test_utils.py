from collections import OrderedDict
from io import open
import os
import shutil
import tempfile
import unittest
from pypianalyser.utils import order_dict_by_key_name, read_file_lines_into_list, write_list_lines_into_file, \
    append_line_to_file, remove_unknown_keys_from_dict, normalize_package_name, order_release_names_fallback


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

    def test_append_line_to_file(self):
        expected_value = ['A', 'B', 'C', 'D']

        for line in expected_value:
            append_line_to_file(self.temp_filepath, line)

        with open(self.temp_filepath, 'r', encoding='utf-8') as fp:
            actual_value = fp.read()
        actual_value = actual_value.split()
        self.assertListEqual(expected_value, actual_value)

    def test_remove_unknown_keys_from_dict(self):
        input_dict = {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}
        expected_result = {'A': 'a', 'C': 'c'}
        remove_unknown_keys_from_dict(input_dict, ['A', 'C'])
        self.assertDictEqual(expected_result, input_dict)

    def test_normalize_package_name(self):
        input = 'RobotFramework_Lib1'
        expected_result = 'robotframework-lib1'
        actual_result = normalize_package_name(input)
        self.assertEqual(expected_result, actual_result)

    def test_order_release_names_fallback(self):
        inp = {
            '0.0.1':
                [{
                    'filename': 'robotframework-difflibrary-0.0.1.tar.gz',
                    'upload_time': '2016-02-19T13:08:33',
                    'upload_time_iso_8601': '2016-02-19T13:08:33.988065Z'
                }],
            '0.1.0':
                [{
                    'filename': 'robotframework-difflibrary-0.1.0.tar.gz',
                    'upload_time': '2016-11-01T22:36:38',
                    'upload_time_iso_8601': '2016-11-01T22:36:38.451004Z',
                }],
            '0.1dev':
                [{
                    'filename': 'robotframework-difflibrary-0.1dev.tar.gz',
                    'upload_time': '2011-10-05T05:58:49',
                    'upload_time_iso_8601': '2011-10-05T05:58:49.218714Z',
                }]
        }
        expected_value = ['0.1.0', '0.0.1', '0.1dev']
        actual_value = order_release_names_fallback(inp)
        self.assertListEqual(expected_value, actual_value)