

def prepare_entry(name=None,
                  type=None,
                  from_pin=None,
                  to_pin=None,
                  from_pin_condition=None,
                  to_pin_condition=None,
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
    entry['delay_paths'] = delay_paths
    entry['is_timing_check'] = is_timing_check
    entry['is_timing_env'] = is_timing_env
    entry['is_absolute'] = is_absolute
    entry['is_incremental'] = is_incremental
    entry['is_cond'] = is_cond
    entry['cond_equation'] = cond_equation

    return entry


def add_port(portname, paths):

    name = "port_" + portname
    return prepare_entry(name=name,
                         type='port',
                         from_pin=portname,
                         to_pin=portname,
                         delay_paths=paths)


def add_interconnect(pfrom, pto, paths):

    name = "interconnect_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type='interconnect',
                         from_pin=pfrom,
                         to_pin=pto,
                         delay_paths=paths)


def add_iopath(pfrom, pto, paths):

    name = "iopath_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type='iopath',
                         from_pin=pfrom,
                         to_pin=pto,
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
                         delay_paths=paths)


def add_constraint(type, pto, pfrom, paths):

    name = type + "_"
    name += pfrom + "_" + pto
    return prepare_entry(name=name,
                         type=type,
                         is_timing_env=True,
                         from_pin=pfrom,
                         to_pin=pto,
                         delay_paths=paths)
