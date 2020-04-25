from collections import OrderedDict
from io import open
import os


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


def write_list_lines_into_file(file_path, lines):
    """
    Write a list of strings to a file, each one on their own line. OS specific line separator is used

    :param file_path: Path to the file
    :type file_path: str
    :param lines: List of values to write
    :type lines: list
    """
    with open(file_path, 'w', encoding='utf-8') as fp:
        file_data = os.linesep.join(lines)
        fp.writelines(file_data)
