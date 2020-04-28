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

from . import sdflex
from . import sdfyacc
from . import sdfwrite


def init():
    sdfyacc.timings = dict()

    sdfyacc.header = dict()
    sdfyacc.delays_list = list()
    sdfyacc.cells = dict()

    sdfyacc.tmp_delay_list = list()
    sdfyacc.tmp_equation = list()
    sdfyacc.tmp_constr_list = list()

    sdflex.lexer.lineno = 1


def emit(input, timescale='1ps'):
    return sdfwrite.emit_sdf(input, timescale)


def parse(input):
    init()
    sdflex.input_data = input
    sdfyacc.parser.parse(sdflex.input_data)
    return sdfyacc.timings
