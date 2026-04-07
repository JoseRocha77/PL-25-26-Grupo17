from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class FortranType(IntEnum):
    INTEGER  = 0
    REAL     = 1
    LOGICAL  = 2
    CHARACTER = 3

# ---------------------------------------------------------------------------
# Program structure
# ---------------------------------------------------------------------------

@dataclass
class Program:
    name: str
    units: list[ProgramUnit]   # main + functions/subroutines

@dataclass
class ProgramUnit:
    """Represents PROGRAM, FUNCTION or SUBROUTINE block."""
    kind: Literal['program', 'function', 'subroutine']
    name: str
    params: list[str]                        # parameter names (for functions/subroutines)
    return_type: FortranType | None          # only for FUNCTION
    declarations: list[Declaration]
    body: list[Statement]

# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

@dataclass
class Declaration:
    var_type: FortranType
    variables: list[VarDecl]

@dataclass
class VarDecl:
    name: str
    dimensions: list[int] = field(default_factory=list)  # empty = scalar
    scope_offset: int = -1
    is_global: bool = True

# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

BinaryOp = Literal['+', '-', '*', '/', '**',
                   '.EQ.', '.NE.', '.LT.', '.LE.', '.GT.', '.GE.',
                   '.AND.', '.OR.']
UnaryOp  = Literal['+', '-', '.NOT.']

@dataclass
class IntLiteral:
    value: int

@dataclass
class RealLiteral:
    value: float

@dataclass
class LogicalLiteral:
    value: bool   # .TRUE. / .FALSE.

@dataclass
class StringLiteral:
    value: str

@dataclass
class VarRef:
    name: str
    indices: list[Expression] = field(default_factory=list)
    decl: VarDecl | None = None

@dataclass
class BinaryExpr:
    op: BinaryOp
    left: Expression
    right: Expression

@dataclass
class UnaryExpr:
    op: UnaryOp
    operand: Expression

@dataclass
class FunctionCall:
    name: str
    args: list[Expression]

Expression = IntLiteral | RealLiteral | LogicalLiteral | StringLiteral | \
             VarRef | BinaryExpr | UnaryExpr | FunctionCall

# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class AssignStmt:
    label: int | None
    target: VarRef
    value: Expression

@dataclass
class PrintStmt:
    label: int | None
    items: list[Expression]

@dataclass
class ReadStmt:
    label: int | None
    targets: list[VarRef]

@dataclass
class IfStmt:
    label: int | None
    condition: Expression
    then_body: list[Statement]
    else_body: list[Statement]

@dataclass
class DoStmt:
    label: int | None
    end_label: int          # label of matching CONTINUE
    var: str
    start: Expression
    stop: Expression
    step: Expression | None
    body: list[Statement]

@dataclass
class GotoStmt:
    label: int | None
    target: int

@dataclass
class ContinueStmt:
    label: int | None

@dataclass
class ReturnStmt:
    label: int | None

@dataclass
class StopStmt:
    label: int | None

@dataclass
class CallStmt:
    label: int | None
    name: str
    args: list[Expression]

Statement = AssignStmt | PrintStmt | ReadStmt | IfStmt | DoStmt | \
            GotoStmt | ContinueStmt | ReturnStmt | StopStmt | CallStmt
