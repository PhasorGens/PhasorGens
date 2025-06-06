import streamlit as st
import cmath
import math
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from schemdraw import Drawing
from schemdraw import elements as elm

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
    magnitude = abs(Z_total)
    fase_rad = cmath.phase(Z_total)
    fase_graus = math.degrees(fase_rad)
    
    # Componentes real e imaginária
    R = Z_total.real
    X = Z_total.imag
    
    # Plota o fasor como uma seta
    ax.quiver(0, 0, R, X,
             angles='xy', scale_units='xy', scale=1,
             color='red', width=0.02, zorder=3)
    
    # Adiciona texto com os valores
    ax.text(R/2, X/2, f'Z = {magnitude:.2f}∠{fase_graus:.1f}°\nR = {R:.2f}\nX = {X:.2f}',
            horizontalalignment='center', verticalalignment='center',
            bbox=dict(facecolor='white', alpha=0.7))
    
    # Calcula os limites do gráfico
    max_val = max(abs(R), abs(X), magnitude/2)
    lim = max_val * 1.5  # Aumenta a margem para 50%
    
    # Configura os limites e a grade
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    
    # Adiciona linhas de eixo
    ax.axhline(y=0, color='black', linewidth=0.5, zorder=1)
    ax.axvline(x=0, color='black', linewidth=0.5, zorder=1)
    
    # Configura a grade
    ax.grid(True, linestyle='--', alpha=0.3, zorder=0)
    
    # Adiciona rótulos e título
    ax.set_xlabel('Resistência (Ω)')
    ax.set_ylabel('Reatância (Ω)')
    ax.set_title('Diagrama Fasorial da Impedância')
    
    # Garante que o aspecto seja igual (círculo perfeito)
    ax.set_aspect('equal')
    
    # Adiciona um círculo tracejado mostrando a magnitude
    circle = plt.Circle((0, 0), magnitude, fill=False, linestyle='--', color='gray', alpha=0.5)
    ax.add_artist(circle)
    
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
    
    # Função para desenhar um componente
    def add_component(drawing, comp, direction='right'):
        nonlocal last_point
        
        if comp['tipo'] == 'Resistor (R)':
            element = elm.Resistor().label(f'R\n{comp["valor"]:.1f}{comp["unidade"]}')
        elif comp['tipo'] == 'Indutor (L)':
            element = elm.Inductor().label(f'L\n{comp["valor"]:.1f}{comp["unidade"]}')
        else:  # Capacitor
            element = elm.Capacitor().label(f'C\n{comp["valor"]:.1f}{comp["unidade"]}')
        
        if direction == 'right':
            element.right().length(spacing)
        else:
            element.up().length(spacing)
        
        drawing += element.at(last_point)
        last_point = element.end
    
    # Desenha componentes em série
    for comp in series_components:
        # Adiciona uma linha antes do componente
        d += elm.Line().right().length(spacing/2).at(last_point)
        last_point = (last_point[0] + spacing/2, last_point[1])
        
        # Adiciona o componente
        add_component(d, comp)
        
    # Desenha grupos paralelos
    for group in parallel_groups:
        if not group:
            continue
            
        # Ponto inicial do grupo paralelo
        start_x = last_point[0] + spacing/2
        
        # Calcula altura necessária para os componentes paralelos
        height_per_comp = 3  # Aumentei a altura entre componentes paralelos
        total_height = len(group) * height_per_comp
        
        # Desenha linhas verticais de conexão
        d += elm.Line().right().length(spacing/2).at(last_point)
        start_point = (start_x, last_point[1])
        d += elm.Line().up().length(total_height/2).at(start_point)
        d += elm.Line().down().length(total_height/2).at(start_point)
        
        # Desenha componentes paralelos
        for i, comp in enumerate(group):
            y_offset = total_height/2 - i * height_per_comp
            comp_start = (start_x, last_point[1] + y_offset)
            
            # Adiciona o componente
            if comp['tipo'] == 'Resistor (R)':
                element = elm.Resistor().label(f'R\n{comp["valor"]:.1f}{comp["unidade"]}')
            elif comp['tipo'] == 'Indutor (L)':
                element = elm.Inductor().label(f'L\n{comp["valor"]:.1f}{comp["unidade"]}')
            else:  # Capacitor
                element = elm.Capacitor().label(f'C\n{comp["valor"]:.1f}{comp["unidade"]}')
            
            d += element.right().length(spacing*2).at(comp_start)
        
        # Atualiza o último ponto
        last_point = (start_x + spacing*2, last_point[1])
        
        # Desenha linhas verticais de conexão no final
        end_point = (last_point[0], last_point[1])
        d += elm.Line().up().length(total_height/2).at(end_point)
        d += elm.Line().down().length(total_height/2).at(end_point)
    
    # Fecha o circuito
    d += elm.Line().right().length(spacing/2).at(last_point)
    final_point = (last_point[0] + spacing/2, last_point[1])
    d += elm.Line().down().length(altura_fonte).at(final_point)
    # Linha de retorno para a fonte
    d += elm.Line().left().length(final_point[0]).at((final_point[0], 0))
    
    return d

