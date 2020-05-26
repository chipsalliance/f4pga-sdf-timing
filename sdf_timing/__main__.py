#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (C) 2020  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import argparse
import json
from .sdfparse import emit
from .sdfparse import parse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--emit', action='store_const', const=True,
                        help='When set SDF file will be generated from JSON.')
    parser.add_argument('--sdf', type=str, help='Path to SDF file')
    parser.add_argument('--json', type=str, help='Path to JSON file')

    args = parser.parse_args()

    if args.emit:
        with open(args.json, 'r') as fp:
            input = json.loads(fp.read())
            timings = emit(input)
            open(args.sdf, 'w').write(timings)
    else:
        with open(args.sdf, 'r') as fp:
            timings = parse(fp.read())

        with open(args.json, 'w') as fp:
            json.dump(timings, fp, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
