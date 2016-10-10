#!/usr/bin/env python3.5

import os
import os.path
import re
from pprint import pprint
from teftel_docs.utils import merge_dicts
from itertools import chain

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


def qualify_type(typ, namespace):
    """
    >>> qualify_type('null', 'some.name.space')
    'null'

    >>> qualify_type('Role', 'some.name.space')
    'some.name.space.Role'

    >>> qualify_type('some.name.space.Role', 'some.name.space')
    'some.name.space.Role'
    """

    if not is_avro_primitive(typ) and '.' not in typ:
        return '{0}.{1}'.format(namespace, typ)
    else:
        return typ


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


MAX_ORIGIN_LEVEL = 10


def extract_origins(field_map, field):
    """
    returns list of field origins

    >>> extract_origins({'A': {}}, 'A')
    []

    >>> extract_origins({'A': {}}, 'B')
    Traceback (most recent call last):
      ...
    ValueError: Nonexistent field B

    >>> extract_origins({'A': {'origin': 'C'}}, 'A')
    Traceback (most recent call last):
      ...
    ValueError: Invalid origin reference 'C'

    >>> extract_origins({'A': {'origin': 'A'}}, 'A') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: Cyclic reference for field A and origin ['A', ...

    >>> extract_origins({'A': {}, 'B': {}}, 'A')
    []

    >>> extract_origins({'A': {'origin': 'B'}, 'B': {}}, 'A')
    ['B']

    >>> extract_origins({'A': {'origin': 'B'}, 'B': {'origin': 'C'}, 'C':{}}, 'A')
    ['B', 'C']

    >>> extract_origins({'A': {'origin': 'B'}, 'B': {'origin': 'C'}, 'C':{'origin': 'A'}}, 'A') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: Cyclic reference for field A and origin ['B', 'C', 'A', ...

    """
    field_dict = field_map.get(field)

    if field_dict is None:
        raise ValueError('Nonexistent field {0}'.format(field))

    def fn(f, trace):
        origin_key = f.get('origin')
        if origin_key is None:
            return []

        origin_field = field_map.get(origin_key)
        if origin_field is None:
            raise ValueError('Invalid origin reference \'{0}\''.format(origin_key))

        if len(trace) > MAX_ORIGIN_LEVEL:
            raise ValueError('Cyclic reference for field {0} and origin {1}.'.format(field, trace))

        return [origin_key] + fn(origin_field, trace + [origin_key])

    return fn(field_dict, [])


def unlink(link):
    """
    Splits link of the form namespace.Type#field to it's parts.

    >>> unlink('com.toptal.platform.Role#user_id')
    ('com.toptal.platform', 'Role', 'user_id')
    >>> unlink('com.toptal.platform.Role')
    ('com.toptal.platform', 'Role', None)
    >>> unlink('platform.Role')
    ('platform', 'Role', None)
    """
    parts = link.split('#')
    prefix = parts[0]
    field = parts[1] if len(parts) > 1 else None

    parts = prefix.split('.')
    namespace = parts[0] if len(prefix) > 1 else None
    typ = parts[-1]

    return namespace, typ, field


def build_field(field_id, field_map):
    namespace, record, name = unlink(field_id)
    field = field_map[field_id]
    origins = extract_origins(field_map, field_id)
    origin_fields = {o: field_map[o] for o in origins}

    ret = merge_dicts(field, {
        'id': field_id,
        'name': name,
        'doc': field['doc'],
        'is_linkable': is_linkable(field['type']),
        'origin_fields': origin_fields
    })
    return ret


NO_DOC_STRING = 'documentation missing'


def simplify_protocol(protocol):
    namespace = protocol['namespace']

    def qualified_name(t):
        return '{0}.{1}'.format(t.get('namespace', namespace), t['name'])

    def sort_by_qualified_name(it):
        return sorted(it, key=lambda x: x['qualified_name'])

    local_types = [t for t in protocol['types'] if not t.get('namespace')]

    enums = sort_by_qualified_name(
        {
            'qualified_name': qualified_name(t),
            'doc': t.get('doc', NO_DOC_STRING),
            'symbols': sorted(t['symbols'])
        }
        for t in local_types if t['type'] == 'enum' and t['type'])

    def record_dict(x):
        bq_table = x.get('bq-table')
        qname = qualified_name(x)

        return {
            'bq_table': bq_table,
            'qualified_name': qname,
            'doc': x.get('doc', NO_DOC_STRING),
            'title': bq_table if bq_table is not None else qname,
            'fields': sorted(['{0}#{1}'.format(qname, f['name']) for f in x['fields']])}

    records = sort_by_qualified_name(record_dict(t) for t in local_types if t['type'] == 'record')

    return {
        'protocol': protocol['protocol'],
        'namespace': namespace,
        'doc': protocol.get('doc', NO_DOC_STRING),
        'enums': enums,
        'records': records,
        'tables': {t['bq_table']: t['qualified_name'] for t in records if t['bq_table']}
    }


def extract_fields(p):
    protocol_namespace = p.get('namespace')

    for t in p['types']:
        if t['type'] != 'record':
            continue
        namespace = t.get('namespace', protocol_namespace)
        type_name = t['name']
        for f in t.get('fields', []):
            field_name = f['name']
            field_key = '{0}.{1}#{2}'.format(namespace, type_name, field_name)
            field_type_dict = dictify_type(f['type'])
            field_type_dict.update({
                'doc': f.get('doc'),
                'type': qualify_type(field_type_dict['type'], namespace)
            })

            yield field_key, field_type_dict


def build_protocol_docs(protocol, field_map):

    # records
    for dct in protocol.get('records', []):
        file_name = os.path.join('records', dct['qualified_name'] + '.rst')
        fields = (build_field(f, field_map) for f in dct['fields'])
        yield file_name, TEMPLATE_TABLE.render(merge_dicts(dct, {'fields': fields}))

    # enums
    for dct in protocol.get('enums', []):
        file_name = os.path.join('enums', dct['qualified_name'] + '.rst')
        yield file_name, TEMPLATE_ENUM.render(dct)

    # protocol file
    file_name = os.path.join('{protocol}.rst'.format(**protocol))

    yield file_name, TEMPLATE_PROTOCOL.render(
        name=protocol['protocol'],
        namespace=protocol['namespace'],
        doc=protocol.get('doc'),
        tables=protocol['tables']
    )


def build_docs(protocols):
    field_map = dict(chain(*[extract_fields(p) for p in protocols]))

    for p in protocols:
        for filename, content in build_protocol_docs(simplify_protocol(p), field_map):
            yield filename, content
    yield 'index.rst', TEMPLATE_INDEX.render(protocols=[p['protocol'] for p in protocols])
