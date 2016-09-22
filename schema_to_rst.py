#!/usr/bin/env python3.5

import argparse
import glob
import json
import os
import os.path
import re
from pprint import pprint

from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '_templates', 'schema')),
    trim_blocks=True, lstrip_blocks=True)


def slug(text):
    """
    >>> slug("com.toptal.platform.Role#user_id")
    'com-toptal-platform-role-user_id'
    """
    return re.sub('[^a-z0-9_]+', '-', text.strip().lower())

env.filters['slug'] = slug


AVRO_PRIMITIVE_TYPES = {'null', 'int', 'long', 'float',
                        'double', 'bytes', 'string', 'boolean'}
TEMPLATE_TABLE = env.get_template('table.rst')
TEMPLATE_ENUM = env.get_template('enum.rst')
TEMPLATE_PROTOCOL = env.get_template('protocol.rst')
TEMPLATE_INDEX = env.get_template('index.rst')


def is_avro_primitive(typ_name):
    return typ_name in AVRO_PRIMITIVE_TYPES

def is_linkable(typ_name):
    datetime_type = typ_name.endswith('Timestamp') or typ_name.endswith('Date')
    avro_primitive = is_avro_primitive(typ_name)
    return not (datetime_type or avro_primitive)



def dictify_type(typ):
    if typ == 'null':
        return {'type': 'null',
                'nullable': True,
                'origin': None,
                'is_linkable': False,
                'is_acro_primitive': True
                }
    if isinstance(typ, str):
        return {'type': typ,
                'nullable': False,
                'origin': None,
                'is_linkable': is_linkable(typ),
                'is_avro_primitive': is_avro_primitive(typ)}
    elif isinstance(typ, dict):
        if typ['type'] == 'array':
            item_type = typ['items']
            custom = {
                'container': 'array',
                'origin': typ.get('origin'),
                'type': item_type,
                'nullable': False,
                'is_linkable': is_linkable(item_type),
                'is_avro_primitive': is_avro_primitive(item_type)
            }
            return _merge_dicts(typ, custom)
        else:
            custom = {
                'nullable': False,
                'origin': typ.get('origin'),
                'is_linkable': is_linkable(typ['type']),
                'is_avro_primitive': is_avro_primitive(typ['type'])
            }
            return _merge_dicts(typ, custom)

    elif isinstance(typ, list) and 'null' in typ:
        dict_typ = map(dictify_type, typ)
        return {
            **list(filter( lambda x: x['type'] != 'null', dict_typ))[0],
            **{'nullable': True}}
    else:
        raise RuntimeError("Unsupported type: {0}".format(typ))

# Regex for 'some.name.space.Type#field'
LINK = re.compile(
    '(?P<namespace>[a-z_\.]+)*\.(?P<type>[a-z0-9_]+)(#(?P<field>[a-z0-9_]+))*',
    re.IGNORECASE)


def unlink(link):
    '''
    >>> unlink('com.toptal.platform.Role#user_id')
    ('com.toptal.platform', 'Role', 'user_id')
    >>> unlink('com.toptal.platform.Role')
    ('com.toptal.platform', 'Role', None)
    >>> unlink('platform.Role')
    ('platform', 'Role', None)
    '''
    m = LINK.match(link)
    if m:
        parts = m.groupdict()
        return parts['namespace'], parts['type'], parts['field']
    else:
        raise ValueError('Invalid type name {0}'.format(link))


def find_type(protocol_map, type_name):
    namespace, type_name, _ = unlink(type_name)
    for typ in protocol_map[namespace]['types']:
        if typ['name'] == type_name:
            return typ


def find_field(protocols_map, name):
    namespace, type_name, field_name = unlink(name)
    typ = find_type(protocols_map, "{0}.{1}".format(namespace, type_name))
    for field in typ.get('fields', []):
        if field['name'] == field_name:
            return field


def find_field_usages(protocols_map, origin):
    for protocol in protocols_map.values():
        for typ in protocol['types']:
            for field in typ.get('fields', []):
                dct = dictify_type(field['type'])
                if dct.get('origin') == origin:
                    yield '{0}.{1}#{2}'.format(
                        protocol['namespace'], typ['name'], field['name'])

