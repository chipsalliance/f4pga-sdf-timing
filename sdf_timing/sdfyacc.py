#!/usr/bin/env python3
# coding: utf-8
#
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import ply.yacc as yacc

from . import utils
from .sdflex import tokens


def remove_quotation(s):
    return s.replace('"', '')


def p_sdf_file(p):
    '''sdf_file : LPAR DELAYFILE sdf_header RPAR
                | LPAR DELAYFILE sdf_header cell_list RPAR'''

    timings = dict()
    timings['header'] = p[3]
    if p[4] != ')':
        timings['cells'] = p[4]

    p[0] = timings


def p_sdf_header(p):
    '''sdf_header : sdf_header_qstring
                  | sdf_header_qfloat
                  | sdf_header sdf_header_qstring
                  | sdf_header sdf_header_qfloat
                  | sdf_header voltage
                  | sdf_header temperature
                  | sdf_header hierarchy_divider
                  | sdf_header timescale'''

    #p[0] = p[1]
    if len(p)==2:
        p[0] = p[1];
    else:
        p[0] = {**p[1],**p[2]};


def p_sdf_header_qstring(p):
    '''sdf_header_qstring : LPAR qstring_header_entry QSTRING RPAR
                          | LPAR qstring_header_entry RPAR'''
    if len(p) == 5:
        p[0] = {p[2].lower(): remove_quotation(p[3])};
    else:
        p[0] = {p[2].lower(): ''};


def p_qstring_header_entry(p):
    '''qstring_header_entry : SDFVERSION
                            | DATE
                            | PROCESS
                            | DESIGN
                            | VENDOR
                            | PROGRAM
                            | VERSION'''
    p[0] = p[1]


def p_sdf_header_qfloat(p):
    '''sdf_header_qfloat : LPAR qfloat_header_entry QFLOAT RPAR'''
    if len(p) == 5:
        p[0] = {p[2].lower(): remove_quotation(p[3])};
    else:
        p[0] = {p[2].lower(): None};


def p_qfloat_header_entry(p):
    '''qfloat_header_entry : SDFVERSION
                           | VERSION'''
    p[0] = p[1]


def p_sdf_voltage(p):
    '''voltage : LPAR VOLTAGE real_triple_no_par RPAR'''
    p[0] = {'voltage': p[3]};


def p_sdf_temperature(p):
    '''temperature : LPAR TEMPERATURE real_triple_no_par RPAR'''
    p[0] = {'temperature': p[3]};


def p_sdf_divider(p):
    '''hierarchy_divider : LPAR DIVIDER DOT RPAR
               | LPAR DIVIDER SLASH RPAR'''
    p[0] = {'divider': p[3]};


def p_sdf_timescale(p):
    '''timescale : LPAR TIMESCALE FLOAT STRING RPAR'''
    p[0] = {'timescale': str(p[3]) + p[4]};


def p_cell_list(p):
    '''cell_list : cell
                 | cell_list cell'''
    if len(p) == 2:
        p[0] = [p[1]];
    else:
        p[0] = p[1] + [p[2]];


def add_delays_to_cell(cell, delays):

    if delays is None:
        return

    occurrences = {};
    for delay in delays:
        delay_name = delay['name'];
        if not delay_name in occurrences:
            occurrences[delay_name] = 1;
        else:
            suffix = "#" + str(occurrences[delay_name]);
            delay_name += suffix;
            if delay_name in occurrences:
                # The way how delay entries names are constructed shall guarantee
                # there will be no other namig collision. Hence we raise an exception
                # if the case occurs as it points to an underlying issue.
                raise Exception("Unexpected name clash!", delay);

            occurrences[delay_name] = 1;
            occurrences[delay['name']] += 1;
            delay['name'] = delay_name;
        if not 'delays' in cell:
            cell['delays'] = dict();
        cell['delays'][delay['name']] = delay


def p_timing_cell(p):
    '''cell : LPAR CELL celltype instance timing_cell_lst RPAR
            | LPAR CELL celltype instance RPAR'''

    cell = {'cell':p[3], 'inst':p[4]};
    delays = [];
    if len(p)==7:
        delays = p[5];
    add_delays_to_cell(cell, delays)
    p[0] = cell


