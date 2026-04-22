! ============================================================
! TESTE: Strength Reduction + AST Lowering
! O operador ** e resolvido no Otimizador (Middle-end) por
! AST Lowering, antes de chegar ao Gerador de Codigo.
! O codegen nunca ve um no (**) — so ve multiplicacoes.
!
! Casos testados:
!   X**2  -> X*X             (Strength Reduction)
!   X**3  -> X*X*X           (Strength Reduction)
!   X**4  -> X*X*X*X         (Strength Reduction)
!   3**3  -> 3*3*3 -> 27     (Strength Reduction + Constant Folding)
!   X**0  -> 1               (identidade)
!   X**1  -> X               (identidade)
!
! Introduza o valor: 5
! Output esperado:
!   5 ao quadrado = 25
!   5 ao cubo = 125
!   5 a quarta = 625
!   3 ao cubo = 27
!   5 a zero = 1
!   5 a um = 5
! ============================================================
PROGRAM OPT4STRENGTH
  INTEGER X, Y, Z, W

  PRINT *, 'Introduza um numero:'
  READ *, X

  ! X**2 -> X*X (Strength Reduction na AST)
  ! No .vm: dois PUSHG X seguidos de MUL, sem nenhum POWER
  Y = X ** 2
  PRINT *, X, ' ao quadrado = ', Y

  ! X**3 -> X*X*X (Strength Reduction com 3 nos na AST)
  ! No .vm: tres PUSHG X seguidos de dois MUL
  Z = X ** 3
  PRINT *, X, ' ao cubo = ', Z

  ! X**4 -> X*X*X*X (Strength Reduction com 4 nos)
  W = X ** 4
  PRINT *, X, ' a quarta = ', W

  ! 3**3 -> 3*3*3 (Strength Reduction) -> 27 (Constant Folding)
  ! No .vm: apenas PUSHI 27, sem nenhuma operacao
  PRINT *, '3 ao cubo = ', 3 ** 3

  ! X**0 -> 1 (qualquer numero a 0 e 1)
  ! No .vm: apenas PUSHI 1
  PRINT *, X, ' a zero = ', X ** 0

  ! X**1 -> X (expoente 1 e identidade)
  ! No .vm: apenas PUSHG X, sem nenhum MUL
  PRINT *, X, ' a um = ', X ** 1

END
