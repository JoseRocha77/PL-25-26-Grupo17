! ============================================================
! TESTE: Strength Reduction
! X ** 2 deve ser convertido para X * X em tempo de compilacao.
! No codigo .vm NAO deve aparecer a instrucao MUL com POWER —
! deve aparecer o valor de X empurrado duas vezes e um MUL.
!
! Introduza o valor: 5
! Output esperado:
!   5 ao quadrado = 25
!   9 ao quadrado = 81
! ============================================================
PROGRAM OPT4STRENGTH
  INTEGER X, Y, BASE, QUAD

  PRINT *, 'Introduza um numero:'
  READ *, X

  Y = X ** 2

  PRINT *, X, ' ao quadrado = ', Y

  ! Segundo caso: literais encadeiam com Folding
  ! 9 ** 2 -> 9 * 9 (Strength Reduction) -> 81 (Constant Folding)
  BASE = 9
  QUAD = BASE ** 2

  PRINT *, BASE, ' ao quadrado = ', QUAD
END
