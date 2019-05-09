import re


def get_scale(timescale):
    """Convert sdf timescale to scale factor

    >>> get_scale('1.0 fs')
    1e-15

    >>> get_scale('1ps')
    1e-12

    >>> get_scale('10 ns')
    1e-08

    >>> get_scale('10.0 us')
    9.999999999999999e-06

    >>> get_scale('100.0ms')
    0.1

    >>> get_scale('100 s')
    100.0

    """
    mm = re.match(r'(10{0,2})(\.0)? *([munpf]?s)', timescale)
    sc_lut = {
        's': 1.0,
        'ms': 1e-3,
        'us': 1e-6,
        'ns': 1e-9,
        'ps': 1e-12,
        'fs': 1e-15,
    }
    ret = None
    if mm:
        base, _, sc = mm.groups()
        ret = int(base) * sc_lut[sc]
    return ret


def prepare_entry(name=None,
                  type=None,
                  from_pin=None,
                  to_pin=None,
                  from_pin_edge=None,
                  to_pin_edge=None,
                  delay_paths=None,
                  cond_equation=None,
                  is_timing_check=False,
                  is_timing_env=False,
                  is_absolute=False,
                  is_incremental=False,
                  is_cond=False):

    entry = dict()
    entry['name'] = name
    entry['type'] = type
    entry['from_pin'] = from_pin
    entry['to_pin'] = to_pin
    entry['from_pin_edge'] = from_pin_edge
    entry['to_pin_edge'] = to_pin_edge
    entry['delay_paths'] = delay_paths
    entry['is_timing_check'] = is_timing_check
    entry['is_timing_env'] = is_timing_env
    entry['is_absolute'] = is_absolute
    entry['is_incremental'] = is_incremental
    entry['is_cond'] = is_cond
    entry['cond_equation'] = cond_equation

    return entry


def add_port(portname, paths):

    name = "port_" + portname['port']
    return prepare_entry(name=name,
                         type='port',
                         from_pin=portname['port'],
                         to_pin=portname['port'],
                         delay_paths=paths)


def add_interconnect(pfrom, pto, paths):

    name = "interconnect_"
    name += pfrom['port'] + "_" + pto['port']
    return prepare_entry(name=name,
                         type='interconnect',
                         from_pin=pfrom['port'],
                         to_pin=pto['port'],
                         from_pin_edge=pfrom['port_edge'],
                         to_pin_edge=pto['port_edge'],
                         delay_paths=paths)


def add_iopath(pfrom, pto, paths):

    name = "iopath_"
    name += pfrom['port'] + "_" + pto['port']
    return prepare_entry(name=name,
                         type='iopath',
                         from_pin=pfrom['port'],
                         to_pin=pto['port'],
                         from_pin_edge=pfrom['port_edge'],
                         to_pin_edge=pto['port_edge'],
                         delay_paths=paths)


def add_tcheck(type, pto, pfrom, paths):

    name = type + "_"
    name += pfrom['port'] + "_" + pto['port']
    return prepare_entry(name=name,
                         type=type,
                         is_timing_check=True,
                         is_cond=pfrom['cond'],
                         cond_equation=pfrom['cond_equation'],
                         from_pin=pfrom['port'],
                         to_pin=pto['port'],
                         from_pin_edge=pfrom['port_edge'],
                         to_pin_edge=pto['port_edge'],
                         delay_paths=paths)


def add_constraint(type, pto, pfrom, paths):

    name = type + "_"
    name += pfrom['port'] + "_" + pto['port']
    return prepare_entry(name=name,
                         type=type,
                         is_timing_env=True,
                         from_pin=pfrom['port'],
                         to_pin=pto['port'],
                         from_pin_edge=pfrom['port_edge'],
                         to_pin_edge=pto['port_edge'],
                         delay_paths=paths)
