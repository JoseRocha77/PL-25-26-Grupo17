"""
EWVM code generator for Fortran 77.
"""
from .ast import *
from .symboltable import SymbolTable

class CodeGenError(Exception):
    pass

class CodeGenerator:
    def __init__(self):
        self.code: list[str] = []
        self._label_counter = 0
        self._unit_name = None
        self._sym: SymbolTable | None = None

    def generate(self, program: Program) -> str:
        self._sym = SymbolTable()
        for unit in program.units:
            if unit.kind != 'program':
                self._sym.add_function(unit)
        main = next((u for u in program.units if u.kind == 'program'), None)
        subs = [u for u in program.units if u.kind != 'program']
        if main:
            self._gen_unit(main)
        for sub in subs:
            self._gen_unit(sub)
        return '\n'.join(self.code)

    def _gen_unit(self, unit: ProgramUnit):
        self._unit_name = unit.name.upper()
        self._sym.push_scope()

        if unit.kind == 'program':
            self._emit('START')
        else:
            self._label(f'F{self._unit_name}')

        offset = 0

        if unit.return_type is not None:
            ret_decl = VarDecl(name=unit.name.upper(), dimensions=[],
                               is_global=False, scope_offset=offset)
            self._sym.add_variable(ret_decl, unit.return_type)
            self._push_default(unit.return_type)
            offset += 1

        param_offset = -(len(unit.params))
        for pname in unit.params:
            pd = VarDecl(name=pname.upper(), dimensions=[], is_global=False,
                         scope_offset=param_offset)
            try:
                self._sym.add_variable(pd, FortranType.INTEGER)
            except Exception:
                pass
            param_offset += 1

        for decl in unit.declarations:
            for vd in decl.variables:
                vd.is_global = (unit.kind == 'program')
                vd.scope_offset = offset
                size = 1
                for d in vd.dimensions:
                    size *= d
                try:
                    self._sym.add_variable(vd, decl.var_type)
                except Exception:
                    pass
                if len(vd.dimensions) == 0:
                    self._push_default(decl.var_type)
                    offset += 1
                else:
                    self._emit(f'ALLOC {size}')
                    offset += 1

        for stmt in unit.body:
            self._gen_stmt(stmt)

        if unit.kind == 'program':
            self._emit('STOP')
        else:
            self._emit('RETURN')

        self._sym.pop_scope()

    def _gen_stmt(self, stmt: Statement):
        lbl = getattr(stmt, 'label', None)
        if lbl is not None:
            self._label(self._stmt_label(lbl))

        if isinstance(stmt, AssignStmt):
            self._gen_expr(stmt.value)
            self._store_varref(stmt.target)

        elif isinstance(stmt, PrintStmt):
            for item in stmt.items:
                self._gen_expr(item)
                self._emit_write(item)
            self._emit('WRITELN')

        elif isinstance(stmt, ReadStmt):
            for target in stmt.targets:
                decl = self._sym.lookup_var(target.name)
                sym  = self._sym.lookup(target.name)
                if len(target.indices) > 0 and decl is not None:
                    # Array: precisa de [base_ptr, offset, valor] para STOREN
                    instr = 'PUSHL' if not decl.is_global else 'PUSHG'
                    self._emit(f'{instr} {decl.scope_offset}')
                    self._gen_expr(target.indices[0])
                    self._emit('PUSHI 1')
                    self._emit('SUB')
                    if sym and sym.sym_type == FortranType.REAL:
                        self._emit('READ')
                        self._emit('ATOF')
                    else:
                        self._emit('READ')
                        self._emit('ATOI')
                    self._emit('STOREN')
                else:
                    if sym and sym.sym_type == FortranType.REAL:
                        self._emit('READ')
                        self._emit('ATOF')
                    else:
                        self._emit('READ')
                        self._emit('ATOI')
                    self._store_varref(target)

        elif isinstance(stmt, IfStmt):
            else_lbl = self._new_label('ELSE')
            end_lbl  = self._new_label('ENDIF')
            self._gen_expr(stmt.condition)
            self._emit(f'JZ {else_lbl}')
            for s in stmt.then_body:
                self._gen_stmt(s)
            self._emit(f'JUMP {end_lbl}')
            self._label(else_lbl)
            for s in stmt.else_body:
                self._gen_stmt(s)
            self._label(end_lbl)

        elif isinstance(stmt, DoStmt):
            start_lbl = self._new_label('DOSTART')
            end_lbl   = self._new_label('DOEND')
            self._gen_expr(stmt.start)
            self._store_name(stmt.var)
            self._label(start_lbl)
            self._load_name(stmt.var)
            self._gen_expr(stmt.stop)
            self._emit('INFEQ')
            self._emit(f'JZ {end_lbl}')
            for s in stmt.body:
                self._gen_stmt(s)
            self._load_name(stmt.var)
            if stmt.step:
                self._gen_expr(stmt.step)
            else:
                self._emit('PUSHI 1')
            self._emit('ADD')
            self._store_name(stmt.var)
            self._emit(f'JUMP {start_lbl}')
            self._label(end_lbl)

        elif isinstance(stmt, GotoStmt):
            self._emit(f'JUMP {self._stmt_label(stmt.target)}')

        elif isinstance(stmt, ContinueStmt):
            pass

        elif isinstance(stmt, ReturnStmt):
            self._emit('RETURN')

        elif isinstance(stmt, StopStmt):
            self._emit('STOP')

        elif isinstance(stmt, CallStmt):
            for arg in stmt.args:
                self._gen_expr(arg)
            self._emit(f'CALL F{stmt.name.upper()}')
            if stmt.args:
                self._emit(f'POP {len(stmt.args)}')

    def _gen_expr(self, expr: Expression):
        if isinstance(expr, IntLiteral):
            self._emit(f'PUSHI {expr.value}')
        elif isinstance(expr, RealLiteral):
            self._emit(f'PUSHF {expr.value:.10f}')
        elif isinstance(expr, LogicalLiteral):
            self._emit(f'PUSHI {1 if expr.value else 0}')
        elif isinstance(expr, StringLiteral):
            escaped = expr.value.replace('"', '')
            self._emit(f'PUSHS "{escaped}"')
        elif isinstance(expr, VarRef):
            self._load_varref(expr)
        elif isinstance(expr, BinaryExpr):
            self._gen_expr(expr.left)
            self._gen_expr(expr.right)
            self._emit(self._binop_instr(expr.op))
        elif isinstance(expr, UnaryExpr):
            self._gen_expr(expr.operand)
            if expr.op == '-':
                self._emit('PUSHI -1')
                self._emit('MUL')
            elif expr.op == '.NOT.':
                self._emit('NOT')
        elif isinstance(expr, FunctionCall):
            self._gen_funcall(expr)

    def _gen_funcall(self, call: FunctionCall):
        name = call.name.upper()
        # Verifica se é um array declarado (ex: NUMS(I))
        decl = self._sym.lookup_var(name)
        if decl is not None:
            # É um acesso a array — trata como VarRef com índices
            self._load_varref(VarRef(name=call.name, indices=call.args))
            return
        # Funções intrínsecas
        if name == 'MOD':
            self._gen_expr(call.args[0])
            self._gen_expr(call.args[1])
            self._emit('MOD')
        elif name == 'ABS':
            self._gen_expr(call.args[0])
            self._emit('ABS')
        elif name == 'SQRT':
            self._gen_expr(call.args[0])
            self._emit('SQRT')
        elif name == 'INT':
            self._gen_expr(call.args[0])
            self._emit('FTOI')
        elif name in ('MAX', 'MIN'):
            self._gen_expr(call.args[0])
            for arg in call.args[1:]:
                self._gen_expr(arg)
                self._emit('MAX' if name == 'MAX' else 'MIN')
        else:
            for arg in call.args:
                self._gen_expr(arg)
            self._emit(f'CALL F{name}')

    def _load_varref(self, ref: VarRef):
        decl = self._sym.lookup_var(ref.name)
        if decl is None:
            print(f"[CodeGen] Warning: undeclared variable '{ref.name}', assuming 0")
            self._emit('PUSHI 0')
            return
        instr = 'PUSHL' if not decl.is_global else 'PUSHG'
        if len(ref.indices) == 0:
            self._emit(f'{instr} {decl.scope_offset}')
        else:
            # Array load: base_ptr, index-1, LOADN
            self._emit(f'{instr} {decl.scope_offset}')
            self._gen_expr(ref.indices[0])
            self._emit('PUSHI 1')
            self._emit('SUB')
            self._emit('LOADN')

    def _store_varref(self, ref: VarRef):
        decl = self._sym.lookup_var(ref.name)
        if decl is None:
            print(f"[CodeGen] Warning: undeclared variable '{ref.name}'")
            return
        instr = 'PUSHL' if not decl.is_global else 'PUSHG'
        if len(ref.indices) == 0:
            store_instr = 'STOREL' if not decl.is_global else 'STOREG'
            self._emit(f'{store_instr} {decl.scope_offset}')
        else:
            # Array store: stack tem [valor] no topo
            # Precisamos de [base_ptr, index-1, valor] para STOREN
            self._emit(f'{instr} {decl.scope_offset}')
            self._gen_expr(ref.indices[0])
            self._emit('PUSHI 1')
            self._emit('SUB')
            self._emit('ROT')
            self._emit('STOREN')

    def _load_name(self, name: str):
        decl = self._sym.lookup_var(name)
        if decl:
            instr = 'PUSHL' if not decl.is_global else 'PUSHG'
            self._emit(f'{instr} {decl.scope_offset}')
        else:
            self._emit('PUSHI 0')

    def _store_name(self, name: str):
        decl = self._sym.lookup_var(name)
        if decl:
            instr = 'STOREL' if not decl.is_global else 'STOREG'
            self._emit(f'{instr} {decl.scope_offset}')

    def _emit_write(self, expr: Expression):
        if isinstance(expr, StringLiteral):
            self._emit('WRITES')
        elif isinstance(expr, RealLiteral):
            self._emit('WRITEF')
        elif isinstance(expr, IntLiteral):
            self._emit('WRITEI')
        elif isinstance(expr, LogicalLiteral):
            self._emit('WRITEI')
        elif isinstance(expr, VarRef):
            var_type = self._sym.get_type(expr.name)
            if var_type == FortranType.REAL:
                self._emit('WRITEF')
            elif var_type == FortranType.CHARACTER:
                self._emit('WRITES')
            else:
                self._emit('WRITEI')
        else:
            self._emit('WRITEI')

    def _binop_instr(self, op: str) -> str:
        return {
            '+':     'ADD',
            '-':     'SUB',
            '*':     'MUL',
            '/':     'DIV',
            '**':    'MUL',
            '.EQ.':  'EQUAL',
            '.NE.':  'EQUAL\nNOT',
            '.LT.':  'INF',
            '.LE.':  'INFEQ',
            '.GT.':  'SUP',
            '.GE.':  'SUPEQ',
            '.AND.': 'AND',
            '.OR.':  'OR',
        }.get(op, f'// unknown op {op}')

    def _new_label(self, prefix: str) -> str:
        self._label_counter += 1
        return f'L{prefix}{self._label_counter}'

    def _stmt_label(self, n: int) -> str:
        unit = self._unit_name or 'MAIN'
        return f'LBL{unit}{n}'

    def _label(self, name: str):
        clean = name.replace(' ', '').replace('\r', '')
        if not clean.endswith(':'):
            clean += ':'
        self.code.append(clean)

    def _push_default(self, t: FortranType):
        if t == FortranType.REAL:
            self._emit('PUSHF 0.0000000000')
        elif t == FortranType.CHARACTER:
            self._emit('PUSHS ""')
        else:
            self._emit('PUSHI 0')

    def _emit(self, instr: str):
        for line in instr.replace('\r', '').split('\n'):
            line = line.strip()
            if line:
                self.code.append(f' {line}')


def generate(program: Program) -> str:
    return CodeGenerator().generate(program)
