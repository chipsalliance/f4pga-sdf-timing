import ply.yacc as yacc
import utils

from sdflex import tokens

timings = dict()

header = dict()
delays_list = list()
cells = dict()


def remove_quotation(s):
    return s.replace('"', '')


def p_sdf_file(p):
    '''sdf_file : LPAR DELAYFILE sdf_header RPAR
                | LPAR DELAYFILE sdf_header cell_list RPAR'''

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

    p[0] = p[1]


def p_sdf_header_qstring(p):
    '''sdf_header_qstring : LPAR qstring_header_entry QSTRING RPAR
                          | LPAR qstring_header_entry RPAR'''
    if len(p) == 5:
        header[p[2].lower()] = remove_quotation(p[3])
        p[0] = header


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
    'sdf_header_qfloat : LPAR qfloat_header_entry QFLOAT RPAR'
    if len(p) == 5:
        header[p[2].lower()] = remove_quotation(str(p[3]))
        p[0] = header


def p_qfloat_header_entry(p):
    '''qfloat_header_entry : SDFVERSION
                           | VERSION'''
    p[0] = p[1]


def p_sdf_voltage(p):
    'voltage : LPAR VOLTAGE real_triple RPAR'
    header['voltage'] = p[3]
    p[0] = header


def p_sdf_temperature(p):
    'temperature : LPAR TEMPERATURE real_triple RPAR'
    header['temperature'] = p[3]
    p[0] = header


def p_sdf_divider(p):
    '''hierarchy_divider : LPAR DIVIDER DOT RPAR
               | LPAR DIVIDER SLASH RPAR'''
    header['divider'] = p[3]
    p[0] = header


def p_sdf_timescale(p):
    'timescale : LPAR TIMESCALE FLOAT STRING RPAR'
    header['timescale'] = str(p[3]) + p[4]
    p[0] = header


def p_cell_list(p):
    '''cell_list : cell
                 | cell_list cell'''
    p[0] = p[1]


def add_delays_to_cell(celltype, instance, delays):

    if delays is None:
        return
    for delay in delays:
        cells[celltype][instance][delay['name']] = delay


def add_cell(name, instance):

    # name
    if name not in cells:
        cells[name] = dict()
    # instance
    if instance not in cells[name]:
        cells[name][instance] = dict()


def p_timing_cell(p):
    '''cell : LPAR CELL celltype instance timing_check RPAR
            | LPAR CELL celltype instance RPAR
            | LPAR CELL celltype instance delay timing_check RPAR
            | LPAR CELL celltype instance delay RPAR'''

    add_cell(p[3], p[4])
    add_delays_to_cell(p[3], p[4], delays_list)
    p[0] = cells
    delays_list[:] = []


def p_celltype(p):
    'celltype : LPAR CELLTYPE QSTRING RPAR'
    p[0] = remove_quotation(p[3])


def p_instance(p):
    '''instance : LPAR INSTANCE STRING RPAR
                | LPAR INSTANCE RPAR'''
    if p[3] == ')':
        p[0] = None
    else:
        p[0] = p[3]


def p_timing_check(p):
    '''timing_check : LPAR TIMINGCHECK timing_check_list RPAR'''


def p_timing_check_list(p):
    '''timing_check_list : t_check
                         | timing_check_list t_check'''


def p_t_check(p):
    '''t_check : removal_check
               | recovery_check
               | hold_check
               | setup_check
               | width_check
               | setuphold_check'''


def p_removal_check(p):
    'removal_check : LPAR REMOVAL port_spec port_spec real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('removal', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_recovery_check(p):
    'recovery_check : LPAR RECOVERY port_spec port_spec real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('recovery', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_hold_check(p):
    'hold_check : LPAR HOLD port_spec port_spec real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('hold', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_setup_check(p):
    'setup_check : LPAR SETUP port_spec port_spec real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('setup', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_width_check(p):
    'width_check : LPAR WIDTH port_spec real_triple RPAR'

    paths = dict()
    paths['nominal'] = p[5]
    tcheck = utils.add_tcheck('width', p[3], p[3], paths)
    delays_list.append(tcheck)


