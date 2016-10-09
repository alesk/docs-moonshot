#!/usr/bin/env python3.5

import argparse
import glob
import json
import os
from pprint import pprint

from teftel_docs.schema import build_docs, dictify_type, extract_origin
from teftel_docs.utils import create_file_path

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generates schema docs from avro protocol files')
    parser.add_argument('-p', '--protocol-path', required=True,
                        help='Path to folder containing AVPR files')
    parser.add_argument('-o', '--output-path', required=True,
                        help='Output path')

    return parser.parse_args()


def main2():
    args = parse_arguments()
    protocol_files = glob.glob(os.path.join(args.protocol_path, '*.avpr'))
    protocols = [json.load(open(filename, 'r')) for filename in protocol_files]

    protocols_map = dict((p['namespace'], p) for p in protocols)
    for file_name, content in build_docs(protocols_map):
        file_path = os.path.join(args.output_path, file_name)
        create_file_path(file_path)
        with open(file_path, 'w') as fw:
            fw.write(content)

def print_protocol_content(p):
    print('# protocol: {0}.{1}'.format(p['namespace'], p['protocol']))
    print('## types')
    protocol_namespace = p.get('namespace')

    for t in p['types']:
        namespace = t.get('namespace', protocol_namespace)
        type_name = t['name']
        print("  {0}.{1}".format(namespace, type_name))
        for f in t.get('fields', []):
            field_name = f['name']
            field_key = "{0}.{1}#{2}".format(namespace, type_name, field_name)
            field_type_dict = dictify_type(f['type'])
            field_type_dict.update({'doc': f.get('doc')})
            print('    {0}: {1}'.format(field_key, field_type_dict))

def extract_fields(p):
    protocol_namespace = p.get('namespace')

    for t in p['types']:
        if t['type'] != 'record': continue
        namespace = t.get('namespace', protocol_namespace)
        type_name = t['name']
        for f in t.get('fields', []):
            field_name = f['name']
            field_key = "{0}.{1}#{2}".format(namespace, type_name, field_name)
            field_type_dict = dictify_type(f['type'])
            field_type_dict.update({'doc': f.get('doc')})
            yield field_key, field_type_dict


def main():
    args = parse_arguments()
    protocol_files = glob.glob(os.path.join(args.protocol_path, '*.avpr'))
    protocols = [json.load(open(filename, 'r')) for filename in protocol_files]

    print(os.getcwd())
    for p in protocols:
        #print_protocol_content(p)
        field_map = dict(extract_fields(p))
        #pprint(field_map)
        for key in field_map.keys():
            pprint('{0}: {1}'.format(key, extract_origin(field_map, key)))


if __name__ == '__main__':
    main()
