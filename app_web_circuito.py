import streamlit as st
import cmath
import math

def formatar_complexo(numero_complexo):
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

def init_session_state():
    if 'componentes_adicionados' not in st.session_state:
        st.session_state.componentes_adicionados = []
    if 'impedancia_total_eq' not in st.session_state:
        st.session_state.impedancia_total_eq = complex(0, 0)
    if 'primeiro_componente' not in st.session_state:
        st.session_state.primeiro_componente = True
    if 'ultimo_tipo_conexao' not in st.session_state:
        st.session_state.ultimo_tipo_conexao = "SÉRIE"
    if 'tipo_componente_atual' not in st.session_state:
        st.session_state.tipo_componente_atual = 'Resistor (R)'
    if 'valor_componente_atual' not in st.session_state:
        st.session_state.valor_componente_atual = 0.0
    if 'ultimo_tipo_componente' not in st.session_state:
        st.session_state.ultimo_tipo_componente = 'Resistor (R)'

st.set_page_config(page_title="Calculadora de Circuitos CA", layout="wide")
st.title("Calculadora de Impedâncias de Circuitos CA ⚡")

init_session_state()

st.subheader("Adicionar Novo Componente ao Circuito")

with st.form(key="form_componente"):
    col1, col2 = st.columns(2)
    with col1:
        tipo_componente = st.selectbox(
            "Tipo de Componente:",
            ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'),
            key='select_tipo_componente'
        )
        
        # Verifica se o tipo de componente mudou
        if tipo_componente != st.session_state.ultimo_tipo_componente:
            st.session_state.valor_componente_atual = 0.0
            st.session_state.ultimo_tipo_componente = tipo_componente
    
    with col2:
        if tipo_componente == 'Resistor (R)':
            label_valor = "Resistência (Ohms):"
        elif tipo_componente == 'Indutor (L)':
            label_valor = "Reatância Indutiva XL (Ohms):"
        else:
            label_valor = "Reatância Capacitiva XC (Ohms):"
        
        valor_componente = st.number_input(
            label_valor,
            step=0.01,
            format="%.2f",
            value=float(st.session_state.valor_componente_atual),
            key='input_valor_componente'
        )
    
    if not st.session_state.primeiro_componente:
        tipo_conexao = st.radio(
            "Conectar em:",
            ('SÉRIE', 'PARALELO'),
            index=0 if st.session_state.ultimo_tipo_conexao == "SÉRIE" else 1,
            key='radio_tipo_conexao'
        )
    
    submit_button = st.form_submit_button(label="Adicionar Componente")

if submit_button:
    # Atualiza o valor na sessão
    st.session_state.valor_componente_atual = valor_componente
    
    # Verifica se o valor é válido
    if valor_componente <= 0:
        st.error("O valor do componente deve ser positivo e maior que zero.")
    else:
        # Calcula a impedância do novo componente
        if tipo_componente == 'Resistor (R)':
            impedancia_nova = complex(valor_componente, 0)
            desc_comp = f"Resistor: {valor_componente:.2f} Ω"
        elif tipo_componente == 'Indutor (L)':
            impedancia_nova = complex(0, valor_componente)
            desc_comp = f"Indutor: j{valor_componente:.2f} Ω (XL)"
        else:  # Capacitor
            impedancia_nova = complex(0, -valor_componente)
            desc_comp = f"Capacitor: -j{valor_componente:.2f} Ω (XC)"
        
        # Adiciona ao circuito
        if st.session_state.primeiro_componente:
            st.session_state.impedancia_total_eq = impedancia_nova
            st.session_state.primeiro_componente = False
            mensagem = f"Primeiro componente adicionado: {desc_comp}"
            st.session_state.componentes_adicionados.append(
                f"{desc_comp} | Z = {formatar_complexo(impedancia_nova)[0]}"
            )
        else:
            st.session_state.ultimo_tipo_conexao = tipo_conexao
            if tipo_conexao == 'SÉRIE':
                st.session_state.impedancia_total_eq += impedancia_nova
                conexao_str = "em SÉRIE"
            else:  # PARALELO
                soma_denominador = st.session_state.impedancia_total_eq + impedancia_nova
                if abs(soma_denominador) < 1e-9:
                    st.error("ERRO: Divisão por zero.")
                else:
                    st.session_state.impedancia_total_eq = (
                        st.session_state.impedancia_total_eq * impedancia_nova
                    ) / soma_denominador
                    conexao_str = "em PARALELO"
            
            if 'conexao_str' in locals():
                mensagem = f"Componente ({desc_comp}) adicionado {conexao_str}."
                st.session_state.componentes_adicionados.append(
                    f"Conectado {conexao_str} -> {desc_comp} | Z_comp = {formatar_complexo(impedancia_nova)[0]}"
                )
        
        st.success(mensagem)
        st.session_state.valor_componente_atual = 0.0
        st.rerun()

st.markdown("---")
st.subheader("Circuito Atual")
if not st.session_state.componentes_adicionados:
    st.write("Nenhum componente adicionado ainda.")
else:
    for i, comp_str in enumerate(st.session_state.componentes_adicionados):
        st.write(f"{i+1}. {comp_str}")

st.markdown("---")
ret_total, pol_total = formatar_complexo(st.session_state.impedancia_total_eq)
st.subheader(f"Impedância Total Equivalente (Z_total):")
st.markdown(f"**Retangular:** `{ret_total}` Ohms")
st.markdown(f"**Polar:** `{pol_total}` Ohms")

if st.button("Reiniciar Circuito", key="reiniciar_btn"):
    st.session_state.componentes_adicionados = []
    st.session_state.impedancia_total_eq = complex(0, 0)
    st.session_state.primeiro_componente = True
    st.session_state.ultimo_tipo_conexao = "SÉRIE"
    st.session_state.tipo_componente_atual = 'Resistor (R)'
    st.session_state.valor_componente_atual = 0.0
    st.session_state.ultimo_tipo_componente = 'Resistor (R)'
    st.success("Circuito reiniciado!")
    st.rerun()