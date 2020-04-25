from collections import OrderedDict
from io import open

def order_dict_by_key_name(unordered_dict):
    sorted_keys = sorted(unordered_dict.keys())
    ret_val = OrderedDict()
    for key in sorted_keys:
        ret_val[key] = unordered_dict[key]

    return ret_val


def read_file_lines_into_list(file_path):
    ret_val = []
    with open(file_path, 'r', encoding='utf-8') as fp:
        ret_val = fp.readlines()
        ret_val = map(lambda x: x.strip(), ret_val)
    return list(ret_val)