import sqlite3
from sqlite_db_schema_queries import CREATE_TABLE_SQL_QUERIES, INSERT_PACKAGE_SQL, INSERT_CLASSIFIER_STRING_SQL, \
    INSERT_PACKAGE_CLASSIFIER_SQL, INSERT_PACKAGE_RELEASES_SQL, SELECT_ID_FOR_CLASSIFIER_STRING_SQL, \
    SELECT_CLASSIFIERS_FOR_PACKAGE_SQL, SELECT_RELEASE_FILES_FOR_PACKAGE_SQL, SELECT_PACKAGE_BY_NAME_SQL
from utils import order_dict_by_key_name
from sqlite3worker import Sqlite3Worker


class SQLiteHelper(object):

    def __init__(self, db_path):
        self._db_path = db_path
        self.sql_worker = Sqlite3Worker(db_path)

    def __del__(self):
        self.close()

    def create_table(self, sql):
        self.sql_worker.execute(sql)
        # if not self.conn:
        #     raise Exception('Database not open')
        # cur = self.conn.cursor()
        # cur.execute(sql)

    # def commit(self):
    #     self.conn.commit()

    def close(self):
        if self.sql_worker:
            self.sql_worker.close()
            self.sql_worker = None

    # def open(self, db_path=None):
    #     if self.conn:
    #         raise Exception('Database already open!')
    #     if db_path:
    #         self._db_path = db_path
    #     self.conn = sqlite3.connect(db_path)


class PyPiAnalyserSqliteHelper(SQLiteHelper):

    def __init__(self, db_path='PyPi_index.sqlite'):
        SQLiteHelper.__init__(self, db_path)
        for table_sql in CREATE_TABLE_SQL_QUERIES:
            self.create_table(table_sql)
        self._classifier_ids_cache = {}

    def commit_package_to_db(self, package_metadata):
        package_id = self.add_package_info(package_metadata['info'])
        for release_name, release in package_metadata['releases'].items():
            self.add_release(package_id, release_name, release)
        #self.commit()

    def add_package_info(self, package_info):
        """
        Adds the main package metadata to the database

        :param package_info: Dictionary of metadata
        :type package_info: dict

        :return: Primary key ID of the entry added to the packages table
        :rtype int
        """
        # Do some data processing...
        # Classifiers will go into their own table so remove here
        classifiers = package_info.pop('classifiers')
        # For simplicity concat project urls and store in one field
        project_urls = package_info['project_urls'].items() if package_info['project_urls'] else []
        package_info['project_urls'] = u', '.join([u'{}: {}'.format(k, v) for k, v in project_urls])
        # downloads field is not used
        package_info.pop('downloads')

        requires_dist = package_info['requires_dist']
        if requires_dist:
            package_info['requires_dist'] = ', '.join(requires_dist)

        # Order the dictionary alphabetically by key name. We need to do this so that we get an ordered tuple
        ordered_package_info = order_dict_by_key_name(package_info)

        # Add to the database
        #cur = self.conn.cursor()
        self.sql_worker.execute(INSERT_PACKAGE_SQL, tuple(ordered_package_info.values()))
        #result = cur.execute()
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
            #cur = self.conn.cursor()
            self.sql_worker.execute(INSERT_PACKAGE_RELEASES_SQL, tuple(ordered_release_dict.values()))
            #cur.execute()

    def add_classifier(self, package_id, classifier):
        #cur = self.conn.cursor()

        if classifier in self._classifier_ids_cache:
            classifier_id = self._classifier_ids_cache[classifier]
        else:
            # Insert the classifier string if this is the first time we've come across it
            self.sql_worker.execute(INSERT_CLASSIFIER_STRING_SQL, (classifier,))
            #cur.execute(INSERT_CLASSIFIER_STRING_SQL, (classifier,))
            # Query for the ID
            classifier_id = self.get_classifier_id(classifier)
            self._classifier_ids_cache[classifier] = classifier_id

        # Now add an entry in the package_classifiers table that links the package to that classifier
        self.sql_worker.execute(INSERT_PACKAGE_CLASSIFIER_SQL, (classifier_id, package_id))

    def get_classifier_id(self, classifier_str):
        res = self.sql_worker.execute(SELECT_ID_FOR_CLASSIFIER_STRING_SQL, (classifier_str,))
        return res[0][0]

    def get_classifiers_for_package(self, package_name):
        #cur = self.conn.cursor()
        ret = self.sql_worker.execute(SELECT_CLASSIFIERS_FOR_PACKAGE_SQL, (package_name,))
        rows = ret

        return [x[0] for x in rows]

    # def get_releases_for_package(self, package_name):
    #     ret_val = {}
    #     #cur = self.conn.cursor()
    #     cur.execute(SELECT_RELEASE_FILES_FOR_PACKAGE_SQL, (package_name,))
    #     column_names = [x[0] for x in cur.description]
    #     rows = cur.fetchall()
    #
    #     for row in rows:
    #         row_dict = self._map_tuple_column_names(row, column_names)
    #         release_name = row_dict['version']
    #         if release_name not in ret_val:
    #             ret_val[release_name] = [row_dict]
    #         else:
    #             ret_val[release_name].append(row_dict)
    #     return ret_val

    # def _map_tuple_column_names(self, values, column_names):
    #     ret_val = {}
    #     for key, val in zip(column_names, values):
    #         ret_val[key] = val
    #
    #     return ret_val

    # def get_package_by_name(self, package_name):
    #     #cur = self.conn.cursor()
    #     rows = self.sql_worker.execute(SELECT_PACKAGE_BY_NAME_SQL, (package_name,))
    #     column_names = [x[0] for x in cur.description]
    #     row = cur.fetchone()
    #
    #     ret_val = self._map_tuple_column_names(row, column_names)
    #     return ret_val

    def get_package_names(self):
        rows = self.sql_worker.execute("SELECT name FROM packages")
        return [x[0] for x in rows]

    def get_package_id(self, package_name):
        rows = self.sql_worker.execute("SELECT id FROM packages WHERE name=?", (package_name,))
        row = rows[0]

        return row[0]