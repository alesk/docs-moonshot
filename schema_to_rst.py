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
TEMPLATE_INDEX = env.get_template('index.rst')
TEMPLATE_PROTOCOL = env.get_template('protocol.rst')
TEMPLATE_TABLE = env.get_template('table.rst')
TEMPLATE_AVRO_FILE = env.get_template('avro-file.rst')
TEMPLATE_ENUM = env.get_template('enum.rst')


def is_avro_primitive(typ_name):
    return not (typ_name in AVRO_PRIMITIVE_TYPES)


def dictify_type(typ):
    if typ == 'null':
        return {'type': 'null',
                'nullable': True,
                'origin': None,
                'is_acro_primitive': True
                }
    if isinstance(typ, str):
        return {'type': typ,
                'nullable': False,
                'origin': None,
                'is_avro_primitive': is_avro_primitive(typ)}
    elif isinstance(typ, dict):
        return dict(**typ,
            nullable=False,
            is_avro_primitive=is_avro_primitive(typ['type']))
    elif isinstance(typ, list) and 'null' in typ:
        dict_typ = map(dictify_type, typ)
        return {
            **list(filter( lambda x: x['type'] != 'null', dict_typ))[0],
            **{'nullable': True}}
    else:
        raise RuntimeError("Unsupported type: {0}".format(typ))


LINK = re.compile(
    '(?P<namespace>[a-z_\.]+)*\.(?P<type>[a-z0-9_]+)(#(?P<field>[a-z0-9_]+))*',
    re.IGNORECASE)


def unlink(link):
    '''
    >>> unlink('com.toptal.platform.Role#user_id')
    ('com.toptal.platform', 'Role', 'user_id')
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
    for field in typ['fields']:
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


def get_tables(protocols_map):
    def build_field(namespace, type_name, field):
        name = field['name']
        id = '{0}.{1}#{2}'.format(namespace, type_name, field.get('name'))
        origin = field.get('origin')
        doc = field.get('doc')

        if doc is None and origin is not None:
            origin_field = find_field(protocols_map, origin)
            doc = origin_field.get('doc')


        ret = {
                'id': id,
                'name': name,
                'origin': origin,
                'usages': list(find_field_usages(protocols_map, id)),
                'type': dictify_type(field.get('type')),
                'doc': doc}

        return ret

    # for each table
    for protocol_namespace, protocol in protocols_map.items():
        for record in protocol.get('types'):
            bq_table = record.get('bq-table')
            if not bq_table:
                continue
            yield {
                'namespace': protocol_namespace,
                'bq_table': bq_table,
                'doc': record.get('doc'),
                'fields': [
                    build_field(
                        record.get('namespace', protocol_namespace),
                        record.get('name'),
                        f)
                    for f in record.get('fields')]
            }


def build_docs(protocol_map):

    for dct in get_tables(protocol_map):
        file_name = os.path.join('tables', '{0}.rst'.format(dct['bq_table']))
        yield file_name, TEMPLATE_TABLE.render(dct)


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
