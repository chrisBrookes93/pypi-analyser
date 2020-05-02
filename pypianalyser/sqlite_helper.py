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

    @staticmethod
    def map_data_to_column_names(row_tuples, column_names):
        """
        Maps a list of tuples (table rows) to column names to produde a list of dictionaries

        :param row_tuples: List of tuples
        :type row_tuples: list
        :param column_names: Names of the columns
        :type column_names: list

        :return: List of dicts
        :rtype: list
        """
        ret_val = []
        for row in row_tuples:
            ret_val.append(dict(zip(column_names, row)))
        return ret_val
