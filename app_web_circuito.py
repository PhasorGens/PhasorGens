import streamlit as st
import cmath
import math
import matplotlib.pyplot as plt
import numpy as np
from schemdraw import Drawing
from schemdraw import elements as elm

# --- FUNÇÕES DE CÁLCULO E AUXILIARES ---

def calcular_impedancia_total(componentes, frequencia):
    # Esta função já estava correta e foi mantida.
    if not componentes: return complex(0, 0)
    def get_impedancia_componente(comp):
        if comp['tipo'] == 'Resistor (R)': unidade_base = 'Ω'
        elif comp['tipo'] == 'Indutor (L)': unidade_base = 'H'
        else: unidade_base = 'F'
        valor_base = converter_valor(comp['valor'], comp['unidade'], unidade_base, comp['tipo'])
        if comp['tipo'] == 'Resistor (R)': return complex(valor_base, 0)
        elif comp['tipo'] == 'Indutor (L)':
            if frequencia == 0: return complex(0, 0)
            return complex(0, 2 * math.pi * frequencia * valor_base)
        elif comp['tipo'] == 'Capacitor (C)':
            if valor_base == 0 or frequencia == 0: return complex(0, float('inf'))
            return complex(0, -1 / (2 * math.pi * frequencia * valor_base))
        return complex(0, 0)
    impedancias_finais_em_serie = []
    i = 0
    while i < len(componentes):
        comp_atual = componentes[i]
        if comp_atual['conexao'] in ['SÉRIE', 'PRIMEIRO']:
            impedancias_finais_em_serie.append(get_impedancia_componente(comp_atual))
            i += 1
        elif comp_atual['conexao'] == 'PARALELO':
            if not impedancias_finais_em_serie:
                i += 1
                continue
            impedancia_anterior = impedancias_finais_em_serie.pop()
            admitancias_do_grupo = [1 / impedancia_anterior] if impedancia_anterior != 0 else []
            while i < len(componentes) and componentes[i]['conexao'] == 'PARALELO':
                z_paralelo = get_impedancia_componente(componentes[i])
                if z_paralelo != 0: admitancias_do_grupo.append(1 / z_paralelo)
                i += 1
            admitancia_total_grupo = sum(admitancias_do_grupo)
            impedancia_equivalente = 1 / admitancia_total_grupo if admitancia_total_grupo != 0 else complex(0, float('inf'))
            impedancias_finais_em_serie.append(impedancia_equivalente)
    return sum(impedancias_finais_em_serie)

