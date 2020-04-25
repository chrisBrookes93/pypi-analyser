from sql_queries import CREATE_TABLE_SQL_QUERIES, INSERT_PACKAGE_SQL, INSERT_CLASSIFIER_STRING_SQL, \
    INSERT_PACKAGE_CLASSIFIER_SQL, INSERT_PACKAGE_RELEASES_SQL, SELECT_ID_FOR_CLASSIFIER_STRING_SQL, \
    SELECT_CLASSIFIERS_FOR_PACKAGE_SQL
from utils import order_dict_by_key_name
from sqlite3worker import Sqlite3Worker


class SQLiteHelper(object):
    """
    Class to wrap a concurrent SQLite database
    """
    def __init__(self, db_path):
        """
        Constructor for SQLiteHelper

        :param db_path: Path to the database file
        :type db_path: str
        """
        self._db_path = db_path
        self.sql_worker = Sqlite3Worker(db_path)

    def __del__(self):
        """
        Ensure that the database file is closed
        """
        self.close()

    def close(self):
        """
        Closes the database file
        """
        if self.sql_worker:
            self.sql_worker.close()
            self.sql_worker = None


class PyPiAnalyserSqliteHelper(SQLiteHelper):

    def __init__(self, db_path):
        """
        Constructor for PyPiAnalyserSqliteHelper. Opens a handle to the database and created the table if they do not
        exist

        :param db_path: Path to the database file
        :type db_path: str
        """
        SQLiteHelper.__init__(self, db_path)
        for table_sql in CREATE_TABLE_SQL_QUERIES:
            self.sql_worker.execute(table_sql)

        # Cache of classifier strings to reduce database querying
        self._classifier_ids_cache = {}

    def commit_package_to_db(self, package_metadata):
        """
        Commit a dictionary (in the spec of what PyPi returns) into the database

        :param package_metadata: Metadata dictionary returned from PyPi's API
        :type package_metadata: dict
        """
        package_id = self.add_package_info(package_metadata['info'])
        for release_name, release in package_metadata['releases'].items():
            self.add_release(package_id, release_name, release)

    def add_package_info(self, package_info):
        """
        Adds the main package metadata to the database

        :param package_info: Dictionary of metadata
        :type package_info: dict

        :return: Primary key ID of the entry added to the packages table
        :rtype int
        """
        # Classifiers will go into their own table so remove here
        classifiers = package_info.pop('classifiers')
        # For simplicity concat project urls and store in one field
        project_urls = package_info['project_urls'].items() if package_info['project_urls'] else []
        package_info['project_urls'] = u', '.join([u'{}: {}'.format(k, v) for k, v in project_urls])

        # downloads field is not used, remove this
        package_info.pop('downloads')

        # Join this field for simplicity
        requires_dist = package_info['requires_dist']
        if requires_dist:
            package_info['requires_dist'] = ', '.join(requires_dist)

        # Order the dictionary alphabetically by key name. We need to do this so that we get an ordered tuple
        ordered_package_info = order_dict_by_key_name(package_info)

        # Add to the database
        self.sql_worker.execute(INSERT_PACKAGE_SQL, tuple(ordered_package_info.values()))
        package_id = self.get_package_id(package_info['name'])

        # Now process each classifier
        for classifier in classifiers:
            self.add_classifier(package_id, classifier)

        return package_id

    def add_release(self, package_id, release_name, release):
        # A release may have multiple files and therefore 'release' is a list. To simplify the DB, treat each one as a
        # release, they can be retrieved easily because they're have the same release version field.
        for release_file in release:
            # Drop the digests to save space
            release_file.pop('digests')
            # The 'downloads' field is unused so remove this as well
            release_file.pop('downloads')

            # Add in the package_id (foreign key for packages table)
            # Add in the release name (version string)
            release_file['package_id'] = package_id
            release_file['version'] = release_name

            ordered_release_dict = order_dict_by_key_name(release_file)
            self.sql_worker.execute(INSERT_PACKAGE_RELEASES_SQL, tuple(ordered_release_dict.values()))

    def add_classifier(self, package_id, classifier):
        if classifier in self._classifier_ids_cache:
            classifier_id = self._classifier_ids_cache[classifier]
        else:
            # Insert the classifier string if this is the first time we've come across it
            self.sql_worker.execute(INSERT_CLASSIFIER_STRING_SQL, (classifier,))
            # Query for the ID
            classifier_id = self.get_classifier_id(classifier)
            self._classifier_ids_cache[classifier] = classifier_id

        # Now add an entry in the package_classifiers table that links the package to that classifier
        self.sql_worker.execute(INSERT_PACKAGE_CLASSIFIER_SQL, (classifier_id, package_id))

    def get_classifier_id(self, classifier_str):
        """
        Queries for the ID of a classifier string

        :param classifier_str: Classifier string to query
        :type classifier_str: str

        :return: ID of the classifier
        :rtype: int
        """
        res = self.sql_worker.execute(SELECT_ID_FOR_CLASSIFIER_STRING_SQL, (classifier_str,))
        return res[0][0]

    def get_classifiers_for_package_name(self, package_name):
        """
        Returns a list of classifier strings to a given package name

        :param package_name: Name of the package
        :type package_name: str

        :return: List of classifier strings
        :rtype: list
        """
        ret = self.sql_worker.execute(SELECT_CLASSIFIERS_FOR_PACKAGE_SQL, (package_name,))
        rows = ret

        return [x[0] for x in rows]

    def get_package_names(self):
        """
        Returns the names of packages that are in the database

        :return: List of package names
        :rtype: list
        """
        rows = self.sql_worker.execute("SELECT name FROM packages")
        return [x[0] for x in rows]

    def get_package_id(self, package_name):
        """
        Query's the database and returns the ID for a given package name

        :param package_name: Name of the package to query
        :type package_name: str

        :return: Package ID
        :rtype: int
        """
        rows = self.sql_worker.execute("SELECT id FROM packages WHERE name=?", (package_name,))
        row = rows[0]

        return row[0]