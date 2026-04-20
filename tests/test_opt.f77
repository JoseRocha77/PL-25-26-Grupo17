PROGRAM STRESS
      
!     Se o otimizador funcionar, o .vm so tera PUSHI 50
      A = 10 + 20 * 2
      
!     Isto deve desaparecer e virar apenas carregar o A
      B = A * 1 + 0
      
!     A inversao de comparacao entra aqui (.NOT. A < B vira A >= B)
      IF (.NOT. (A .LT. B)) THEN
         PRINT *, 'SUCESSO: OTIMIZADOR FUNCIONOU (A = B)'
      ENDIF
      
!     Dead Code Elimination: NADA disto pode ir para o .vm
      IF (.FALSE.) THEN
         PRINT *, 'FALHA FATAL: ISTO NAO DEVIA ESTAR NA MAQUINA VIRTUAL'
      ENDIF
      
      END