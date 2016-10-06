DOCUMENTATION_MISSING = 'TODO: Documentation missing'

def normalize_protocol(protocol_map):

    name = protocol_map['protocol']
    namespace = protocol_map['namespace']
    doc = protocol_map.get('doc', DOCUMENTATION_MISSING)

    types = ( normalize_type(typ, namespace) for typ in protocol_map['types'])

    yield {
        'name': name,
        'namespace': namespace,
        'doc': doc,
        'types': [ for typ in types]
    }

def normalize_type(typ, namespace):

    kind = typ['type']
    if kind == 'record':
        yield normalize_record(typ, namespace)
    elif kind == 'enum':
        yield normaliye_enum(typ, namespace)
    else:
        raise RuntimeError('Unkwnown type kind {0}'.format(kind))

def normalize_enum