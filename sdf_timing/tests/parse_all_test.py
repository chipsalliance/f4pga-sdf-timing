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


import os
import os.path


from sdf_timing import sdfparse


__path__ = os.path.dirname(__file__)

datafiles_path = os.path.join(__path__, 'data')
goldenfiles_path = os.path.join(__path__, 'data', 'golden')
parsed_sdfs = list()
generated_sdfs = list()


def test_parse():
    files = sorted(os.listdir(datafiles_path))
    for f in files:
        if f.endswith('.sdf'):
            with open(os.path.join(datafiles_path, f)) as sdffile:
                parsed_sdfs.append(sdfparse.parse(sdffile.read()))


def test_emit():
    for s in parsed_sdfs:
        generated_sdfs.append(sdfparse.emit(s))


def test_output_stability():
    """ Checks if the generated SDF are identical with golden files"""

    parsed_sdfs_check = list()
    # read the golden files
    files = sorted(os.listdir(goldenfiles_path))
    for f in sorted(files):
        if f.endswith('.sdf'):
            with open(os.path.join(goldenfiles_path, f)) as sdffile:
                parsed_sdfs_check.append(sdffile.read())

    for s0, s1 in zip(parsed_sdfs, parsed_sdfs_check):
        sdf0 = sdfparse.emit(s0)
        assert sdf0 == s1


def test_parse_generated():
    for s in generated_sdfs:
        sdfparse.parse(s)