def p_timing_cell_lst(p):
    '''timing_cell_lst : timing_cell_entry
                       | timing_cell_lst timing_cell_entry'''
    if len(p)==2:
        p[0] = p[1];
    else:
        p[0] = p[1] + p[2];


def p_timing_cell_entry(p):
    '''timing_cell_entry : timing_check
                         | delay
                         | timingenv'''
    p[0] = p[1];


def p_celltype(p):
    '''celltype : LPAR CELLTYPE QSTRING RPAR'''
    p[0] = remove_quotation(p[3])


def p_instance(p):
    '''instance : LPAR INSTANCE STRING RPAR
                | LPAR INSTANCE ASTERISK RPAR
                | LPAR INSTANCE RPAR'''
    if p[3] == ')':
        p[0] = None
    else:
        p[0] = p[3]


def p_timing_check(p):
    '''timing_check : LPAR TIMINGCHECK timing_check_list RPAR'''
    p[0] = p[3];


def p_timing_port(p):
    '''timing_port : port_check
                   | cond_check'''
    p[0] = p[1]


def p_port_check(p):
    '''port_check : port_spec'''
    port = dict()
    port['cond'] = False
    port['cond_equation'] = None
    port['port'] = p[1]['port']
    port['port_edge'] = p[1]['port_edge']
    p[0] = port


def p_timing_cond(p):
    '''cond_check : LPAR COND equation port_spec RPAR'''
    port = dict()
    port['cond'] = True
    port['cond_equation'] = " ".join(p[3])
    port['port'] = p[4]['port']
    port['port_edge'] = p[4]['port_edge']
    p[0] = port


def p_timing_check_list(p):
    '''timing_check_list : t_check
                         | timing_check_list t_check'''
    if len(p) == 2:
        p[0] = [p[1]];
    else:
        p[0] = p[1] + [p[2]];


def p_t_check(p):
    '''t_check : removal_check
               | recovery_check
               | hold_check
               | setup_check
               | width_check
               | period_check
               | nochange_check
               | setuphold_check
               | recrem_check'''
    p[0] = p[1]


def p_removal_check(p):
    '''removal_check : LPAR REMOVAL timing_port timing_port real_triple RPAR'''

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('removal', p[3], p[4], paths)
    p[0] = tcheck;


def p_recovery_check(p):
    '''recovery_check : LPAR RECOVERY timing_port timing_port real_triple \
    RPAR'''

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('recovery', p[3], p[4], paths)
    p[0] = tcheck;


def p_hold_check(p):
    '''hold_check : LPAR HOLD timing_port timing_port real_triple RPAR'''

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('hold', p[3], p[4], paths)
    p[0] = tcheck;


def p_setup_check(p):
    '''setup_check : LPAR SETUP timing_port timing_port real_triple RPAR'''

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('setup', p[3], p[4], paths)
    p[0] = tcheck;


def p_width_check(p):
    '''width_check : LPAR WIDTH timing_port real_triple RPAR'''

    paths = dict()
    paths['nominal'] = p[4]
    tcheck = utils.add_tcheck('width', p[3], p[3], paths)
    p[0] = tcheck;


def p_period_check(p):
    '''period_check : LPAR PERIOD timing_port real_triple RPAR'''

    paths = dict()
    paths['nominal'] = p[4]
    tcheck = utils.add_tcheck('period', p[3], p[3], paths)
    p[0] = tcheck;


def p_nochange_check(p):
    '''nochange_check : LPAR NOCHANGE timing_port timing_port real_triple real_triple RPAR'''

    paths = dict()
    paths['setup'] = p[5]
    paths['hold'] = p[6]
    tcheck = utils.add_tcheck('nochange', p[3], p[4], paths)
    p[0] = tcheck;


def p_setuphold_check(p):
    '''setuphold_check : LPAR SETUPHOLD timing_port timing_port real_triple \
    real_triple RPAR'''

    paths = dict()
    paths['setup'] = p[5]
    paths['hold'] = p[6]
    tcheck = utils.add_tcheck('setuphold', p[3], p[4], paths)
    p[0] = tcheck;


def p_recrem_check(p):
    '''recrem_check : LPAR RECREM timing_port timing_port real_triple \
    real_triple RPAR'''

    paths = dict()
    paths['setup'] = p[5]
    paths['hold'] = p[6]
    tcheck = utils.add_tcheck('recrem', p[3], p[4], paths)
    p[0] = tcheck;