# ==============================================================================
# SUA FUNÇÃO DE DESENHO DO CIRCUITO (Implementada como solicitado)
# ==============================================================================
def desenhar_circuito(componentes):
    """Desenha o circuito com os componentes adicionados."""
    d = Drawing()
    
    # Configurações iniciais
    spacing = 3  # Aumentei o espaçamento para melhor visualização
    
    # Adiciona fonte AC e guarda a altura
    fonte_elemento = elm.SourceSin().label('V').up()
    d += fonte_elemento
    altura_fonte = fonte_elemento.end[1]
    last_point = fonte_elemento.end
    
    # Se não há componentes, fecha o circuito
    if not componentes:
        d += elm.Line().right().length(spacing)
        d += elm.Line().down().length(altura_fonte)
        d += elm.Line().left().length(spacing)
        return d
    
    # Organiza componentes por conexão
    series_components = []
    parallel_groups = []
    current_parallel = []
    
    # Este bloco de agrupamento é a chave da lógica desta função.
    # Ele separa todos os componentes em série e paralelo, sem manter a ordem mista.
    for comp in componentes:
        if comp['conexao'] == 'PARALELO':
            current_parallel.append(comp)
        else:
            if current_parallel:
                parallel_groups.append(current_parallel)
                current_parallel = []
            if comp['conexao'] == 'SÉRIE' or comp['conexao'] == 'PRIMEIRO':
                series_components.append(comp)
    
    if current_parallel:
        parallel_groups.append(current_parallel)
    
    # Função aninhada para desenhar um componente individual
    def add_component(drawing, comp, direction='right'):
        nonlocal last_point
        
        if comp['tipo'] == 'Resistor (R)':
            element = elm.Resistor().label(f'R{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        elif comp['tipo'] == 'Indutor (L)':
            element = elm.Inductor().label(f'L{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        else:  # Capacitor
            element = elm.Capacitor().label(f'C{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        
        if direction == 'right':
            element.right().length(spacing)
        else:
            element.up().length(spacing)
        
        drawing += element.at(last_point)
        last_point = element.end
    
    # 1. Desenha todos os componentes em série primeiro
    for comp in series_components:
        d += elm.Line().right().length(spacing/2).at(last_point)
        last_point = (last_point[0] + spacing/2, last_point[1])
        add_component(d, comp)
        
    # 2. Desenha todos os grupos paralelos
    for group in parallel_groups:
        if not group:
            continue
            
        start_x = last_point[0] + spacing/2
        height_per_comp = 3
        total_height = len(group) * height_per_comp
        
        # Linhas de conexão verticais
        d += elm.Line().right().length(spacing/2).at(last_point)
        start_point = (start_x, last_point[1])
        d += elm.Line().up().length(total_height/2).at(start_point)
        d += elm.Line().down().length(total_height/2).at(start_point)
        
        # Desenha os componentes em paralelo
        for i, comp in enumerate(group):
            y_offset = total_height/2 - i * height_per_comp - height_per_comp / 2
            comp_start = (start_x, last_point[1] + y_offset)
            
            if comp['tipo'] == 'Resistor (R)':
                element = elm.Resistor().label(f'R{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            elif comp['tipo'] == 'Indutor (L)':
                element = elm.Inductor().label(f'L{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            else:  # Capacitor
                element = elm.Capacitor().label(f'C{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            
            d += element.right().length(spacing*2).at(comp_start)
        
        last_point = (start_x + spacing*2, last_point[1])
        
        end_point = (last_point[0], last_point[1])
        d += elm.Line().up().length(total_height/2).at(end_point)
        d += elm.Line().down().length(total_height/2).at(end_point)
    
    # Fecha o circuito
    d += elm.Line().right().length(spacing/2).at(last_point)
    final_point = (last_point[0] + spacing/2, last_point[1])
    d += elm.Line().down().length(altura_fonte).at(final_point)
    d += elm.Line().left().length(final_point[0]).at((final_point[0], 0))
    
    return d


def plotar_resposta_em_frequencia(componentes, freq_min, freq_max, freq_atual):
    freqs = np.logspace(np.log10(freq_min), np.log10(freq_max), 400)
    magnitudes = [abs(calcular_impedancia_total(componentes, f)) for f in freqs]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.semilogx(freqs, magnitudes)
    ax.set_xlabel('Frequência (Hz)'); ax.set_ylabel('Magnitude da Impedância |Z| (Ω)'); ax.set_title('Resposta em Frequência do Circuito')
    ax.grid(True, which="both", ls="-")
    Z_atual = calcular_impedancia_total(componentes, freq_atual)
    ax.axvline(freq_atual, color='red', linestyle='--', alpha=0.8)
    ax.plot(freq_atual, abs(Z_atual), 'ro')
    ax.text(freq_atual, abs(Z_atual), f'  {freq_atual:.0f} Hz', verticalalignment='bottom')
    return fig

# Funções auxiliares (sem alterações)
def formatar_complexo(numero_complexo):
    if abs(numero_complexo.real) < 1e-9 and abs(numero_complexo.imag) < 1e-9: retangular = "0.0000"
    elif abs(numero_complexo.imag) < 1e-9: retangular = f"{numero_complexo.real:.4f}"
    elif abs(numero_complexo.real) < 1e-9: retangular = f"{'' if numero_complexo.imag >= 0 else '-'}j{abs(numero_complexo.imag):.4f}"
    else: retangular = f"{numero_complexo.real:.4f} {'+' if numero_complexo.imag >= 0 else '-'} j{abs(numero_complexo.imag):.4f}"
    magnitude, fase_rad = cmath.polar(numero_complexo)
    fase_graus = math.degrees(fase_rad) if abs(magnitude) > 1e-9 else 0.0
    polar = f"{magnitude:.4f} ∠ {fase_graus:.2f}°"
    return retangular, polar

def calcular_potencias(V, I_complexa):
    S_complexa = V * I_complexa.conjugate()
    P, Q, S = S_complexa.real, S_complexa.imag, abs(S_complexa)
    fp = P / S if S > 1e-9 else 1.0
    return P, Q, S, fp

def plot_fasores(Z_total):
    fig, ax = plt.subplots(figsize=(6, 6))
    magnitude, R, X = abs(Z_total), Z_total.real, Z_total.imag
    fase_graus = math.degrees(cmath.phase(Z_total))
    ax.quiver(0, 0, R, X, angles='xy', scale_units='xy', scale=1, color='red', width=0.02, zorder=3)
    ax.text(R/2, X/2, f'Z = {magnitude:.2f}∠{fase_graus:.1f}°\nR = {R:.2f}\nX = {X:.2f}', ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7))
    lim = max(abs(R), abs(X), 1) * 1.5
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    ax.axhline(0, color='black', lw=0.5); ax.axvline(0, color='black', lw=0.5)
    ax.grid(True, linestyle='--', alpha=0.3); ax.set_aspect('equal')
    ax.set_xlabel('Resistência (Ω)'); ax.set_ylabel('Reatância (Ω)'); ax.set_title('Diagrama Fasorial da Impedância')
    ax.add_artist(plt.Circle((0, 0), magnitude, fill=False, linestyle='--', color='gray', alpha=0.5))
    return fig

def init_session_state():
    if 'componentes' not in st.session_state: st.session_state.componentes = []
    if 'impedancia_total' not in st.session_state: st.session_state.impedancia_total = complex(0, 0)
    if 'primeiro_componente' not in st.session_state: st.session_state.primeiro_componente = True
    if 'unidade_atual' not in st.session_state: st.session_state.unidade_atual = {'Resistor (R)': 'Ω', 'Indutor (L)': 'mH', 'Capacitor (C)': 'µF'}
    if 'valor_atual' not in st.session_state: st.session_state.valor_atual = {'Resistor (R)': 100.0, 'Indutor (L)': 10.0, 'Capacitor (C)': 10.0}
    if 'fonte_voltagem' not in st.session_state: st.session_state.fonte_voltagem = 120.0
    if 'fonte_frequencia' not in st.session_state: st.session_state.fonte_frequencia = 60.0

def converter_valor(valor, unidade_origem, unidade_destino, tipo):
    fatores = {'Resistor (R)': {'Ω': 1, 'kΩ': 1e3, 'MΩ': 1e6}, 'Indutor (L)': {'H': 1, 'mH': 1e-3, 'µH': 1e-6}, 'Capacitor (C)': {'F': 1, 'mF': 1e-3, 'µF': 1e-6, 'nF': 1e-9, 'pF': 1e-12}}
    valor_base = valor * fatores[tipo][unidade_origem]
    return valor_base / fatores[tipo][unidade_destino]

def get_step_and_format(unidade):
    if unidade in ['MΩ', 'F']: return 0.000001, "%.6f"
    elif unidade in ['kΩ', 'H', 'mF']: return 0.001, "%.3f"
    else: return 0.1, "%.1f"

# --- INTERFACE PRINCIPAL ---
st.set_page_config(page_title="Simulador de Circuitos CA", layout="wide", page_icon="⚡")
init_session_state()

st.title("⚡ Simulador de Circuitos de Corrente Alternada")
st.markdown("*Simule circuitos RLC com associações em série e paralelo e visualize as propriedades do circuito.*")

with st.sidebar:
    st.header("Configurações da Fonte")
    st.session_state.fonte_voltagem = st.slider("Tensão (Vrms):", 0.0, 240.0, st.session_state.fonte_voltagem, 1.0)
    st.session_state.fonte_frequencia = st.slider("Frequência (Hz):", 1.0, 10000.0, st.session_state.fonte_frequencia, 1.0, format="%f Hz")
    if st.button("Reiniciar Circuito", use_container_width=True):
        st.session_state.componentes, st.session_state.primeiro_componente = [], True
        st.success("Circuito reiniciado!"); st.rerun()

with st.expander("Adicionar Componentes", expanded=True):
    with st.form(key="form_componente"):
        col1, col2 = st.columns(2)
        with col1:
            tipo_anterior = st.session_state.get('tipo_anterior', 'Resistor (R)')
            tipo = st.selectbox("Tipo de Componente:", ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'), key='select_tipo_componente')
            if tipo != tipo_anterior:
                st.session_state.tipo_anterior = tipo
                st.rerun()
        with col2:
            if tipo == 'Resistor (R)': label, unidades, default_unidade = "Resistência", ('Ω', 'kΩ', 'MΩ'), 'Ω'
            elif tipo == 'Indutor (L)': label, unidades, default_unidade = "Indutância", ('H', 'mH', 'µH'), 'mH'
            else: label, unidades, default_unidade = "Capacitância", ('F', 'mF', 'µF', 'nF', 'pF'), 'µF'
            valor_col, unidade_col = st.columns([2, 1])
            unidade_atual = st.session_state.unidade_atual.get(tipo, default_unidade)
            step, fmt = get_step_and_format(unidade_atual)
            with valor_col:
                valor = st.number_input(label, 0.0, value=st.session_state.valor_atual.get(tipo, 100.0), step=step, format=fmt, key=f'valor_new_{tipo}')
            with unidade_col:
                unidade = st.selectbox("Unidade", unidades, index=unidades.index(unidade_atual), key=f'unidade_{tipo}', label_visibility="collapsed")
                if unidade != unidade_atual:
                    st.session_state.valor_atual[tipo] = converter_valor(valor, unidade_atual, unidade, tipo)
                    st.session_state.unidade_atual[tipo] = unidade
                    st.rerun()
            st.session_state.valor_atual[tipo] = valor
        if not st.session_state.primeiro_componente:
            conexao = st.radio("Conectar em:", ('SÉRIE', 'PARALELO'), index=0, horizontal=True, key='radio_conexao')
        
        submitted = st.form_submit_button("Adicionar Componente")
        if submitted:
            if valor <= 0: st.error("O valor do componente deve ser positivo!")
            else:
                conexao_final = 'PRIMEIRO' if st.session_state.primeiro_componente else conexao
                st.session_state.componentes.append({'id': len(st.session_state.componentes), 'tipo': tipo, 'valor': valor, 'unidade': unidade, 'conexao': conexao_final})
                if st.session_state.primeiro_componente: st.session_state.primeiro_componente = False
                st.success(f"Componente {tipo} adicionado em {conexao_final.lower()}."); st.rerun()

if st.session_state.componentes:
    for comp in st.session_state.componentes:
        comp['valor'] = st.session_state.get(f"slider_{comp['id']}", comp['valor'])
    st.session_state.impedancia_total = calcular_impedancia_total(st.session_state.componentes, st.session_state.fonte_frequencia)

st.subheader("Circuito Montado e Resultados")
if not st.session_state.componentes:
    st.info("Nenhum componente adicionado ainda. Use o formulário acima para começar.")
else:
    col_circ, col_res = st.columns(2)
    with col_circ:
        st.write("##### Diagrama do Circuito")
        st.warning("Aviso: O diagrama agrupa elementos série e paralelo, o que pode não refletir a ordem de cálculo para circuitos mistos complexos.", icon="⚠️")
        try:
            d = desenhar_circuito(st.session_state.componentes)
            st.image(d.get_imagedata('svg').decode(), use_container_width=True)
        except Exception as e:
            st.error(f"Ocorreu um erro ao desenhar o circuito: {e}")
        
        st.write("##### Ajuste de Componentes")
        for comp in st.session_state.componentes:
            max_val, (step, fmt) = (comp['valor'] * 5 if comp['valor'] > 0 else 100, get_step_and_format(comp['unidade']))
            st.slider(f"Ajuste {comp['tipo'][0]}{comp['id']+1} ({comp['unidade']})", 0.0, max_val, comp['valor'], key=f"slider_{comp['id']}", format=fmt)
    
    with col_res:
        st.write("##### Análise na Frequência de Operação")
        Z_total = st.session_state.impedancia_total
        ret_total, pol_total = formatar_complexo(Z_total)
        st.metric(label="Impedância Total (Retangular)", value=f"{ret_total} Ω")
        st.metric(label="Impedância Total (Polar)", value=f"{pol_total}")
        reatancia_total = Z_total.imag
        if reatancia_total > 1e-6: st.info("**🔸 Característica Indutiva:** A corrente se atrasa em relação à tensão.", icon="💡")
        elif reatancia_total < -1e-6: st.info("**🔹 Característica Capacitiva:** A corrente se adianta em relação à tensão.", icon="💡")
        else: st.info("**✅ Característica Resistiva:** A corrente e a tensão estão em fase.", icon="💡")

        if st.session_state.fonte_voltagem > 0 and abs(Z_total) > 1e-9:
            I_total_complexa = st.session_state.fonte_voltagem / Z_total
            st.metric(label="Corrente Total (Polar)", value=f"{abs(I_total_complexa):.4f} A ∠ {math.degrees(cmath.phase(I_total_complexa)):.2f}°")
            P, Q, S, fp = calcular_potencias(st.session_state.fonte_voltagem, I_total_complexa)
            c1, c2 = st.columns(2)
            c1.metric("Potência Aparente (S)", f"{S:.2f} VA"); c2.metric("Fator de Potência (FP)", f"{fp:.4f}")
            c1.metric("Potência Ativa (P)", f"{P:.2f} W"); c2.metric("Potência Reativa (Q)", f"{Q:.2f} VAR")
        
        st.write("##### Diagrama Fasorial da Impedância")
        st.pyplot(plot_fasores(Z_total))

        tem_L = any(c['tipo'] == 'Indutor (L)' for c in st.session_state.componentes)
        tem_C = any(c['tipo'] == 'Capacitor (C)' for c in st.session_state.componentes)
        
        if tem_L or tem_C:
            with st.expander("Ver Resposta em Frequência", expanded=False):
                st.pyplot(plotar_resposta_em_frequencia(
                    st.session_state.componentes,
                    freq_min=1,
                    freq_max=max(1000, st.session_state.fonte_frequencia * 5),
                    freq_atual=st.session_state.fonte_frequencia
                ))

st.markdown("---")
st.markdown("Desenvolvido com Python + Streamlit | Versão 1.4")