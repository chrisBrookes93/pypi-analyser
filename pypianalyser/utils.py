from collections import OrderedDict
from datetime import datetime
from io import open
import os
import six
from six.moves import xrange

if six.PY3:
    unicode = str


def order_dict_by_key_name(unordered_dict):
    """
    Converts a dictionary into an ordered dictionary based on the key

    :param unordered_dict: Dictionary to order
    :type unordered_dict: dict

    :return: Input dictionary ordered
    :rtype: OrderedDict
    """
    sorted_keys = sorted(unordered_dict.keys())
    ret_val = OrderedDict()
    for key in sorted_keys:
        ret_val[key] = unordered_dict[key]

    return ret_val


def read_file_lines_into_list(file_path):
    """
    Read from a file, returning a list of lines. If the file does not exist then an empty list is returned

    :param file_path: Path to the file
    :type file_path: str

    :return: List of strings
    :rtype: list
    """
    ret_val = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as fp:
            ret_val = fp.readlines()
            ret_val = list(map(lambda x: x.strip(), ret_val))
    return ret_val


def write_list_lines_into_file(file_path, lines, file_mode='w'):
    """
    Write a list of strings to a file, each one on their own line.

    :param file_path: Path to the file
    :type file_path: str
    :param lines: List of values to write
    :type lines: list
    :param file_mode: Mode to open the file
    :type: str
    """
    with open(file_path, file_mode, encoding='utf-8') as fp:
        file_data = unicode('\r'.join(lines))
        fp.write(file_data)


def append_line_to_file(file_path, line_data):
    """
    Appends a line to the end of a file

    :param file_path: Path to the file
    :type file_path: str
    :param line_data: Line to add
    :type line_data: str
    """
    line_data += '\r'
    write_list_lines_into_file(file_path, [line_data], file_mode='a')


def remove_unknown_keys_from_dict(dict_to_process, known_keys):
    """
    Removes all key entries from dict_to_process if they are not present in known_keys

    :param dict_to_process: Dictionary to process
    :type dict_to_process: dict
    :param known_keys: Keys that are allowed in the dictionary
    :type known_keys: list
    """
    unknown_keys = set(dict_to_process.keys()) - set(known_keys)
    for key in unknown_keys:
        del dict_to_process[key]


def normalize_package_name(package_name):
    """
    Normalizes a package name by lowercasing and changing underscores to hyphens

    :param package_name: Name of the package
    :type package_name: str

    :return: Normalized package name
    :rtype: str
    """
    return package_name.lower().replace('_', '-')


def order_release_names_fallback(release_dict):
    """
    In Python3 if you compare two versions using LooseVersion where one has a string in, e.g.
    LooseVersion('0.1dev') < LooseVersion('0.1.0')
    an error is thrown because its trying to compare a string to an int. This is a fallback that orders versions by the
    upload date of the first file in each release

    :param release_dict: Releases to order keys for
    :type release_dict: dict

    :return: Ordered list of keys, with releases with no files removed
    :rtype: list
    """
    release_keys = list(release_dict.keys())
    # Begin by removing any releases that do no have any files
    release_keys = [x for x in release_keys if release_dict[x]]

    # Now order based on upload date of the first file in the release
    ordered_releases_names = sorted(
        release_keys,
        key=lambda x: datetime.strptime(release_dict[x][0]['upload_time'], '%Y-%m-%dT%H:%M:%S'),
        reverse=True)

    return ordered_releases_names


def split_list_into_chunks(full_list, chunk_count):
    """
    Splits a list into X chunks. If the number is not exactly divisible, the remainder is added to the last chunk

    :param full_list: List to split
    :type full_list: list
    :param chunk_count: Number of chunks to split into
    :type chunk_count: int

    :return: List with chunk_count elements
    :rtype: list
    """
    chunk_size = int(len(full_list) / chunk_count)
    chunks = [full_list[x:x + chunk_size] for x in xrange(0, len(full_list), chunk_size)]
    # If the size isn't exactly divisible there will be an extra chunk, append this onto the second last one
    if len(chunks) > chunk_count:
        extra_chunk = chunks[-1]
        chunks = chunks[:-1]
        chunks[-1].extend(extra_chunk)
    return chunks
