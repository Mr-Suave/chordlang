import ply.lex as lex

# Reserved keywords
reserved = {
    'tempo': 'TEMPO',
    'volume': 'VOLUME',
    'sequence': 'SEQUENCE',
    'chord': 'CHORD',
    'play': 'PLAY',
    'repeat': 'REPEAT',
    'times': 'TIMES',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'rest': 'REST',
    'instrument': 'INSTRUMENT'
}

# Token list
tokens = [
    'IDENTIFIER',
    'INTEGER',
    'NOTE_LITERAL',
    'ASSIGN',
    'GT',
    'LT',
    'GTE',
    'LTE',
    'EQ',
    'NEQ',
    'PLUS',
    'MINUS',
    'MODULO',
    'LBRACE',
    'RBRACE',
    'COMMA',
    'COLON'
] + list(reserved.values())

# Token rules
t_ASSIGN = r'='
t_GTE = r'>='
t_LTE = r'<='
t_EQ = r'=='
t_NEQ = r'!='
t_GT = r'>'
t_LT = r'<'
t_PLUS = r'\+'
t_MINUS = r'-'
t_MODULO = r'%'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_COLON = r':'

# Note literal with optional duration
def t_NOTE_LITERAL(t):
    r'[A-Za-z]+[#b]?[0-9]+(:-?[0-9]+)?'
    return t

# Identifier (note to self: must come after NOTE_LITERAL to avoid conflicts)
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# Integer
def t_INTEGER(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Ignored characters (whitespace)
t_ignore = ' \t'

# Newline handling
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Comment handling
def t_COMMENT(t):
    r'\#.*'
    pass  # Ignore comments

# Error handling
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()
