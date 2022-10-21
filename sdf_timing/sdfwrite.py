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


def gen_timing_entry(entry):

    if 'all' in entry:
        if entry['all'] is None: return "()";
    elif entry['min'] is None and entry['avg'] is None\
            and entry['max'] is None:
        # if all the values are None return empty timing
        return "()"

    if 'all' in entry:
        return "(" + str(entry['all']) + ")";
    else:
        return "({MIN}:{AVG}:{MAX})".format(
            MIN=entry['min'],
            AVG=entry['avg'],
            MAX=entry['max'])


def emit_timingenv_entries(delays):

    entries = ""
    tenv_entries = ""
    for delay in sorted(delays):
        delay = delays[delay]
        entry = ""
        if not delay['is_timing_env']:
            # handle only timing_env here
            continue

        input_str = ""
        output_str = ""
        if delay['to_pin_edge'] is not None:
            output_str = "(" + delay['to_pin_edge'] + " "\
                + delay['to_pin'] + ")"
        else:
            output_str = delay['to_pin']

        if delay['from_pin_edge'] is not None:
            input_str = "(" + delay['from_pin_edge'] + " "\
                + delay['from_pin'] + ")"
        else:
            input_str = delay['from_pin']

        entry += """
                (PATHCONSTRAINT {output} {input} {RISE} {FALL})""".format(
            output=output_str,
            input=input_str,
            RISE=gen_timing_entry(delay['delay_paths']['rise']),
            FALL=gen_timing_entry(delay['delay_paths']['fall']))
        entries += entry

    if entries != "":
        tenv_entries += """
        (TIMINGENV"""
        tenv_entries += entries
        tenv_entries += """
        )"""

    return tenv_entries


def emit_timingcheck_entries(delays):

    entries = ""
    tcheck_entries = ""
    for delay in sorted(delays):
        delay = delays[delay]
        entry = ""
        if not delay['is_timing_check']:
            # handle only timing checks here
            continue

        input_str = ""
        output_str = ""
        if delay['to_pin_edge'] is not None:
            output_str = "(" + delay['to_pin_edge'] + " "\
                + delay['to_pin'] + ")"
        else:
            output_str = delay['to_pin']

        if delay['from_pin_edge'] is not None:
            input_str = "(" + delay['from_pin_edge'] + " "\
                + delay['from_pin'] + ")"
        else:
            input_str = delay['from_pin']

        if delay['is_cond']:
            input_str = "(COND {equation} {input})".format(
                equation=delay['cond_equation'],
                input=input_str)

        if delay['name'].startswith("width"):
            output_str = ""

        if delay['name'].startswith("setuphold"):
            entry += """
                ({type} {output} {input} {SETUP} {HOLD})""".format(
                type=delay['type'].upper(),
                input=input_str,
                output=output_str,
                SETUP=gen_timing_entry(delay['delay_paths']['setup']),
                HOLD=gen_timing_entry(delay['delay_paths']['hold']))

        else:
            entry += """
                ({type} {output} {input} {NOMINAL})""".format(
                type=delay['type'].upper(),
                input=input_str,
                output=output_str,
                NOMINAL=gen_timing_entry(delay['delay_paths']['nominal']))
        entries += entry

    if entries != "":
        tcheck_entries += """
        (TIMINGCHECK"""
        tcheck_entries += entries
        tcheck_entries += """
        )"""

    return tcheck_entries