# Inicialização adicional do estado da sessão
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
    if 'valores_ajuste' not in st.session_state:
        st.session_state.valores_ajuste = {}
    if 'unidade_atual' not in st.session_state:
        st.session_state.unidade_atual = {'Resistor (R)': 'Ω', 'Indutor (L)': 'H', 'Capacitor (C)': 'F'}
    if 'valor_atual' not in st.session_state:
        st.session_state.valor_atual = {'Resistor (R)': 0.0, 'Indutor (L)': 0.0, 'Capacitor (C)': 0.0}

def converter_valor(valor, unidade_origem, unidade_destino, tipo):
    """Converte valor entre diferentes unidades."""
    # Primeiro converte para a unidade base
    if tipo == 'Resistor (R)':
        if unidade_origem == 'kΩ':
            valor_base = valor * 1000
        elif unidade_origem == 'MΩ':
            valor_base = valor * 1000000
        else:  # Ω
            valor_base = valor
            
        # Depois converte para a unidade destino
        if unidade_destino == 'kΩ':
            return valor_base / 1000
        elif unidade_destino == 'MΩ':
            return valor_base / 1000000
        else:  # Ω
            return valor_base
            
    elif tipo == 'Indutor (L)':
        if unidade_origem == 'mH':
            valor_base = valor / 1000
        elif unidade_origem == 'µH':
            valor_base = valor / 1000000
        else:  # H
            valor_base = valor
            
        if unidade_destino == 'mH':
            return valor_base * 1000
        elif unidade_destino == 'µH':
            return valor_base * 1000000
        else:  # H
            return valor_base
            
    else:  # Capacitor
        if unidade_origem == 'mF':
            valor_base = valor / 1000
        elif unidade_origem == 'µF':
            valor_base = valor / 1000000
        elif unidade_origem == 'nF':
            valor_base = valor / 1000000000
        elif unidade_origem == 'pF':
            valor_base = valor / 1000000000000
        else:  # F
            valor_base = valor
            
        if unidade_destino == 'mF':
            return valor_base * 1000
        elif unidade_destino == 'µF':
            return valor_base * 1000000
        elif unidade_destino == 'nF':
            return valor_base * 1000000000
        elif unidade_destino == 'pF':
            return valor_base * 1000000000000
        else:  # F
            return valor_base

