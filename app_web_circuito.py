import streamlit as st
import cmath
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc
from schemdraw import Drawing
from schemdraw import elements as elm
import pandas as pd

# --- FUNÇÕES DE CÁLCULO E AUXILIARES ---

def converter_valor(valor, unidade_origem, unidade_destino, tipo):
    fatores = {'Resistor (R)': {'Ω': 1, 'kΩ': 1e3, 'MΩ': 1e6}, 'Indutor (L)': {'H': 1, 'mH': 1e-3, 'µH': 1e-6}, 'Capacitor (C)': {'F': 1, 'mF': 1e-3, 'µF': 1e-6, 'nF': 1e-9, 'pF': 1e-12}}
    valor_base = valor * fatores[tipo][unidade_origem]
    return valor_base / fatores[tipo][unidade_destino]

def get_impedancia_componente(comp, frequencia):
    if comp.get('valor', 0) == 0: return complex(0, 0)
    
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

def analisar_circuito_detalhadamente(componentes, frequencia, V_fonte):
    if not componentes:
        return complex(0, 0), complex(0, 0), []

    # Passo 1: Calcular Z_total e I_total
    blocos_impedancia = []
    i = 0
    while i < len(componentes):
        comp_atual = componentes[i]
        if comp_atual['conexao'] in ['SÉRIE', 'PRIMEIRO']:
            blocos_impedancia.append({'tipo': 'serie', 'impedancia': get_impedancia_componente(comp_atual, frequencia), 'indices': [i]})
            i += 1
        elif comp_atual['conexao'] == 'PARALELO':
            bloco_anterior = blocos_impedancia.pop()
            impedancia_anterior = bloco_anterior['impedancia']
            indices_grupo = bloco_anterior['indices']
            admitancias_do_grupo = [1 / impedancia_anterior] if impedancia_anterior != 0 else []
            
            while i < len(componentes) and componentes[i]['conexao'] == 'PARALELO':
                indices_grupo.append(i)
                z_paralelo = get_impedancia_componente(componentes[i], frequencia)
                if z_paralelo != 0:
                    admitancias_do_grupo.append(1 / z_paralelo)
                i += 1
            
            admitancia_total_grupo = sum(admitancias_do_grupo)
            impedancia_equivalente = 1 / admitancia_total_grupo if admitancia_total_grupo != 0 else complex(float('inf'))
            blocos_impedancia.append({'tipo': 'paralelo', 'impedancia': impedancia_equivalente, 'indices': indices_grupo})
            
    Z_total = sum(b['impedancia'] for b in blocos_impedancia)
    I_total = V_fonte / Z_total if Z_total != 0 else complex(0,0)

    # Passo 2: Calcular V e I para cada componente
    componentes_analisados = [c.copy() for c in componentes] 
    
    for bloco in blocos_impedancia:
        # A corrente que entra em cada bloco série é a corrente total
        I_bloco = I_total
        V_bloco = I_bloco * bloco['impedancia']
        
        if bloco['tipo'] == 'serie':
            idx = bloco['indices'][0]
            componentes_analisados[idx]['tensao'] = V_bloco
            componentes_analisados[idx]['corrente'] = I_bloco
        
        elif bloco['tipo'] == 'paralelo':
            # A tensão é a mesma para todos os componentes em paralelo
            for idx in bloco['indices']:
                Z_comp = get_impedancia_componente(componentes_analisados[idx], frequencia)
                I_comp = V_bloco / Z_comp if Z_comp != 0 else complex(0,0)
                componentes_analisados[idx]['tensao'] = V_bloco
                componentes_analisados[idx]['corrente'] = I_comp

    return Z_total, I_total, componentes_analisados

def formatar_complexo(numero_complexo, unidade=''):
    if abs(numero_complexo.real) < 1e-9 and abs(numero_complexo.imag) < 1e-9: retangular = f"0.00 {unidade}"
    elif abs(numero_complexo.imag) < 1e-9: retangular = f"{numero_complexo.real:.2f} {unidade}"
    elif abs(numero_complexo.real) < 1e-9: retangular = f"{'' if numero_complexo.imag >= 0 else '-'}j{abs(numero_complexo.imag):.2f} {unidade}"
    else: retangular = f"{numero_complexo.real:.2f} {'+' if numero_complexo.imag >= 0 else '-'} j{abs(numero_complexo.imag):.2f} {unidade}"
    
    magnitude, fase_rad = cmath.polar(numero_complexo)
    fase_graus = math.degrees(fase_rad)
    polar = f"{magnitude:.2f} {unidade} ∠ {fase_graus:.2f}°"
    return retangular, polar

