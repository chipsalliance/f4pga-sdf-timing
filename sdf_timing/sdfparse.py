#!/usr/bin/env python3

from . import sdflex
from . import sdfyacc
from . import sdfwrite


def emit(input):
    return sdfwrite.emit_sdf(input)


def parse(input):
    sdflex.input_data = input
    sdfyacc.parser.parse(sdflex.input_data)
    return sdfyacc.timings
