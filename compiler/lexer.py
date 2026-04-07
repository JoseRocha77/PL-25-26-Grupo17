"""
Fortran 77 Lexer (free-form) using PLY.
"""
import re
import ply.lex

# ---------------------------------------------------------------------------
# Token list
# ---------------------------------------------------------------------------

reserved = {
    'PROGRAM'    : 'PROGRAM',
    'END'        : 'END',
    'INTEGER'    : 'INTEGER',
    'REAL'       : 'REAL',
    'LOGICAL'    : 'LOGICAL',
    'CHARACTER'  : 'CHARACTER',
    'IF'         : 'IF',
    'THEN'       : 'THEN',
    'ELSE'       : 'ELSE',
    'ENDIF'      : 'ENDIF',
    'DO'         : 'DO',
    'CONTINUE'   : 'CONTINUE',
    'GOTO'       : 'GOTO',
    'PRINT'      : 'PRINT',
    'READ'       : 'READ',
    'RETURN'     : 'RETURN',
    'STOP'       : 'STOP',
    'CALL'       : 'CALL',
    'SUBROUTINE' : 'SUBROUTINE',
    'FUNCTION'   : 'FUNCTION',
}

tokens = list(reserved.values()) + [
    # Literals
    'INT_LITERAL',
    'REAL_LITERAL',
    'TRUE',
    'FALSE',
    'STRING_LITERAL',

    # Identifiers
    'ID',

    # Relational operators (Fortran style)
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',

    # Logical operators
    'AND', 'OR', 'NOT',

    # Arithmetic
    'POWER',     # **

    # Punctuation
    'COMMA', 'LPAREN', 'RPAREN', 'EQUALS', 'STAR', 'SLASH',
    'PLUS', 'MINUS', 'COLON',

    # Special
    'LABEL',     # numeric label at start of statement
    'NL',        
    'LABEL_NL',
]

# ---------------------------------------------------------------------------
# Simple tokens
# ---------------------------------------------------------------------------

t_POWER  = r'\*\*'
t_STAR   = r'\*'
t_SLASH  = r'/'
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA  = r','
t_EQUALS = r'='
t_COLON  = r':'

t_ignore = ' \t\r'

# ---------------------------------------------------------------------------
# Fortran logical / relational operators  (.EQ. etc.)
# ---------------------------------------------------------------------------

def t_EQ(t):
    r'\.EQ\.'
    return t

def t_NE(t):
    r'\.NE\.'
    return t

def t_LE(t):
    r'\.LE\.'
    return t

def t_LT(t):
    r'\.LT\.'
    return t

def t_GE(t):
    r'\.GE\.'
    return t

def t_GT(t):
    r'\.GT\.'
    return t

def t_AND(t):
    r'\.AND\.'
    return t

def t_OR(t):
    r'\.OR\.'
    return t

def t_NOT(t):
    r'\.NOT\.'
    return t

def t_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

# ---------------------------------------------------------------------------
# Identifiers and keywords  (case-insensitive)
# ---------------------------------------------------------------------------

def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'ID')
    t.value = t.value.upper()
    return t

# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------

# REAL_LITERAL deve vir antes de INT_LITERAL para não capturar apenas a parte inteira
def t_REAL_LITERAL(t):
    r'[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+'
    t.value = float(t.value)
    return t

def t_STRING_LITERAL(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t

# ---------------------------------------------------------------------------
# Comments (! to end of line, Fortran 90+ style; also C in col 1 — free-form
# ---------------------------------------------------------------------------

def t_COMMENT(t):
    r'!.*'
    pass   # discard

# ---------------------------------------------------------------------------
# Newlines — track line numbers; emit LABEL if line starts with a number
# ---------------------------------------------------------------------------

def t_LABEL_NL(t):
    r'\n\s*[0-9]+'
    # Captura uma nova linha seguida de um número (Label)
    t.lexer.lineno += 1
    # Extraímos apenas o número para o valor do token
    t.value = int(re.search(r'[0-9]+', t.value).group())
    return t

def t_NL(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# INT_LITERAL definido depois de LABEL_NL para evitar conflitos no início de linha
def t_INT_LITERAL(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def t_error(t):
    print(f"[Lexer] Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

lexer = ply.lex.lex(reflags=re.IGNORECASE)

def create_lexer():
    return ply.lex.lex(reflags=re.IGNORECASE)