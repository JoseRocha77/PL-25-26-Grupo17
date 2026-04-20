"""
Otimizador da Árvore Sintática (AST) para o compilador Fortran 77.
"""
from typing import Any, List, Optional, Union
from compiler.ast import (
    Program, ProgramUnit, VarDecl, IntLiteral, RealLiteral, 
    LogicalLiteral, StringLiteral, VarRef, BinaryExpr, UnaryExpr, 
    FunctionCall, AssignStmt, PrintStmt, ReadStmt, IfStmt, 
    DoStmt, GotoStmt, ContinueStmt, ReturnStmt, StopStmt, CallStmt
)

class ASTOptimizer:
    def __init__(self) -> None:
        # Contador para mostrar no terminal quantas operações inúteis cortámos
        self.optimizations_applied: int = 0

    def optimize(self, node: Program) -> Program:
        # Ponto de entrada do otimizador
        return self._visit(node)

    def _visit(self, node: Any) -> Any:
        if node is None:
            return None

        # Se for uma lista de instruções, visita cada uma e "achata" listas aninhadas geradas por blocos IF mortos
        if isinstance(node, list):
            optimized_list = []
            for child in node:
                opt_child = self._visit(child)
                if isinstance(opt_child, list):
                    optimized_list.extend(opt_child)
                elif opt_child is not None:
                    optimized_list.append(opt_child)
            return optimized_list

        # Despachante dinâmico: chama a função certa com base no nome da classe do nó (Visitor Pattern)
        method_name = f'_visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node: Any) -> Any:
        # Fallback para nós da AST que são simples e não precisam de ser percorridos
        return node

    # ==========================================
    # Travessias Recursivas da Árvore
    # ==========================================
    def _visit_Program(self, node: Program) -> Program:
        node.units = self._visit(node.units)
        return node

    def _visit_ProgramUnit(self, node: ProgramUnit) -> ProgramUnit:
        node.body = self._visit(node.body)
        return node

    def _visit_AssignStmt(self, node: AssignStmt) -> AssignStmt:
        node.target = self._visit(node.target)
        node.value = self._visit(node.value)
        return node

    def _visit_PrintStmt(self, node: PrintStmt) -> PrintStmt:
        node.items = self._visit(node.items)
        return node

    def _visit_ReadStmt(self, node: ReadStmt) -> ReadStmt:
        node.targets = self._visit(node.targets)
        return node

    def _visit_DoStmt(self, node: DoStmt) -> DoStmt:
        node.start = self._visit(node.start)
        node.stop = self._visit(node.stop)
        node.step = self._visit(node.step) if node.step else None
        node.body = self._visit(node.body)
        return node

    def _visit_CallStmt(self, node: CallStmt) -> CallStmt:
        node.args = self._visit(node.args)
        return node

    def _visit_VarRef(self, node: VarRef) -> VarRef:
        node.indices = self._visit(node.indices)
        return node

    def _visit_FunctionCall(self, node: FunctionCall) -> FunctionCall:
        node.args = self._visit(node.args)
        return node

    # ==========================================
    # 1. Constant Folding & Álgebra Simples
    # ==========================================
    def _visit_BinaryExpr(self, node: BinaryExpr) -> Union[BinaryExpr, IntLiteral]:
        # Otimiza os filhos primeiro (Bottom-Up)
        node.left = self._visit(node.left)
        node.right = self._visit(node.right)

        # Constant Folding: Se ambos os lados forem números estáticos, faz a conta no compilador
        if isinstance(node.left, IntLiteral) and isinstance(node.right, IntLiteral):
            l, r = node.left.value, node.right.value
            if node.op == '+': self.optimizations_applied += 1; return IntLiteral(l + r)
            if node.op == '-': self.optimizations_applied += 1; return IntLiteral(l - r)
            if node.op == '*': self.optimizations_applied += 1; return IntLiteral(l * r)
            if node.op == '/' and r != 0: self.optimizations_applied += 1; return IntLiteral(l // r)

        # Simplificações Algébricas: corta operações matematicamente neutras
        if node.op == '+' and isinstance(node.right, IntLiteral) and node.right.value == 0:
            self.optimizations_applied += 1
            return node.left
            
        if node.op == '*' and isinstance(node.right, IntLiteral) and node.right.value == 1:
            self.optimizations_applied += 1
            return node.left
            
        if node.op == '*' and isinstance(node.right, IntLiteral) and node.right.value == 0:
            self.optimizations_applied += 1
            return IntLiteral(0)

        return node

    # ==========================================
    # 2. Simplificação Lógica (.NOT.)
    # ==========================================
    def _visit_UnaryExpr(self, node: UnaryExpr) -> Union[UnaryExpr, BinaryExpr, Any]:
        node.operand = self._visit(node.operand)

        if node.op == '.NOT.':
            # Dupla Negação: .NOT. (.NOT. X) vira apenas X
            if isinstance(node.operand, UnaryExpr) and node.operand.op == '.NOT.':
                self.optimizations_applied += 1
                return node.operand.operand
            
            # Inversão de Comparações: .NOT. (A < B) vira A >= B
            if isinstance(node.operand, BinaryExpr):
                inverse_ops = {
                    '.LT.': '.GE.', '.LE.': '.GT.',
                    '.GT.': '.LE.', '.GE.': '.LT.',
                    '.EQ.': '.NE.', '.NE.': '.EQ.'
                }
                if node.operand.op in inverse_ops:
                    self.optimizations_applied += 1
                    return BinaryExpr(inverse_ops[node.operand.op], node.operand.left, node.operand.right)

        return node

    # ==========================================
    # 3. Eliminação de Código Morto (IF Estático)
    # ==========================================
    def _visit_IfStmt(self, node: IfStmt) -> Union[IfStmt, List[Any]]:
        node.condition = self._visit(node.condition)
        node.then_body = self._visit(node.then_body)
        node.else_body = self._visit(node.else_body)

        # Se a condição for um valor absoluto (True ou False) já se sabe qual ramo vai correr
        if isinstance(node.condition, LogicalLiteral):
            self.optimizations_applied += 1
            
            # Mantém apenas o bloco que faz sentido e descarta o outro (Dead Code Elimination)
            surviving_body = node.then_body if node.condition.value else node.else_body
            
            # Se o IF tinha uma label, convertemos para CONTINUE para não quebrar a lógica de possíveis GOTOs noutras partes do código
            if node.label is not None:
                return [ContinueStmt(label=node.label)] + surviving_body
            
            return surviving_body

        return node