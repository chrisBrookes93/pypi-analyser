from collections import OrderedDict
from datetime import datetime
from distutils.version import LooseVersion
import logging
import re
import threading
from pypianalyser.pypi_sqlite_helper import PyPiAnalyserSqliteHelper
from pypianalyser.pypi_index_helpers import get_package_list, get_metadata_for_package
from pypianalyser.exceptions import Exception404
from pypianalyser.utils import append_line_to_file, read_file_lines_into_list, order_release_names_fallback, \
    split_list_into_chunks

logger = logging.getLogger(__file__)


class PyPiMetadataRetriever:

    def __init__(self, trunc_description=-1, trunc_releases=-1, thread_count=1, db_path='pypi.sqlite', max_packages=-1,
                 package_regex=None, file_404='404.txt', verbose=False):
        """
        Constructor for PyPiMetadataRetriever

        :param trunc_description: Number of characters to truncate the description field to, to reduce the size of the
         database
        :type trunc_description: int
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
        self.truncate_description = trunc_description
        self.truncate_releases = trunc_releases
        self.thread_count = thread_count
        self.db_path = db_path
        self.max_packages = max_packages
        self.package_regex = package_regex
        self.file_path_404 = file_404
        self.verbose = verbose
        self.package_list = None
        self._threads = []
        self._progress_counter_lock = threading.Lock()
        self._404_file_lock = threading.Lock()
        self._progress_counter = 0
        self._start_time = 0
        self._shutdown = False

        self._db_helper = None
        # Set the logging
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    def __del__(self):
        if self._db_helper:
            self._db_helper.close()

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
        self._open_db()
        try:
            # Obtain the list from PyPi
            pypi_set = set(get_package_list())
            logger.info('Obtained a list of {} packages from the mirror'.format(len(pypi_set)))

            if self.package_regex:
                regex = re.compile(self.package_regex)
                pypi_set = set(filter(regex.search, pypi_set))
                logger.info('Applied regex {}, reduced list to {}'.format(self.package_regex, len(pypi_set)))

            # Remove packages that returned 404.txt on the previous run
            failed_links = set(read_file_lines_into_list(self.file_path_404))
            if failed_links:
                pypi_set = pypi_set - failed_links
                logger.info('Found {} broken links to packaged in {}, removing these from the list. List size is now {}'
                             .format(len(failed_links), self.file_path_404, len(pypi_set)))

            # Remove the package already present in the DB
            already_in_db = set(self._db_helper.get_package_names())
            if already_in_db:
                pypi_set = pypi_set - already_in_db
                logger.info('Found {} packages already in the DB, removing these from the list. List size is now {}'
                            .format(len(already_in_db), len(pypi_set)))

            pypi_set = sorted(list(pypi_set))
            if self.max_packages and len(pypi_set) > self.max_packages:
                logger.info('Reducing size of the package list down to {}'.format(self.max_packages))
                pypi_set = pypi_set[:self.max_packages]

            self.package_list = pypi_set
            return self.package_list
        finally:
            self._close_db()

    def run(self):
        """
        Run the metadata downloader
        """
        try:
            if self.package_list is None:
                self.calculate_package_list()
            if not self.package_list:
                logger.warn('0 packages matched the input filter')
                return
            self._open_db()
            self._start_time = datetime.now()

            # Optimisation - little point in multi-threading if there's a small number of packages
            if len(self.package_list) < 100:
                logger.debug('Small number of packages to process, reducing down to 1 thread')
                self._threaded_process(self.package_list)
            else:
                chunks = split_list_into_chunks(self.package_list, self.thread_count)

                for i in range(self.thread_count):
                    t = threading.Thread(target=self._threaded_process, args=(chunks[i],))
                    self._threads.append(t)
                    t.start()

                # Wait for the threads. We use a while loop and .join(100) so that we can still react catch
                # KeyboardInterrupt. Once a thread has finished it is popped from the list until there are
                # none left at which point the program closes.
                while self._threads:
                    ind0_thread = self._threads[0]
                    ind0_thread.join(100)
                    if not ind0_thread.isAlive():
                        self._threads.pop(0)
                time_diff = datetime.now() - self._start_time
                logger.info('Runtime: {}, finished processing all packages'.format(time_diff))
        except KeyboardInterrupt:
            # Inform the threads of the shutdown
            self._shutdown = True
            logger.info('Caught a KeyboardInterrupt event, waiting for threads to shutdown...')
            # Wait for the threads to finish what they're doing so that the we don't get partial data in the DB for a
            # package
            for t in self._threads:
                t.join()
        finally:
            self._close_db()

    def _close_db(self):
        """
        Close the database if its open
        """
        if self._db_helper:
            self._db_helper.close()
            self._db_helper = None

    def _open_db(self):
        """
        Open the database
        """
        if not self._db_helper:
            self._db_helper = PyPiAnalyserSqliteHelper(self.db_path)

    def _threaded_process(self, package_list):
        """
        Threaded function that downloads package metadata from PyPi

        :param package_list: List of packages to obtain metadata for
        :type package_list: list
        """
        logger.debug('Thread {} started'.format(threading.current_thread().ident))
        i = 0
        # Calculate a sensible period to update a locked counter based on the size of the package list. This ensures we
        # don't do an operation that requires obtaining a lock too often.
        update_period = int(min(1000, max(len(package_list) / 10, 1)))

        for package in package_list:
            if self._shutdown:
                break
            try:
                logger.debug('Processing: {}'.format(package))
                metadata = get_metadata_for_package(package)
                if self.truncate_description >= 0:
                    self._truncate_description(metadata)

                if self.truncate_releases >= 0:
                    self._truncate_releases(metadata)

                self._db_helper.commit_package_to_db(metadata)
            except Exception404 as e:
                # HTTP 404 exceptions are common if the package is no longer on PyPi. We save these to a file so that
                # we don't bother connecting to them on future runs
                self._report_404(package)
                logger.warn(e)
            except Exception as e:
                logger.error(e)
            i += 1
            # Update the global progress counter
            if i % update_period == 0:
                self._update_progress(update_period)
        logger.debug('Thread {} finished'.format(threading.current_thread().ident))

    def _truncate_description(self, metadata):
        """
        Truncates the description and summary fields in the metadata dict to a specified length

        :param metadata: Metadata containing the description
        :type metadata: dict
        """
        description = metadata['info']['description']
        if description:
            metadata['info']['description'] = description[:self.truncate_description]

        summary = metadata['info']['summary']
        if summary:
            metadata['info']['summary'] = summary[:self.truncate_description]

    def _truncate_releases(self, metadata):
        """
        Truncates the releases in the metadata dict after ordering them

        :param metadata: Metadata containing the releases
        :type metadata: dict
        """
        releases = metadata['releases'] or {}

        # In Py3 by default we can't rely on the order of the release dictionary so order the releases using an
        # OrderedDict
        try:
            ordered_releases_names = sorted(list(releases.keys()), key=LooseVersion, reverse=True)
        except TypeError:
            # Handle a Py3 issue when trying to compare two versions where one contains a string
            # (https://bugs.python.org/issue14894). Instead sort by upload time of the first file of each release
            ordered_releases_names = order_release_names_fallback(releases)

        ordered_releases = OrderedDict()
        for release_name in ordered_releases_names[:self.truncate_releases]:
            ordered_releases[release_name] = releases[release_name]
        metadata['releases'] = ordered_releases

    def _report_404(self, package_name):
        """
        Adds the package name to the 404 file in a thread safe way

        :param package_name: Name of the package to add
        :type package_name: str
        """
        with self._404_file_lock:
            append_line_to_file(self.file_path_404, package_name)

    def _update_progress(self, number_to_add):
        """
        Update the progress counter in a thread safe way and log out the progress

        :param number_to_add: Number of packages processed by the calling thread since the last invocation
        :type number_to_add: int
        """
        if self._start_time:
            with self._progress_counter_lock:
                self._progress_counter += number_to_add
            time_diff = datetime.now() - self._start_time
            logger.info('Runtime: {}, processed {}/{}'.format(time_diff, self._progress_counter, len(self.package_list)))
