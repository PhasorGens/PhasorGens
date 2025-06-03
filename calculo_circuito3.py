# Nome do arquivo: calculadora_circuito.py (continuação)
import cmath
import math

# ... (função formatar_complexo - sem alterações)
def formatar_complexo(numero_complexo):
    """Converte um número complexo para string em formato retangular e polar."""
    if abs(numero_complexo.real) < 1e-9 and abs(numero_complexo.imag) < 1e-9:
        retangular = "0.0000"
    elif abs(numero_complexo.imag) < 1e-9:
        retangular = f"{numero_complexo.real:.4f}"
    elif abs(numero_complexo.real) < 1e-9:
        retangular = f"{'' if numero_complexo.imag >= 0 else '-'}j{abs(numero_complexo.imag):.4f}"
    else:
        retangular = f"{numero_complexo.real:.4f} {'+' if numero_complexo.imag >= 0 else '-'} j{abs(numero_complexo.imag):.4f}"

    magnitude, fase_rad = cmath.polar(numero_complexo)
    if abs(magnitude) < 1e-9: 
        fase_graus = 0.0
    else:
        fase_graus = math.degrees(fase_rad)
    polar = f"{magnitude:.4f} ∠ {fase_graus:.2f}°"
    return retangular, polar

# ... (função obter_impedancia_componente - sem alterações)
def obter_impedancia_componente():
    """Pergunta ao usuário o tipo e valor de um componente e retorna sua impedância complexa."""
    while True:
        tipo_componente = input("Qual o tipo do componente? (R para Resistor, L para Indutor, C para Capacitor): ").upper()
        if tipo_componente in ['R', 'L', 'C']:
            break
        else:
            print("Tipo inválido. Por favor, digite R, L ou C.")

    while True:
        try:
            if tipo_componente == 'R':
                valor_str = input("Digite o valor da resistência (em Ohms, ex: 100): ")
                valor = float(valor_str)
                if valor < 0:
                    print("A resistência não pode ser negativa. Tente novamente.")
                    continue
                return complex(valor, 0)
            elif tipo_componente == 'L':
                valor_str = input("Digite o valor da reatância indutiva (XL em Ohms, ex: 50 para j50 Ohms): ")
                valor = float(valor_str)
                if valor < 0:
                    print("A reatância indutiva (XL) não pode ser negativa. O 'j' é adicionado automaticamente. Tente novamente.")
                    continue
                return complex(0, valor)
            elif tipo_componente == 'C':
                valor_str = input("Digite o valor da reatância capacitiva (XC em Ohms, ex: 25 para -j25 Ohms): ")
                valor = float(valor_str)
                if valor < 0:
                    print("A reatância capacitiva (XC) deve ser um valor positivo. O '-j' é adicionado automaticamente. Tente novamente.")
                    continue
                return complex(0, -valor)
        except ValueError:
            print("Valor inválido. Por favor, digite um número.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}. Tente novamente.")