#TODO SDF Std. defines other entries than just PATHCONSTRAINT's
#     (e.g. PERIODCONSTRAINT, ARRIVAL and others).
def p_timingenv(p):
    'timingenv : LPAR TIMINGENV constraints_list RPAR'
    p[0] = p[3];


def p_constraints_list(p):
    '''constraints_list : path_constraint
                        | constraints_list path_constraint'''
    if len(p) == 2:
        p[0] = [p[1]];
    else:
        p[0] = p[1] + [p[2]];


#TODO SDF Std. defines an optional constraint name of the type
#     `(NAME <string>)` (before the 1st `port_spec`).
#TODO SDF Std. allows more than two ports in the constraint
#     definition. All but the 1st and last are intermediate
#     points of the path. To capture the intermediate points
#     (or better the full path) into an existing dict structure,
#     it may go under the `paths` dicktionary.
def p_path_constraint(p):
    '''path_constraint : LPAR PATHCONSTRAINT port_spec port_spec real_triple \
    real_triple RPAR'''

    paths = dict()
    paths['rise'] = p[5]
    paths['fall'] = p[6]
    # Per SDF Std. the 1st port_spec is `from` and the last port_spec
    # is `to`.
    constr = utils.add_constraint('pathconstraint', p[4], p[3], paths)
    p[0] = constr;


def p_delay(p):
    '''delay : LPAR DELAY absolute_list RPAR
             | LPAR DELAY increment_list RPAR'''
    p[0] = p[3];


def p_absolute_list(p):
    '''absolute_list : absolute
                     | absolute_list absolute'''
    if len(p)==2:
        p[0] = p[1];
    else:
        p[0] = p[1] + p[2];


#TODO SDF Std. does not seem to allow empty delay specification (neither
#TODO absolute, nor incremental).
def p_absolute_empty(p):
    '''absolute : LPAR ABSOLUTE RPAR'''
    p[0] = []


def p_absolute_delay_list(p):
    '''absolute : LPAR ABSOLUTE delay_list RPAR'''
    for d in p[3]:
        d['is_absolute'] = True
    p[0] = p[3]


def p_increment_list(p):
    '''increment_list : increment
                      | increment_list increment'''
    if len(p)==2:
        p[0] = p[1];
    else:
        p[0] = p[1] + p[2];


def p_increment_delay_list(p):
    '''increment : LPAR INCREMENT delay_list RPAR'''

    for d in p[3]:
        d['is_incremental'] = True
    p[0] = p[3]


#TODO there shall be `iopath` instead of `delval_list` in the rule
def p_cond_delay(p):
    '''cond_delay : LPAR COND delay_condition delay_list RPAR'''
    # add condition to every list element
    for d in p[4]:
        d['is_cond'] = True
        d['cond_equation'] = " ".join(p[3])
    p[0] = p[4]


#TODO `delay_condition` can be reduced to `cond_expr` and hence we can
#     optimize the grammar. `delay_condition` has been kept for compatibility
#     so that syntax unit tests work with the legacy code, too.
def p_delay_condition(p):
    '''delay_condition : cond_expr'''
    p[0] = p[1]


