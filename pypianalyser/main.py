# Strip the description tag
# Prune the releases to a specific number
# Methodology
    # Parse                     "requires_python": ">=3.6, <4",
    # Parse classifiers - regex and print out the interesting ones (https://pypi.org/classifiers/)
    # Check the filename
    # If zip, install and run unit tests if there are any
# Include section about 'interesting elements of the PyPi API
    # unused downloads count
    # Includes libraries that have no files and are not publically searchable in the /simple list

# Other interesting observations:
    # Developers future-proofing: e.g. "requires_python": ">=3.6, <4",  (or does PyPi do this)

# Future Improvements
    # Analyse when Python3 compatibilty was first added
import sys
import logging
import threading
import os

from pypi_index_helpers import get_metadata_for_package, get_package_list
from sqlite_helpers import PyPiAnalyserSqliteHelper
from PyPi_Py3_Analyser.exceptions import Exception404

lock_404_file = threading.Lock()
lock_exception_file = threading.Lock()
shutdown = False


def get_404_list(path='404.txt'):
    ret_val = []
    if os.path.exists(path):
        with open(path, 'r') as fp:
            ret_val = fp.readlines()
            ret_val = map(lambda x: x.strip('\n'), ret_val)
    return ret_val


def append_to_404_packages(package_name):
    have_lock = False
    try:
        lock_404_file.acquire()
        have_lock = True
        with open('404.txt', 'a') as fp:
            fp.write(package_name + '\n')
    except Exception, e:
        print(e)
    finally:
        if have_lock:
            lock_404_file.release()


def append_to_exception_list(package_name, ex):
    have_lock = False
    try:
        lock_exception_file.acquire()
        have_lock = True
        with open('exceptions.txt', 'a') as fp:
            fp.write('{}: {}\n'.format(package_name, ex))
    except Exception, e:
        print(e)
    finally:
        if have_lock:
            lock_exception_file.release()


def process_package_list(package_list, db_helper):
    for package in package_list:
        try:
            print package
            metadata = get_metadata_for_package(package, truncate_description=100, truncate_releases=1)
            if metadata:
                db_helper.commit_package_to_db(metadata)
        except Exception404, e:
            append_to_404_packages(package)
            print e
        except Exception, e:
            append_to_exception_list(package, e)
            print e


logger = logging.getLogger(__file__)

DOMAIN = 'https://pypi.org'
HTTP_SUCCESS = 200
UNSET_VAL = -1

full_package_list = get_package_list()
db_helper = PyPiAnalyserSqliteHelper('test_pypi7.sqlite')

# Skip ones we've already done
package_list = set(full_package_list)
print('Full package list: ' + str(len(package_list)))
# Remove the packages that returned a 404 on a previous run
packages_returning_404 = get_404_list()
package_list = package_list - set(get_404_list())
print('List with 404 errors removed: {} ({} removed)'.format(len(package_list), len(packages_returning_404)))

# Remove the packages already present in the DB
existing_package_names = db_helper.get_package_names()
existing_package_names =  [x.lower() for x in existing_package_names]
package_list = package_list - set(existing_package_names)
print('List with packages already processed removed: {} ({} removed)'.format(len(package_list), len(existing_package_names)))

package_list = sorted(list(package_list))

threads = []
thread_count = 1
chunk_size = len(package_list) / thread_count

chunks = [package_list[x:x+chunk_size] for x in xrange(0, len(package_list), chunk_size)]


for i in range(thread_count):
    t = threading.Thread(target=process_package_list, args=(chunks[i], db_helper))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

db_helper.close()

# metadata = get_package_metadata('robotframework', truncate_description=200, truncate_releases=2)
# db_helper.commit_package_to_db(metadata)
# metadata = get_package_metadata('robotframework-remoterunner', truncate_description=200, truncate_releases=2)
# db_helper.commit_package_to_db(metadata)