def p_setuphold_check(p):
    'setuphold_check : LPAR SETUPHOLD port_spec port_spec real_triple \
    real_triple RPAR'

    paths = dict()
    paths['setup'] = p[5]
    paths['hold'] = p[6]
    tcheck = utils.add_tcheck('setup', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_path_constraint(p):
    'path_constraint : LPAR PATHCONSTRAINT port_spec port_spec real_triple \
    real_triple RPAR'

    paths = dict()
    paths['rise'] = p[5]
    paths['fall'] = p[6]
    tcheck = utils.add_tcheck('pathconstraint', p[3], p[4], paths)
    delays_list.append(tcheck)


def p_delay(p):
    'delay : LPAR DELAY absolute RPAR'


def p_absolute_empty(p):
    'absolute : LPAR ABSOLUTE RPAR'


def p_absolute_list(p):
    'absolute : LPAR ABSOLUTE delay_list RPAR'


def p_delay_list_interconnect(p):
    '''delay_list : del
                  | delay_list del'''


def p_del(p):
    '''del : interconnect
           | iopath
           | port'''


def p_iopath(p):
    'iopath : LPAR IOPATH port_spec port_spec real_triple real_triple RPAR'
    paths = dict()
    paths['fast'] = p[5]
    paths['slow'] = p[6]
    iopath = utils.add_iopath(p[3], p[4], paths)
    delays_list.append(iopath)


def p_port_spec(p):
    '''port_spec : STRING
                 | LPAR port_condition STRING RPAR
                 | FLOAT'''

    if p[1] != '(':
        p[0] = str(p[1])
    else:
        p[0] = p[3]


def p_interconnect(p):
    'interconnect : LPAR INTERCONNECT port_spec port_spec real_triple \
    real_triple RPAR'
    paths = dict()
    paths['fast'] = p[5]
    paths['slow'] = p[6]
    interconnect = utils.add_interconnect(p[3], p[4], paths)
    delays_list.append(interconnect)


def p_interconnect_single(p):
    'interconnect : LPAR INTERCONNECT port_spec port_spec real_triple \
    RPAR'
    paths = dict()
    paths['nominal'] = p[5]
    interconnect = utils.add_interconnect(p[3], p[4], paths)
    delays_list.append(interconnect)


def p_port_single(p):
    'port : LPAR PORT port_spec real_triple RPAR'
    paths = dict()
    paths['nominal'] = p[4]
    port = utils.add_port(p[3], paths)
    delays_list.append(port)


def p_port(p):
    'port : LPAR PORT port_spec real_triple real_triple RPAR'
    paths = dict()
    paths['fast'] = p[4]
    paths['slow'] = p[5]
    port = utils.add_port(p[3], paths)
    delays_list.append(port)


def p_port_condition(p):
    '''port_condition : POSEDGE
                      | NEGEDGE'''
    p[0] = p[1]


def p_real_triple_no_par(p):
    '''real_triple : FLOAT COLON FLOAT COLON FLOAT
                   | FLOAT COLON COLON FLOAT
                   | COLON FLOAT COLON'''
    delays_triple = dict()
    if len(p) > 4:
        if p[3] == ':':
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = None
            delays_triple['max'] = float(p[4])
        else:
            delays_triple['min'] = float(p[1])
            delays_triple['avg'] = float(p[3])
            delays_triple['max'] = float(p[5])
    else:
        delays_triple['min'] = None
        delays_triple['avg'] = p[2]
        delays_triple['max'] = None

    p[0] = delays_triple


def p_real_triple(p):
    '''real_triple : LPAR FLOAT COLON FLOAT COLON FLOAT RPAR
                   | LPAR RPAR
                   | LPAR FLOAT COLON COLON FLOAT RPAR
                   | LPAR COLON FLOAT COLON RPAR'''

    delays_triple = dict()
    if len(p) > 3:
        if p[4] == ':':
            if p[2] == ':':
                delays_triple['min'] = None
                delays_triple['avg'] = float(p[3])
                delays_triple['max'] = None
            else:
                delays_triple['min'] = float(p[2])
                delays_triple['avg'] = None
                delays_triple['max'] = float(p[5])
        else:
            delays_triple['min'] = float(p[2])
            delays_triple['avg'] = float(p[4])
            delays_triple['max'] = float(p[6])
    else:
        delays_triple['min'] = None
        delays_triple['avg'] = None
        delays_triple['max'] = None

    p[0] = delays_triple


def p_error(p):
    raise Exception("Syntax error at '%s' line: %d" % (p.value, p.lineno))


parser = yacc.yacc()
