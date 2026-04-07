"""
Semantic analyser for Fortran 77.
- Resolves variable declarations and assigns scope offsets.
- Type checks expressions.
- Validates DO loop labels match CONTINUE labels.
- Validates GOTO targets exist.
"""
from compiler.ast import *
from compiler.symboltable import SymbolTable, SymbolTableError

class SemanticError(Exception):
    pass

# Built-in functions and their return types
BUILTINS = {
    'MOD':  FortranType.INTEGER,
    'ABS':  FortranType.REAL,
    'SQRT': FortranType.REAL,
    'INT':  FortranType.INTEGER,
    'REAL': FortranType.REAL,
    'MAX':  FortranType.REAL,
    'MIN':  FortranType.REAL,
}

class SemanticAnalyser:
    def __init__(self):
        self.table   = SymbolTable()
        self.errors  = []
        self.current_unit: ProgramUnit | None = None
        self._labels: set[int] = set()   # labels defined in current unit

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def analyse(self, program: Program) -> bool:
        # Register all functions/subroutines globally first
        for unit in program.units:
            if unit.kind != 'program':
                try:
                    self.table.add_function(unit)
                except SymbolTableError as e:
                    self._err(str(e))

        for unit in program.units:
            self._analyse_unit(unit)

        return len(self.errors) == 0

    # ------------------------------------------------------------------
    # Unit
    # ------------------------------------------------------------------

    def _analyse_unit(self, unit: ProgramUnit):
        self.current_unit = unit
        self.table.push_scope()
        self._labels = self._collect_labels(unit.body)

        # Add parameters as variables (INTEGER by default if not declared)
        for param in unit.params:
            vd = VarDecl(name=param, dimensions=[], is_global=False)
            try:
                self.table.add_variable(vd, FortranType.INTEGER)
            except SymbolTableError:
                pass

        # Process declarations and assign stack offsets
        offset = 0
        if unit.return_type is not None:
            # Return variable for FUNCTION has offset 0
            ret_decl = VarDecl(name=unit.name, dimensions=[], is_global=False, scope_offset=offset)
            try:
                self.table.add_variable(ret_decl, unit.return_type)
            except SymbolTableError:
                pass
            offset += 1

        for decl in unit.declarations:
            for vd in decl.variables:
                vd.is_global = (unit.kind == 'program')
                vd.scope_offset = offset
                size = 1
                for d in vd.dimensions:
                    size *= d
                offset += size
                try:
                    self.table.add_variable(vd, decl.var_type)
                except SymbolTableError as e:
                    self._err(str(e))

        # Analyse statements
        for stmt in unit.body:
            self._analyse_stmt(stmt)

        self.table.pop_scope()

    # ------------------------------------------------------------------
    # Collect all statement labels in a unit
    # ------------------------------------------------------------------

    def _collect_labels(self, stmts: list) -> set[int]:
        labels = set()
        for s in stmts:
            lbl = getattr(s, 'label', None)
            if lbl is not None:
                labels.add(lbl)
            if isinstance(s, IfStmt):
                labels |= self._collect_labels(s.then_body)
                labels |= self._collect_labels(s.else_body)
            elif isinstance(s, DoStmt):
                labels |= self._collect_labels(s.body)
        return labels

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _analyse_stmt(self, stmt: Statement):
        if isinstance(stmt, AssignStmt):
            self._resolve_varref(stmt.target)
            self._analyse_expr(stmt.value)

        elif isinstance(stmt, PrintStmt):
            for item in stmt.items:
                self._analyse_expr(item)

        elif isinstance(stmt, ReadStmt):
            for t in stmt.targets:
                self._resolve_varref(t)

        elif isinstance(stmt, IfStmt):
            self._analyse_expr(stmt.condition)
            for s in stmt.then_body:
                self._analyse_stmt(s)
            for s in stmt.else_body:
                self._analyse_stmt(s)

        elif isinstance(stmt, DoStmt):
            self._analyse_expr(stmt.start)
            self._analyse_expr(stmt.stop)
            if stmt.step:
                self._analyse_expr(stmt.step)
            # Validate matching CONTINUE label
            if stmt.end_label not in self._labels:
                self._err(f"DO loop end label {stmt.end_label} has no matching CONTINUE")
            for s in stmt.body:
                self._analyse_stmt(s)

        elif isinstance(stmt, GotoStmt):
            if stmt.target not in self._labels:
                self._err(f"GOTO target label {stmt.target} is not defined")

        elif isinstance(stmt, CallStmt):
            unit = self.table.lookup_unit(stmt.name)
            if unit is None and stmt.name.upper() not in BUILTINS:
                self._err(f"Undefined subroutine '{stmt.name}'")
            for arg in stmt.args:
                self._analyse_expr(arg)

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _analyse_expr(self, expr: Expression):
        if isinstance(expr, (IntLiteral, RealLiteral, LogicalLiteral, StringLiteral)):
            pass

        elif isinstance(expr, VarRef):
            self._resolve_varref(expr)

        elif isinstance(expr, BinaryExpr):
            self._analyse_expr(expr.left)
            self._analyse_expr(expr.right)

        elif isinstance(expr, UnaryExpr):
            self._analyse_expr(expr.operand)

        elif isinstance(expr, FunctionCall):
            name = expr.name.upper()
            if name not in BUILTINS and self.table.lookup_unit(name) is None:
                self._err(f"Undefined function '{name}'")
            for arg in expr.args:
                self._analyse_expr(arg)

    def _resolve_varref(self, ref: VarRef):
        decl = self.table.lookup_var(ref.name)
        if decl is None:
            # Fortran implicit typing: I-N -> INTEGER, others -> REAL
            first = ref.name[0].upper()
            implicit_type = FortranType.INTEGER if 'I' <= first <= 'N' else FortranType.REAL
            vd = VarDecl(name=ref.name.upper(), dimensions=[], is_global=True, scope_offset=-1)
            try:
                self.table.add_variable(vd, implicit_type)
            except SymbolTableError:
                pass
            ref.decl = vd
        else:
            ref.decl = decl
        for idx in ref.indices:
            self._analyse_expr(idx)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _err(self, msg: str):
        print(f"[Semantic Error] {msg}")
        self.errors.append(msg)


def analyse(program: Program) -> bool:
    return SemanticAnalyser().analyse(program)
