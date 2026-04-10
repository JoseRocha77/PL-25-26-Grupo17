"""
Fortran 77 Parser (free-form) using PLY.
"""
import ply.yacc
from .lexer import tokens, create_lexer
from .ast import *

# ---------------------------------------------------------------------------
# Precedence
# ---------------------------------------------------------------------------

precedence = (
    ('left',  'OR'),
    ('left',  'AND'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'STAR', 'SLASH'),
    ('right', 'UMINUS'),
    ('right', 'POWER'),
)

# ---------------------------------------------------------------------------
# Newlines
# ---------------------------------------------------------------------------

def p_nls(p):
    """nls : NL
           | nls NL"""
    p[0] = None

# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------

def p_program(p):
    """program : unit_list"""
    main = next((u for u in p[1] if u.kind == 'program'), p[1][0])
    p[0] = Program(name=main.name, units=p[1])

def p_unit_list_one(p):
    """unit_list : unit"""
    p[0] = [p[1]]

def p_unit_list_many(p):
    """unit_list : unit_list unit"""
    p[0] = p[1] + [p[2]]

# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

def p_unit_program(p):
    """unit : PROGRAM ID nls decl_list stmt_list END nls
            | PROGRAM ID nls decl_list stmt_list END"""
    p[0] = ProgramUnit(kind='program', name=p[2], params=[],
                       return_type=None, declarations=p[4], body=p[5])

def p_unit_subroutine(p):
    """unit : SUBROUTINE ID LPAREN param_list RPAREN nls decl_list stmt_list END nls
            | SUBROUTINE ID LPAREN param_list RPAREN nls decl_list stmt_list END"""
    p[0] = ProgramUnit(kind='subroutine', name=p[2], params=p[4],
                       return_type=None, declarations=p[7], body=p[8])

def p_unit_function(p):
    """unit : type_spec FUNCTION ID LPAREN param_list RPAREN nls decl_list stmt_list END nls
            | type_spec FUNCTION ID LPAREN param_list RPAREN nls decl_list stmt_list END"""
    p[0] = ProgramUnit(kind='function', name=p[3], params=p[5],
                       return_type=p[1], declarations=p[8], body=p[9])

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def p_param_list_empty(p):
    """param_list :"""
    p[0] = []

def p_param_list_one(p):
    """param_list : ID"""
    p[0] = [p[1]]

def p_param_list_many(p):
    """param_list : param_list COMMA ID"""
    p[0] = p[1] + [p[3]]

# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

def p_decl_list_empty(p):
    """decl_list :"""
    p[0] = []

def p_decl_list_many(p):
    """decl_list : decl_list decl"""
    p[0] = p[1] + [p[2]]

def p_decl(p):
    """decl : type_spec vardecl_list nls"""
    p[0] = Declaration(var_type=p[1], variables=p[2])