def p_delay_list_interconnect(p):
    '''delay_list : del
                  | delay_list del'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]


def p_del(p):
    '''del : interconnect
           | iopath
           | port
           | device
           | cond_delay'''
    if type(p[1]) is list:
        p[0] = p[1]
    else:
        p[0] = [p[1]]


def expand_delval_list(l):
    # The number of delvals in the delval_list can be one, two, three, six or
    # twelve. Note, however, that the amount of data you include in a delay
    # definition entry must be consistent with the analysis tool’s ability to
    # model that kind of delay. For example, if the modeling primitives of
    # a particular tool can accept only three delay values, perhaps rising,
    # falling and Z transitions, you should not attempt to annotate different
    # values for 0-to-1 and Z-to-1 transitions or for 1-to-Z and 0-to-Z
    # transitions. It is recommended that in such situations annotators
    # combine the information given in some documented manner and issue
    # a warning.
    # 
    # The following rules apply for annotation:
    # 
    # - If twelve delvals are specified in delval_list, then each corresponds,
    #   in sequence, to the delay value applicable when the port (for `IOPATH`
    #   and `INTERCONNECT`, the output port) makes the following transitions:
    # 
    #       0-to-1, 1-to-0, 0-to-Z, Z-to-1, 1-to-Z, Z-to-0,
    #       0-to-X, X-to-1, 1-to-X, X-to-0, X-to-Z, Z-to-X
    # 
    #   If fewer than twelve delvals are specified in delval_list, then the
    #   table below shows how the delays for each transition of the port are
    #   found from the values given.
    # 
    # - If only two delvals are specified, the first (rising) is denoted in the
    #   table by 0-to-1 and the second (falling) by 1-to-0.
    # 
    # - If three delvals are specified, the first and second are denoted as
    #   before and the third, the Z transition value, by to−Z.
    # 
    # - If six delvals are specified, they are denoted, in sequence, by 0-to-1,
    #   1-to-0, 0-to-Z, Z-to-1, 1-to-Z and Z-to-0.
    # 
    # - If a single delval is specified, it applies to all twelve possible
    #   transitions. This is not shown in the table.
    # 
    # +------------+--------------------------------------------------------------+
    # |            | Number of delvals in delval_list                             |
    # +------------+--------------------------------------------------------------+
    # | Transition | 2                  | 3                  | 6                  |
    # +------------+--------------------+--------------------+--------------------+
    # | 0-to-1     | 0-to-1             | 0-to-1             | 0-to-1             | 
    # | 1-to-0     | 1-to-0             | 1-to-0             | 1-to-0             | 
    # | 0-to-Z     | 0-to-1             | to−Z               | 0-to-Z             |
    # | Z-to-1     | 0-to-1             | 0-to-1             | Z-to-1             | 
    # | 1-to-Z     | 1-to-0             | to−Z               | 1-to-Z             |
    # | Z-to-0     | 1-to-0             | 1-to-0             | Z-to-0             | 
    # | 0-to-X     | 0-to-1             | min(0-to-1,to−Z)   | min(0-to-1,0-to-Z) | 
    # | X-to-1     | 0-to-1             | 0-to-1             | max(0-to-1,Z-to-1) | 
    # | 1-to-X     | 1-to-0             | min(1-to-0,to−Z)   | min(1-to-0,1-to-Z) | 
    # | X-to-0     | 1-to-0             | 1-to-0             | max(1-to-0,Z-to-0) | 
    # | X-to-Z     | max(0-to-1,1-to-0) | to−Z               | max(0-to-Z,1-to-Z) | 
    # | Z-to-X     | min(0-to-1,1-to-0) | min(0-to-1,1-to-0) | min(Z-to-0,Z-to-1) | 
    # +------------+--------------------+--------------------+--------------------+

    trans_list = ['01','10','0Z','Z1','1Z','Z0','0X','X1','1X','X0','XZ','ZX'];
    paths = dict()
    if len(l) == 12:
        for i in range(0,12):
            paths[trans_list[i]] = l[i]
    elif len(l) == 1:
        for i in range(0,12):
            paths[trans_list[i]] = l[0]
    elif len(l) == 2:
        paths['01'] = l[0]
        paths['10'] = l[1]
        paths['0Z'] = l[0]
        paths['Z1'] = l[0]
        paths['1Z'] = l[1]
        paths['Z0'] = l[1]
        paths['0X'] = l[0]
        paths['X1'] = l[0]
        paths['1X'] = l[1]
        paths['X0'] = l[1]
        paths['XZ'] = None; # IEEE Std: shall be max('01','10')
        paths['ZX'] = None; # IEEE Std: shall be min('01','10')
    elif len(l) == 3:
        paths['01'] = l[0]
        paths['10'] = l[1]
        paths['0Z'] = l[2]
        paths['Z1'] = l[0]
        paths['1Z'] = l[2]
        paths['Z0'] = l[1]
        paths['0X'] = None; # IEEE Std: shall be min('01','0Z')
        paths['X1'] = l[0]
        paths['1X'] = None; # IEEE Std: shall be min('10','0Z')
        paths['X0'] = l[1]
        paths['XZ'] = l[2]
        paths['ZX'] = None; # IEEE Std: shall be min('01','10')
    elif len(l) == 6:
        paths['01'] = l[0]
        paths['10'] = l[1]
        paths['0Z'] = l[2]
        paths['Z1'] = l[3]
        paths['1Z'] = l[4]
        paths['Z0'] = l[5]
        paths['0X'] = None; # IEEE Std: shall be min('01','0Z')
        paths['X1'] = None; # IEEE Std: shall be max('01','Z1')
        paths['1X'] = None; # IEEE Std: shall be min('10','1Z')
        paths['X0'] = None; # IEEE Std: shall be max('10','Z0')
        paths['XZ'] = None; # IEEE Std: shall be max('0Z','1Z')
        paths['ZX'] = None; # IEEE Std: shall be min('Z0','Z1')
    else:
        raise Exception("Semanic error for delval_list line: %d: len=%d can be 1, 2, 3, 6 or 12 values %s" % (p.lineno(0),len(l),str(l)))

    return paths

def p_delval_list(p):
    '''delval_list : real_triple_list'''
    if not len(p[1]) in [1,2,3,6,12]:
        raise Exception("Semanic error for delval_list line: %d: len=%d can be 1, 2, 3, 6 or 12 values %s" % (p.lineno(0),len(p[1]),str(p[1])))

    p[0] = p[1]


def p_device(p):
    '''device : LPAR DEVICE port_spec delval_list RPAR'''
    device = utils.add_device(p[3], p[4])
    p[0] = device


def p_iopath(p):
    '''iopath : LPAR IOPATH port_spec port_spec delval_list RPAR
              | LPAR IOPATH port_spec port_spec retain_def delval_list RPAR'''
    if (len(p)==7):
        # 1st rule (w/o RETAIN)
        iopath = utils.add_iopath(p[3], p[4], p[5])
        iopath['has_retain'] = False;
        p[0] = iopath
    else:
        # 2nd rule (w/- RETAIN)
        iopath = utils.add_iopath(p[3], p[4], p[6])
        iopath['has_retain'] = True;
        iopath['retain_paths'] = p[5];
        p[0] = iopath


def p_retain_def(p):
    '''retain_def : LPAR RETAIN delval_list RPAR'''
    p[0] = p[3]


def p_port_spec(p):
    '''port_spec : STRING
                 | LPAR port_condition STRING RPAR
                 | FLOAT'''

    port = dict()
    if p[1] != '(':
        port['port'] = str(p[1])
        port['port_edge'] = None
    else:
        port['port'] = p[3]
        port['port_edge'] = p[2].lower()

    p[0] = port


def p_interconnect(p):
    '''interconnect : LPAR INTERCONNECT port_spec port_spec delval_list RPAR'''
    interconnect = utils.add_interconnect(p[3], p[4], p[5])
    p[0] = interconnect


def p_port(p):
    '''port : LPAR PORT port_spec delval_list RPAR'''
    port = utils.add_port(p[3], p[4])
    p[0] = port


def p_port_condition(p):
    '''port_condition : POSEDGE
                      | NEGEDGE'''
    p[0] = p[1]


# TODO This really is `rtriple` (as SDF Std. calls it). Keeping the legacy
#      code naming for easier diffing.
def p_real_triple_no_par(p):
    '''real_triple_no_par : FLOAT COLON FLOAT COLON FLOAT
                   | COLON FLOAT COLON FLOAT
                   | FLOAT COLON COLON FLOAT
                   | FLOAT COLON FLOAT COLON
                   | COLON COLON FLOAT
                   | COLON FLOAT COLON
                   | FLOAT COLON COLON
                   | FLOAT'''

    delays_triple = dict()
    if len(p) == 6:
        delays_triple['min'] = float(p[1])
        delays_triple['avg'] = float(p[3])
        delays_triple['max'] = float(p[5])

    elif len(p) == 5:

        if p[1] == ':' and p[3] == ':':
            delays_triple['min'] = None
            delays_triple['avg'] = float(p[2])
            delays_triple['max'] = float(p[4])

        elif p[2] == ':' and p[3] == ':':
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = None
            delays_triple['max'] = float(p[4])

        elif p[2] == ':' and p[4] == ':':
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = float(p[3])
            delays_triple['max'] = None

    elif len(p) == 4:
        delays_triple['min'] = float(p[1]) if p[1] != ':' else None
        delays_triple['avg'] = float(p[2]) if p[2] != ':' else None
        delays_triple['max'] = float(p[3]) if p[3] != ':' else None

    elif len(p) == 2:
        # Using `all` key instead of the `min`, `avg`, `max` triplet
        # keys. Using a different key makes it possible to differentiate if the input
        # was a single scalar value or a triplet and hence enables doing an identity
        # "format transformation" (or "pretty printing") with 100% accuracy. Using
        # triplet keys, one would need to either collapse an all-the-same
        # triplet to a single value, or expand a single value to an all-the-same
        # triplet, which may cause differences to the input, parsed syntax.
        delays_triple['all'] = float(p[1]);

    else:
        # Same comment as for the `len()==2` case.
        delays_triple['all'] = None;

    p[0] = delays_triple


#TODO This really is `rvalue` (as SDF Std. calls it). Keeping the legacy
#     code naming for compatibility of syntax unit tests.
def p_real_triple(p):
    '''real_triple : LPAR real_triple_no_par RPAR
                   | LPAR RPAR'''

    if len(p) == 3:
        p[0] = {'all': None};
    else:
        p[0] = p[2];


def p_real_triple_list(p):
    '''real_triple_list : real_triple
                   | real_triple_list real_triple'''
    if len(p)==2:
        p[0] = [p[1]];
    else:
        p[0] = p[1] + [p[2]];


def p_equation(p):
    '''equation : operator
                | STRING
                | FLOAT
                | SCALARCONSTANT
                | equation operator
                | equation FLOAT
                | equation SCALARCONSTANT
                | equation STRING'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_cond_expr(p):
    '''cond_expr : cond_expr_term
                 | cond_expr binary_op cond_expr_term'''
    if len(p)==2:
        p[0] = p[1];
    else:
        p[0] = p[1] + [p[2]] + p[3];


