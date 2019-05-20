#!/usr/bin/env python3

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


def emit(input):
    return sdfwrite.emit_sdf(input)


def parse(input):
    init()
    sdflex.input_data = input
    sdfyacc.parser.parse(sdflex.input_data)
    return sdfyacc.timings
