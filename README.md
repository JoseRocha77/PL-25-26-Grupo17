# PL-25-26-Grupo17

# Compilador Fortran 77 → EWVM

Projeto de Processamento de Linguagens 2026 — Grupo 17.

## Estrutura do Projeto

```
PL-25-26-Grupo17/
├── main.py               ← entry point do compilador
├── requirements.txt      ← dependências Python
├── compiler/
│   ├── ast.py            ← nós da AST (árvore sintática abstrata)
│   ├── lexer.py          ← análise léxica (ply.lex)
│   ├── parser.py         ← análise sintática (ply.yacc)
│   ├── semantic.py       ← análise semântica
│   ├── symboltable.py    ← tabela de símbolos
│   └── codegen.py        ← geração de código EWVM
├── tests/
│   ├── hello.f77         ← Exemplo 1: Olá Mundo
│   ├── fatorial.f77      ← Exemplo 2: Fatorial
│   ├── primo.f77         ← Exemplo 3: Verificação de primo
│   ├── somaarr.f77       ← Exemplo 4: Soma de array
│   └── conversor.f77     ← Exemplo 5: Conversão de bases (com FUNCTION)

```

## Instalação e Uso

### Requisitos

- Python 3.10+
- PLY (Python Lex-Yacc)

```bash
pip install ply
```

### Compilar um programa Fortran

```bash
python main.py <ficheiro.f77>
```

O compilador gera um ficheiro `.vm` com o código para a [EWVM](https://ewvm.epl.di.uminho.pt/).

### Exemplo

```bash
python main.py examples/fatorial.f77
```

O ficheiro `examples/fatorial.vm` é gerado e o seu conteúdo pode ser colado diretamente na EWVM para execução.

## Funcionalidades Suportadas

### Tipos de dados
- `INTEGER`, `REAL`, `LOGICAL`, `CHARACTER`
- Declaração de variáveis escalares e arrays unidimensionais
- Tipagem implícita Fortran (variáveis I-N → INTEGER, resto → REAL)

### Expressões
- Aritméticas: `+`, `-`, `*`, `/`, `**`
- Relacionais: `.EQ.`, `.NE.`, `.LT.`, `.LE.`, `.GT.`, `.GE.`
- Lógicas: `.AND.`, `.OR.`, `.NOT.`

### Controlo de fluxo
- `IF-THEN-ELSE-ENDIF`
- `IF (...) GOTO label` (logical IF)
- Ciclos `DO label VAR = start, stop` com `CONTINUE`
- `GOTO`

### Input/Output
- `PRINT *, ...` — impressão de valores e strings
- `READ *, ...` — leitura de valores escalares e arrays

### Subprogramas (valorização)
- `FUNCTION` com valor de retorno
- `SUBROUTINE` com `CALL`
- Passagem de argumentos por posição

### Funções intrínsecas
- `MOD`, `ABS`, `SQRT`, `INT`, `MAX`, `MIN`

## Formato de Entrada

O compilador aceita **formato livre** (free-form), não o formato de colunas fixas do Fortran 77 clássico. Comentários com `!` são suportados.

## Exemplos dos 5 programas do enunciado

Todos os exemplos fornecidos no enunciado são suportados e compilam corretamente:

| Exemplo | Ficheiro | Funcionalidade testada |
|---------|----------|----------------------|
| Olá Mundo | `hello.f77` | `PRINT`, strings |
| Fatorial | `fatorial.f77` | `DO`, `READ`, variáveis inteiras |
| É primo? | `primo.f77` | `IF-THEN-ELSE`, `GOTO`, `.AND.`, `MOD` |
| Soma de array | `somaarr.f77` | Arrays, `DO`, `READ` com índices |
| Conversor de bases | `conversor.f77` | `FUNCTION`, chamada de função, `GOTO` |