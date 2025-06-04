import streamlit as st
import cmath
import math
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# Funções auxiliares
def formatar_complexo(numero_complexo):
    """Formata um número complexo para exibição nas formas retangular e polar."""
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

def calcular_potencias(V, I, Z):
    """Calcula as potências ativa, reativa e aparente."""
    S = V * I  # Potência aparente (VA)
    P = S * math.cos(cmath.phase(Z))  # Potência ativa (W)
    Q = S * math.sin(cmath.phase(Z))  # Potência reativa (VAR)
    fp = math.cos(cmath.phase(Z))  # Fator de potência
    return P, Q, S, fp

def plot_fasores(Z_total):
    """Gera um diagrama fasorial da impedância."""
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Calcula a magnitude e fase para o texto
    magnitude, fase_rad = cmath.polar(Z_total)
    fase_graus = math.degrees(fase_rad)
    
    # Plota o fasor como uma seta
    ax.quiver(0, 0, Z_total.real, Z_total.imag,
              angles='xy', scale_units='xy', scale=1,
              color='red', width=0.005, zorder=3,
              label=f'Z = {magnitude:.2f}∠{fase_graus:.1f}°')
    
    # Calcula os limites do gráfico
    max_val = max(abs(Z_total.real), abs(Z_total.imag), 1)
    lim = max_val * 1.2  # Adiciona 20% de margem
    
    # Configura os limites e a grade
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    
    # Adiciona linhas de eixo
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    
    # Configura a grade
    ax.grid(True, linestyle='--', alpha=0.3, zorder=0)
    
    # Adiciona rótulos e título
    ax.set_xlabel('Parte Real (Ω)')
    ax.set_ylabel('Parte Imaginária (Ω)')
    ax.set_title('Diagrama Fasorial da Impedância')
    
    # Adiciona legenda
    ax.legend(loc='upper right')
    
    # Garante que o aspecto seja igual (círculo perfeito)
    ax.set_aspect('equal')
    
    return fig

def plot_resposta_frequencia(R, L, C, freq_min=10, freq_max=1000):
    """Gera o gráfico da resposta em frequência para um circuito RLC série."""
    freqs = np.logspace(np.log10(freq_min), np.log10(freq_max), 200)
    impedancias = []
    
    for f in freqs:
        XL = 2 * math.pi * f * L if L > 0 else 0
        XC = 1/(2 * math.pi * f * C) if C > 0 else 0
        Z = complex(R, XL - XC)
        impedancias.append(abs(Z))
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.semilogx(freqs, impedancias)
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel('Impedância (Ω)')
    ax.set_title('Resposta em Frequência do Circuito')
    ax.grid(True, which="both", ls="-")
    
    # Marcar frequência de ressonância se aplicável
    if L > 0 and C > 0:
        fr = 1/(2 * math.pi * math.sqrt(L * C))
        Zr = math.sqrt(R**2 + (2 * math.pi * fr * L - 1/(2 * math.pi * fr * C))**2)
        ax.axvline(fr, color='red', linestyle='--', alpha=0.7)
        ax.text(fr, max(impedancias)*0.9, f'Ressonância: {fr:.2f} Hz', 
                horizontalalignment='center')
    
    return fig

# Inicialização do estado da sessão
def init_session_state():
    """Inicializa todas as variáveis de estado necessárias."""
    if 'componentes' not in st.session_state:
        st.session_state.componentes = []
    if 'impedancia_total' not in st.session_state:
        st.session_state.impedancia_total = complex(0, 0)
    if 'primeiro_componente' not in st.session_state:
        st.session_state.primeiro_componente = True
    if 'conexao' not in st.session_state:
        st.session_state.conexao = "SÉRIE"
    if 'tipo_componente' not in st.session_state:
        st.session_state.tipo_componente = 'Resistor (R)'
    if 'valor_componente' not in st.session_state:
        st.session_state.valor_componente = 0.0
    if 'fonte_voltagem' not in st.session_state:
        st.session_state.fonte_voltagem = 120.0
    if 'fonte_frequencia' not in st.session_state:
        st.session_state.fonte_frequencia = 60.0
    if 'modo_avancado' not in st.session_state:
        st.session_state.modo_avancado = False

