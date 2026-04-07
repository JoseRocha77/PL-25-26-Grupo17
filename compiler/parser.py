"""
Fortran 77 Parser (free-form) using PLY.
Builds an AST defined in ast.py.
"""
import ply.yacc
from .lexer import tokens, create_lexer
from .ast import *

# ---------------------------------------------------------------------------
# Precedence / associativity
# ---------------------------------------------------------------------------

precedence = (
    ('left',  'OR'),
    ('left',  'AND'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'STAR', 'SLASH'),
    ('right', 'UMINUS', 'UPLUS'),
    ('right', 'POWER'),
)

# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

def p_program(p):
    """program : program_unit_list"""
    main = next((u for u in p[1] if u.kind == 'program'), p[1][0])
    p[0] = Program(name=main.name, units=p[1])

def p_program_unit_list(p):
    """program_unit_list : program_unit_list program_unit
                         | program_unit"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# ---------------------------------------------------------------------------
# Program / Function / Subroutine units
# ---------------------------------------------------------------------------

def p_program_unit_program(p):
    """program_unit : PROGRAM ID newlines declaration_list statement_list END newlines
                    | PROGRAM ID newlines declaration_list statement_list END"""
    p[0] = ProgramUnit(
        kind='program', name=p[2], params=[],
        return_type=None,
        declarations=p[4], body=p[5]
    )

def p_program_unit_function(p):
    """program_unit : type_spec FUNCTION ID LPAREN param_list RPAREN newlines declaration_list statement_list END newlines"""
    p[0] = ProgramUnit(
        kind='function', name=p[3], params=p[5],
        return_type=p[1],
        declarations=p[8], body=p[9]
    )

def p_program_unit_subroutine(p):
    """program_unit : SUBROUTINE ID LPAREN param_list RPAREN newlines declaration_list statement_list END newlines"""
    p[0] = ProgramUnit(
        kind='subroutine', name=p[2], params=p[4],
        return_type=None,
        declarations=p[7], body=p[8]
    )

# ---------------------------------------------------------------------------
# Newlines (Separadores obrigatórios)
# ---------------------------------------------------------------------------

def p_newlines(p):
    """newlines : NL
                | newlines NL"""
    p[0] = None

# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

def p_declaration_list(p):
    """declaration_list : declaration_list declaration
                        | """
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_declaration(p):
    """declaration : type_spec var_decl_list NL
                   | type_spec var_decl_list LABEL_NL"""
    p[0] = Declaration(var_type=p[1], variables=p[2])

def p_type_spec(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL
                 | CHARACTER"""
    mapping = {
        'INTEGER': FortranType.INTEGER,
        'REAL': FortranType.REAL,
        'LOGICAL': FortranType.LOGICAL,
        'CHARACTER': FortranType.CHARACTER
    }
    p[0] = mapping[p[1]]

def p_var_decl_list(p):
    """var_decl_list : var_decl_list COMMA var_decl
                     | var_decl"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_var_decl(p):
    """var_decl : ID
                | ID LPAREN dim_list RPAREN"""
    if len(p) == 2:
        p[0] = VarDecl(name=p[1], dimensions=[])
    else:
        p[0] = VarDecl(name=p[1], dimensions=p[3])

def p_dim_list(p):
    """dim_list : dim_list COMMA INT_LITERAL
                | INT_LITERAL"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# ---------------------------------------------------------------------------
# Parameter list
# ---------------------------------------------------------------------------

def p_param_list(p):
    """param_list : param_list COMMA ID
                  | ID
                  | """
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = []

# ---------------------------------------------------------------------------
# Statement list
# ---------------------------------------------------------------------------

def p_statement_list(p):
    """statement_list : statement_list statement
                      | """
    if len(p) == 3:
        p[0] = p[1] + ([p[2]] if p[2] is not None else [])
    else:
        p[0] = []

# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

def p_statement_separator(p):
    """stmt_end : NL
                | LABEL_NL"""
    p[0] = p[1] if isinstance(p[1], int) else None

def p_statement_assign(p):
    """statement : opt_label ID EQUALS expr stmt_end
                 | opt_label ID LPAREN index_list RPAREN EQUALS expr stmt_end"""
    lbl = p[1] if p[1] else p[len(p)-1]
    if len(p) == 6:
        p[0] = AssignStmt(label=lbl, target=VarRef(name=p[2]), value=p[4])
    else:
        p[0] = AssignStmt(label=lbl, target=VarRef(name=p[2], indices=p[4]), value=p[7])

