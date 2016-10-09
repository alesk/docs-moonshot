#!/usr/bin/env python3.5

import os
import os.path
import re
from pprint import pprint
from teftel_docs.utils import merge_dicts, create_file_path

from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
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
    """
    Translates various type definitions to dict with fields:
    is_array, is_avro_primitive, origin, nullable and type.

    >>> pprint(dictify_type('null'))
    {'is_array': False,
     'is_avro_primitive': True,
     'nullable': True,
     'origin': None,
     'type': 'null'}

    >>> pprint(dictify_type('int'))
    {'is_array': False,
     'is_avro_primitive': True,
     'nullable': False,
     'origin': None,
     'type': 'int'}

    >>> pprint(dictify_type(['int', 'null']))
    {'is_array': False,
     'is_avro_primitive': True,
     'nullable': True,
     'origin': None,
     'type': 'int'}

    >>> pprint(dictify_type({'type': 'com.toptal.etl.Role'}))
    {'is_array': False,
     'is_avro_primitive': False,
     'nullable': False,
     'origin': None,
     'type': 'com.toptal.etl.Role'}

    >>> pprint(dictify_type(['null', {'type': 'com.toptal.etl.Role'}]))
    {'is_array': False,
     'is_avro_primitive': False,
     'nullable': True,
     'origin': None,
     'type': 'com.toptal.etl.Role'}

    >>> pprint(dictify_type({'type': 'array', 'items': 'com.toptal.etl.Role'}))
    {'is_array': True,
     'is_avro_primitive': False,
     'nullable': False,
     'origin': None,
     'type': 'com.toptal.etl.Role'}
    """
    if typ == 'null':
        return {
                'is_array': False,
                'type': 'null',
                'nullable': True,
                'origin': None,
                'is_avro_primitive': True
                }
    elif isinstance(typ, str):
        return {
                'is_array': False,
                'type': typ,
                'nullable': False,
                'origin': None,
                'is_avro_primitive': is_avro_primitive(typ)}
    elif isinstance(typ, dict):
        base_type = typ['type']
        if base_type == 'array':
            item_type = typ['items']
            return {
                'is_array': True,
                'type': item_type,
                'nullable': False,
                'origin': typ.get('origin'),
                'is_avro_primitive': is_avro_primitive(item_type)
            }
        else:
            return {
                'is_array': False,
                'type': base_type,
                'nullable': False,
                'origin': typ.get('origin'),
                'is_avro_primitive': is_avro_primitive(typ['type'])
            }

    elif isinstance(typ, list) and 'null' in typ:
        dict_typ = map(dictify_type, typ)
        return {
            **list(filter(lambda x: x['type'] != 'null', dict_typ))[0],
            **{'nullable': True, 'is_array': False}}
    else:
        raise RuntimeError('Unsupported type: {0}'.format(str(typ)))


# Regex for 'some.name.space.Type#field'
LINK = re.compile(
    '(?P<namespace>[a-z_\.]+)*\.(?P<type>[a-z0-9_]+)(#(?P<field>[a-z0-9_]+))*',
    re.IGNORECASE)


def unlink(link):
    """
    >>> unlink('com.toptal.platform.Role#user_id')
    ('com.toptal.platform', 'Role', 'user_id')
    >>> unlink('com.toptal.platform.Role')
    ('com.toptal.platform', 'Role', None)
    >>> unlink('platform.Role')
    ('platform', 'Role', None)
    """
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
    typ = find_type(protocols_map, '{0}.{1}'.format(namespace, type_name))
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
        field_id = '{0}.{1}#{2}'.format(namespace, type_name, field.get('name'))
        dict_type = dictify_type(field.get('type'))
        type_name = dict_type['type']
        qualified_type_name = type_name if '.' in type_name else '{0}.{1}'.format(namespace, type_name)
        origin = dict_type.get('origin')
        doc = field.get('doc')

        # link to origin
        if origin is not None:
            origin_field = find_field(protocols_map, origin)
            if origin_field is None:
                raise ValueError('Invalid origin reference in: {0}'.format(origin))
            origin_doc = origin_field.get('doc')
        else:
            origin_doc = None

        return {
            'id': field_id,
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
                fields = (
                    build_field(
                        record.get('namespace', protocol_namespace),
                        record.get('name'),
                        f)
                    for f in record.get('fields'))

                custom = {
                    'namespace': namespace,
                    'bq_table': bq_table,
                    'title': bq_table or qualified_name,
                    'qualified_name': qualified_name,
                    'fields': sorted(fields, key=lambda x: x['name'])}

                yield merge_dicst(record, custom)

            elif record['type'] == 'enum':
                custom = {
                    'namespace': namespace,
                    'qualified_name': qualified_name}
                yield merge_dicst(record, custom)


def build_docs(protocol_map):
    # tables and enums
    types = list(get_types(protocol_map))

    def is_record(x): return x.get('type') == 'record'
    def has_table(x): return x.get('bq_table') is not None
    def is_enum(x): return x.get('type') == 'enum'

    # records
    for dct in filter(is_record, types):
        file_name = os.path.join('records', '{namespace}.{name}.rst'.format(**dct))
        yield file_name, TEMPLATE_TABLE.render(dct)

    # enums
    for dct in filter(is_enum, types):
        file_name = os.path.join('enums', '{namespace}.{name}.rst'.format(**dct))
        yield file_name, TEMPLATE_ENUM.render(dct)

    # protocol file
    for protocol in protocol_map.values():
        namespace = protocol['namespace']
        file_name = os.path.join('{protocol}.rst'.format(**protocol))

        # use set to get rid of duplicates
        tables = set([(t['bq_table'], t['qualified_name'])
                      for t in filter(has_table, types) if t['namespace'] == namespace])

        yield file_name, TEMPLATE_PROTOCOL.render(
            name=protocol['protocol'],
            namespace=namespace,
            doc=protocol.get('doc'),
            tables=sorted(list(tables), key=lambda x: x[0]))

    # protocol index
    yield 'index.rst', TEMPLATE_INDEX.render(protocols=[p['protocol'] for p in protocol_map.values()])