def emit_delay_entries(delays):

    entries_absolute = ""
    entries_incremental = ""
    entries = ""

    for delay in sorted(delays):
        entry = ""
        delay = delays[delay]
        if not delay['is_absolute'] and not delay['is_incremental']:
            # if it's neiter absolute, nor incremental
            # it must be a timingcheck entry. It will be
            # handled later
            continue

        input_str = ""
        output_str = ""
        if delay['to_pin_edge'] is not None:
            output_str = "(" + delay['to_pin_edge'] + " "\
                + delay['to_pin'] + ")"
        else:
            output_str = delay['to_pin']

        if delay['from_pin_edge'] is not None:
            input_str = "(" + delay['from_pin_edge'] + " "\
                + delay['from_pin'] + ")"
        else:
            input_str = delay['from_pin']

        tim_val_str = ""
        for delval in delay['delay_paths']:
            tim_val_str += gen_timing_entry(delval)

        indent = ""
        if delay['type'].startswith("port"):
            entry += """
                (PORT {input} {timval})""".format(
                input=input_str,
                timval=tim_val_str)
        elif delay['type'].startswith("interconnect"):
            entry += """
                (INTERCONNECT {input} {output} {timval})""".format(
                input=input_str,
                output=output_str,
                timval=tim_val_str)
        elif delay['type'].startswith("device"):
            entry += """
                (DEVICE {input} {timval})""".format(
                input=input_str,
                timval=tim_val_str)
        else:
            if delay['is_cond']:
                indent = "     "
                entry += """
                (COND ({equation})""".format(
                    equation=delay['cond_equation'])

            retain_str = '';
            if 'retain_paths' in delay:
                for delval in delay['retain_paths']:
                    retain_str += gen_timing_entry(delval)
                retain_str = "(RETAIN " + retain_str + ") ";

            entry += """
                {indent}(IOPATH {input} {output} {retain}{timval})""".format(
                indent=indent,
                input=input_str,
                output=output_str,
                retain=retain_str,
                timval=tim_val_str)

            if delay['is_cond']:
                entry += """
                )"""

        if delay['is_absolute']:
            entries_absolute += entry
            # if it is not absolute it must be incremental
            # all the other types are filtered above
        else:
            entries_incremental += entry

    if entries_absolute != "" or entries_incremental != "":
        entries += """
        (DELAY"""
    if entries_absolute != "":
        entries += """
            (ABSOLUTE"""
        entries += entries_absolute
        entries += """
            )"""
    if entries_incremental != "":
        entries += """
            (INCREMENT"""
        entries += entries_incremental
        entries += """
            )"""
    if entries_absolute != "" or entries_incremental != "":
        entries += """
        )"""

    return entries


def emit_sdf(timings, timescale='1ps', uppercase_celltype=False):

    for slice in timings:
        sdf = \
            """(DELAYFILE
    (SDFVERSION \"3.0\")
    (TIMESCALE {})
""".format(timescale)
        if 'cells' in timings:
            cells = dict();
            for cell in timings['cells']:
                cellname = cell['cell'];
                instname = cell['inst'];
                if cellname not in cells:
                    cells[cellname] = dict();
                if instname not in cells[cellname]:
                    cells[cellname][instname] = dict();

                if 'delays' in cell:
                    cells[cellname][instname].update( cell['delays'] );
                    #for  in cell['delays']:
                    #    cells[cellname][instname][delay['name']] = delay

            for cell in sorted(cells):
                for location in sorted(cells[cell]):

                    if uppercase_celltype:
                        celltype = cell.upper()
                    else:
                        celltype = cell

                    sdf += """
    (CELL
        (CELLTYPE \"{name}\")""".format(name=celltype)

                    sdf += """
        (INSTANCE {location})""".format(location=location)
                    sdf += emit_delay_entries(
                        cells[cell][location])
                    sdf += emit_timingcheck_entries(
                        cells[cell][location])
                    sdf += emit_timingenv_entries(
                        cells[cell][location])
                    sdf += """
    )"""
        sdf += """
)"""

    # fix "None" entries
    sdf = sdf.replace("None", "")
    return sdf

import os
import sys
import json
import re
from ply import yacc
from sdf_timing import sdfparse, sdfyacc, sdflex

def parse(input):
    sdfparse.init()
    sdflex.input_data = input
    return sdfyacc.parser.parse(sdflex.input_data)