def p_statement_print(p):
    """statement : opt_label PRINT STAR COMMA print_list stmt_end
                 | opt_label PRINT STAR stmt_end"""
    lbl = p[1] if p[1] else p[len(p)-1]
    items = p[5] if len(p) == 7 else []
    p[0] = PrintStmt(label=lbl, items=items)

def p_print_list(p):
    """print_list : print_list COMMA expr
                  | expr"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_statement_read(p):
    """statement : opt_label READ STAR COMMA read_list stmt_end"""
    lbl = p[1] if p[1] else p[6]
    p[0] = ReadStmt(label=lbl, targets=p[5])

def p_read_list(p):
    """read_list : read_list COMMA var_ref
                 | var_ref"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_statement_if_then(p):
    """statement : opt_label IF LPAREN expr RPAREN THEN NL statement_list ENDIF stmt_end
                 | opt_label IF LPAREN expr RPAREN THEN NL statement_list ELSE NL statement_list ENDIF stmt_end"""
    lbl = p[1]
    if len(p) == 11:
        p[0] = IfStmt(label=lbl, condition=p[4], then_body=p[8], else_body=[])
    else:
        p[0] = IfStmt(label=lbl, condition=p[4], then_body=p[8], else_body=p[11])

def p_statement_do(p):
    """statement : opt_label DO INT_LITERAL ID EQUALS expr COMMA expr stmt_end statement_list INT_LITERAL CONTINUE stmt_end"""
    p[0] = DoStmt(label=p[1], end_label=p[3], var=p[4], start=p[6], stop=p[8], step=None, body=p[10])

def p_statement_goto(p):
    """statement : opt_label GOTO INT_LITERAL stmt_end"""
    p[0] = GotoStmt(label=p[1], target=p[3])

def p_statement_continue(p):
    """statement : opt_label CONTINUE stmt_end"""
    lbl = p[1] if p[1] else p[3]
    p[0] = ContinueStmt(label=lbl)

def p_opt_label(p):
    """opt_label : INT_LITERAL
                 | """
    p[0] = p[1] if len(p) == 2 else None

# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

def p_expr_binop(p):
    """expr : expr PLUS   expr
            | expr MINUS  expr
            | expr STAR   expr
            | expr SLASH  expr
            | expr POWER  expr
            | expr EQ     expr
            | expr NE     expr
            | expr LT     expr
            | expr LE     expr
            | expr GT     expr
            | expr GE     expr
            | expr AND    expr
            | expr OR     expr"""
    p[0] = BinaryExpr(op=p[2], left=p[1], right=p[3])

def p_expr_unary(p):
    """expr : MINUS expr %prec UMINUS
            | PLUS expr %prec UPLUS
            | NOT expr"""
    if p[1] == '-':
        p[0] = UnaryExpr(op='-', operand=p[2])
    elif p[1] == '+':
        p[0] = p[2]
    else:
        p[0] = UnaryExpr(op='.NOT.', operand=p[2])

def p_expr_group(p):
    """expr : LPAREN expr RPAREN
            | INT_LITERAL
            | REAL_LITERAL
            | TRUE
            | FALSE
            | STRING_LITERAL
            | var_ref"""
    if len(p) == 4:
        p[0] = p[2]
    else:
        if isinstance(p[1], VarRef):
            p[0] = p[1]
        elif isinstance(p[1], bool):
            p[0] = LogicalLiteral(value=p[1])
        elif isinstance(p[1], int):
            p[0] = IntLiteral(value=p[1])
        elif isinstance(p[1], float):
            p[0] = RealLiteral(value=p[1])
        else:
            p[0] = StringLiteral(value=p[1])

def p_var_ref(p):
    """var_ref : ID
               | ID LPAREN index_list RPAREN"""
    if len(p) == 2:
        p[0] = VarRef(name=p[1])
    else:
        p[0] = VarRef(name=p[1], indices=p[3])

def p_index_list(p):
    """index_list : index_list COMMA expr
                  | expr"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_error(p):
    if p:
        print(f"[Parser] Erro de sintaxe em '{p.value}' (linha {p.lineno})")
    else:
        print("[Parser] Erro de sintaxe no fim do ficheiro (EOF)")

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

parser = ply.yacc.yacc()

def parse(source: str):
    lx = create_lexer()
    return parser.parse(source, lexer=lx)