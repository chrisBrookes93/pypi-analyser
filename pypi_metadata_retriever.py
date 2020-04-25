import logging
import os
import re
import threading
import time
from sqlite_helpers import PyPiAnalyserSqliteHelper
from pypi_index_helpers import get_package_list, get_metadata_for_package
from exceptions import Exception404

logger = logging.getLogger(__file__)


class PyPiMetadataRetriever:

    def __init__(self, trunc_descriptions, trunc_releases, thread_count, db_path, max_packages, package_regex, file_404,
                 verbose=False):
        """
        Constructor for PyPiMetadataRetriever

        :param trunc_descriptions: Number of characters to truncate the description field to, to reduce the size of the
         database
        :type trunc_descriptions: int
        :param trunc_releases: Number of releases to process for each package,
        :type trunc_releases: int
        :param thread_count: Number of threads to run to download the metadata
        :type thread_count: int
        :param db_path: Path to the DB file. If this does not exist it will be created
        :type db_path: str
        :param max_packages: Maximum number of packages to download metadata for
        :type max_packages: int or None
        :param package_regex: Regex to match package names against
        :type package_regex: str or None
        :param file_404: Path to the file to store the package names that returned a HTTP 404
        :type file_404: str
        :param verbose: Enable verbose logging
        :type verbose: bool
        """
        self.truncate_description = trunc_descriptions,
        self.truncate_releases = trunc_releases,
        self.thread_count = thread_count
        self.db_path = db_path
        self.max_packages = max_packages
        self.package_regex = package_regex
        self.file_path_404 = file_404
        self.verbose = verbose
        self.package_list = None
        self._threads = []
        self._progress_counter_lock = threading.Lock()
        self._progress_counter = 0
        self._start_time = 0

        # Initialize the connection to the DB
        self._db_helper = PyPiAnalyserSqliteHelper(db_path)
        # Set the logging
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    def calculate_package_list(self):
        """
        Calculates the package list to be processed.
        This is the list downloaded from PyPi with the following values removed:
        - Packages already in the database
        - Packages that have previously returned a HTTP 404 on a previous run (recorded in the 404 file0
        - Packages that do not match the package name regex (if supplied)
        The list is finally reduced to max_packages (if supplied)

        :return: List of packages that match the input specifications
        :rtype: list
        """
        # Obtain the list from PyPi
        pypi_set = set(get_package_list())
        logger.debug('Obtained a list of {} packages from the mirror'.format(len(pypi_set)))
        # Remove the package already present in the DB
        already_in_db = set(self._db_helper.get_package_names())
        if already_in_db:
            pypi_set = pypi_set - already_in_db
            logger.debug('Found {} packages already in the DB, removing these from the list. List size is now {}'
                         .format(len(already_in_db), len(pypi_set)))
        # Remove packages that returned 404.txt on the previous run
        failed_links = set(self.get_404_list())
        if failed_links:
            pypi_set = pypi_set - failed_links
            logger.debug('Found {} broken links to packaged in {}, removing these from the list. List size is now {}'
                         .format(len(already_in_db), self.file_path_404, len(pypi_set)))

        if self.package_regex:
            regex = re.compile(self.package_regex)
            pypi_set = set(filter(regex.search, pypi_set))
            logger.debug('Applied regex {}, reduced list to {}'.format(self.package_regex, len(pypi_set)))

        if len(pypi_set) > self.max_packages:
            logger.debug('Reducing size of the package list down to {}'.format(self.max_packages))
            pypi_set = sorted(list(pypi_set))[:self.max_packages]

        self.package_list = pypi_set
        return self.package_list

    def get_404_list(self):
        ret_val = []
        if os.path.exists(self.file_path_404):
            pass
        # TODO implement, should this go into a utils file?
        return ret_val

    def run(self):
        if self.package_list is None:
            self.calculate_package_list()
        self._start_time = time.time()

        # Optimisation - little point in multi-threading if there's a small number of packages
        if len(self.package_list) < 100:
            logger.debug('Small number of packages to process, reducing down to 1 thread')
            self._threaded_process(self.package_list, True)
        else:
            chunk_size = len(self.package_list) / self.thread_count
            chunks = [self.package_list[x:x + chunk_size] for x in xrange(0, len(self.package_list), chunk_size)]

            for i in range(self.thread_count):
                t = threading.Thread(target=self._threaded_process, args=(chunks[i], (i == 0)))
                self._threads.append(t)
                t.start()

            for t in self._threads:
                t.join()

    def _threaded_process(self, package_list):
        i = 0
        # Calculate a sensible period to update a locked counter based on the size of the package list. This ensures we
        # don't do an operation that requires obtaining a lock too often.
        update_period = min(5000, len(package_list) / 10)

        for package in package_list:
            try:
                logger.info('Processing: {}'.format(package))
                metadata = get_metadata_for_package(package, self.truncate_description, self.truncate_releases)
                if metadata:
                    self._db_helper.commit_package_to_db(metadata)
            except Exception404, e:
                # HTTP 404 exceptions are common if the package is no longer on PyPi. We save these to a file so that
                # we don't bother connecting to them on future runs
                append_to_404_packages(package)
                logger.warn(e)
            except Exception, e:
                logger.error(e)
            i += 1
            # Update the global progress counter
            if i % update_period == 0:
                self._update_progress(update_period)

    def _update_progress(self, number_to_add):
        """
        Update the progress counter in a thread safe way and log out the progress

        :param number_to_add: Number of packages processed by the calling thread since the last invocation
        :type number_to_add: int
        """
        with self._progress_counter_lock:
            self._progress_counter += number_to_add
        elapsed_time = self._start_time = time.time()
        str_time = time.strftime('%H:%M:%S', elapsed_time)
        logger.info('Runtime: {}, processed {}/{}'.format(str_time, self._progress_counter, len(self.package_list)))
