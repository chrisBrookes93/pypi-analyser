import unittest
import os
import json
from pypianalyser.sqlite_helpers import PyPiAnalyserSqliteHelper


class PyPiAnalyserSqliteHelperTests(unittest.TestCase):

    def setUp(self):
        self.db_name = 'test-db.sqlite'
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

        self.resources_dir = os.path.join(os.path.dirname(__file__), 'resources')
        with open(os.path.join(self.resources_dir, 'robotframework.json'), 'r') as fp:
            self.input_1 = json.load(fp)
        with open(os.path.join(self.resources_dir, 'robotframework-remoterunner.json'), 'r') as fp:
            self.input_2 = json.load(fp)

        self.test_obj = PyPiAnalyserSqliteHelper(self.db_name)
        self.test_obj.commit_package_to_db(self.input_1)
        self.test_obj.commit_package_to_db(self.input_2)

    def tearDown(self):
        if self.test_obj:
            self.test_obj.close()

        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_package(self):
        actual_value = self.test_obj.get_package_by_name('robotframework')
        expected_value = {
            "maintainer": "Pekka Klrck",
            "docs_url": None,
            "requires_python": "",
            "maintainer_email": "peke@eliga.fi",
            "keywords": "robotframework automation testautomation rpa testing acceptancetesting atdd bdd",
            "package_url": "https://pypi.org/project/robotframework/",
            "author": "Pekka Klrck",
            "author_email": "peke@eliga.fi",
            "download_url": "https://pypi.python.org/pypi/robotframework",
            "platform": "any",
            "version": "3.1.2",
            "description": "Robot Framework\n===============\n\n.. contents::\n   :local:\n\nIntroduction\n------------\n\n`Robot Framework <http://robotframework.org>`_ is a generic open source\nautomation framework for acceptance testin",
            "release_url": "https://pypi.org/project/robotframework/3.1.2/",
            "description_content_type": "",
            "requires_dist": None,
            "project_url": "https://pypi.org/project/robotframework/",
            "bugtrack_url": None,
            "name": "robotframework",
            "license": "Apache License 2.0",
            "summary": "Generic automation framework for acceptance testing and robotic process automation (RPA)",
            "home_page": "http://robotframework.org"
    }

        self.assertDictContainsSubset(expected_value, actual_value)

    def test_classifiers(self):
        actual_value = self.test_obj.get_classifiers_for_package_name('robotframework')
        expected_value = [
            "Development Status :: 5 - Production/Stable",
            "Framework :: Robot Framework",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: IronPython",
            "Programming Language :: Python :: Implementation :: Jython",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Topic :: Software Development :: Testing",
            "Topic :: Software Development :: Testing :: Acceptance",
            "Topic :: Software Development :: Testing :: BDD"
        ]
        self.assertListEqual(expected_value, actual_value)

        actual_value = self.test_obj.get_classifiers_for_package_name('robotframework-remoterunner')
        expected_value = [
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.7"
        ]
        self.assertListEqual(expected_value, actual_value)

    def test_releases(self):
        result = self.test_obj.get_releases_for_package('robotframework')
        self.assertIn('3.2b2', result.keys())
        self.assertIn('3.2rc1', result.keys())

        actual_release = result['3.2b2']
        self.assertEqual(2, len(actual_release))

        actual_release_file1 = actual_release[0]
        expected_release_file1 = {
            "has_sig": False,
            "upload_time": "2020-02-14T10:16:11",
            "comment_text": "robotframework",
            "python_version": "py2.py3",
            "url": "https://files.pythonhosted.org/packages/e5/a3/ef5738bd0e2c2532eadfeeec15e1b5e1b7be866b9a4805113f4b2fd06349/robotframework-3.2b2-py2.py3-none-any.whl",
            "md5_digest": "627c58f83dd25abb3350bd924bf66728",
            "requires_python": None,
            "filename": "robotframework-3.2b2-py2.py3-none-any.whl",
            "packagetype": "bdist_wheel",
            "upload_time_iso_8601": "2020-02-14T10:16:11.756394Z",
            "size": 609083
            }
        self.assertDictContainsSubset(expected_release_file1, actual_release_file1)

        actual_release_file2 = actual_release[1]
        expected_release_file2 = {
            "has_sig": False,
            "upload_time": "2020-02-14T10:16:14",
            "comment_text": "robotframework",
            "python_version": "source",
            "url": "https://files.pythonhosted.org/packages/9d/81/56b08ea5d142c103abac02d9cddfed6119eceb9134a0a6b00284d4373c69/robotframework-3.2b2.zip",
            "md5_digest": "6290cd1217df095fe8b3dd1bf6024524",
            "requires_python": None,
            "filename": "robotframework-3.2b2.zip",
            "packagetype": "sdist",
            "upload_time_iso_8601": "2020-02-14T10:16:14.640963Z",
            "size": 642901
            }
        self.assertDictContainsSubset(expected_release_file2, actual_release_file2)

        actual_release = result['3.2rc1']
        self.assertEqual(2, len(actual_release))

        actual_release_file1 = actual_release[0]
        expected_release_file1 = {
            "has_sig": True,
            "upload_time": "2020-04-03T18:49:29",
            "comment_text": "robotframework",
            "python_version": "py2.py3",
            "url": "https://files.pythonhosted.org/packages/41/a4/fb508058d72b07b5264e175e3f1943b45ec2ccdfc66a672d121b3cf64542/robotframework-3.2rc1-py2.py3-none-any.whl",
            "md5_digest": "58780c0b23b6aedaf10a12b03d14221a",
            "requires_python": ">=2.7",
            "filename": "robotframework-3.2rc1-py2.py3-none-any.whl",
            "packagetype": "bdist_wheel",
            "upload_time_iso_8601": "2020-04-03T18:49:29.892892Z",
            "size": 613098
            }
        self.assertDictContainsSubset(expected_release_file1, actual_release_file1)

        actual_release_file2 = actual_release[1]
        expected_release_file2 = {
            "has_sig": True,
            "upload_time": "2020-04-03T18:49:33",
            "comment_text": "robotframework",
            "python_version": "source",
            "url": "https://files.pythonhosted.org/packages/02/dc/773ca3480977596f4ae43b98a539cbbc85a0c14745cfada1bd866345be1a/robotframework-3.2rc1.zip",
            "md5_digest": "6bbadd96485e3eb81c80c0f388529535",
            "requires_python": None,
            "filename": "robotframework-3.2rc1.zip",
            "packagetype": "sdist",
            "upload_time_iso_8601": "2020-04-03T18:49:33.705752Z",
            "size": 647126
            }
        self.assertDictContainsSubset(expected_release_file2, actual_release_file2)
