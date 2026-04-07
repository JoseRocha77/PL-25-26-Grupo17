# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026.

## Estrutura

```
fortran77/
├── main.py               ← entry point
├── requirements.txt
├── compiler/
│   ├── ast.py            ← nós da AST
│   ├── lexer.py          ← análise léxica (ply.lex)
│   ├── parser.py         ← análise sintática (ply.yacc)
│   ├── semantic.py       ← análise semântica
│   └── codegen.py        ← geração de código EWVM
├── examples/
│   ├── hello.f77
│   └── fatorial.f77
└── tests/
```

## Como usar

```bash
pip install ply
python main.py examples/hello.f77
```

O compilador gera um ficheiro `.vm` com código para a [EWVM](https://ewvm.epl.di.uminho.pt/).

## Funcionalidades suportadas

- Tipos: `INTEGER`, `REAL`, `LOGICAL`, `CHARACTER`
- Declaração de variáveis (escalares e arrays)
- Expressões aritméticas, lógicas e relacionais
- `IF-THEN-ELSE-ENDIF`
- Ciclos `DO` com label + `CONTINUE`
- `GOTO`
- `PRINT *` e `READ *`
- `STOP`, `RETURN`
- `CALL` (subroutines)
- `FUNCTION` e `SUBROUTINE`
- Funções intrínsecas: `MOD`, `ABS`, `SQRT`, `INT`, `MAX`, `MIN`
- Tipagem implícita Fortran (I-N → INTEGER, resto → REAL)

## Formato

O compilador usa **formato livre** (free-form), não o formato de colunas fixas do Fortran 77 clássico.