def format_triplet(entry):

    if 'all' in entry:
        if entry['all'] is None: return "";
    elif entry['min'] is None and entry['avg'] is None\
            and entry['max'] is None:
        # if all the values are None return empty timing
        return ""

    if 'all' in entry:
        v = entry['all'];
        if v.is_integer():
            s = str(int(v));
        else:
            s = str(v);
        return s;
    else:
        l = [];
        for k in ['min','avg','max']:
            v = entry[k];
            if v is None:
                l.append("");
            elif v.is_integer():
                l.append(str(int(v)));
            else:
                l.append(str(v));
        return ":".join(l);


def print_timing_record(rec, indent):
    if rec is None or not 'type' in rec:
        pass


def print_sdf(sdfdata, indent="  ", channel=sys.stdout):
    print("(DELAYFILE", file=channel);

    for k,v in sdfdata['header'].items():
        if k == "voltage" or k == 'temperature':
            v = format_triplet(v);
        elif k == 'divider':
            pass
        elif k == 'timescale':
            m = re.match('^(\d+)(\D+)$',v);
            v = m.group(1) + ' ' + m.group(2);
        else:
            v = '\"' + v + '\"';
        print( indent + "({key} {value})".format(key=k.upper(), value=v), file=channel );

    if 'cells' in sdfdata:
        for instdata in sdfdata['cells']:
            print(indent + "(CELL", file=channel);
            print( indent*2 + "(CELLTYPE \"{}\")".format(instdata['cell']), file=channel );
            inst = instdata['inst'] if 'inst' in instdata else None;
            print( indent*2 + "(INSTANCE {})".format(inst if inst is not None else ''), file=channel );

            if 'delays' in instdata:
                last_rectype = None;
                rectype = None;
                for rec,recdata in instdata['delays'].items():
                    if any(recdata['type'] in s for s in ['interconnect', 'iopath', 'port', 'device']):
                        rectype = "absdelay" if recdata['is_absolute'] else "incdelay";
                    elif any(recdata['type'] in s for s in ['setup', 'hold', 'setuphold', 'recovery', 'removal',
                        'recrem', 'width', 'period', 'nochange']):
                        rectype = 'tcheck';
                    elif any(recdata['type'] in s for s in ['pathconstraint']):
                        rectype = 'tenv';
                    else:
                        rectype = None

                    if rectype != last_rectype:
                        print_closing_bracket(last_rectype, indent, channel);
                        print_opening_bracket(rectype, indent, channel);

                    if rectype=='absdelay' or rectype=='incdelay':
                        print( 4*indent + format_delay(recdata), file=channel );
                    elif rectype=='tcheck':
                        print( 3*indent + format_tcheck(recdata), file=channel );
                    elif rectype=='tenv':
                        print( 3*indent + format_tenv(recdata), file=channel );
                    else:
                        raise Exception('Wrongly detected record type!', recdata, rectype)

                    last_rectype = rectype;

                print_closing_bracket(last_rectype, indent, channel);

            print(indent + ")", file=channel);
    print(")", end='', file=channel);


def print_closing_bracket(rectype, indent, channel):
    if rectype is None:
        pass

    if rectype == 'absdelay' or rectype == 'incdelay':
        print(3*indent + ")\n" + 2*indent + ")", file=channel);
    elif rectype == 'tcheck' or rectype == 'tenv':
        print(2*indent + ")", file=channel);


def print_opening_bracket(rectype, indent, channel):
    if rectype is None:
        pass

    if rectype == 'absdelay' or rectype == 'incdelay':
        print(2*indent + "(DELAY", file=channel);
        print(3*indent + ("(ABSOLUTE" if rectype=='absdelay' else "(INCREMENT"), file=channel);
    elif rectype == 'tcheck':
        print(2*indent + "(TIMINGCHECK", file=channel);
    elif rectype == 'tenv':
        print(2*indent + "(TIMINGENV", file=channel);