# --- Parte Principal Atualizada ---
if __name__ == "__main__":
    print("--- Calculadora de Impedância e Corrente de Circuito CA ---")

    # Coleta da frequência da fonte (opcional para os cálculos atuais, mas bom para ter)
    while True:
        try:
            frequencia_hz_str = input("Digite a frequência da fonte CA (em Hz, ex: 60): ")
            frequencia_hz = float(frequencia_hz_str)
            if frequencia_hz <= 0:
                print("A frequência deve ser um valor positivo. Tente novamente.")
                continue
            break
        except ValueError:
            print("Valor inválido para frequência. Por favor, digite um número.")
    
    print(f"Frequência da fonte: {frequencia_hz:.2f} Hz")


    print("\n--- Adicionando o PRIMEIRO componente do circuito ---")
    impedancia_total_equivalente = obter_impedancia_componente()
    ret_eq, pol_eq = formatar_complexo(impedancia_total_equivalente)
    print(f"Impedância equivalente atual: Retangular: {ret_eq} | Polar: {pol_eq}")

    contador_componentes = 1
    while True:
        contador_componentes += 1
        adicionar_mais = input(f"\nDeseja adicionar o {contador_componentes}º componente? (S/N): ").upper()
        if adicionar_mais != 'S':
            break

        print(f"\n--- Adicionando o {contador_componentes}º componente ---")
        nova_impedancia = obter_impedancia_componente()
        ret_nova, pol_nova = formatar_complexo(nova_impedancia)
        print(f"Impedância do novo componente: Retangular: {ret_nova} | Polar: {pol_nova}")

        while True:
            tipo_conexao = input("Conectar em SÉRIE (S) ou PARALELO (P) com a impedância equivalente atual? ").upper()
            if tipo_conexao in ['S', 'P']:
                break
            else:
                print("Opção inválida. Digite S para série ou P para paralelo.")

        if tipo_conexao == 'S':
            impedancia_total_equivalente += nova_impedancia
            print("Componente adicionado em SÉRIE.")
        elif tipo_conexao == 'P':
            soma_denominador = impedancia_total_equivalente + nova_impedancia
            if abs(soma_denominador) < 1e-9: # Verifica se o denominador é próximo de zero
                print("\nERRO: Divisão por zero ao calcular impedância em paralelo (Z_eq_ant + Z_novo ≈ 0).")
                print("Não é possível conectar estas duas impedâncias em paralelo desta forma (ressonância).")
                print("O último componente não foi adicionado. A impedância equivalente anterior foi mantida.")
                contador_componentes -=1 
            else:
                impedancia_total_equivalente = (impedancia_total_equivalente * nova_impedancia) / soma_denominador
                print("Componente adicionado em PARALELO.")
        
        ret_eq, pol_eq = formatar_complexo(impedancia_total_equivalente)
        print(f"Nova impedância equivalente: Retangular: {ret_eq} | Polar: {pol_eq}")

    print("\n--- Configuração do Circuito Finalizada ---")
    ret_final, pol_final = formatar_complexo(impedancia_total_equivalente)
    print(f"Impedância Total Equivalente do Circuito (Z_total):")
    print(f"  Forma Retangular: {ret_final} Ohms")
    print(f"  Forma Polar:      {pol_final} Ohms")

    # Adicionar entrada da tensão da fonte e cálculo da corrente
    if abs(impedancia_total_equivalente) < 1e-9: # Verifica se Z_total é praticamente zero (curto-circuito)
        print("\nA impedância total do circuito é zero (curto-circuito). A corrente tenderá ao infinito se uma tensão for aplicada.")
        print("Não é possível calcular a corrente de forma significativa neste caso.")
    else:
        print("\n--- Entrada da Fonte de Tensão ---")
        while True:
            try:
                v_magnitude_str = input("Digite a magnitude da tensão da fonte (em Volts, ex: 120): ")
                v_magnitude = float(v_magnitude_str)
                if v_magnitude < 0:
                    print("A magnitude da tensão não pode ser negativa. Tente novamente.")
                    continue
                
                v_fase_str = input("Digite a fase da tensão da fonte (em Graus, ex: 0): ")
                v_fase_graus = float(v_fase_str)
                break
            except ValueError:
                print("Valor inválido para tensão ou fase. Por favor, digite um número.")
        
        v_fase_rad = math.radians(v_fase_graus)
        tensao_fonte = cmath.rect(v_magnitude, v_fase_rad) # Converte (Mag, Fase_rad) para complexo

        ret_v, pol_v = formatar_complexo(tensao_fonte)
        print(f"\nTensão da Fonte (V_fonte):")
        print(f"  Forma Retangular: {ret_v} V")
        print(f"  Forma Polar:      {pol_v} V")

        # Calcular Corrente Total I = V / Z
        corrente_total = tensao_fonte / impedancia_total_equivalente
        
        ret_i, pol_i = formatar_complexo(corrente_total)
        print(f"\nCorrente Total do Circuito (I_total):")
        print(f"  Forma Retangular: {ret_i} A")
        print(f"  Forma Polar:      {pol_i} A")

    print("\n--- Fim do Programa ---")