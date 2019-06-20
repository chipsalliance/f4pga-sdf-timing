#!/usr/bin/env python3


def gen_timing_entry(entry):

    if entry['min'] is None and entry['avg'] is None\
            and entry['max'] is None:
        # if all the values are None return empty timing
        return "()"

    return "({MIN}:{AVG}:{MAX})".format(
        MIN=entry['min'],
        AVG=entry['avg'],
        MAX=entry['max'])


def emit_timingenv_entry(delay):

    entry = ""
    if not delay['is_timing_env']:
        # handle only timing_env here
        return ""

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

    return entry


def emit_timingcheck_entry(delay):

    entry = ""
    if not delay['is_timing_check']:
        # handle only timing checks here
        return ""

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

    return entry


def emit_delay_entry(delay):

    entry = ""
    dtype = ""
    if delay['is_absolute']:
        dtype = "ABSOLUTE"
    elif delay['is_incremental']:
        dtype = "INCREMENTAL"
    else:
        # if it's neiter absolute, nor incremental
        # it must be a timingcheck entry. It will be
        # handled later
        return ""

    entry += """
            ({dtype}""".format(dtype=dtype)

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

    for path in ['fast', 'nominal', 'slow']:
        if path in delay['delay_paths']:
            tim_val_str += gen_timing_entry(delay['delay_paths'][path])

    intent = ""
    if delay['type'].startswith("port"):
        entry += """
                (PORT {input} {timval})""".format(
            intent=intent,
            input=input_str,
            output=output_str,
            timval=tim_val_str)
    elif delay['type'].startswith("interconnect"):

        entry += """
                (INTERCONNECT {input} {output} {timval})""".format(
            intent=intent,
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
            intent = "     "
            entry += """
                (COND ({equation})""".format(
                equation=delay['cond_equation'])

        entry += """
                {intent}(IOPATH {input} {output} {timval})""".format(
            intent=intent,
            input=input_str,
            output=output_str,
            timval=tim_val_str)

        if delay['is_cond']:
            entry += """
                )"""
    entry += """
            )"""

    return entry


def emit_sdf(timings, timescale='1ps'):

    for slice in timings:
        sdf = \
            """(DELAYFILE
    (SDFVERSION \"3.0\")
    (TIMESCALE {})
""".format(timescale)
        if 'cells' in timings:
            for cell in sorted(timings['cells']):
                for location in sorted(timings['cells'][cell]):
                    sdf += """
    (CELL
        (CELLTYPE \"{name}\")""".format(name=cell.upper())

                    sdf += """
        (INSTANCE {location})""".format(location=location)
                    for delay in sorted(timings['cells'][cell][location]):
                        delay_entry = emit_delay_entry(
                            timings['cells'][cell][location][delay])
                        if delay_entry != "":
                            sdf += """
        (DELAY"""
                            sdf += delay_entry
                            sdf += """
        )"""
                        timingcheck = emit_timingcheck_entry(
                            timings['cells'][cell][location][delay])
                        if timingcheck != "":
                            sdf += """
        (TIMINGCHECK"""
                            sdf += timingcheck
                            sdf += """
        )"""
                        timingenv = emit_timingenv_entry(
                            timings['cells'][cell][location][delay])
                        if timingenv != "":
                            sdf += """
        (TIMINGENV"""
                            sdf += timingenv
                            sdf += """
        )"""

                    sdf += """
    )"""
        sdf += """
)"""

    # fix "None" entries
    sdf = sdf.replace("None", "")
    return sdf