# Configuração da página
st.set_page_config(
    page_title="Simulador de Circuitos CA", 
    layout="wide",
    page_icon="⚡"
)

# Inicializa o estado da sessão
init_session_state()

# Interface principal
st.title("⚡ Simulador de Circuitos de Corrente Alternada")
st.markdown("""
    *Simule circuitos RLC em série ou paralelo e visualize as propriedades do circuito.*
    """)

# Barra lateral para configurações da fonte
with st.sidebar:
    st.header("Configurações da Fonte")
    st.session_state.fonte_voltagem = st.number_input(
        "Tensão (Vrms):", 
        min_value=0.0, 
        value=st.session_state.fonte_voltagem, 
        step=1.0
    )
    st.session_state.fonte_frequencia = st.number_input(
        "Frequência (Hz):", 
        min_value=0.0, 
        value=st.session_state.fonte_frequencia, 
        step=1.0
    )
    
    st.header("Opções Avançadas")
    st.session_state.modo_avancado = st.checkbox(
        "Modo Avançado (L/C como valores físicos)", 
        value=st.session_state.modo_avancado
    )
    
    if st.button("Reiniciar Circuito"):
        st.session_state.componentes = []
        st.session_state.impedancia_total = complex(0, 0)
        st.session_state.primeiro_componente = True
        st.session_state.conexao = "SÉRIE"
        st.session_state.valor_componente = 0.0
        st.success("Circuito reiniciado com sucesso!")
        st.rerun()

