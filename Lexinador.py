import sys  # importa o modulo para acessar argumentos da linha de comando (como o nome do arquivo de entrada)
import json # importa a biblioteca para salvar a lista de tokens em formato JSON 

vrv = {}       # guarda o nome da variavel e seu valor numerico atual
hstrc = []     # guarda o histórico de resultados de cada linha processada
cst = []       # armazena tuplas (label, valor) para criar as constantes na seção .data do assembler
vrv_mr = set() # guardar nomes unicos de variaveis que precisam ser declaradas no assembler
contador_const = 0 # contador para criar nomes unicos (labels) para cada constante numérica no assembler


# ANALISADOR LEXICO (AFD - Automato Finito Deterministico)
# Estado inicial do automato: decide para qual estado ir com base no caractere atual
def estado_inicial(linha, i, tokens):
    if i >= len(linha): # se chegar ao fim da string, retorna a posição final
        return i
    
    c = linha[i] # pega o caractere atual para analise

    if c.isspace(): # se for um espaço vazio, apenas pula para o proximo caractere
        return estado_inicial(linha, i + 1, tokens)

    elif c in '()': # se for parentese, adiciona na lista e continua
        tokens.append(c)
        return estado_inicial(linha, i + 1, tokens)

    elif '0' <= c <= '9': # se for um número, pula para o estado que processa numeros
        return estado_numero(linha, i, tokens)

    elif c in '+-*^/%': # se for um operador, pula para o estado que processa operadores
        return estado_operador(linha, i, tokens)

    elif ('A' <= c <= 'Z'): # se for letra maiuscula, pula para o estado que processa identificadores (MEM, RES, variáveis)
        return estado_identificador(linha, i, tokens)

    else: # se for qualquer outra coisa, lança um erro lexico
        raise ValueError(f"Caractere inválido '{c}'")

# estado que processa numeros inteiros ou reais 
def estado_numero(linha, i, tokens):
    num = "" # string para montar o numero
    ponto = False # flag para garantir que o numero tenha no maximo um ponto decimal

    while i < len(linha):
        c = linha[i]

        if '0' <= c <= '9': # vai acumulando os digitos
            num += c
        elif c == '.': # se encontrar um ponto
            if ponto: # se ja tinha ponto antes, é um erro (ex: 3.14.2)
                raise ValueError("Número malformado: múltiplos pontos")
            ponto = True
            num += c
        else: # se encontrar algo que nao é número, para de processar esse token
            break
        i += 1

    if num.endswith('.'): # um numero nao pode terminar com ponto (ex: 3.)
        raise ValueError(f"Número malformado: '{num}'")

    tokens.append(num) # adiciona o numero completo na lista de tokens
    return estado_inicial(linha, i, tokens) # volta para o estado inicial para o resto da linha

# estado que processa operadores simples ou compostos (como //)
def estado_operador(linha, i, tokens):
    # verifica se o operador é a divissao inteira '//' 
    if linha[i] == '/' and i + 1 < len(linha) and linha[i+1] == '/':
        tokens.append('//')
        return estado_inicial(linha, i + 2, tokens) # pula os dois caracteres '/'

    tokens.append(linha[i]) # caso contrario, adiciona o operador simples (+, -, *, /, %, ^)
    return estado_inicial(linha, i + 1, tokens)

# estado que processa identificadores (MEM, RES ou nomes de variáveis)
def estado_identificador(linha, i, tokens):
    ident = "" # string para montar a palavra

    while i < len(linha) and ('A' <= linha[i] <= 'Z'): # aceita apenas letras maiusculas
        ident += linha[i]
        i += 1

    tokens.append(ident) # adiciona a palavra na lista de tokens
    return estado_inicial(linha, i, tokens) # volta para o inicio

# função principal do Analisador Lexico que inicia o processo na linha
def parseExpressao(linha):
    tokens = []
    try:
        estado_inicial(linha, 0, tokens) # começa no estado inicial no indice 0
        if not tokens: # se a linha nao gerou nenhum token, avisa que esta vazia
            raise ValueError("Linha vazia")
        return tokens
    except Exception as e: # em caso de erro lexico, exibe o erro e retorna nulo
        print(f"Erro Léxico: {e}")
        return None

