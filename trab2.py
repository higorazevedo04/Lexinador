# =========================================================
# Nomes: Higor Azevedo
# Grupo: SEU_GRUPO
# =========================================================

import json
import os

# =========================================================
# ALUNO 1: ANALISADOR LÉXICO (FSM COM FUNÇÕES)
# =========================================================

class LexerRPN:
    def __init__(self, linha):
        self.linha = linha
        self.pos = 0
        self.tokens = []

    def proximo_char(self):
        if self.pos < len(self.linha):
            c = self.linha[self.pos]
            self.pos += 1
            return c
        return None

    def retroceder(self):
        self.pos -= 1

    def estado_inicial(self):
        c = self.proximo_char()

        if c is None: return None
        if c.isspace(): return self.estado_inicial
        if c == '(': return self.estado_abre
        if c == ')': return self.estado_fecha
        if c.isdigit(): return lambda: self.estado_numero(c)
        if c.isalpha(): return lambda: self.estado_id(c)
        if c in "+-*/%^": return lambda: self.estado_op(c)

        return self.estado_erro

    def estado_abre(self):
        self.tokens.append(('ABRE', '('))
        return self.estado_inicial

    def estado_fecha(self):
        self.tokens.append(('FECHA', ')'))
        return self.estado_inicial

    def estado_numero(self, acumulado):
        c = self.proximo_char()

        if c and (c.isdigit() or c == '.'):
            if c == '.' and '.' in acumulado:
                return self.estado_erro
            return lambda: self.estado_numero(acumulado + c)

        if c is not None:
            self.retroceder()

        self.tokens.append(('NUM', float(acumulado)))
        return self.estado_inicial

    def estado_id(self, acumulado):
        c = self.proximo_char()

        if c and c.isalpha():
            return lambda: self.estado_id(acumulado + c)

        if c is not None:
            self.retroceder()

        self.tokens.append(('ID', acumulado))
        return self.estado_inicial

    def estado_op(self, c):
        if c == '/':
            prox = self.proximo_char()
            if prox == '/':
                self.tokens.append(('OP', '//'))
            else:
                if prox is not None:
                    self.retroceder()
                self.tokens.append(('OP', '/'))
        else:
            self.tokens.append(('OP', c))

        return self.estado_inicial

    def estado_erro(self):
        pos = self.pos - 1
        char = self.linha[pos] if pos < len(self.linha) else "EOF"
        raise Exception(f"Erro léxico: caractere '{char}' na posição {pos}")

    def run(self):
        estado = self.estado_inicial
        while estado:
            prox = estado()
            if prox is None:
                break
            estado = prox if callable(prox) else prox
        return self.tokens


def parseExpressao(linha):
    lexer = LexerRPN(linha)
    return lexer.run()


# =========================================================
# ALUNO 2: EXECUÇÃO (APENAS TESTE)
# =========================================================

class ExecutorRPN:
    def executarExpressao(self, tokens):
        pilha = []

        for tipo, valor in tokens:
            if tipo == 'NUM':
                pilha.append(valor)

            elif tipo == 'OP':
                b = pilha.pop()
                a = pilha.pop()

                if valor == '+': pilha.append(a + b)
                elif valor == '-': pilha.append(a - b)
                elif valor == '*': pilha.append(a * b)
                elif valor == '/': pilha.append(a / b)
                elif valor == '//': pilha.append(int(a) // int(b))
                elif valor == '%': pilha.append(int(a) % int(b))
                elif valor == '^': pilha.append(a ** b)

        return pilha[-1] if pilha else 0


# =========================================================
# ALUNO 3: LEITURA + ASSEMBLY
# =========================================================

def lerArquivo(nome):
    caminho = os.path.join(os.path.dirname(__file__), nome)
    with open(caminho, 'r') as f:
        return f.readlines()


def gerarAssembly(lista_tokens):
    asm = []

    asm.append(".global _start")
    asm.append(".data")
    asm.append("stack: .space 1024")
    asm.append("sp: .word 0")

    asm.append(".text")
    asm.append("_start:")
    asm.append("LDR R10, =stack")
    asm.append("LDR R11, =sp")

    asm.append("""
push:
    LDR R1, [R11]
    STR R0, [R10, R1]
    ADD R1, R1, #4
    STR R1, [R11]
    BX LR

pop:
    LDR R1, [R11]
    SUB R1, R1, #4
    STR R1, [R11]
    LDR R0, [R10, R1]
    BX LR
""")

    asm.append("""
add:
    BL pop
    MOV R2, R0
    BL pop
    ADD R0, R0, R2
    BL push
    BX LR

sub:
    BL pop
    MOV R2, R0
    BL pop
    SUB R0, R0, R2
    BL push
    BX LR

mul:
    BL pop
    MOV R2, R0
    BL pop
    MUL R0, R0, R2
    BL push
    BX LR

div:
    BL pop
    MOV R2, R0
    BL pop
    SDIV R0, R0, R2
    BL push
    BX LR

mod:
    BL pop
    MOV R2, R0
    BL pop
    SDIV R3, R0, R2
    MLS R0, R3, R2, R0
    BL push
    BX LR

pow:
    BL pop
    MOV R2, R0
    BL pop
    MOV R3, #1
loop_pow:
    CMP R2, #0
    BEQ fim_pow
    MUL R3, R3, R0
    SUB R2, R2, #1
    B loop_pow
fim_pow:
    MOV R0, R3
    BL push
    BX LR
""")

    for tokens in lista_tokens:
        for tipo, valor in tokens:
            if tipo == 'NUM':
                asm.append(f"LDR R0, ={int(valor)}")
                asm.append("BL push")

            elif tipo == 'OP':
                if valor == '+': asm.append("BL add")
                elif valor == '-': asm.append("BL sub")
                elif valor == '*': asm.append("BL mul")
                elif valor == '/': asm.append("BL div")
                elif valor == '//': asm.append("BL div")
                elif valor == '%': asm.append("BL mod")
                elif valor == '^': asm.append("BL pow")

    asm.append("B .")

    return "\n".join(asm)


# =========================================================
# ALUNO 4: MAIN
# =========================================================

def main():
    linhas = lerArquivo("teste1.txt")

    executor = ExecutorRPN()
    todos_tokens = []
    resultados = []

    for i, linha in enumerate(linhas):
        linha = linha.strip()
        if not linha:
            continue

        try:
            tokens = parseExpressao(linha)
            todos_tokens.append(tokens)

            resultado = executor.executarExpressao(tokens)
            resultados.append(resultado)

        except Exception as e:
            print(f"\nERRO NA LINHA {i+1}: {linha}")
            print(e)
            return

    for i, r in enumerate(resultados):
        print(f"Linha {i+1}: {r}")

    with open("tokens.json", "w") as f:
        json.dump(todos_tokens, f, indent=4)

    asm = gerarAssembly(todos_tokens)
    with open("saida.s", "w") as f:
        f.write(asm)

    print("\nArquivos gerados: tokens.json e saida.s")


if __name__ == "__main__":
    main()