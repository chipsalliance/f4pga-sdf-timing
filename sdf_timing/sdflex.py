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
}

tokens = (
    'LPAR',
    'RPAR',
    'DOT',
    'SLASH',
    'COLON',
    'FLOAT',
    'QFLOAT',
    'QSTRING',
    'STRING',
) + tuple(reserved.values())

t_LPAR = r'\('
t_RPAR = r'\)'
t_COLON = r':'
t_QFLOAT = r'\"[-+]?(?: [0-9]+)(?: \.[0-9]+)\"'
t_QSTRING = r'\"[a-zA-Z0-9_/.,: ]+\"'

t_ignore = ' \t'


# define FLOAT as function so it takes precendence over STRING
def t_FLOAT(t):
    r'[-]?\.?[0-9]+(\.[0-9]+)?'
    return t

# the same for dot and slash
def t_DOT(t):
    r'\.'
    return t


def t_SLASH(t):
    r'\/'
    return t


def t_STRING(t):
    r'[a-zA-Z0-9_/.\[\]]+'
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