def get_step_and_format(unidade, tipo):
    """Retorna o step e formato adequados para cada unidade."""
    if tipo == 'Resistor (R)':
        if unidade == 'MΩ':
            return 0.000001, "%.6f"
        elif unidade == 'kΩ':
            return 0.001, "%.3f"
        else:  # Ω
            return 0.1, "%.1f"
    elif tipo == 'Indutor (L)':
        if unidade == 'µH':
            return 0.1, "%.1f"
        elif unidade == 'mH':
            return 0.1, "%.1f"
        else:  # H
            return 0.001, "%.3f"
    else:  # Capacitor
        if unidade == 'pF':
            return 0.1, "%.1f"
        elif unidade == 'nF':
            return 0.1, "%.1f"
        elif unidade == 'µF':
            return 0.1, "%.1f"
        elif unidade == 'mF':
            return 0.001, "%.3f"
        else:  # F
            return 0.000001, "%.6f"

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
    st.session_state.fonte_voltagem = st.slider(
        "Tensão (Vrms):", 
        min_value=0.0,
        max_value=220.0,
        value=st.session_state.fonte_voltagem,
        step=1.0
    )
    st.session_state.fonte_frequencia = st.slider(
        "Frequência (Hz):", 
        min_value=1.0,
        max_value=1000.0,
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
        st.session_state.valores_ajuste = {}
        st.success("Circuito reiniciado com sucesso!")
        st.rerun()

# Formulário para adicionar componentes
with st.expander("Adicionar Componentes", expanded=True):
    with st.form(key="form_componente"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_anterior = st.session_state.get('tipo_anterior', 'Resistor (R)')
            tipo = st.selectbox(
                "Tipo de Componente:",
                ('Resistor (R)', 'Indutor (L)', 'Capacitor (C)'),
                key='select_tipo_componente'
            )
            # Se o tipo mudou, atualiza o estado
            if tipo != tipo_anterior:
                st.session_state.tipo_anterior = tipo
                st.rerun()
            
        with col2:
            if tipo == 'Resistor (R)':
                label = "Resistência"
                unidades = ('Ω', 'kΩ', 'MΩ')
                default_unidade = 'Ω'
            elif tipo == 'Indutor (L)':
                label = "Indutância"
                unidades = ('H', 'mH', 'µH')
                default_unidade = 'H'
            else:  # Capacitor
                label = "Capacitância"
                unidades = ('F', 'mF', 'µF', 'nF', 'pF')
                default_unidade = 'µF'
            
            valor_col, unidade_col = st.columns([2, 1])
            
            # Obtém a unidade atual para o tipo de componente
            unidade_atual = st.session_state.unidade_atual.get(tipo, default_unidade)
            step, format = get_step_and_format(unidade_atual, tipo)
            
            with valor_col:
                valor = st.number_input(
                    label,
                    min_value=0.0,
                    value=st.session_state.valor_atual.get(tipo, 0.0),
                    step=step,
                    format=format,
                    key=f'valor_new_{tipo}'
                )
                
            with unidade_col:
                unidade = st.selectbox(
                    "Unidade",
                    unidades,
                    index=unidades.index(unidade_atual),
                    key=f'unidade_{tipo}',
                    label_visibility="collapsed"
                )
                
                # Se a unidade mudou, converte o valor
                if unidade != unidade_atual:
                    valor_convertido = converter_valor(valor, unidade_atual, unidade, tipo)
                    st.session_state.valor_atual[tipo] = valor_convertido
                    st.session_state.unidade_atual[tipo] = unidade
                    st.rerun()
            
            # Armazena o valor atual
            st.session_state.valor_atual[tipo] = valor
            
            # Converte para a unidade base (para cálculos)
            valor_base = converter_valor(valor, unidade, 'Ω' if tipo == 'Resistor (R)' else 'H' if tipo == 'Indutor (L)' else 'F', tipo)
            st.session_state.valor_componente = valor_base

        if not st.session_state.primeiro_componente:
            conexao = st.radio(
                "Conectar em:",
                ('SÉRIE', 'PARALELO'),
                index=0 if st.session_state.conexao == "SÉRIE" else 1,
                horizontal=True,
                key='radio_conexao'
            )
            st.session_state.conexao = conexao
        
        submitted = st.form_submit_button("Adicionar Componente")
        if submitted:
            if valor <= 0:
                st.error("O valor do componente deve ser positivo!")
            else:
                # Calcula a impedância do componente
                if tipo == 'Resistor (R)':
                    Z = complex(valor_base, 0)
                    desc = f"R: {valor:.4f} {unidade}"
                elif tipo == 'Indutor (L)':
                    XL = 2 * math.pi * st.session_state.fonte_frequencia * valor_base
                    Z = complex(0, XL)
                    desc = f"L: {valor:.4f} {unidade} (j{XL:.2f} Ω)"
                else:  # Capacitor
                    XC = 1/(2 * math.pi * st.session_state.fonte_frequencia * valor_base)
                    Z = complex(0, -XC)
                    desc = f"C: {valor:.4f} {unidade} (-j{XC:.2f} Ω)"
                
                # Adiciona ao circuito
                comp_id = len(st.session_state.componentes)
                if st.session_state.primeiro_componente:
                    st.session_state.impedancia_total = Z
                    st.session_state.primeiro_componente = False
                    st.session_state.componentes.append({
                        'id': comp_id,
                        'tipo': tipo,
                        'valor': valor,
                        'unidade': unidade,
                        'desc': f"Primeiro componente: {desc}",
                        'Z': Z,
                        'conexao': 'PRIMEIRO'
                    })
                else:
                    if st.session_state.conexao == 'SÉRIE':
                        st.session_state.impedancia_total += Z
                        st.session_state.componentes.append({
                            'id': comp_id,
                            'tipo': tipo,
                            'valor': valor,
                            'unidade': unidade,
                            'desc': f"Adicionado em série: {desc}",
                            'Z': Z,
                            'conexao': 'SÉRIE'
                        })
                    else:  # PARALELO
                        if abs(st.session_state.impedancia_total + Z) < 1e-9:
                            st.error("Erro: Divisão por zero na conexão paralela!")
                        else:
                            st.session_state.impedancia_total = (
                                st.session_state.impedancia_total * Z
                            ) / (st.session_state.impedancia_total + Z)
                            st.session_state.componentes.append({
                                'id': comp_id,
                                'tipo': tipo,
                                'valor': valor,
                                'unidade': unidade,
                                'desc': f"Adicionado em paralelo: {desc}",
                                'Z': Z,
                                'conexao': 'PARALELO'
                            })
                
                st.success(f"Componente adicionado: {desc}")
                st.rerun()

# Visualização e ajuste do circuito
st.subheader("Circuito Montado")
if not st.session_state.componentes:
    st.info("Nenhum componente adicionado ainda. Use o formulário acima para começar.")
else:
    # Desenha o circuito
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("Diagrama do Circuito:")
        d = desenhar_circuito(st.session_state.componentes)
        # Converte o desenho para uma imagem
        fig = d.get_imagedata('png')
        st.image(fig, use_container_width=True)
    
    with col2:
        st.write("Ajuste os valores dos componentes:")
        
        # Recalcular impedância total com os valores ajustados
        Z_total = complex(0, 0)
        primeiro = True
        
        for comp in st.session_state.componentes:
            # Criar um slider para cada componente
            novo_valor = st.slider(
                f"Ajuste {comp['desc']}",
                0.0, comp['valor'] * 2, 
                comp['valor'],
                step=comp['valor']/100 if comp['valor'] > 0 else 0.1,
                key=f"slider_{comp['id']}"
            )
            
            # Calcula a nova impedância
            if comp['tipo'] == 'Resistor (R)':
                Z = complex(novo_valor, 0)
            elif comp['tipo'] == 'Indutor (L)':
                XL = 2 * math.pi * st.session_state.fonte_frequencia * novo_valor
                Z = complex(0, XL)
            else:  # Capacitor
                XC = 1/(2 * math.pi * st.session_state.fonte_frequencia * novo_valor)
                Z = complex(0, -XC)
            
            # Atualizar a impedância total
            if primeiro:
                Z_total = Z
                primeiro = False
            else:
                if comp['conexao'] == 'SÉRIE':
                    Z_total += Z
                else:  # PARALELO
                    Z_total = (Z_total * Z) / (Z_total + Z)
        
        # Atualizar a impedância total no estado da sessão
        st.session_state.impedancia_total = Z_total

# Resultados e análises
st.subheader("Resultados da Análise")

# Exibir resultados
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
        
        # Verificar se existem componentes L e C no circuito
        tem_L = False
        tem_C = False
        L_total = 0
        C_total = 0
        
        for comp in st.session_state.componentes:
            if comp['tipo'] == 'Indutor (L)':
                tem_L = True
                if st.session_state.modo_avancado:
                    # Se estiver em modo avançado, o valor já está em H
                    L_total = comp['valor']
                else:
                    # Se não estiver em modo avançado, converter de reatância para H
                    XL = comp['valor']
                    L_total = XL / (2 * math.pi * st.session_state.fonte_frequencia)
            elif comp['tipo'] == 'Capacitor (C)':
                tem_C = True
                if st.session_state.modo_avancado:
                    # Se estiver em modo avançado, o valor já está em F
                    C_total = comp['valor']
                else:
                    # Se não estiver em modo avançado, converter de reatância para F
                    XC = comp['valor']
                    C_total = 1 / (2 * math.pi * st.session_state.fonte_frequencia * XC)
        
        # Plotar resposta em frequência se houver L e C
        if tem_L and tem_C:
            st.pyplot(plot_resposta_frequencia(
                R=abs(st.session_state.impedancia_total.real),
                L=L_total,
                C=C_total,
                freq_min=1,
                freq_max=1000
            ))

# Rodapé
st.markdown("---")
st.markdown("""
    **Simulador de Circuitos CA**  
    Desenvolvido com Python + Streamlit  
    *Versão 1.0 - Para fins educacionais*
""")