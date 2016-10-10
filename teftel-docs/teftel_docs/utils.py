import os
from pprint import pprint


def merge_dicts(*args):
    """
    >>> merge_dicts({})
    {}
    >>> pprint(merge_dicts({'a': 1, 'b': 2}, {'a': 2, 'c': 1}))
    {'a': 2, 'b': 2, 'c': 1}
    """
    ret = {}
    for d in args:
        ret.update(d)
    return ret


def create_file_path(file):
    path = os.path.dirname(file)
    if not os.path.exists(path):
        os.makedirs(path)
