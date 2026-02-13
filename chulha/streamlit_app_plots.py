import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import glob

# Importar módulos locais
from dataprep import DataLoader
from plot_utils import PlotterGFET

# Configuração da página
st.set_page_config(
    page_title="📊 GFET Curves - Análise de Curvas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos customizados
st.markdown("""
    <style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Análise de Curvas de Transferência - GFET")
st.markdown("---")


@st.cache_data
def carregar_dados(base_path, chip):
    """Carrega todos os dados do chip selecionado usando DataLoader"""
    loader = DataLoader(base_path)
    return loader.carregar_chip(chip)


# ==================== INTERFACE PRINCIPAL ====================

# Sidebar para configurações
st.sidebar.header("⚙️ Configurações")

# Caminho fixo para os dados
base_path = "data/silver"

# Verificar se a pasta existe
if not os.path.exists(base_path):
    st.error(f"⚠️ A pasta {base_path} não foi encontrada!")
    st.info("Certifique-se de que os dados processados estão em `data/silver/`")
    st.stop()

# Listar experimentos (ex: 19abr, 03abr, etc.)
experimentos = [d for d in os.listdir(base_path) 
                if os.path.isdir(os.path.join(base_path, d)) and not d.startswith('.')]

if not experimentos:
    st.error("Nenhum experimento encontrado em `data/silver/`")
    st.stop()

st.sidebar.markdown("### 📅 Navegação de Dados")

# Seletor de experimento/data
experimento_selecionado = st.sidebar.selectbox(
    "1️⃣ Selecione o Experimento:",
    sorted(experimentos),
    help="Escolha o experimento (ex: 19abr, 03abr)"
)

# Caminho completo do experimento
pasta_experimento = os.path.join(base_path, experimento_selecionado)

# Verificar se tem subpastas
subpastas = [d for d in os.listdir(pasta_experimento) 
             if os.path.isdir(os.path.join(pasta_experimento, d)) and not d.startswith('.')]

# Se houver subpastas, permitir seleção
if subpastas:
    subpasta_selecionada = st.sidebar.selectbox(
        "2️⃣ Selecione a Subpasta:",
        sorted(subpastas),
        help="Escolha a subpasta com os dados"
    )
    pasta_dados = os.path.join(pasta_experimento, subpasta_selecionada)
else:
    pasta_dados = pasta_experimento

st.sidebar.info(f"📂 `{pasta_dados}`")

# Usar DataLoader para listar chips
loader = DataLoader(pasta_dados)
chips_disponiveis = loader.listar_chips_disponiveis()

if not chips_disponiveis:
    st.error(f"Nenhum arquivo CSV ajustado encontrado em:\n{pasta_dados}")
    st.stop()

# Seletor de chip
chip_selecionado = st.sidebar.selectbox(
    "3️⃣ Selecione o Chip:",
    sorted(chips_disponiveis),
    help="Escolha o chip para análise"
)

# Carregar dados
with st.spinner("Carregando dados..."):
    dados = carregar_dados(pasta_dados, chip_selecionado)

if not dados:
    st.error(f"Não foi possível carregar dados para o chip {chip_selecionado}")
    st.stop()

# Obter lista de devices disponíveis usando DataLoader
devices_disponiveis = loader.obter_colunas_disponiveis(dados)

# Mostrar estatísticas na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estatísticas")
st.sidebar.success(f"✅ Etapas carregadas: **{len(dados)}**")
st.sidebar.info(f"🎯 Devices disponíveis: **{len(devices_disponiveis)}**")

# Mostrar arquivos carregados
with st.sidebar.expander("📋 Ver Etapas Carregadas"):
    etapas_labels = {
        'bare': '🔵 BARE',
        'etoh': '⚪ ETOH',
        'ddt': '🟡 DDT',
        'pbse': '🟢 PBSE',
        'apt': '🟣 APT',
        'eta': '🟠 ETA',
        'b1': '⬜ BLANK1',
        'b2': '⬜ BLANK2',
        'b3': '⬜ BLANK3',
        'menos18': '🔴 1 aM',
        'menos17': '🔴 10 aM',
        'menos16': '🔴 100 aM',
        'menos15': '🟡 1 fM',
        'menos14': '🟡 10 fM',
        'menos13': '🟡 100 fM',
        'menos12': '🔵 1 pM',
        'menos11': '🔵 10 pM',
        'menos10': '🔵 100 pM',
        'menos9': '🟣 1 nM',
        'menos8': '🟣 10 nM',
    }
    for etapa in sorted(dados.keys()):
        label = etapas_labels.get(etapa, f"▫️ {etapa}")
        st.markdown(f"- {label}")

with st.sidebar.expander("🎯 Ver Devices"):
    for i, dev in enumerate(devices_disponiveis, 1):
        st.markdown(f"{i}. Device **{dev}**")

# Criar plotter
plotter = PlotterGFET(chip_name=chip_selecionado)

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Curvas de Transferência", 
    "🔄 Curvas Normalizadas",
    "🎯 Device Individual",
    "💧 Curvas de Concentração"
])

# ==================== TAB 1: Curvas de Transferência ====================
with tab1:
    st.header("📈 Curvas de Transferência - Todos os Devices")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**📂 Experimento:** `{experimento_selecionado}`")
        st.markdown(f"**🔬 Chip:** `{chip_selecionado}`")
    with col2:
        st.metric("Etapas", len(dados))
        st.metric("Devices", len(devices_disponiveis))
    
    # Seletor de etapas para plotar
    st.markdown("---")
    st.markdown("### 🎨 Selecione as Etapas para Plotar")
    
    etapas_disponiveis_tab1 = [e for e in ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'] if e in dados]
    
    if etapas_disponiveis_tab1:
        col_etapas, col_devices = st.columns([1, 1])
        
        with col_etapas:
            etapas_selecionadas = st.multiselect(
                "📊 Escolha as etapas:",
                etapas_disponiveis_tab1,
                default=etapas_disponiveis_tab1,
                help="Selecione quais etapas incluir no gráfico"
            )
        
        with col_devices:
            # Permitir seleção de devices específicos
            max_devices = st.slider(
                "🎯 Número de devices:",
                min_value=1,
                max_value=min(20, len(devices_disponiveis)),
                value=min(20, len(devices_disponiveis)),
                help="Quantos devices plotar (máximo 20 para grid 4x5)"
            )
        
        if etapas_selecionadas:
            if st.button("🔄 Gerar Gráfico - Curvas de Transferência", key="btn_todas_transferencia"):
                with st.spinner("Gerando gráfico..."):
                    try:
                        fig = plotter.plot_curvas_transferencia_grid(
                            dados, 
                            etapas=etapas_selecionadas,
                            figsize=(20, 16)
                        )
                        st.pyplot(fig)
                        plt.close()
                    except Exception as e:
                        st.error(f"Erro ao gerar gráfico: {e}")
        else:
            st.warning("⚠️ Selecione pelo menos uma etapa para plotar")
    else:
        st.warning("⚠️ Nenhuma etapa de transferência disponível (bare, etoh, ddt, pbse, apt, eta)")

# ==================== TAB 2: Curvas Normalizadas ====================
with tab2:
    st.header("🔄 Curvas de Transferência Normalizadas - Todos os Devices")
    st.markdown(f"**Chip:** {chip_selecionado}")
    
    # Seleção de etapas
    etapas_disponiveis_tab2 = [etapa for etapa in ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'] 
                                if etapa in dados]
    
    if etapas_disponiveis_tab2:
        col_etapas_norm, col_devices_norm = st.columns([1, 1])
        
        with col_etapas_norm:
            etapas_selecionadas_norm = st.multiselect(
                "📊 Escolha as etapas:",
                etapas_disponiveis_tab2,
                default=etapas_disponiveis_tab2,
                key="etapas_norm",
                help="Selecione quais etapas incluir no gráfico normalizado"
            )
        
        with col_devices_norm:
            max_devices_norm = st.slider(
                "🎯 Número de devices:",
                min_value=1,
                max_value=min(20, len(devices_disponiveis)),
                value=min(20, len(devices_disponiveis)),
                key="max_devices_norm",
                help="Quantos devices plotar"
            )
        
        if etapas_selecionadas_norm:
            if st.button("🔄 Gerar Gráfico - Todas as Curvas Normalizadas", key="btn_todas_norm"):
                with st.spinner("Gerando gráfico..."):
                    try:
                        fig = plotter.plot_curvas_normalizadas_grid(
                            dados, 
                            etapas=etapas_selecionadas_norm,
                            figsize=(20, 16)
                        )
                        st.pyplot(fig)
                        plt.close()
                    except Exception as e:
                        st.error(f"Erro ao gerar gráfico: {e}")
        else:
            st.warning("⚠️ Selecione pelo menos uma etapa para plotar")
    else:
        st.warning("⚠️ Nenhuma etapa disponível para normalização")


# ==================== TAB 3: Device Individual ====================
with tab3:
    st.header("🎯 Análise de Device Individual")
    
    st.markdown(f"**📂 Experimento:** `{experimento_selecionado}` | **🔬 Chip:** `{chip_selecionado}`")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        device_selecionado = st.selectbox(
            "1️⃣ Selecione o Device:",
            devices_disponiveis,
            key="device_individual",
            help="Escolha qual device analisar"
        )
    
    with col2:
        # Filtrar etapas disponíveis
        etapas_device = [e for e in ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'] if e in dados]
        etapas_device_sel = st.multiselect(
            "2️⃣ Etapas:",
            etapas_device,
            default=etapas_device,
            key="etapas_device_individual",
            help="Etapas a incluir no gráfico"
        )
    
    with col3:
        tipo_grafico = st.radio(
            "3️⃣ Tipo:",
            ["Normal", "Normalizada"],
            key="tipo_individual"
        )
    
    if etapas_device_sel:
        if st.button("📊 Gerar Gráfico do Device", key="btn_device_individual"):
            with st.spinner("Gerando gráfico..."):
                try:
                    normalizado = tipo_grafico == "Normalizada"
                    fig = plotter.plot_device_individual(
                        dados, 
                        device_selecionado, 
                        etapas=etapas_device_sel,
                        normalizado=normalizado
                    )
                    st.pyplot(fig)
                    plt.close()
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico: {e}")
    else:
        st.warning("⚠️ Selecione pelo menos uma etapa")

# ==================== TAB 4: Curvas de Concentração ====================
with tab4:
    st.header("💧 Curvas de Concentração")
    
    st.markdown(f"**📂 Experimento:** `{experimento_selecionado}` | **🔬 Chip:** `{chip_selecionado}`")
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        device_concentracao = st.selectbox(
            "1️⃣ Selecione o Device:",
            devices_disponiveis,
            key="device_concentracao",
            help="Device para análise de concentrações"
        )
    
    with col2:
        normalizar_conc = st.checkbox("Normalizar", value=False, help="Normalizar curvas pelo máximo")
    
    # Seletor de concentrações disponíveis
    st.markdown("### 🧪 Selecione as Concentrações")
    
    concentracoes_disponiveis = {
        'menos18': '1 aM',
        'menos17': '10 aM',
        'menos16': '100 aM',
        'menos15': '1 fM',
        'menos14': '10 fM',
        'menos13': '100 fM',
        'menos12': '1 pM',
        'menos11': '10 pM',
        'menos10': '100 pM',
        'menos9': '1 nM',
        'menos8': '10 nM',
    }
    
    # Filtrar apenas as disponíveis nos dados
    concs_no_dados = {k: v for k, v in concentracoes_disponiveis.items() if k in dados}
    
    if concs_no_dados:
        col_conc1, col_conc2 = st.columns([3, 1])
        
        with col_conc1:
            concentracoes_selecionadas = st.multiselect(
                "Escolha as concentrações:",
                list(concs_no_dados.keys()),
                default=list(concs_no_dados.keys())[:3] if len(concs_no_dados) >= 3 else list(concs_no_dados.keys()),
                format_func=lambda x: concs_no_dados[x],
                help="Selecione quais concentrações plotar"
            )
        
        with col_conc2:
            incluir_branca = st.checkbox("Incluir Branca", value=True, help="Incluir curva branca (média BLANKs)")
        
        if concentracoes_selecionadas:
            if st.button("📊 Gerar Gráfico de Concentração", key="btn_concentracao"):
                with st.spinner("Gerando gráfico..."):
                    try:
                        fig = plotter.plot_concentracoes(
                            dados, 
                            device_concentracao, 
                            concentracoes=concentracoes_selecionadas,
                            incluir_branca=incluir_branca,
                            normalizado=normalizar_conc
                        )
                        st.pyplot(fig)
                        plt.close()
                    except Exception as e:
                        st.error(f"Erro ao gerar gráfico: {e}")
        else:
            st.warning("⚠️ Selecione pelo menos uma concentração")
    else:
        st.warning("⚠️ Nenhuma concentração disponível nos dados carregados")

# ==================== RODAPÉ ====================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>📊 GFET Curves Analysis Tool | Desenvolvido com Streamlit</p>
    </div>
""", unsafe_allow_html=True)