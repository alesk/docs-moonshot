import os
import re
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


def indent_avro_doc(text, indent):
    """
    Avro comments usually get stripped so the 2nd row is indented, thus
    rendering as rst definition. To prevent this, the same indent is added to the 1st line.

    >>> indent_avro_doc('Some text\\n  2nd indented line\\n  3rd indented line', 2)
    '  Some text\\n  2nd indented line\\n  3rd indented line'

    """
    lines = text.split('\n')

    def lindent(s): return len(s) - len(s.lstrip())

    if len(lines) == 1:
        return ' ' * indent + text

    indents = list(map(lindent, lines[1:]))
    min_indent = min(filter(lambda x: x > 0, indents))
    fixed_indents = list(map(lambda x: indent + x - min_indent, indents))
    indented_lines = map(lambda s, ind: ' ' * ind + s.lstrip(), lines, [indent] + fixed_indents)
    return '\n'.join(indented_lines)


def slug(text):
    """
    >>> slug("com.toptal.platform.Role#user_id")
    'com-toptal-platform-role-user_id'
    """
    return re.sub('[^a-z0-9_]+', '-', text.strip().lower())
