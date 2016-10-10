#!/usr/bin/env python3.5

import argparse
import glob
import json
import os

from teftel_docs.avrodoc import build_docs
from teftel_docs.utils import create_file_path


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generates schema docs from avro protocol files')
    parser.add_argument('-p', '--protocol-path', required=True,
                        help='Path to folder containing AVPR files')
    parser.add_argument('-o', '--output-path', required=True,
                        help='Output path')

    return parser.parse_args()


def main():
    args = parse_arguments()
    protocol_files = glob.glob(os.path.join(args.protocol_path, '*.avpr'))
    protocols = [json.load(open(filename, 'r')) for filename in protocol_files]

    for filename, content in build_docs(protocols):
        filename_abs = os.path.join(args.output_path, filename)
        create_file_path(filename_abs)
        with open(filename_abs, 'w') as fw:
            fw.write(content)


if __name__ == '__main__':
    main()
