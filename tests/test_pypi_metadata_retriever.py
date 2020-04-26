import os
import tempfile
import unittest
from mock import MagicMock, patch
import shutil
from pypianalyser.pypi_metadata_retriever import PyPiMetadataRetriever
from pypianalyser.exceptions import Exception404


class TestPyPiMetadataRetriever(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db_path = os.path.join(self.temp_dir, 'db.sqlite')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_calculate_package_list(self):
        expected_result = ['aaa-123', 'aaa-789']
        test_obj = PyPiMetadataRetriever(db_path=self.temp_db_path,
                                         max_packages=2,
                                         package_regex='^(aaa-.*)|(ccc-.*)',
                                         file_404='404.txt')

        list_from_pypi = ['aaa-123', 'aaa-456', 'aaa-789', 'bbb-123', 'bbb-456', 'bbb-789', 'ccc-123', 'ccc-456',
                          'ccc-789']
        list_404 = ['aaa-456']
        mock_db = MagicMock()
        mock_db.get_package_names.return_value = ['ccc-456', 'ccc-789']
        with patch('pypianalyser.pypi_metadata_retriever.get_package_list', return_value=list_from_pypi), \
             patch('pypianalyser.pypi_metadata_retriever.read_file_lines_into_list', return_value=list_404), \
             patch('pypianalyser.pypi_metadata_retriever.PyPiAnalyserSqliteHelper', return_value=mock_db):
            actual_result = test_obj.calculate_package_list()
        self.assertListEqual(expected_result, actual_result)

    def test_truncate_description(self):
        test_obj = PyPiMetadataRetriever(trunc_description=10,
                                         db_path=self.temp_db_path)
        input_metadata = {'info': {
            'description': 'A' * 1000,
            'summary': 'B' * 1000
        }}
        test_obj._truncate_description(input_metadata)
        self.assertEqual(10, len(input_metadata['info']['description']))
        self.assertEqual(10, len(input_metadata['info']['summary']))

    def test_truncate_releases(self):
        test_obj = PyPiMetadataRetriever(trunc_releases=2,
                                         db_path=self.temp_db_path)
        input_metadata = \
            {'releases':
                {
                    '1.0.1': {},
                    '2.1.0': {},
                    '1.5.2': {}
                }
            }
        test_obj._truncate_releases(input_metadata)
        self.assertEqual(2, len(input_metadata['releases']))
        self.assertListEqual(['2.1.0', '1.5.2'], list(input_metadata['releases'].keys()))

    def test_truncate_releases_fallback(self):
        test_obj = PyPiMetadataRetriever(trunc_releases=1,
                                         db_path=self.temp_db_path)
        input_metadata = \
            {'releases':
                {
                    '1.0.1': [{'upload_time': '2016-02-19T13:08:33'}],
                    '2.1.0': {},
                    '2.2.1dev': [{'upload_time': '2018-02-19T13:08:33'}],
                }
            }
        with patch('pypianalyser.pypi_metadata_retriever.LooseVersion', side_effect=TypeError):
            test_obj._truncate_releases(input_metadata)
        self.assertEqual(1, len(input_metadata['releases']))
        self.assertListEqual(['2.2.1dev'], list(input_metadata['releases'].keys()))

    def test_run_single_thread_override(self):
        test_obj = PyPiMetadataRetriever(db_path=self.temp_db_path)
        test_obj.package_list = ['a', 'b', 'c']
        with patch('pypianalyser.pypi_metadata_retriever.PyPiMetadataRetriever._threaded_process') as mock_tp:
            test_obj.run()
        mock_tp.assert_called_once_with(test_obj.package_list)

    def test_run_multi_threaded(self):
        test_obj = PyPiMetadataRetriever(thread_count=3,
                                         db_path=self.temp_db_path)
        expected_chunk1 = list('A' * 40)
        expected_chunk2 = list('B' * 40)
        expected_chunk3 = list('C' * 41)

        test_obj.package_list = expected_chunk1 + expected_chunk2 + expected_chunk3
        with patch('pypianalyser.pypi_metadata_retriever.PyPiMetadataRetriever._threaded_process') as mock_tp:
            test_obj.run()
            mock_tp.assert_any_call(expected_chunk1)
            mock_tp.assert_any_call(expected_chunk2)
            mock_tp.assert_any_call(expected_chunk3)

    def test_threaded_process_exception_reported_on_404(self):
        test_obj = PyPiMetadataRetriever(db_path=self.temp_db_path)
        with patch('pypianalyser.pypi_metadata_retriever.get_metadata_for_package', side_effect=Exception404('err')),\
             patch('pypianalyser.pypi_metadata_retriever.PyPiMetadataRetriever._report_404') as mock_r404:
            test_obj._threaded_process(['a'])
            mock_r404.assert_called_once_with('a')

    def test_test_threaded_process_commit_to_db(self):
        test_obj = PyPiMetadataRetriever(db_path=self.temp_db_path)
        mock_metadata = {'info': {
            'description': 'A' * 1000,
            'summary': 'B' * 1000
        }}
        mock_db = MagicMock()
        with patch('pypianalyser.pypi_metadata_retriever.get_metadata_for_package', return_value=mock_metadata),\
             patch('pypianalyser.pypi_metadata_retriever.PyPiAnalyserSqliteHelper', return_value=mock_db):
            test_obj._open_db()
            test_obj._threaded_process(['a'])
            mock_db.commit_package_to_db.assert_called_once_with(mock_metadata)
