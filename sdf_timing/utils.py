

def prepare_entry(name=None,
                  type=None,
                  from_pin=None,
                  to_pin=None,
                  from_pin_condition=None,
                  to_pin_condition=None,
                  delay_paths=None,
                  is_timing_check=False,
                  is_absolute=False,
                  is_incremental=False,
                  is_cond=False):

    entry = dict()
    entry['name'] = name
    entry['type'] = type
    entry['from_pin'] = from_pin
    entry['to_pin'] = to_pin
    entry['delay_paths'] = delay_paths
    entry['is_timing_check'] = is_timing_check
    entry['is_absolute'] = is_absolute
    entry['is_incremental'] = is_incremental
    entry['is_cond'] = is_cond

    return entry


def add_port(portname, paths):

    name = "port_" + portname
    return prepare_entry(name=name,
                         type='port',
                         is_absolute=True,
                         from_pin=portname,
                         to_pin=portname,
                         delay_paths=paths)


def add_interconnect(pfrom, pto, paths):

    name = "interconnect_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type='interconnect',
                         is_absolute=True,
                         from_pin=pfrom,
                         to_pin=pto,
                         delay_paths=paths)


def add_iopath(pfrom, pto, paths):

    name = "iopath_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type='iopath',
                         is_absolute=True,
                         from_pin=pfrom,
                         to_pin=pto,
                         delay_paths=paths)


def add_tcheck(type, pfrom, pto, paths):

    name = type + "_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type=type,
                         is_timing_check=True,
                         from_pin=pfrom,
                         to_pin=pto,
                         delay_paths=paths)
