# symboltable.py

from dataclasses import dataclass
from .ast import FortranType, VarDecl, ProgramUnit

class SymbolTableError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        # Escopo global para funções e subrotinas
        self.globals: dict[str, ProgramUnit] = {}
        # Pilha de escopos para variáveis locais (cada elemento é um dict)
        self.scopes: list[dict[str, VarDecl]] = []
        # Tipos das variáveis (para o semantic.py)
        self.types: dict[str, FortranType] = {}
        # Contador de offset para a VM
        self.next_offset = 0

    def push_scope(self):
        """Cria um novo contexto (ex: ao entrar num PROGRAM ou FUNCTION)."""
        self.scopes.append({})
        self.next_offset = 0  # Reinicia o offset para variáveis locais

    def pop_scope(self):
        """Destrói o contexto atual ao sair de uma unidade."""
        if self.scopes:
            self.scopes.pop()

    def add_function(self, unit: ProgramUnit):
        """Regista uma FUNCTION ou SUBROUTINE globalmente."""
        name = unit.name.upper()
        if name in self.globals:
            raise SymbolTableError(f"Subprograma '{name}' já definido.")
        self.globals[name] = unit

    def lookup_unit(self, name: str) -> ProgramUnit | None:
        """Procura uma função ou subrotina pelo nome."""
        return self.globals.get(name.upper())

    def add_variable(self, decl: VarDecl, var_type: FortranType):
        """Adiciona uma variável ao escopo atual e define o seu offset na VM."""
        if not self.scopes:
            raise SymbolTableError("Tentativa de adicionar variável sem escopo ativo.")
        
        name = decl.name.upper()
        current_scope = self.scopes[-1]
        
        if name in current_scope:
            raise SymbolTableError(f"Variável '{name}' já declarada neste escopo.")
        
        # Define o endereço de memória (offset) para a geração de código
        decl.scope_offset = self.next_offset
        self.next_offset += 1
        
        current_scope[name] = decl
        self.types[name] = var_type

    def lookup_var(self, name: str) -> VarDecl | None:
        """Procura uma variável do escopo mais interno para o mais externo."""
        name = name.upper()
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def get_type(self, name: str) -> FortranType | None:
        """Retorna o tipo (INTEGER, REAL, etc) de uma variável."""
        return self.types.get(name.upper())