def format_pin(pin, edge, conditional=False, condition=None):
    if edge is not None:
        pin = "(" + edge + " " + pin + ")"

    if conditional:
        pin = '(COND ' + condition + ' ' + pin + ')'

    return pin


def format_delval(triplet):
    return "("+format_triplet(triplet)+")"


def format_delval_list( delval_list ):
    if delval_list is None:
        return None

    tim_val_str = ""
    for delval in delval_list:
        tim_val_str += format_delval(delval)
    return tim_val_str


def format_delay(data):
    if data is None:
        return None

    if not data['is_absolute'] and not data['is_incremental']:
        raise Exception('Misconfigured delay entry!', data);

    entry = None
    if data['type']=='port' or data['type']=='device':
        entry = "({type} {input} {timval})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge']),
            timval=format_delval_list( data['delay_paths'] ))
    elif data['type']=='interconnect':
        entry = "({type} {input} {output} {timval})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge']),
            output=format_pin(data['to_pin'], data['to_pin_edge']),
            timval=format_delval_list( data['delay_paths'] ))
    elif data['type']=='iopath':
        retain = '';
        if 'retain_paths' in data:
            retain = "(RETAIN " + format_delval_list( data['retain_paths'] ) + ") ";
        entry = "({type} {input} {output} {retain}{timval})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge']),
            output=format_pin(data['to_pin'], data['to_pin_edge']),
            retain=retain,
            timval=format_delval_list( data['delay_paths'] ))
    else:
        raise Exception('Unknown delay type!', data);

    if data['is_cond']:
        entry = "(COND {equation} {entry})".format( entry=entry,
            equation=data['cond_equation'])

    return entry;


def format_tenv(data):
    if data is None:
        return None

    if not data['is_timing_env']:
        raise Exception('Misconfigured timingenv entry!', data);

    entry = None
    if data['type']=='pathconstraint':
        entry = "(PATHCONSTRAINT {input} {output} {RISE} {FALL})".format(
            input=format_pin(data['from_pin'], data['from_pin_edge']),
            output=format_pin(data['to_pin'], data['to_pin_edge']),
            RISE=format_delval(data['delay_paths']['rise']),
            FALL=format_delval(data['delay_paths']['fall']))
    return entry


def format_tcheck(data):
    if data is None:
        return None

    if data['is_absolute'] or data['is_incremental']:
        raise Exception('Misconfigured timingcheck entry!', data);
    if not data['is_timing_check']:
        raise Exception('Misconfigured timingcheck entry!', data);

    entry = None
    if data['type']=='width' or data['type']=='period':
        entry = "({type} {input} {timval})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge'], data['is_cond'],
                data['cond_equation']),
            timval=format_delval(data['delay_paths']['nominal']))

    elif data['type']=='setuphold' or data['type']=='recrem' or data['type']=='nochange':
        entry = "({type} {output} {input} {SETUP} {HOLD})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge'], data['is_cond'],
                data['cond_equation']),
            output=format_pin(data['to_pin'], data['to_pin_edge']),
            SETUP=format_delval(data['delay_paths']['setup']),
            HOLD=format_delval(data['delay_paths']['hold']))

    else:
        entry = "({type} {output} {input} {timval})".format(
            type=data['type'].upper(),
            input=format_pin(data['from_pin'], data['from_pin_edge'], data['is_cond'],
                data['cond_equation']),
            output=format_pin(data['to_pin'], data['to_pin_edge']),
            timval=format_delval(data['delay_paths']['nominal']))

    return entry;


def print_sdf_file(f, indent='  ', channel=sys.stdout):
    #print(f);
    with open(f) as sdffile:
        sdfdata = parse( sdffile.read() );
        #print( json.dumps(sdfdata, indent=2) );
        print_sdf( sdfdata, indent, channel );


def print_sdf_files(files, indent='  '):
    for f in files:
        print_sdf_file(f,indent);

