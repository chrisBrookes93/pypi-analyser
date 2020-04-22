from collections import OrderedDict


def order_dict_by_key_name(unordered_dict):
    sorted_keys = sorted(unordered_dict.keys())
    ret_val = OrderedDict()
    for key in sorted_keys:
        ret_val[key] = unordered_dict[key]

    return ret_val
