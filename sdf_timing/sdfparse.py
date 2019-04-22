#!/usr/bin/env python3

from . import sdflex
from . import sdfyacc


def parse(input):
    sdflex.input_data = input
    sdfyacc.parser.parse(sdflex.input_data)
    return sdfyacc.timings
