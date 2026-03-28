# Lexinador
- Integrante: Higor Leonardo da Silva Azevedo
- Instituição: Pontifícia Universidade Católica do Paraná (PUCPR)
- Disciplina: Linguagens Formais e Compiladores
- Professor: Frank de Alcantara



Este projeto é um tradutor de expressões em Notação Polonesa Reversa (RPN) para Assembly ARMv7, desenvolvido como parte dos estudos de Compiladores e Microprocessadores. O sistema realiza a análise léxica de expressões matemáticas, traduz a RPN para a linguagem Assembly e gera um arquivo .s compatível com simuladores como o Cpulator.


Funcionalidades
Analisador Léxico (AFD): Implementação de um Autômato Finito Determinístico para identificar números, operadores, variáveis e comandos especiais.
Execução RPN: Avaliação de expressões usando uma pilha lógica.
Suporte a Variáveis: Uso do comando MEM para armazenar valores em memória e recuperação posterior.
Histórico de Resultados: Comando RES para acessar resultados de linhas processadas anteriormente.
Geração de Assembly: Tradução direta para instruções ARMv7, utilizando a unidade de ponto flutuante (VFP - Vector Floating-Point).


Tecnologias Utilizadas
Linguagem: Python 
Target: Assembly ARMv7 (Precisão dupla/Double Precision)
Simulação: Recomendado o uso do Cpulator (ARMv7 System).

Estrutura do Código
O tradutor é dividido em três etapas principais:
parseExpressao: O estado inicial e os estados subsequentes (estado_numero, estado_operador, etc.) processam a string de entrada.
executarExpressao: Valida a lógica da calculadora RPN e mantém o dicionário de variáveis e o histórico de resultados.
gerarAssembly: Mapeia as operações para instruções VADD, VSUB, VMUL, VDIV, gerindo o uso de registradores de ponto flutuante (D0, D1) e a pilha VFP.

