import os
from io import open
import unittest
from mock import MagicMock, patch
from pypianalyser.pypi_index_helpers import get_package_list, get_metadata_for_package
from pypianalyser.exceptions import Exception404


class TestPyPiIndexHelpers(unittest.TestCase):

    def setUp(self):
        self.resources_dir = os.path.join(os.path.dirname(__file__), 'resources')
        with open(os.path.join(self.resources_dir, 'raw_simple_index.dat'), 'r', encoding='utf-8') as fp:
            self.mock_simple_index = fp.read()
        with open(os.path.join(self.resources_dir, 'raw_package_metadata_blob.dat'), 'r', encoding='utf-8') as fp:
            self.mock_metadata_blob = fp.read()

    def test_get_metadata_for_package(self):
        mock_response = MagicMock()
        mock_response.content = self.mock_metadata_blob
        mock_response.status_code = 200

        with patch('pypianalyser.pypi_index_helpers.requests.get', return_value=mock_response):
            result = get_metadata_for_package('pack1')
            self.assertIn('info', result)
            self.assertIn('releases', result)

    def test_get_metadata_for_package_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch('pypianalyser.pypi_index_helpers.requests.get', return_value=mock_response):
            self.assertRaises(Exception404, get_metadata_for_package, 'pack1')

    def test_get_metadata_for_package_other_http_code(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch('pypianalyser.pypi_index_helpers.requests.get', return_value=mock_response):
            self.assertRaisesRegexp(Exception, 'HTTP Error: 500 on https://pypi.org/pypi/pack1/json',
                                    get_metadata_for_package, 'pack1')

    def test_get_package_list(self):
        mock_response = MagicMock()
        mock_response.content = self.mock_simple_index
        expected_result = ['pack-a', 'pack-b', 'pack-c', 'pack-d', 'pack-e']

        with patch('pypianalyser.pypi_index_helpers.requests.get', return_value=mock_response):
            actual_result = get_package_list()
            self.assertListEqual(expected_result, actual_result)