def get_types(protocols_map):
    def build_field(namespace, type_name, field):
        name = field['name']
        id = '{0}.{1}#{2}'.format(namespace, type_name, field.get('name'))
        dict_type = dictify_type(field.get('type'))
        type_name = dict_type['type']
        qualified_type_name = type_name if '.' in type_name else '{0}.{1}'.format(namespace, type_name)
        origin = dict_type.get('origin')
        doc = field.get('doc')

        # link to origin
        if origin is not None:
            origin_field = find_field(protocols_map, origin)
            origin_doc = origin_field.get('doc')
        else:
            origin_doc = None

        return {
                'id': id,
                'name': name,
                'origin': origin,
                'usages': list(find_field_usages(protocols_map, id)),
                'type': dict_type,
                'doc': doc,
                'is_linkable': dict_type['is_linkable'],
                'qualified_type_name': qualified_type_name,
                'origin_doc': origin_doc}

    # for each table
    for protocol_namespace, protocol in protocols_map.items():
        for record in protocol.get('types'):
            name = record['name']
            bq_table = record.get('bq-table')
            namespace = record.get('namespace', protocol_namespace)
            qualified_name = '{0}.{1}'.format(namespace, name)

            if record['type'] == 'record':
                custom = {
                    'namespace': namespace,
                    'bq_table': bq_table,
                    'title': bq_table or qualified_name,
                    'qualified_name': qualified_name,
                    'fields': [
                        build_field(
                            record.get('namespace', protocol_namespace),
                            record.get('name'),
                            f)
                        for f in record.get('fields')]}
                yield _merge_dicts(record, custom)

            elif record['type'] == 'enum':
                custom = {
                    'namespace': namespace,
                    'qualified_name': qualified_name}
                yield _merge_dicts(record, custom)


def build_docs(protocol_map):

    # tables and enums
    types = list(get_types(protocol_map))


    records = list(filter(lambda x: x.get('type')  == 'record' is not None, types))
    tables = list(filter(lambda x: x.get('bq_table') is not None, types))
    enums = list(filter(lambda x: x.get('type') == 'enum', types))

    # records
    for dct in records:
        file_name = os.path.join('tables', '{namespace}.{name}.rst'.format(**dct))
        yield file_name, TEMPLATE_TABLE.render(dct)

    # enums
    for dct in enums:
        file_name = os.path.join('enums', '{namespace}.{name}.rst'.format(**dct))
        yield file_name, TEMPLATE_ENUM.render(dct)

    # protocol file
    for protocol in protocol_map.values():
        namespace = protocol['namespace']
        file_name = os.path.join('{protocol}.rst'.format(**protocol))
        tables_ = dict([
            (t['bq_table'], t['qualified_name']) for t in tables if t['namespace'] == namespace])

        yield file_name, TEMPLATE_PROTOCOL.render(
            name=protocol['protocol'],
            namespace=namespace,
            doc=protocol['doc'],
            tables=tables_)


    # protocol index
    yield 'index.rst', TEMPLATE_INDEX.render(protocols= [ p['protocol'] for p in protocol_map.values()])


def _merge_dicts(*args):
    '''
    >>> _merge_dicts({})
    {}
    >>> pprint(_merge_dicts({'a': 1, 'b': 2}, {'a': 2, 'c': 1}))
    {'a': 2, 'b': 2, 'c': 1}
    '''
    ret = {}
    for d in args:
        ret.update(d)
    return ret

def _create_file_path(file):
    path = os.path.dirname(file)
    if not os.path.exists(path):
        os.makedirs(path)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generates schema docs from avro protocol files')
    parser.add_argument('--protocol-path', required=True,
                        help='Path to folder containing AVPR files')
    parser.add_argument('--output-path', required=True,
                        help='Output path')

    return parser.parse_args()


def main():
    args = parse_arguments()
    protocol_files = glob.glob(os.path.join(args.protocol_path, '*.avpr'))
    protocols = [json.load(open(filename, 'r')) for filename in protocol_files]

    protocols_map = {p['namespace']: p for p in protocols}
    for file_name, content in build_docs(protocols_map):
        file_path = os.path.join(args.output_path, file_name)
        _create_file_path(file_path)
        with open(file_path, 'w') as fw:
            fw.write(content)


if __name__ == '__main__':
    main()
