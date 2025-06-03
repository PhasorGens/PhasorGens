# Nome do arquivo: app_web_circuito.py
import streamlit as st
import cmath
import math

# --- Funções do nosso código anterior (formatar_complexo) ---
# Podemos copiar a função formatar_complexo aqui
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

# --- Lógica da Aplicação Web ---
st.set_page_config(page_title="Calculadora de Circuitos CA", layout="wide") # Configura o título da aba e layout
st.title("Calculadora de Impedâncias de Circuitos CA ⚡")

st.subheader("Adicionar Novo Componente ao Circuito")

# Usaremos o st.session_state para guardar a lista de componentes e a impedância total
if 'componentes_adicionados' not in st.session_state:
    st.session_state.componentes_adicionados = [] # Lista para guardar strings descritivas
if 'impedancia_total_eq' not in st.session_state:
    st.session_state.impedancia_total_eq = complex(0,0)
if 'primeiro_componente' not in st.session_state:
    st.session_state.primeiro_componente = True


# Formulário para adicionar componentes
with st.form(key="form_componente"):
    col1, col2, col3 = st.columns([2,2,1]) # Dividir em colunas para melhor layout
    
    with col1:
        tipo_componente = st.selectbox(
            "Tipo de Componente:",
            ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'),
            key="tipo_comp"
        )
    
    with col2:
        if tipo_componente == 'Resistor (R)':
            label_valor = "Resistência (Ohms):"
        elif tipo_componente == 'Indutor (L)':
            label_valor = "Reatância Indutiva XL (Ohms):"
        else: # Capacitor (C)
            label_valor = "Reatância Capacitiva XC (Ohms):"
        
        valor_componente_str = st.text_input(label_valor, value="0.0", key="valor_comp_str")

    with col3:
        st.write("") # Espaçador
        st.write("") # Espaçador para alinhar botão com os inputs
        submit_button = st.form_submit_button(label="Adicionar Componente")


if submit_button:
    try:
        valor_componente = float(valor_componente_str)
        impedancia_nova = complex(0,0)
        desc_comp = ""

        if valor_componente < 0 and tipo_componente != 'Resistor (R)': # R pode ser 0, L e C reatâncias devem ser >0
             st.error("Valores de reatância (XL, XC) devem ser positivos. O sinal de 'j' é aplicado automaticamente.")
        elif valor_componente < 0 and tipo_componente == 'Resistor (R)':
            st.error("Resistência não pode ser negativa.")
        else:
            if tipo_componente == 'Resistor (R)':
                impedancia_nova = complex(valor_componente, 0)
                desc_comp = f"Resistor: {valor_componente:.2f} Ω"
            elif tipo_componente == 'Indutor (L)':
                impedancia_nova = complex(0, valor_componente)
                desc_comp = f"Indutor: j{valor_componente:.2f} Ω (XL)"
            elif tipo_componente == 'Capacitor (C)':
                impedancia_nova = complex(0, -valor_componente)
                desc_comp = f"Capacitor: -j{valor_componente:.2f} Ω (XC)"

            if st.session_state.primeiro_componente:
                st.session_state.impedancia_total_eq = impedancia_nova
                st.session_state.primeiro_componente = False
                st.success(f"Primeiro componente adicionado: {desc_comp}")
            else:
                # Por enquanto, vamos apenas mostrar o componente. A lógica de série/paralelo virá depois.
                # Aqui precisaremos perguntar se é série ou paralelo
                # E então atualizar st.session_state.impedancia_total_eq
                st.info(f"Novo componente (lógica de conexão pendente): {desc_comp}")
                st.warning("A lógica para conectar em série/paralelo ainda será implementada nesta interface.")
            
            st.session_state.componentes_adicionados.append(f"{desc_comp} | Z = {formatar_complexo(impedancia_nova)[0]}")


    except ValueError:
        st.error("Valor do componente inválido. Por favor, insira um número.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

st.subheader("Circuito Atual")
if not st.session_state.componentes_adicionados:
    st.write("Nenhum componente adicionado ainda.")
else:
    for comp_str in st.session_state.componentes_adicionados:
        st.write(f"- {comp_str}")
    
    st.markdown("---")
    ret_total, pol_total = formatar_complexo(st.session_state.impedancia_total_eq)
    st.subheader(f"Impedância Total Equivalente (Z_total):")
    st.markdown(f"**Retangular:** `{ret_total}` Ohms")
    st.markdown(f"**Polar:** `{pol_total}` Ohms")


# Para rodar este app:
# 1. Salve como app_web_circuito.py
# 2. Abra o terminal na pasta do arquivo
# 3. Digite: streamlit run app_web_circuito.py