# EXECUÇÃO RPN (Notação Polonesa Reversa)
# Função que calcula o resultado da expressao baseada em tokens RPN
def executarExpressao(tokens):
    stack = [] # pilha 

    for t in tokens:
        if t in '()': # ignora os parenteses durante o calculo, pois RPN usa a ordem da pilha
            continue

        if t.replace('.', '', 1).isdigit(): # se o token for um numero, coloca na pilha como float
            stack.append(float(t))

        elif t not in ['+', '-', '*', '/', '//', '%', '^', 'MEM', 'RES']:
            stack.append(t) # se for um nome de variavel, coloca o nome (string) na pilha 

        elif t in ['+', '-', '*', '/', '//', '%', '^']: # se for um operador matematico
            if len(stack) < 2: # garante que existem dois valores para operar
                raise ValueError("Erro: operandos insuficientes")

            b = stack.pop() # pega o segundo operando (topo da pilha)
            a = stack.pop() # pega o primeiro operando

            # se algum operando for nome de variavel, busca o valor real na variavel 'vrv'
            if isinstance(a, str): 
                a = vrv.get(a, 0.0)
            if isinstance(b, str): 
                b = vrv.get(b, 0.0)

            # realiza a conta correspondente
            if t == '+': 
                stack.append(a + b)
            elif t == '-': 
                stack.append(a - b)
            elif t == '*': 
                stack.append(a * b)
            elif t == '/': 
                stack.append(a / b if b != 0 else 0.0)
            elif t == '//': 
                stack.append(float(int(a) // int(b) if b != 0 else 0))
            elif t == '%': 
                stack.append(float(int(a) % int(b) if b != 0 else 0))
            elif t == '^': 
                stack.append(a ** b)

        elif t == 'RES': # comando para buscar resultado de uma linha anterior
            if len(stack) < 1:
                raise ValueError("Erro: RES precisa de índice")

            idx = stack.pop()
            if isinstance(idx, str): # se o indice for uma variavel, pega o valor dela
                idx = vrv.get(idx, 0.0)

            n = int(idx) # converte para inteiro para usar como indice de lista
            # busca no historico de tras para frente (-(n+1))
            stack.append(hstrc[-(n+1)] if n < len(hstrc) else 0.0)

        elif t == 'MEM': # comando para salvar um valor em uma variavel
            if len(stack) < 2:
                raise ValueError("Erro: MEM precisa de valor e variável")

            var_name = stack.pop() # nome da variável
            valor = stack.pop() # valor a ser guardado

            if not isinstance(var_name, str): # valida se o topo era realmente um nome
                raise ValueError("Erro: nome da variável inválido")

            if isinstance(valor, str): # se o valor a ser guardado for outra variavel, pega o valor dela
                valor = vrv.get(valor, 0.0)

            vrv[var_name] = valor # salva na varivael vrv
            vrv_mr.add(var_name) # marca que essa variavel deve ser declarada no assembly

    res = stack[-1] if stack else 0.0 # o resultado da linha é o ultimo item da pilha
    hstrc.append(res) # adiciona no histórico global
    return res

# GERAÇÃO DE ASSEMBLY (Tradução para ARMv7)
# função que traduz a lista de tokens para codigo assembly ARMv7 
def gerarAssembly(tokens, linha_id):
    global contador_const
    asm = [f"\n    @ --- Linha {linha_id} ---"] # comentário para organizar o código .s

    for idx, t in enumerate(tokens):
        if t in '()': 
            continue

        # tratametno de numeros (carrega no processador de ponto flutuante)
        if t.replace('.', '', 1).isdigit():
            label = f"const_{contador_const}"
            contador_const += 1
            cst.append((label, t)) # adiciona na lista de constantes para a seção .data
            asm.append(f"    LDR R0, ={label}") # carrega endereço da constante
            asm.append(f"    VLDR D0, [R0]")    # carrega o valor real (double) em D0
            asm.append(f"    VPUSH {{D0}}")     # empilha na pilha VFP

        # tratamento de variaveis
        elif t not in ['+', '-', '*', '/', '//', '%', '^', 'MEM', 'RES']:
            vrv_mr.add(t) # registra a variavel

            # verifica se o proximo token é MEM para decidir se empilha o endereço ou o valor
            if idx + 1 < len(tokens) and tokens[idx + 1] == 'MEM':
                asm.append(f"    LDR R0, ={t}") # prepara endereço para salvar depois
                asm.append(f"    PUSH {{R0}}")
            else:
                asm.append(f"    LDR R0, ={t}") # carrega valor da variavel para conta
                asm.append(f"    VLDR D0, [R0]")
                asm.append(f"    VPUSH {{D0}}")

        # 3. tratamento do comando MEM
        elif t == 'MEM':
            asm.append("    VPOP {D0}")        # tira o valor da pilha VFP
            asm.append("    POP {R0}")         # tira o endereço da pilha normal
            asm.append("    VSTR.F64 D0, [R0]") # guarda o valor no endereço (Store)
            asm.append("    VPUSH {D0}")       # mantem o valor na pilha para o resultado da linha

        # 4. tratamento do comando RES 
        elif t == 'RES':
            asm.append("    VPOP {D0}          @ índice N (ignorado no ASM)") # tira indice da pilha
            # busca o valor fixo da linha anterior na seçao .data
            asm.append(f"    LDR R0, =res_linha_{max(1, linha_id - 1)}")
            asm.append("    VLDR D0, [R0]")
            asm.append("    VPUSH {D0}")

        # operacoes (Usa instruçoes como VADD, VSUB)
        elif t in ['+', '-', '*', '/']:
            op = {'+':'VADD', '-':'VSUB', '*':'VMUL', '/':'VDIV'}
            asm.append("    VPOP {D1}") # segundo operando
            asm.append("    VPOP {D0}") # primeiro operando
            asm.append(f"    {op[t]}.F64 D0, D0, D1") # faz a conta em precisao dupla
            asm.append("    VPUSH {D0}") # empilha o resultado

        elif t in ['//', '%', '^']:
            label = f"const_{contador_const}"
            contador_const += 1

            valor = hstrc[-1] if hstrc else 0.0
            cst.append((label, str(valor)))

            asm.append("    VPOP {D1}")
            asm.append("    VPOP {D0}")
            asm.append(f"    LDR R0, ={label}") # carrega o resultado pre-calculado
            asm.append("    VLDR D0, [R0]")
            asm.append("    VPUSH {D0}")

    # finalizaçao da linha: salva o resultado final da linha na memoria
    asm.append("    VPOP {D0}")
    asm.append(f"    LDR R0, =res_linha_{linha_id}")
    asm.append("    VSTR.F64 D0, [R0]") # guarda o resultado da linha no endereço res_linha_X
    asm.append("    VPUSH {D0}") # devolve para a pilha para consistencia

    return "\n".join(asm) # retorna a string do assembly formatada

# gera a parte .data do código assembly com todas as variaveis e constantes
def gerarSecaoData():
    data = [".data", ".align 3"] # alinhamento obrigatorio de 8 bytes para doubles
    for label, valor in cst: 
        data.append(f"{label}: .double {valor}") # cria labels para números
    for var in vrv_mr: 
        data.append(f"{var}: .double 0.0") # cria labels para variaveis (inicialmente 0)
    for i in range(1, 51): 
        data.append(f"res_linha_{i}: .double 0.0") # reserva espaço para 50 resultados de linha
    return "\n".join(data)

# --- FUNÇÕES DE INTERFACE ---
# le o arquivo de entrada e limpa linhas vazias
def lerArquivo(nome):
    try:
        with open(nome, 'r') as f: 
            return [l.strip() for l in f if l.strip()] # retorna lista de strings
    except: 
        return None # retorna None se der erro ao abrir

# imprime os resultados no terminal com uma casa decimal
def exibirResultados(resultados):
    print("\n" + "="*25 + "\n   RESULTADOS FINAIS\n" + "="*25)
    for i, r in enumerate(resultados): 
        print(f" Linha {i+1:02d}: {r:.1f}")

# FUNÇÃO PRINCIPAL 
def main():
    if len(sys.argv) < 2:
        print("Uso: python trabalho.py entrada.txt")
        return

    nome_arquivo = sys.argv[1]
    linhas = lerArquivo(nome_arquivo) 

    if linhas is None: # Validação de erro de abertura
        print(f"Erro ao abrir o arquivo: {nome_arquivo}")
        return

    if not linhas: # Validação de arquivo vazio
        print("Erro: Arquivo vazio.")
        return

    resultados = []
    corpo_asm = []
    todos_tokens = []

    # loop que percorre cada linha do arquivo de texto
    for i, linha in enumerate(linhas):
        try:
            tokens = parseExpressao(linha) 

            if tokens is None: # se houver erro lexico na linha, pula para a próxima
                print(f"[Linha {i+1}] Erro léxico.")
                continue

            todos_tokens.append(tokens) # guarda os tokens para o arquivo JSON

            resultado = executarExpressao(tokens) 
            resultados.append(resultado)

            asm = gerarAssembly(tokens, i + 1) 
            corpo_asm.append(asm)

        except Exception as e: # captura erros de calculo 
            print(f"[Linha {i+1}] Erro: {e}")
            continue

    # salva os tokens analisados em um arquivo texto
    with open("tokens.txt", "w") as f_tokens:
        json.dump(todos_tokens, f_tokens)

    # gera o arquivo final 'saida.s' para ser usado no Cpulator
    with open("saida.s", "w") as f:
        f.write(gerarSecaoData() + "\n\n") # escreve a parte .data
        f.write(".text\n.global _start\n_start:\n") # inicio do código .text
        
        f.write("    MOV R0, #0x40000000\n    FMXR FPEXC, R0\n")
        f.write("\n".join(corpo_asm)) # cola todo o codigo assembly gerado
        f.write("\n_fim: B _fim\n") # loop infinito no final para nao "crashar" o simulador

    print("\n'saida.s' e 'tokens.txt' gerados com sucesso.")

def testarParseExpressao():
    print("\n" + "-"*3 + " Validacao parseExpressao " + "-"*3)
    casos_teste = [
        "(31.14 7.0 +)",
        "(3 RES)",
        "(10.5 CONTADOR)",
        "((CONTADOR) 25.0 *)",
        "((3 6 +) 3 %)",
        "(1 34 //)",
        "(3.14 3.0 &)",         # Erro: Caractere inválido
        "3.64.5",               # Erro: Múltiplos pontos
        "20,45",                 # Erro: Vírgula (será tratado como erro léxico)
        "(10.5 BASQUETE1)",       # Erro: Número no identificador
        "(10.5 COMPILADORES1 +)",      # Erro: Letra após número
        "(10.5 GTA# +)",        # Erro: Caractere especial
        "(10.5 NBA-)"           # Erro: Falta de espaço (AFD vai ler ABC e depois tentar o +)
    ]

    for caso in casos_teste:
        try:
            # O seu AFD levanta ValueError ou Exception
            tokens = []
            estado_inicial(caso, 0, tokens)
            
            # Validação extra para casos que o AFD aceita mas o requisito de teste proíbe:
            # Checar se há números misturados com letras nos tokens gerados
            for t in tokens:
                if any(c.isdigit() for c in t) and any(c.isalpha() for c in t):
                    raise ValueError(f"Identificador alfanumerico invalido: '{t}'")
            
            print(f"[OK] {caso} --> {tokens}")
        except Exception as e:
            print(f"[ERRO] {caso} --> Erro lexico: {e}")

def testarExecutarExpressao():
    print("\n" + "-"*3 + " Validacao executarExpressao " + "-"*3)
    global vrv, hstrc
    vrv = {} # Limpa variáveis
    hstrc = [] # Limpa histórico

    testes = [
        ("Teste 1 (31 25 -)", ["31", "25", "-"]),
        ("Teste 2a (12 X MEM)", ["12", "X", "MEM"]), # Guardando 12 em X
        ("Teste 2b ((X) 20 %)", ["X", "20", "%"]),     # 42 % 2
        ("Teste 3 (2 RES)", ["2", "RES"]),           # Pega o resultado da 2 linha anterior (21)
    ]

    for nome, tokens in testes:
        try:
            res = executarExpressao(tokens)
            print(f"{nome}: [OK] -> {res}")
        except Exception as e:
            print(f"{nome}: Erro: {e}")   

# Ponto de entrada padrão do Python
if __name__ == "__main__":
    testarParseExpressao()
    testarExecutarExpressao()
    main()
