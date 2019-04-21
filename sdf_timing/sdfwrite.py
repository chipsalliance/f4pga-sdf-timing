#!/usr/bin/env python3


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
                (PATHCONSTRAINT {output} {input} ({RISEMIN}:{RISEAVG}:\
{RISEMAX})({FALLMIN}:{FALLAVG}:{FALLMAX}))""".format(
        output=output_str,
        input=input_str,
        RISEMIN=delay['delay_paths']['rise']['min'],
        RISEAVG=delay['delay_paths']['rise']['avg'],
        RISEMAX=delay['delay_paths']['rise']['max'],
        FALLMIN=delay['delay_paths']['fall']['min'],
        FALLAVG=delay['delay_paths']['fall']['avg'],
        FALLMAX=delay['delay_paths']['fall']['max'])

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
                ({type} {output} {input} ({SETUPMIN}:{SETUPAVG}:{SETUPMAX})\
({HOLDMIN}:{HOLDAVG}:{HOLDMAX}))""".format(
            type=delay['type'].upper(),
            input=input_str,
            output=output_str,
            SETUPMIN=delay['delay_paths']['setup']['min'],
            SETUPAVG=delay['delay_paths']['setup']['avg'],
            SETUPMAX=delay['delay_paths']['setup']['max'],
            HOLDMIN=delay['delay_paths']['hold']['min'],
            HOLDAVG=delay['delay_paths']['hold']['avg'],
            HOLDMAX=delay['delay_paths']['hold']['max'])

    else:
        entry += """
                ({type} {output} {input} ({MIN}:{AVG}:{MAX}))""".format(
            type=delay['type'].upper(),
            input=input_str,
            output=output_str,
            MIN=delay['delay_paths']['nominal']['min'],
            AVG=delay['delay_paths']['nominal']['avg'],
            MAX=delay['delay_paths']['nominal']['max'])

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
    if 'fast' in delay['delay_paths']:
        tim_val_str += "({MIN}:{AVG}:{MAX})".format(
            MIN=delay['delay_paths']['fast']['min'],
            AVG=delay['delay_paths']['fast']['avg'],
            MAX=delay['delay_paths']['fast']['max'])
    if 'nominal' in delay['delay_paths']:
        tim_val_str += "({MIN}:{AVG}:{MAX})".format(
            MIN=delay['delay_paths']['nominal']['min'],
            AVG=delay['delay_paths']['nominal']['avg'],
            MAX=delay['delay_paths']['nominal']['max'])
    if 'slow' in delay['delay_paths']:
        tim_val_str += "({MIN}:{AVG}:{MAX})".format(
            MIN=delay['delay_paths']['slow']['min'],
            AVG=delay['delay_paths']['slow']['avg'],
            MAX=delay['delay_paths']['slow']['max'])

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


def emit_sdf(timings):

    for slice in timings:
        sdf = """
(DELAYFILE
    (SDFVERSION \"3.0\")
    (TIMESCALE 1ps)
"""
        for cell in timings['cells']:
            sdf += """
    (CELL
        (CELLTYPE \"{name}\")""".format(name=cell.upper())
            for location in timings['cells'][cell]:

                sdf += """
        (INSTANCE {location})""".format(location=location)
                for delay in timings['cells'][cell][location]:
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
    )
)"""
    return sdf
