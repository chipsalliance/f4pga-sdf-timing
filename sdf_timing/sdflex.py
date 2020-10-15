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

import ply.lex as lex

input_data = ""

reserved = {
    'DELAYFILE': 'DELAYFILE',
    'SDFVERSION': 'SDFVERSION',
    'DESIGN': 'DESIGN',
    'VENDOR': 'VENDOR',
    'PROGRAM': 'PROGRAM',
    'VERSION': 'VERSION',
    'TIMESCALE': 'TIMESCALE',
    'CELL': 'CELL',
    'CELLTYPE': 'CELLTYPE',
    'INSTANCE': 'INSTANCE',
    'DELAY': 'DELAY',
    'ABSOLUTE': 'ABSOLUTE',
    'INCREMENT': 'INCREMENT',
    'IOPATH': 'IOPATH',
    'posedge': 'POSEDGE',
    'negedge': 'NEGEDGE',
    'SETUP': 'SETUP',
    'HOLD': 'HOLD',
    'REMOVAL': 'REMOVAL',
    'RECOVERY': 'RECOVERY',
    'TIMINGCHECK': 'TIMINGCHECK',
    'DIVIDER': 'DIVIDER',
    'DATE': 'DATE',
    'VOLTAGE': 'VOLTAGE',
    'PROCESS': 'PROCESS',
    'TEMPERATURE': 'TEMPERATURE',
    'TIMINGENV': 'TIMINGENV',
    'PATHCONSTRAINT': 'PATHCONSTRAINT',
    'INTERCONNECT': 'INTERCONNECT',
    'PORT': 'PORT',
    'SETUPHOLD': 'SETUPHOLD',
    'WIDTH': 'WIDTH',
    'COND': 'COND',
    'DEVICE': 'DEVICE',
}

operators = (
    'ARITHMETIC',
    'MODULO',
    'LOGIC_NOT',
    'BIT_NOT',
    'LOGIC_AND',
    'BIT_AND',
    'NAND',
    'LOGIC_OR',
    'BIT_OR',
    'NOR',
    'XOR',
    'XNOR',
    'EQUAL',
    'NEQUAL',
    'CASEEQUAL',
    'CASENEQUAL',
    'LEFTSHIFT',
    'RIGHTSHIFT',
    'GT',
    'LT',
    'GTE',
    'LTE',
)

tokens = (
    'LPAR',
    'RPAR',
    'ASTERISK',
    'DOT',
    'SLASH',
    'COLON',
    'FLOAT',
    'SCALARCONSTANT',
    'QFLOAT',
    'QSTRING',
    'STRING',
) + tuple(reserved.values()) + operators

t_ARITHMETIC = r'[\+\-\*]'
t_MODULO = r'%'
t_LOGIC_NOT = r'!'
t_BIT_NOT = r'~'
t_LOGIC_AND = r'&&'
t_BIT_AND = r'&'
t_NAND = r'~&'
t_LOGIC_OR = r'\|\|'
t_BIT_OR = r'\|'
t_NOR = r'~\|'
t_XOR = r'\^'
t_XNOR = r'~\^|\^~'
t_EQUAL = r'=='
t_NEQUAL = r'!='
t_CASEEQUAL = r'==='
t_CASENEQUAL = r'!=='
t_LEFTSHIFT = r'<<'
t_RIGHTSHIFT = 'r>>'
t_GT = r'>'
t_GTE = r'>='
t_LT = r'<'
t_LTE = r'<='


t_LPAR = r'\('
t_RPAR = r'\)'
t_COLON = r':'
t_QFLOAT = r'\"[-+]?(?: [0-9]+)(?: \.[0-9]+)\"'
t_QSTRING = r'\"[a-zA-Z0-9_!#$%&\'()*+,\-./:;<=>?@\[\\\]^`{|}~ \t\n]+\"'

t_ignore = ' \t'


# define FLOAT&SCALARCONSTANT as function so they take precendence over STRING
def t_SCALARCONSTANT(t):
    r"[01]?'[Bb][01]"
    return t


def t_FLOAT(t):
    r'[-]?\.?[0-9]+(\.[0-9]+)?'
    return t


# the same for dot and slash
def t_DOT(t):
    r'\.'
    return t


def t_ASTERISK(t):
    r'\*'
    return t


def t_SLASH(t):
    r'\/'
    return t


def t_STRING(t):
    r'[a-zA-Z0-9_\/.\[\]]+'
    t.type = reserved.get(t.value, 'STRING')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise Exception("Illegal character '%s' in line %d, column %d"
                    % (t.value[0], t.lineno, find_column(input_data, t)))

# Compute column.
# input is the input text string
# token is a token instance


def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


lexer = lex.lex()
