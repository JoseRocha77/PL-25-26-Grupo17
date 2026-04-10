"""
Symbol table for Fortran 77 compiler.
"""
from .ast import FortranType, VarDecl, ProgramUnit

class SymbolTableError(Exception):
    pass

class Symbol:
    def __init__(self, name: str, sym_type, decl=None):
        self.name     = name
        self.sym_type = sym_type  # FortranType | 'function' | 'subroutine'
        self.decl     = decl      # VarDecl or ProgramUnit

class SymbolTable:
    def __init__(self):
        self.scopes: list[dict[str, Symbol]] = [{}]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add_variable(self, decl: VarDecl, var_type: FortranType):
        name = decl.name.upper()
        if name in self.scopes[-1]:
            raise SymbolTableError(f"Variável '{name}' já declarada neste escopo.")
        sym = Symbol(name=name, sym_type=var_type, decl=decl)
        self.scopes[-1][name] = sym
        return sym

    def add_function(self, unit: ProgramUnit):
        name = unit.name.upper()
        if name in self.scopes[0]:
            raise SymbolTableError(f"Subprograma '{name}' já definido.")
        sym = Symbol(name=name, sym_type=unit.kind, decl=unit)
        self.scopes[0][name] = sym
        return sym

    def lookup(self, name: str):
        """Devolve o Symbol completo (tem .sym_type e .decl)."""
        upper = name.upper()
        for scope in reversed(self.scopes):
            if upper in scope:
                return scope[upper]
        return None

    def lookup_var(self, name: str) -> VarDecl | None:
        """Devolve o VarDecl da variável, ou None."""
        sym = self.lookup(name)
        if sym and isinstance(sym.decl, VarDecl):
            return sym.decl
        return None

    def lookup_unit(self, name: str) -> ProgramUnit | None:
        """Devolve o ProgramUnit (função/subrotina), ou None."""
        sym = self.lookup(name)
        if sym and isinstance(sym.decl, ProgramUnit):
            return sym.decl
        return None

    def get_type(self, name: str) -> FortranType | None:
        """Devolve o tipo da variável, ou None."""
        sym = self.lookup(name)
        if sym and isinstance(sym.sym_type, FortranType):
            return sym.sym_type
        return None

    def current_scope_vars(self) -> list[Symbol]:
        return list(self.scopes[-1].values())