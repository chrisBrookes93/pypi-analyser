from collections import OrderedDict
from datetime import datetime
from io import open
import os
import six

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
    Write a list of strings to a file, each one on their own line. OS specific line separator is used

    :param file_path: Path to the file
    :type file_path: str
    :param lines: List of values to write
    :type lines: list
    :param file_mode: Mode to open the file
    :type: str
    """
    with open(file_path, file_mode, encoding='utf-8') as fp:
        file_data = unicode(os.linesep.join(lines))
        fp.write(file_data)


def append_line_to_file(file_path, line_data):
    """
    Appends a line to the end of a file
    :param file_path: Path to the file
    :type file_path: str
    :param line_data: Line to add
    :type line_data: str
    """
    line_data += os.linesep
    write_list_lines_into_file(file_path, [line_data], file_mode='a')


def remove_unknown_keys_from_dict(dict_to_process, known_keys):
    unknown_keys = set(dict_to_process.keys()) - set(known_keys)
    for key in unknown_keys:
        del dict_to_process[key]


def normalize_package_name(package_name):
    return package_name.lower().replace('_', '-')


def order_release_names_fallback(release_dict):
    """
    
    :param release_dict:
    :return:
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