def p_binary_op(p):
    '''binary_op : TIMES
                 | SLASH
                 | MODULO
                 | PLUS
                 | MINUS
                 | LOGIC_AND
                 | BIT_AND
                 | NAND
                 | LOGIC_OR
                 | BIT_OR
                 | NOR
                 | XOR
                 | XNOR
                 | EQUAL
                 | NEQUAL
                 | CASEEQUAL
                 | CASENEQUAL
                 | LEFTSHIFT
                 | RIGHTSHIFT
                 | GT
                 | LT
                 | GTE
                 | LTE'''
    p[0] = p[1]


def p_cond_expr_term(p):
    '''cond_expr_term : simple_term
                      |          LPAR cond_expr RPAR
                      | unary_op LPAR cond_expr RPAR'''
    if len(p)==2:
        p[0] = p[1];
    elif len(p)==4:
        p[0] = [p[1]] + p[2] + [p[3]];
    else:
        p[0] = [p[1],p[2]] + p[3] + [p[4]];


# As per definition, a scalar constant can be one of bit specs (e.g. `1'b1`, `'b1`)
# or one of logical ints (i.e. `0` and `1`). However, the latter cannot be part of
# the `SCALARCONSTANT` token (as it would conflict with the `FLOAT` token). Hence
# we allow a `FLOAT` token in `simple_term` despite it would allow syntax invalid
# per SDF Std. To fix that, there would need to be a semantical check (which we do
# not do at the moment).
def p_simple_term(p):
    '''simple_term :          SCALARCONSTANT
                   | unary_op SCALARCONSTANT
                   |          STRING
                   | unary_op STRING
                   |          FLOAT
                   | unary_op FLOAT'''
    p[0] = list(p[1:]);


def p_unary_op(p):
    '''unary_op : PLUS
                | MINUS
                | LOGIC_NOT
                | BIT_NOT
                | BIT_AND
                | NAND
                | BIT_OR
                | NOR
                | XOR
                | XNOR'''
    p[0] = p[1]


def p_operator(p):
    '''operator : PLUS
                | MINUS
                | TIMES
                | SLASH
                | MODULO
                | LOGIC_NOT
                | BIT_NOT
                | LOGIC_AND
                | BIT_AND
                | NAND
                | LOGIC_OR
                | BIT_OR
                | NOR
                | XOR
                | XNOR
                | EQUAL
                | NEQUAL
                | CASEEQUAL
                | CASENEQUAL
                | LEFTSHIFT
                | RIGHTSHIFT
                | GT
                | LT
                | GTE
                | LTE'''
    p[0] = p[1]


def p_error(p):
    raise Exception("Syntax error at '%s' line: %d" % (p.value, p.lineno))


parser = yacc.yacc(debug=False, write_tables=False)