# Formulário para adicionar componentes
with st.expander("Adicionar Componentes", expanded=True):
    with st.form(key="form_componente"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.selectbox(
                "Tipo de Componente:",
                ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'),
                key='select_tipo_componente'
            )
            
        with col2:
            if st.session_state.modo_avancado:
                if tipo == 'Resistor (R)':
                    label = "Resistência (Ω):"
                    min_val = 0.0
                elif tipo == 'Indutor (L)':
                    label = "Indutância (H):"
                    min_val = 0.0
                else:  # Capacitor
                    label = "Capacitância (F):"
                    min_val = 1e-12  # 1 pF como valor mínimo
            else:
                if tipo == 'Resistor (R)':
                    label = "Resistência (Ω):"
                    min_val = 0.0
                elif tipo == 'Indutor (L)':
                    label = "Reatância Indutiva (Ω):"
                    min_val = 0.0
                else:  # Capacitor
                    label = "Reatância Capacitiva (Ω):"
                    min_val = 0.0
            
            valor = st.number_input(
                label,
                min_value=min_val,
                value=st.session_state.valor_componente,
                step=0.01 if not st.session_state.modo_avancado else 1e-6,
                format="%.4f" if st.session_state.modo_avancado else "%.2f"
            )
        
        if not st.session_state.primeiro_componente:
            conexao = st.radio(
                "Conectar em:",
                ('SÉRIE', 'PARALELO'),
                index=0 if st.session_state.conexao == "SÉRIE" else 1,
                horizontal=True
            )
        
        if st.form_submit_button("Adicionar Componente"):
            if valor <= 0:
                st.error("O valor do componente deve ser positivo!")
            else:
                # Calcula a impedância do componente
                if st.session_state.modo_avancado:
                    if tipo == 'Resistor (R)':
                        Z = complex(valor, 0)
                        desc = f"R: {valor:.4f} Ω"
                    elif tipo == 'Indutor (L)':
                        XL = 2 * math.pi * st.session_state.fonte_frequencia * valor
                        Z = complex(0, XL)
                        desc = f"L: {valor:.4f} H (j{XL:.2f} Ω)"
                    else:  # Capacitor
                        XC = 1/(2 * math.pi * st.session_state.fonte_frequencia * valor)
                        Z = complex(0, -XC)
                        desc = f"C: {valor:.4f} F (-j{XC:.2f} Ω)"
                else:
                    if tipo == 'Resistor (R)':
                        Z = complex(valor, 0)
                        desc = f"R: {valor:.2f} Ω"
                    elif tipo == 'Indutor (L)':
                        Z = complex(0, valor)
                        desc = f"L: j{valor:.2f} Ω"
                    else:  # Capacitor
                        Z = complex(0, -valor)
                        desc = f"C: -j{valor:.2f} Ω"
                
                # Adiciona ao circuito
                if st.session_state.primeiro_componente:
                    st.session_state.impedancia_total = Z
                    st.session_state.primeiro_componente = False
                    st.session_state.componentes.append(f"Primeiro componente: {desc}")
                else:
                    st.session_state.conexao = conexao
                    if conexao == 'SÉRIE':
                        st.session_state.impedancia_total += Z
                        st.session_state.componentes.append(f"Adicionado em série: {desc}")
                    else:  # PARALELO
                        if abs(st.session_state.impedancia_total + Z) < 1e-9:
                            st.error("Erro: Divisão por zero na conexão paralela!")
                        else:
                            st.session_state.impedancia_total = (
                                st.session_state.impedancia_total * Z
                            ) / (st.session_state.impedancia_total + Z)
                            st.session_state.componentes.append(f"Adicionado em paralelo: {desc}")
                
                st.session_state.valor_componente = 0.0
                st.success(f"Componente adicionado: {desc}")
                st.rerun()

# Visualização do circuito
st.subheader("Circuito Montado")
if not st.session_state.componentes:
    st.info("Nenhum componente adicionado ainda. Use o formulário acima para começar.")
else:
    for i, comp in enumerate(st.session_state.componentes, 1):
        st.write(f"{i}. {comp}")

# Resultados e análises
st.subheader("Resultados da Análise")
ret_total, pol_total = formatar_complexo(st.session_state.impedancia_total)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Impedância Total:**")
    st.markdown(f"- Forma retangular: `{ret_total} Ω`")
    st.markdown(f"- Forma polar: `{pol_total}`")
    
    if st.session_state.fonte_voltagem > 0 and abs(st.session_state.impedancia_total) > 1e-9:
        corrente = st.session_state.fonte_voltagem / abs(st.session_state.impedancia_total)
        fase_graus = math.degrees(cmath.phase(st.session_state.impedancia_total))
        st.markdown("**Análise com Fonte:**")
        st.markdown(f"- Corrente total: `{corrente:.4f} A`")
        st.markdown(f"- Ângulo de fase: `{fase_graus:.2f}°`")
        
        P, Q, S, fp = calcular_potencias(
            st.session_state.fonte_voltagem, 
            corrente, 
            st.session_state.impedancia_total
        )
        st.markdown("**Potências:**")
        st.markdown(f"- Ativa (P): `{P:.4f} W`")
        st.markdown(f"- Reativa (Q): `{Q:.4f} VAR`")
        st.markdown(f"- Aparente (S): `{S:.4f} VA`")
        st.markdown(f"- Fator de potência: `{fp:.4f}`")

with col2:
    if abs(st.session_state.impedancia_total) > 1e-9:
        st.pyplot(plot_fasores(st.session_state.impedancia_total))
        
        # Verifica se temos pelo menos um indutor e um capacitor para análise de ressonância
        componentes = [c.split(':')[0] for c in st.session_state.componentes]
        if 'L' in ''.join(componentes) and 'C' in ''.join(componentes) and st.session_state.fonte_frequencia > 0:
            # Estimativa de L e C para o gráfico (simplificado)
            L_est = 0
            C_est = 0
            for comp in st.session_state.componentes:
                if 'L:' in comp:
                    parts = comp.split('j')
                    if len(parts) > 1:
                        xl = float(parts[1].split(' ')[0])
                        L_est = xl / (2 * math.pi * st.session_state.fonte_frequencia)
                elif 'C:' in comp:
                    parts = comp.split('-j')
                    if len(parts) > 1:
                        xc = float(parts[1].split(' ')[0])
                        C_est = 1 / (2 * math.pi * st.session_state.fonte_frequencia * xc)
            
            if L_est > 0 and C_est > 0:
                st.pyplot(plot_resposta_frequencia(
                    R=abs(st.session_state.impedancia_total.real),
                    L=L_est,
                    C=C_est,
                    freq_min=0.1,
                    freq_max=1000
                ))

# Rodapé
st.markdown("---")
st.markdown("""
    **Simulador de Circuitos CA**  
    Desenvolvido com Python + Streamlit  
    *Versão 1.0 - Para fins educacionais*
""")