def calcular_potencias(V, I_complexa):
    S_complexa = V * I_complexa.conjugate()
    return S_complexa.real, S_complexa.imag, abs(S_complexa)

# --- Funções de Plotagem e Visualização ---

def desenhar_circuito(componentes):
    d = Drawing()
    spacing = 3 
    fonte_elemento = elm.SourceSin().label('V').up()
    d += fonte_elemento
    altura_fonte = fonte_elemento.end[1]
    last_point = fonte_elemento.end
    if not componentes:
        d += elm.Line().right().length(spacing)
        d += elm.Line().down().length(altura_fonte)
        d += elm.Line().left().length(spacing)
        return d
    series_components, parallel_groups, current_parallel = [], [], []
    for comp in componentes:
        if comp['conexao'] == 'PARALELO':
            current_parallel.append(comp)
        else:
            if current_parallel:
                parallel_groups.append(current_parallel)
                current_parallel = []
            if comp['conexao'] in ['SÉRIE', 'PRIMEIRO']:
                series_components.append(comp)
    if current_parallel:
        parallel_groups.append(current_parallel)
    def add_component(drawing, comp):
        nonlocal last_point
        if comp['tipo'] == 'Resistor (R)': element = elm.Resistor().label(f'R{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        elif comp['tipo'] == 'Indutor (L)': element = elm.Inductor().label(f'L{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        else: element = elm.Capacitor().label(f'C{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
        element.right().length(spacing)
        drawing += element.at(last_point)
        last_point = element.end
    for comp in series_components:
        d += elm.Line().right().length(spacing/2).at(last_point)
        last_point = (last_point[0] + spacing/2, last_point[1])
        add_component(d, comp)
    for group in parallel_groups:
        if not group: continue
        start_x = last_point[0] + spacing/2
        height_per_comp = 3
        total_height = len(group) * height_per_comp
        d += elm.Line().right().length(spacing/2).at(last_point)
        start_point = (start_x, last_point[1])
        d += elm.Line().up().length(total_height/2).at(start_point)
        d += elm.Line().down().length(total_height/2).at(start_point)
        for i, comp in enumerate(group):
            y_offset = total_height/2 - i * height_per_comp - height_per_comp / 2
            comp_start = (start_x, last_point[1] + y_offset)
            if comp['tipo'] == 'Resistor (R)': element = elm.Resistor().label(f'R{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            elif comp['tipo'] == 'Indutor (L)': element = elm.Inductor().label(f'L{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            else: element = elm.Capacitor().label(f'C{comp["id"]+1}\n{comp["valor"]:.1f}{comp["unidade"]}')
            d += element.right().length(spacing*2).at(comp_start)
        last_point = (start_x + spacing*2, last_point[1])
        end_point = last_point
        d += elm.Line().up().length(total_height/2).at(end_point)
        d += elm.Line().down().length(total_height/2).at(end_point)
    d += elm.Line().right().length(spacing/2).at(last_point)
    final_point = (last_point[0] + spacing/2, last_point[1])
    d += elm.Line().down().length(altura_fonte).at(final_point)
    d += elm.Line().left().length(final_point[0]).at((final_point[0], 0))
    return d

def plotar_resposta_em_frequencia(componentes, freq_min, freq_max, freq_atual):
    freqs = np.logspace(np.log10(freq_min), np.log10(freq_max), 400)
    Z_total_em_frequencia = [abs(analisar_circuito_detalhadamente(componentes, f, 1)[0]) for f in freqs]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.semilogx(freqs, Z_total_em_frequencia)
    ax.set_title('Resposta em Frequência do Circuito')
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel('Impedância |Z| (Ω)')
    ax.grid(True, which="both", ls="-")
    Z_atual = analisar_circuito_detalhadamente(componentes, freq_atual, 1)[0]
    ax.axvline(freq_atual, color='red', linestyle='--', alpha=0.8)
    ax.plot(freq_atual, abs(Z_atual), 'ro')
    ax.text(freq_atual * 1.1, abs(Z_atual), f' {freq_atual:.0f} Hz', verticalalignment='center')
    return fig

def plot_triangulo_potencias(P, Q, S):
    # --- ALTERAÇÃO AQUI ---
    fig, ax = plt.subplots(figsize=(5, 4)) # Tamanho reduzido
    plt.style.use('seaborn-v0_8-whitegrid')
    ax.set_title("Triângulo das Potências", fontsize=12, weight='bold')
    ax.quiver(0, 0, P, 0, angles='xy', scale_units='xy', scale=1, color='blue', label=f'P = {P:.2f} W')
    ax.quiver(P, 0, 0, Q, angles='xy', scale_units='xy', scale=1, color='green', label=f'Q = {Q:.2f} VAR')
    ax.quiver(0, 0, P, Q, angles='xy', scale_units='xy', scale=1, color='red', label=f'S = {S:.2f} VA')
    ax.text(P / 2, max(abs(Q),1)*0.05, 'P', color='blue', ha='center', weight='bold')
    ax.text(P, Q / 2, 'Q', color='green', ha='left', weight='bold')
    ax.text(P / 2, Q / 2, 'S', color='red', ha='center', va='bottom', weight='bold')
    ax.set_xlabel("Potência Ativa (P) [W]"); ax.set_ylabel("Potência Reativa (Q) [VAR]")
    limite_x = max(abs(P), 1) * 1.2
    limite_y = max(abs(Q), 1) * 1.2
    ax.set_xlim(0, limite_x)
    ax.set_ylim(min(-limite_y, Q) if Q < 0 else -0.1, limite_y if Q > 0 else 0.1)
    ax.set_aspect('equal', adjustable='box'); ax.grid(True); ax.legend()
    return fig

def plot_fasores(Z_total, V_fonte, I_total_complexa):
    R, X, Z_mag = Z_total.real, Z_total.imag, abs(Z_total)
    Z_fase_rad, Z_fase_graus = cmath.phase(Z_total), math.degrees(cmath.phase(Z_total))
    V_mag, I_mag = V_fonte, abs(I_total_complexa)
    I_fase_rad, I_fase_graus = cmath.phase(I_total_complexa), math.degrees(cmath.phase(I_total_complexa))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    plt.style.use('seaborn-v0_8-whitegrid')
    ax1.set_title("Triângulo das Impedâncias", fontsize=12, weight='bold')
    ax1.quiver(0, 0, R, 0, angles='xy', scale_units='xy', scale=1, color='blue', label=f'R = {R:.2f} Ω')
    ax1.quiver(R, 0, 0, X, angles='xy', scale_units='xy', scale=1, color='green', label=f'X = {X:.2f} Ω')
    ax1.quiver(0, 0, R, X, angles='xy', scale_units='xy', scale=1, color='red', label=f'|Z| = {Z_mag:.2f} Ω')
    ax1.text(R / 2, Z_mag*0.05, f'{R:.1f}', color='blue', ha='center')
    ax1.text(R, X / 2, f'{X:.1f}', color='green', ha='left')
    ax1.text(R / 2, X / 2, f'|Z|={Z_mag:.1f}', color='red', ha='center', va='bottom')
    lim_arco = Z_mag * 0.25
    arco = Arc((0, 0), lim_arco, lim_arco, angle=0, theta1=0, theta2=Z_fase_graus, color='black', ls=':')
    ax1.add_patch(arco)
    ax1.text(lim_arco * 0.5 * math.cos(Z_fase_rad / 2), lim_arco * 0.5 * math.sin(Z_fase_rad / 2), f'θ={Z_fase_graus:.1f}°', ha='center', va='center')
    ax1.set_xlabel("Resistência (R) [Ω]"); ax1.set_ylabel("Reatância (X) [Ω]")
    ax1.axhline(0, color='black', linewidth=0.5); ax1.axvline(0, color='black', linewidth=0.5)
    limite = max(abs(R), abs(X), Z_mag) * 1.2 if Z_mag > 1e-9 else 1
    ax1.set_xlim(-0.1 if R < 0 else 0, limite)
    ax1.set_ylim(-limite if X < 0 else 0, limite if X > 0 else 0.1)
    ax1.set_aspect('equal', adjustable='box'); ax1.grid(True); ax1.legend()
    ax2 = plt.subplot(122, projection='polar')
    ax2.set_title("Fasores de Tensão e Corrente", fontsize=12, weight='bold')
    ax2.annotate('', xy=(0, V_mag), xytext=(0,0), arrowprops=dict(facecolor='orange', edgecolor='orange', arrowstyle='->', lw=2))
    ax2.annotate('', xy=(I_fase_rad, V_mag), xytext=(0,0), arrowprops=dict(facecolor='purple', edgecolor='purple', arrowstyle='->', lw=2))
    ax2.text(0, V_mag, f'  V={V_mag:.1f}V', color='orange', ha='left', va='center')
    ax2.text(I_fase_rad, V_mag, f'  I={I_mag:.2f}A', color='purple', ha='left', va='top')
    ax2.set_rmax(V_mag * 1.2); ax2.set_yticklabels([])
    return fig

def init_session_state():
    if 'componentes' not in st.session_state: st.session_state.componentes = []
    if 'editing_id' not in st.session_state: st.session_state.editing_id = None
    if 'fonte_voltagem' not in st.session_state: st.session_state.fonte_voltagem = 120.0
    if 'fonte_frequencia' not in st.session_state: st.session_state.fonte_frequencia = 60.0

# --- LÓGICA DA INTERFACE PRINCIPAL ---

st.set_page_config(page_title="Simulador de Circuitos CA", layout="wide", page_icon="⚡")

if 'componentes' not in st.session_state:
    init_session_state()

st.title("⚡ Simulador de Circuitos de Corrente Alternada")
st.markdown("Versão 2.3 - Layout Ajustado")

with st.sidebar:
    st.header("Configurações da Fonte")
    st.session_state.fonte_voltagem = st.number_input("Tensão (Vrms):", 0.0, 1000.0, st.session_state.get('fonte_voltagem', 120.0), 1.0)
    st.session_state.fonte_frequencia = st.number_input("Frequência (Hz):", 1.0, 100000.0, st.session_state.get('fonte_frequencia', 60.0), 1.0, format="%f")
    if st.button("Reiniciar Circuito", use_container_width=True):
        init_session_state()
        st.success("Circuito reiniciado!"); st.rerun()

def get_component_by_id(comp_id):
    if comp_id is None: return None
    for comp in st.session_state.componentes:
        if comp['id'] == comp_id: return comp
    return None

def submit_form(tipo, valor, unidade, conexao):
    editing_id = st.session_state.get('editing_id')
    if editing_id is not None:
        idx_to_edit = next((i for i, item in enumerate(st.session_state.componentes) if item["id"] == editing_id), None)
        if idx_to_edit is not None:
            st.session_state.componentes[idx_to_edit].update({'tipo': tipo, 'valor': valor, 'unidade': unidade, 'conexao': conexao})
        st.session_state.editing_id = None
    else:
        new_id = max([c['id'] for c in st.session_state.componentes] + [-1]) + 1
        st.session_state.componentes.append({'id': new_id, 'tipo': tipo, 'valor': valor, 'unidade': unidade, 'conexao': conexao})
    st.rerun()

is_editing = st.session_state.get('editing_id') is not None
comp_to_edit = get_component_by_id(st.session_state.get('editing_id')) or {}
form_title = f"📝 Editando Componente {st.session_state.get('editing_id', '')+1}" if is_editing else "➕ Adicionar Novo Componente"

with st.expander(form_title, expanded=True):
    with st.form(key="form_componente"):
        default_tipo = comp_to_edit.get('tipo', 'Resistor (R)')
        tipo_index = ['Resistor (R)', 'Indutor (L)', 'Capacitor (C)'].index(default_tipo)
        tipo = st.selectbox("Tipo de Componente:", ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'), index=tipo_index)

        if tipo == 'Resistor (R)': label, unidades = "Resistência", ('Ω', 'kΩ', 'MΩ')
        elif tipo == 'Indutor (L)': label, unidades = "Indutância", ('H', 'mH', 'µH')
        else: label, unidades = "Capacitância", ('F', 'mF', 'µF', 'nF', 'pF')
        
        default_valor = comp_to_edit.get('valor', 100.0)
        default_unidade_index = unidades.index(comp_to_edit.get('unidade', unidades[0])) if comp_to_edit.get('unidade') in unidades else 0
        
        c1, c2 = st.columns([3, 1])
        valor = c1.number_input(label, min_value=0.0, value=default_valor, format="%.3f")
        unidade = c2.selectbox("Unidade", unidades, index=default_unidade_index)

        component_index = next((i for i, item in enumerate(st.session_state.componentes) if item["id"] == st.session_state.get('editing_id')), -1)
        is_first_comp = (not is_editing and len(st.session_state.componentes) == 0) or (is_editing and component_index == 0)

        if not is_first_comp:
            default_conexao_index = ['SÉRIE', 'PARALELO'].index(comp_to_edit.get('conexao', 'SÉRIE'))
            conexao = st.radio("Conexão com o anterior:", ('SÉRIE', 'PARALELO'), index=default_conexao_index, horizontal=True)
        else:
            conexao = 'PRIMEIRO'
        
        submit_text = "Salvar Alterações" if is_editing else "Adicionar Componente"
        if st.form_submit_button(submit_text, use_container_width=True):
            if valor > 0:
                submit_form(tipo, valor, unidade, conexao)
            else:
                st.error("O valor do componente deve ser maior que zero.")

st.subheader("Circuito Montado e Análise Completa")

if not st.session_state.componentes:
    st.info("Nenhum componente adicionado. Use o formulário acima para começar.")
else:
    Z_total, I_total, componentes_analisados = analisar_circuito_detalhadamente(st.session_state.componentes, st.session_state.fonte_frequencia, st.session_state.fonte_voltagem)
    P_total, Q_total, S_total = calcular_potencias(st.session_state.fonte_voltagem, I_total)
    FP_total = P_total / S_total if S_total > 1e-9 else 1.0

    col_circ, col_res = st.columns([1, 1])
    
    with col_circ:
        st.write("##### Componentes do Circuito")
        for i, comp in enumerate(st.session_state.componentes):
            comp_label = f"**{comp['tipo'][0]}{i+1}:** {comp['valor']} {comp['unidade']} `({comp['conexao']})`"
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            c1.markdown(comp_label)
            if c2.button("Editar", key=f"edit_{comp['id']}", use_container_width=True):
                st.session_state.editing_id = comp['id']
                st.rerun()
            if c3.button("Remover", key=f"del_{comp['id']}", use_container_width=True):
                st.session_state.componentes.pop(i)
                st.session_state.editing_id = None 
                st.rerun()
        
        st.write("##### Diagrama do Circuito")
        try:
            d = desenhar_circuito(st.session_state.componentes)
            st.image(d.get_imagedata('svg').decode(), use_container_width=True)
        except Exception as e:
            st.error(f"Ocorreu um erro ao desenhar o circuito: {e}")

    with col_res:
        st.write("##### Análise Geral do Circuito")
        _, pol_Z = formatar_complexo(Z_total, "Ω")
        _, pol_I = formatar_complexo(I_total, "A")
        st.metric(label="Impedância Total (Z)", value=pol_Z)
        st.metric(label="Corrente Total (I)", value=pol_I)
        
        if Q_total > 1e-6: st.info("**🔸 Característica Indutiva:** A corrente se atrasa em relação à tensão.", icon="💡")
        elif Q_total < -1e-6: st.info("**🔹 Característica Capacitiva:** A corrente se adianta em relação à tensão.", icon="💡")
        else: st.info("**✅ Característica Resistiva:** A corrente e a tensão estão em fase.", icon="💡")
        
        c1, c2 = st.columns(2)
        c1.metric("Potência Ativa (P)", f"{P_total:.2f} W"); c2.metric("Potência Reativa (Q)", f"{Q_total:.2f} VAR")
        c1.metric("Potência Aparente (S)", f"{S_total:.2f} VA"); c2.metric("Fator de Potência (FP)", f"{FP_total:.4f}")
    
    with st.expander("Análise Detalhada por Componente", expanded=False):
        df_data = []
        for i, comp in enumerate(componentes_analisados):
            _, V_polar = formatar_complexo(comp.get('tensao', 0), 'V')
            _, I_polar = formatar_complexo(comp.get('corrente', 0), 'A')
            df_data.append({"Componente": f"{comp['tipo'][0]}{i+1}", "Valor": f"{comp['valor']} {comp['unidade']}", "Tensão (V)": V_polar, "Corrente (A)": I_polar})
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)

    with st.expander("Gráficos de Análise", expanded=True):
        st.pyplot(plot_fasores(Z_total, st.session_state.fonte_voltagem, I_total))
        st.pyplot(plot_triangulo_potencias(P_total, Q_total, S_total))

    with st.expander("Ver Resposta em Frequência", expanded=False):
        st.pyplot(plotar_resposta_em_frequencia(st.session_state.componentes, 1, max(1000, st.session_state.fonte_frequencia * 5), st.session_state.fonte_frequencia))

st.markdown("---")
st.markdown("Desenvolvido com Python + Streamlit | Versão 2.3 - Layout Ajustado")