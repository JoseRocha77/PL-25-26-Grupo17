"""
Fortran 77 Compiler — main entry point.
Usage: python main.py <source.f77>
"""
import sys
import os

# Add parent directory to path so 'compiler' package is importable
sys.path.insert(0, os.path.dirname(__file__))

from compiler.lexer   import create_lexer
from compiler.parser  import parse
from compiler.semantic import analyse
from compiler.codegen  import generate

def compile_file(path: str) -> int:
    with open(path, 'r') as f:
        source = f.read()

    print(f"=== Compiling: {path} ===\n")

    # 1. Parse
    ast = parse(source)
    if ast is None:
        print("[Error] Parsing failed.")
        return 1

    # 2. Semantic analysis
    ok = analyse(ast)
    if not ok:
        print("[Error] Semantic analysis failed.")
        return 1

    # 3. Code generation
    ewvm_code = generate(ast)

    # Write output
    out_path = os.path.splitext(path)[0] + '.vm'
    with open(out_path, 'w', newline='\n') as f:
            f.write(ewvm_code)

    print(ewvm_code)
    print(f"\n=== Output written to: {out_path} ===")
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py <source.f77>")
        sys.exit(1)
    sys.exit(compile_file(sys.argv[1]))