def p_type_spec(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL
                 | CHARACTER"""
    mapping = {
        'INTEGER':   FortranType.INTEGER,
        'REAL':      FortranType.REAL,
        'LOGICAL':   FortranType.LOGICAL,
        'CHARACTER': FortranType.CHARACTER,
    }
    p[0] = mapping[p[1]]

def p_vardecl_list_one(p):
    """vardecl_list : vardecl"""
    p[0] = [p[1]]

def p_vardecl_list_many(p):
    """vardecl_list : vardecl_list COMMA vardecl"""
    p[0] = p[1] + [p[3]]

def p_vardecl_scalar(p):
    """vardecl : ID"""
    p[0] = VarDecl(name=p[1], dimensions=[])

def p_vardecl_array(p):
    """vardecl : ID LPAREN dim_list RPAREN"""
    p[0] = VarDecl(name=p[1], dimensions=p[3])

def p_dim_list_one(p):
    """dim_list : INT_LITERAL"""
    p[0] = [p[1]]

def p_dim_list_many(p):
    """dim_list : dim_list COMMA INT_LITERAL"""
    p[0] = p[1] + [p[3]]

# ---------------------------------------------------------------------------
# Statement list — termina quando encontra END, ELSE, ENDIF
# ou um INT_LITERAL seguido de CONTINUE (fim de DO)
# ---------------------------------------------------------------------------

def p_stmt_list_empty(p):
    """stmt_list :"""
    p[0] = []

def p_stmt_list_many(p):
    """stmt_list : stmt_list stmt"""
    p[0] = p[1] + ([p[2]] if p[2] is not None else [])

# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

def p_stmt_blank(p):
    """stmt : nls"""
    p[0] = None

# Atribuição escalar:  [label] VAR = expr NL
def p_stmt_assign(p):
    """stmt : opt_label ID EQUALS expr nls"""
    p[0] = AssignStmt(label=p[1], target=VarRef(name=p[2]), value=p[4])

# Atribuição array:  [label] VAR(idx,...) = expr NL
def p_stmt_assign_array(p):
    """stmt : opt_label ID LPAREN expr_list RPAREN EQUALS expr nls"""
    p[0] = AssignStmt(label=p[1],
                      target=VarRef(name=p[2], indices=p[4]),
                      value=p[7])

# PRINT *, item, item, ...
def p_stmt_print(p):
    """stmt : opt_label PRINT STAR COMMA expr_list nls"""
    p[0] = PrintStmt(label=p[1], items=p[5])

def p_stmt_print_empty(p):
    """stmt : opt_label PRINT STAR nls"""
    p[0] = PrintStmt(label=p[1], items=[])

# READ *, var, var, ...
def p_stmt_read(p):
    """stmt : opt_label READ STAR COMMA expr_list nls"""
    targets = []
    for e in p[5]:
        if isinstance(e, VarRef):
            targets.append(e)
        elif isinstance(e, FunctionCall):
            # NUMS(I) é parseado como FunctionCall mas é acesso a array
            targets.append(VarRef(name=e.name, indices=e.args))
    p[0] = ReadStmt(label=p[1], targets=targets)
    
# IF-THEN-ENDIF
def p_stmt_if(p):
    """stmt : opt_label IF LPAREN expr RPAREN THEN nls stmt_list ENDIF nls"""
    p[0] = IfStmt(label=p[1], condition=p[4], then_body=p[8], else_body=[])

# IF-THEN-ELSE-ENDIF
def p_stmt_if_else(p):
    """stmt : opt_label IF LPAREN expr RPAREN THEN nls stmt_list ELSE nls stmt_list ENDIF nls"""
    p[0] = IfStmt(label=p[1], condition=p[4], then_body=p[8], else_body=p[11])

# IF (...) GOTO label  — Fortran logical IF
def p_stmt_if_goto(p):
    """stmt : opt_label IF LPAREN expr RPAREN GOTO INT_LITERAL nls"""
    p[0] = IfStmt(label=p[1], condition=p[4],
                  then_body=[GotoStmt(label=None, target=p[7])],
                  else_body=[])

# IF (...) stmt  — Fortran logical IF com qualquer statement simples
def p_stmt_if_inline(p):
    """stmt : opt_label IF LPAREN expr RPAREN inline_stmt"""
    p[0] = IfStmt(label=p[1], condition=p[4],
                  then_body=[p[6]], else_body=[])

# Statements simples que podem aparecer depois de IF (...)
def p_inline_stmt_assign(p):
    """inline_stmt : ID EQUALS expr nls"""
    p[0] = AssignStmt(label=None, target=VarRef(name=p[1]), value=p[3])

def p_inline_stmt_goto(p):
    """inline_stmt : GOTO INT_LITERAL nls"""
    p[0] = GotoStmt(label=None, target=p[2])

def p_inline_stmt_stop(p):
    """inline_stmt : STOP nls"""
    p[0] = StopStmt(label=None)

# DO loop:  DO label VAR = start, stop [, step] NL  body  label CONTINUE NL
def p_stmt_do(p):
    """stmt : opt_label DO INT_LITERAL ID EQUALS expr COMMA expr nls do_body"""
    end_lbl, body = p[10]
    if p[3] != end_lbl:
        print(f"[Parser Warning] DO label {p[3]} != CONTINUE label {end_lbl}")
    p[0] = DoStmt(label=p[1], end_label=p[3], var=p[4],
                  start=p[6], stop=p[8], step=None, body=body)

def p_stmt_do_step(p):
    """stmt : opt_label DO INT_LITERAL ID EQUALS expr COMMA expr COMMA expr nls do_body"""
    end_lbl, body = p[12]
    if p[3] != end_lbl:
        print(f"[Parser Warning] DO label {p[3]} != CONTINUE label {end_lbl}")
    p[0] = DoStmt(label=p[1], end_label=p[3], var=p[4],
                  start=p[6], stop=p[8], step=p[10], body=body)

# do_body: zero ou mais statements, terminando com INT_LITERAL CONTINUE NL
def p_do_body(p):
    """do_body : stmt_list INT_LITERAL CONTINUE nls"""
    p[0] = (p[2], p[1])  # (label_do_continue, lista_de_stmts)

def p_stmt_goto(p):
    """stmt : opt_label GOTO INT_LITERAL nls"""
    p[0] = GotoStmt(label=p[1], target=p[3])

def p_stmt_continue(p):
    """stmt : opt_label CONTINUE nls"""
    p[0] = ContinueStmt(label=p[1])

def p_stmt_return(p):
    """stmt : opt_label RETURN nls"""
    p[0] = ReturnStmt(label=p[1])

def p_stmt_stop(p):
    """stmt : opt_label STOP nls"""
    p[0] = StopStmt(label=p[1])

def p_stmt_call_args(p):
    """stmt : opt_label CALL ID LPAREN expr_list RPAREN nls"""
    p[0] = CallStmt(label=p[1], name=p[3], args=p[5])

def p_stmt_call_noargs(p):
    """stmt : opt_label CALL ID nls"""
    p[0] = CallStmt(label=p[1], name=p[3], args=[])

def p_opt_label_none(p):
    """opt_label :"""
    p[0] = None

def p_opt_label_int(p):
    """opt_label : INT_LITERAL"""
    p[0] = p[1]

# ---------------------------------------------------------------------------
# Expression list
# ---------------------------------------------------------------------------

def p_expr_list_one(p):
    """expr_list : expr"""
    p[0] = [p[1]]

def p_expr_list_many(p):
    """expr_list : expr_list COMMA expr"""
    p[0] = p[1] + [p[3]]

# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

def p_expr_binop(p):
    """expr : expr PLUS  expr
            | expr MINUS expr
            | expr STAR  expr
            | expr SLASH expr
            | expr POWER expr
            | expr EQ    expr
            | expr NE    expr
            | expr LT    expr
            | expr LE    expr
            | expr GT    expr
            | expr GE    expr
            | expr AND   expr
            | expr OR    expr"""
    p[0] = BinaryExpr(op=p[2], left=p[1], right=p[3])

def p_expr_uminus(p):
    """expr : MINUS expr %prec UMINUS"""
    p[0] = UnaryExpr(op='-', operand=p[2])

def p_expr_not(p):
    """expr : NOT expr"""
    p[0] = UnaryExpr(op='.NOT.', operand=p[2])

def p_expr_paren(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

def p_expr_int(p):
    """expr : INT_LITERAL"""
    p[0] = IntLiteral(value=p[1])

def p_expr_real(p):
    """expr : REAL_LITERAL"""
    p[0] = RealLiteral(value=p[1])

def p_expr_true(p):
    """expr : TRUE"""
    p[0] = LogicalLiteral(value=True)

def p_expr_false(p):
    """expr : FALSE"""
    p[0] = LogicalLiteral(value=False)

def p_expr_string(p):
    """expr : STRING_LITERAL"""
    p[0] = StringLiteral(value=p[1])

def p_expr_funcall(p):
    """expr : ID LPAREN expr_list RPAREN"""
    p[0] = FunctionCall(name=p[1], args=p[3])

def p_expr_var(p):
    """expr : ID"""
    p[0] = VarRef(name=p[1])

# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

def p_error(p):
    if p:
        print(f"[Parser] Erro de sintaxe em '{p.value}' (linha {p.lineno})")
    else:
        print("[Parser] Erro de sintaxe no fim do ficheiro (EOF)")

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

parser = ply.yacc.yacc(start='program')

def parse(source: str):
    lx = create_lexer()
    return parser.parse(source, lexer=lx)