import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import glob
import io
import plotly.graph_objects as go

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


@st.cache_data
def construir_tabelao(base_path):
    """Monta um DataFrame consolidado (long/tidy) para todos os chips da pasta selecionada."""
    loader_local = DataLoader(base_path)
    chips = loader_local.listar_chips_disponiveis()

    registros = []
    for chip in chips:
        dados_chip = loader_local.carregar_chip(chip)
        for etapa, df_etapa in dados_chip.items():
            if 'V_G' not in df_etapa.columns:
                continue

            colunas_devices = [c for c in df_etapa.columns if c != 'V_G']
            if not colunas_devices:
                continue

            bloco = df_etapa.melt(
                id_vars='V_G',
                value_vars=colunas_devices,
                var_name='device',
                value_name='I_DS'
            ).copy()
            bloco['chip'] = chip
            bloco['etapa'] = etapa
            registros.append(bloco)

    if not registros:
        return pd.DataFrame(columns=['chip', 'etapa', 'V_G', 'device', 'I_DS'])

    df_exec = pd.concat(registros, ignore_index=True)
    df_exec['device'] = df_exec['device'].astype(str)
    df_exec['V_G'] = pd.to_numeric(df_exec['V_G'], errors='coerce')
    df_exec['I_DS'] = pd.to_numeric(df_exec['I_DS'], errors='coerce')
    df_exec = df_exec.dropna(subset=['V_G', 'I_DS']).reset_index(drop=True)

    return df_exec


def df_para_dados_plot(df_base, chip_sel, etapas_sel=None):
    """Reconstrói dicionário etapa -> DataFrame no formato esperado pelo PlotterGFET."""
    df_chip = df_base[df_base['chip'] == chip_sel].copy()
    if df_chip.empty:
        return {}

    if etapas_sel is None:
        etapas_sel = sorted(df_chip['etapa'].unique().tolist())

    dados_plot = {}
    for etapa in etapas_sel:
        df_etapa = df_chip[df_chip['etapa'] == etapa]
        if df_etapa.empty:
            continue

        pivot = (
            df_etapa.pivot_table(
                index='V_G',
                columns='device',
                values='I_DS',
                aggfunc='mean'
            )
            .reset_index()
            .sort_values('V_G')
            .reset_index(drop=True)
        )
        pivot.columns.name = None

        cols_devices = sorted([c for c in pivot.columns if c != 'V_G'], key=lambda x: (len(str(x)), str(x)))
        dados_plot[etapa] = pivot[['V_G'] + cols_devices]

    return dados_plot


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

# Opção de incluir média dos blanks
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Opções de Visualização")
incluir_media_blanks = st.sidebar.checkbox(
    "📊 Incluir Média dos BLANKS (B1+B2+B3)",
    value=True,
    help="Mostra a linha de média dos blanks em rosa nos gráficos"
)

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Curvas de Transferência", 
    "🔄 Curvas Normalizadas",
    "🎯 Device Individual",
    "💧 Curvas de Concentração",
    "🗃️ Tabelão",
    "🔍 Análise Manual",
    "📉 Análise Manual - CURVAS"
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
                        devices_limitados = devices_disponiveis[:max_devices]
                        dados_filtrados = {}
                        for etapa in etapas_selecionadas:
                            if etapa in dados:
                                df = dados[etapa]
                                colunas = ['V_G'] + [d for d in devices_limitados if d in df.columns]
                                if len(colunas) > 1:
                                    dados_filtrados[etapa] = df[colunas]
                        if not dados_filtrados:
                            st.warning("⚠️ Nenhum device selecionado disponível nas etapas escolhidas")
                        else:
                            fig = plotter.plot_curvas_transferencia_grid(
                                dados_filtrados, 
                                etapas=etapas_selecionadas,
                                figsize=(20, 16),
                                incluir_media_blanks=incluir_media_blanks
                            )
                            st.pyplot(fig)
                            plt.close()
                    except Exception as e:
                        st.error(f"Erro ao gerar gráfico: {e}")
            st.markdown("---")
            st.markdown("### 🎯 Seleção de Devices Específicos")

            devices_selecionados = st.multiselect(
                "🧩 Escolha os devices para plotar:",
                devices_disponiveis,
                default=devices_disponiveis[:min(4, len(devices_disponiveis))],
                help="Selecione devices específicos para explorar após a visão geral"
            )

            if devices_selecionados:
                if st.button("🔄 Gerar Gráfico - Devices Selecionados", key="btn_devices_selecionados"):
                    with st.spinner("Gerando gráfico..."):
                        try:
                            dados_filtrados = {}
                            for etapa in etapas_selecionadas:
                                if etapa in dados:
                                    df = dados[etapa]
                                    colunas = ['V_G'] + [d for d in devices_selecionados if d in df.columns]
                                    if len(colunas) > 1:
                                        dados_filtrados[etapa] = df[colunas]

                            if not dados_filtrados:
                                st.warning("⚠️ Nenhum device selecionado disponível nas etapas escolhidas")
                            else:
                                fig = plotter.plot_curvas_transferencia_grid(
                                    dados_filtrados,
                                    etapas=etapas_selecionadas,
                                    figsize=(20, 16),
                                    incluir_media_blanks=incluir_media_blanks
                                )
                                st.pyplot(fig)
                                plt.close()
                        except Exception as e:
                            st.error(f"Erro ao gerar gráfico: {e}")
            else:
                st.warning("⚠️ Selecione pelo menos um device para plotar")
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
                            figsize=(20, 16),
                            incluir_media_blanks=incluir_media_blanks
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
                        normalizado=normalizado,
                        incluir_media_blanks=incluir_media_blanks
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


# ==================== TAB 5: Tabelão ====================
with tab5:
    st.header("🗃️ Tabelão de Dados (Formato Long)")
    st.markdown("Estrutura consolidada para execução de análises e plots: **chip, etapa, V_G, device, I_DS**")
    st.markdown(f"**📂 Experimento:** `{experimento_selecionado}`")
    st.markdown(f"**📁 Pasta:** `{pasta_dados}`")

    with st.spinner("Montando tabelão..."):
        df_exec = construir_tabelao(pasta_dados)

    if df_exec.empty:
        st.warning("⚠️ Não foi possível montar o tabelão com os dados disponíveis.")
    else:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Linhas", f"{len(df_exec):,}")
        col_b.metric("Chips", df_exec['chip'].nunique())
        col_c.metric("Etapas", df_exec['etapa'].nunique())

        resumo = (
            df_exec.groupby('chip')
            .agg(
                n_etapas=('etapa', 'nunique'),
                n_devices=('device', 'nunique'),
                n_pontos=('I_DS', 'size')
            )
            .sort_values(['n_etapas', 'n_devices', 'n_pontos'], ascending=False)
            .reset_index()
        )

        st.markdown("### 📊 Resumo por chip")
        st.dataframe(resumo, use_container_width=True)

        st.markdown("### 🔎 Visualização do tabelão")
        chips_filtro = st.multiselect(
            "Filtrar chips:",
            sorted(df_exec['chip'].unique().tolist()),
            default=sorted(df_exec['chip'].unique().tolist())
        )
        etapas_filtro = st.multiselect(
            "Filtrar etapas:",
            sorted(df_exec['etapa'].unique().tolist()),
            default=sorted(df_exec['etapa'].unique().tolist())
        )

        df_view = df_exec[
            df_exec['chip'].isin(chips_filtro) &
            df_exec['etapa'].isin(etapas_filtro)
        ]

        st.caption(f"Mostrando {len(df_view):,} linhas após filtros")
        st.dataframe(df_view, use_container_width=True, height=420)

        st.markdown("---")
        st.markdown("### 📈 Plot interativo a partir do tabelão")

        chips_plot = sorted(df_view['chip'].unique().tolist())
        if not chips_plot:
            st.warning("⚠️ Não há chips disponíveis após os filtros para plotagem.")
        else:
            chip_plot = st.selectbox(
                "Chip para plot:",
                chips_plot,
                key="chip_plot_tabelao"
            )

            etapas_chip_plot = sorted(df_view[df_view['chip'] == chip_plot]['etapa'].unique().tolist())
            etapas_plot_sel = st.multiselect(
                "Etapas para plot:",
                etapas_chip_plot,
                default=etapas_chip_plot,
                key="etapas_plot_tabelao"
            )

            modo_plot = st.radio(
                "Modo de visualização:",
                ["Plot simples", "Grid de gráficos", "Comparativo de devices"],
                horizontal=True,
                key="modo_plot_tabelao"
            )

            dados_plot_tab = df_para_dados_plot(df_view, chip_sel=chip_plot, etapas_sel=etapas_plot_sel)

            if not dados_plot_tab:
                st.warning("⚠️ Não foi possível reconstruir dados de plot com os filtros atuais.")
            else:
                plotter_tab = PlotterGFET(chip_name=chip_plot)
                etapa_ref = list(dados_plot_tab.keys())[0]
                devices_plot_tab = [c for c in dados_plot_tab[etapa_ref].columns if c != 'V_G']

                if not devices_plot_tab:
                    st.warning("⚠️ Nenhum device disponível para plotagem.")
                else:
                    devices_grid = []
                    if modo_plot == "Plot simples":
                        col_plot_1, col_plot_2 = st.columns([2, 1])
                        with col_plot_1:
                            device_plot = st.selectbox(
                                "Device:",
                                devices_plot_tab,
                                key="device_plot_tabelao"
                            )
                        with col_plot_2:
                            normalizado_plot = st.checkbox(
                                "Normalizado",
                                value=False,
                                key="normalizado_plot_tabelao"
                            )

                        if st.button("Gerar Plot Simples", key="btn_plot_simples_tabelao"):
                            try:
                                fig = plotter_tab.plot_device_individual(
                                    dados=dados_plot_tab,
                                    device=device_plot,
                                    etapas=list(dados_plot_tab.keys()),
                                    normalizado=normalizado_plot,
                                    figsize=(10, 6)
                                )
                                st.pyplot(fig)
                                plt.close()
                            except Exception as e:
                                st.error(f"Erro ao gerar plot simples: {e}")
                    elif modo_plot == "Grid de gráficos":
                        col_grid_1, col_grid_2 = st.columns([2, 1])
                        with col_grid_1:
                            devices_grid = st.multiselect(
                                "Devices para grid:",
                                devices_plot_tab,
                                default=devices_plot_tab[:min(6, len(devices_plot_tab))],
                                key="devices_grid_tabelao"
                            )
                        with col_grid_2:
                            largura_grid = st.slider(
                                "Largura figura",
                                min_value=12,
                                max_value=24,
                                value=16,
                                step=1,
                                key="largura_grid_tabelao"
                            )

                        if st.button("Gerar Grid", key="btn_grid_tabelao"):
                            if not devices_grid:
                                st.warning("⚠️ Selecione pelo menos um device para o grid.")
                            else:
                                try:
                                    fig = plotter_tab.plot_curvas_transferencia_grid(
                                        dados=dados_plot_tab,
                                        etapas=list(dados_plot_tab.keys()),
                                        figsize=(largura_grid, 10),
                                        devices=devices_grid
                                    )
                                    st.pyplot(fig)
                                    plt.close()
                                except Exception as e:
                                    st.error(f"Erro ao gerar grid: {e}")
                    else:
                        col_comp_1, col_comp_2, col_comp_3 = st.columns([2, 2, 1])

                        with col_comp_1:
                            etapa_comp = st.selectbox(
                                "Etapa para comparação:",
                                list(dados_plot_tab.keys()),
                                key="etapa_comp_tabelao"
                            )

                        with col_comp_2:
                            devices_comp = st.multiselect(
                                "Devices para comparar:",
                                devices_plot_tab,
                                default=devices_plot_tab[:min(4, len(devices_plot_tab))],
                                key="devices_comp_tabelao"
                            )

                        with col_comp_3:
                            normalizar_comp = st.checkbox(
                                "Normalizar",
                                value=False,
                                key="normalizar_comp_tabelao"
                            )

                        if st.button("Gerar Comparativo", key="btn_comp_tabelao"):
                            if not devices_comp:
                                st.warning("⚠️ Selecione pelo menos um device para comparar.")
                            else:
                                try:
                                    df_comp = dados_plot_tab[etapa_comp]
                                    fig, ax = plt.subplots(figsize=(11, 7), facecolor="white")

                                    for device in devices_comp:
                                        if device not in df_comp.columns:
                                            continue
                                        y = df_comp[device].copy()
                                        if normalizar_comp:
                                            max_y = y.max()
                                            if pd.notna(max_y) and max_y != 0:
                                                y = y / max_y
                                        ax.plot(df_comp['V_G'], y, linewidth=1.8, label=f"Device {device}")

                                    ax.set_xlabel("V$_{GS}$ (V)")
                                    if normalizar_comp:
                                        ax.set_ylabel("I$_{DS}$ Normalizado")
                                        ax.set_title(f"Comparativo de Devices - {chip_plot} | Etapa {etapa_comp} (Normalizado)")
                                    else:
                                        ax.set_ylabel("I$_{DS}$ (A)")
                                        ax.set_yscale("log")
                                        ax.set_title(f"Comparativo de Devices - {chip_plot} | Etapa {etapa_comp}")
                                    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
                                    ax.legend(fontsize=9, ncol=2, loc='center left', bbox_to_anchor=(1.02, 0.5), frameon=False)
                                    fig.subplots_adjust(right=0.82)
                                    plt.tight_layout()

                                    st.pyplot(fig)
                                    plt.close()
                                except Exception as e:
                                    st.error(f"Erro ao gerar comparativo: {e}")

                    st.markdown("---")
                    st.markdown("### 📌 Device em Destaque")
                    devices_destaque_opcoes = devices_grid if modo_plot == "Grid de gráficos" and devices_grid else devices_plot_tab
                    device_destaque = st.selectbox(
                        "Escolha um device para gráfico grande:",
                        devices_destaque_opcoes,
                        key="device_destaque_tabelao"
                    )
                    normalizado_destaque = st.checkbox(
                        "Normalizar",
                        value=False,
                        key="normalizado_destaque_tabelao"
                    )
                    observacao_destaque = st.text_input(
                        "Observação para incluir na figura:",
                        key="observacao_destaque_tabelao"
                    )

                    if st.button("Gerar Gráfico Grande", key="btn_destaque_tabelao"):
                        try:
                            fig = plotter_tab.plot_device_individual(
                                dados=dados_plot_tab,
                                device=device_destaque,
                                etapas=list(dados_plot_tab.keys()),
                                normalizado=normalizado_destaque,
                                figsize=(12, 8)
                            )
                            if observacao_destaque:
                                fig.subplots_adjust(bottom=0.18)
                                fig.text(0.5, 0.03, observacao_destaque, ha='center', fontsize=10, color='black')
                            else:
                                fig.subplots_adjust(bottom=0.12)

                            st.pyplot(fig)
                            buf = io.BytesIO()
                            fig.savefig(
                                buf,
                                format="png",
                                dpi=300,
                                facecolor="white",
                                bbox_inches="tight",
                                pad_inches=0.8
                            )
                            buf.seek(0)
                            st.download_button(
                                "📥 Baixar PNG",
                                data=buf,
                                file_name=f"device_{device_destaque}.png",
                                mime="image/png"
                            )
                            plt.close(fig)
                        except Exception as e:
                            st.error(f"Erro ao gerar gráfico grande: {e}")

# ==================== TAB 6: Análise Manual ====================
with tab6:
    st.header("🔍 Análise Manual e Curadoria de Dados")
    st.markdown("Pipeline interativo: **Data → Chip → Device** com inspeção visual e aprovação manual")
    
    # Inicializar session state para rastrear seleções
    if 'data_selecionada_analise' not in st.session_state:
        st.session_state.data_selecionada_analise = None
    if 'devices_aprovados' not in st.session_state:
        st.session_state.devices_aprovados = {}
    
    st.markdown("---")
    st.markdown("### 📅 ETAPA 1: Seleção de Data de Aquisição")
    
    # Listar datas disponíveis (pastas em data/silver)
    base_path_analise = "data/silver"
    if os.path.exists(base_path_analise):
        datas_disponiveis = sorted([d for d in os.listdir(base_path_analise) 
                                   if os.path.isdir(os.path.join(base_path_analise, d)) and not d.startswith('.')])
    else:
        datas_disponiveis = []
    
    if not datas_disponiveis:
        st.warning("⚠️ Nenhuma data disponível em `data/silver/`")
    else:
        col_data_1, col_data_2 = st.columns([2, 1])
        with col_data_1:
            data_selecionada_analise = st.selectbox(
                "Escolha a data:",
                datas_disponiveis,
                key="data_analise_manual"
            )
        
        with col_data_2:
            n_datas = len(datas_disponiveis)
            st.metric("Datas Disponíveis", n_datas)
        
        # Carregar dados da data selecionada
        pasta_analise = os.path.join(base_path_analise, data_selecionada_analise)
        
        # Verificar subpastas
        subpastas_analise = [d for d in os.listdir(pasta_analise) 
                            if os.path.isdir(os.path.join(pasta_analise, d)) and not d.startswith('.')]
        
        if subpastas_analise:
            subpasta_analise = st.selectbox(
                "Selecione a subpasta (se houver):",
                subpastas_analise,
                key="subpasta_analise"
            )
            pasta_final_analise = os.path.join(pasta_analise, subpasta_analise)
        else:
            pasta_final_analise = pasta_analise
        
        st.info(f"📂 Pasta: `{pasta_final_analise}`")
        
        # Carregar todos os dados consolidados
        with st.spinner("Carregando dados consolidados..."):
            df_consolidado_analise = construir_tabelao(pasta_final_analise)
        
        if df_consolidado_analise.empty:
            st.warning("⚠️ Nenhum dado disponível para esta data")
        else:
            col_stat_1, col_stat_2, col_stat_3 = st.columns(3)
            with col_stat_1:
                st.metric("Total Chips", df_consolidado_analise['chip'].nunique())
            with col_stat_2:
                st.metric("Total Devices", df_consolidado_analise['device'].nunique())
            with col_stat_3:
                st.metric("Total Pontos", f"{len(df_consolidado_analise):,}")
            
            st.markdown("---")
            st.markdown("### 🔬 ETAPA 2: Seleção de Chips")
            
            chips_disponiveis_analise = sorted(df_consolidado_analise['chip'].unique().tolist())
            
            col_chip_select = st.columns(1)[0]
            chips_selecionados_analise = st.multiselect(
                "Escolha os chips para análise:",
                chips_disponiveis_analise,
                default=chips_disponiveis_analise,
                key="chips_analise_manual"
            )
            
            if not chips_selecionados_analise:
                st.warning("⚠️ Selecione pelo menos um chip")
            else:
                st.markdown("---")
                st.markdown("### 🎯 ETAPA 3: Inspeção Visual e Aprovação de Devices")
                st.markdown("**Fluxo:** Gere GRID com TODOS → Selecione BOM → Gere GRID SELECIONADO → ETAPA 4 consolida")
                
                # Criar tabs para cada chip selecionado
                chip_analise_tabs = st.tabs([f"🔬 {chip}" for chip in chips_selecionados_analise])
                
                for chip_atual, tab_chip in zip(chips_selecionados_analise, chip_analise_tabs):
                    with tab_chip:
                        st.markdown(f"#### Chip {chip_atual}")
                        
                        # Dados deste chip
                        df_chip_analise = df_consolidado_analise[df_consolidado_analise['chip'] == chip_atual]
                        # Ordenar devices numericamente (1, 2, 3, ..., 10, 11, ... em vez de 1, 10, 11, ..., 2)
                        devices_chip_analise = sorted(
                            df_chip_analise['device'].unique().tolist(),
                            key=lambda x: int(x) if str(x).isdigit() else float('inf')
                        )
                        etapas_chip_analise = sorted(df_chip_analise['etapa'].unique().tolist())
                        
                        col_info_chip_1, col_info_chip_2, col_info_chip_3 = st.columns(3)
                        with col_info_chip_1:
                            st.metric("Devices", len(devices_chip_analise))
                        with col_info_chip_2:
                            st.metric("Etapas", len(etapas_chip_analise))
                        with col_info_chip_3:
                            st.metric("Pontos", len(df_chip_analise))
                        
                        # Inicializar session state para seleções deste chip
                        key_selecionados = f"selecionados_{chip_atual}"
                        if key_selecionados not in st.session_state:
                            st.session_state[key_selecionados] = set()
                        
                        # Carregar dados do chip para plotagem
                        dados_chip_completo = carregar_dados(pasta_final_analise, chip_atual)
                        plotter_chip_analise = PlotterGFET(chip_name=chip_atual)
                        etapas_disponibles = [e for e in ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'] 
                                             if e in dados_chip_completo] if dados_chip_completo else []
                        
                        st.markdown("---")
                        st.markdown("##### 🎯 PASSO 1: Gerar Grid de TODOS os Devices")
                        
                        col_btn_1_1, col_btn_1_2, col_btn_1_3 = st.columns([1.5, 1.5, 2])
                        
                        with col_btn_1_1:
                            gerar_grid_todos = st.button(
                                "📊 Gerar Grid (TODOS)",
                                key=f"btn_grid_todos_{chip_atual}",
                                use_container_width=True,
                                help="Mostra todos os devices em um grid"
                            )
                        
                        with col_btn_1_2:
                            n_cols_grid = st.selectbox(
                                "Colunas:",
                                [3, 4, 5, 6],
                                index=1,
                                key=f"ncols_{chip_atual}",
                                help="Número de colunas no grid"
                            )
                        
                        with col_btn_1_3:
                            st.markdown("")  # Espaço para alinhamento
                        
                        # Armazenar grid no session state para não recarregar ao alterar checkboxes
                        key_grid_todos = f"grid_todos_{chip_atual}"
                        
                        if gerar_grid_todos:
                            if dados_chip_completo and etapas_disponibles:
                                with st.spinner(f"Gerando grid com {len(devices_chip_analise)} devices..."):
                                    try:
                                        # Preparar dados para plotagem
                                        nrows = int(np.ceil(len(devices_chip_analise) / n_cols_grid))
                                        figsize_altura = max(4 * nrows, 12)
                                        
                                        fig, axes = plt.subplots(nrows, n_cols_grid, figsize=(3*n_cols_grid, figsize_altura), facecolor='white')
                                        axes = np.array(axes).flatten()
                                        
                                        for idx, device in enumerate(devices_chip_analise):
                                            ax = axes[idx]
                                            
                                            # Plotar device em todas as etapas
                                            for etapa in etapas_disponibles:
                                                if device in dados_chip_completo[etapa].columns:
                                                    df_etapa = dados_chip_completo[etapa]
                                                    cor = plotter_chip_analise.cores_etapas.get(etapa, 'black')
                                                    label = plotter_chip_analise.labels_etapas.get(etapa, etapa)
                                                    ax.plot(df_etapa['V_G'], df_etapa[device], 
                                                           linewidth=1.5, label=label, color=cor, alpha=0.8)
                                            
                                            ax.set_title(f"Device {device}", fontsize=9, fontweight='bold')
                                            ax.set_xlabel("V$_{GS}$ (V)", fontsize=8)
                                            ax.set_ylabel("I$_{DS}$ (A)", fontsize=8)
                                            ax.set_yscale("log")
                                            ax.grid(True, alpha=0.3)
                                            ax.tick_params(labelsize=7)
                                            ax.legend(fontsize=6, loc='best')
                                        
                                        # Remover eixos extras
                                        for j in range(len(devices_chip_analise), len(axes)):
                                            fig.delaxes(axes[j])
                                        
                                        plt.tight_layout()
                                        
                                        # Armazenar figura no session state
                                        buf = io.BytesIO()
                                        fig.savefig(buf, format='png', dpi=100, facecolor='white', bbox_inches='tight')
                                        buf.seek(0)
                                        st.session_state[key_grid_todos] = buf.getvalue()
                                        
                                        st.pyplot(fig, use_container_width=True)
                                        plt.close()
                                        
                                        st.success(f"✅ Grid com {len(devices_chip_analise)} devices gerado!")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao gerar grid: {e}")
                            else:
                                st.warning("⚠️ Dados do chip não disponíveis")
                        elif key_grid_todos in st.session_state:
                            # Exibir grid armazenado sem recarregar
                            st.image(st.session_state[key_grid_todos], use_container_width=True)
                        
                        st.markdown("---")
                        st.markdown("##### ✅ PASSO 2: Selecione os Devices BOM")
                        
                        # Checkboxes para selecionar devices (em ordem numérica)
                        devices_ordenados_checkboxes = sorted(
                            devices_chip_analise,
                            key=lambda x: int(x) if str(x).isdigit() else float('inf')
                        )
                        cols_checkbox = st.columns(min(5, len(devices_ordenados_checkboxes)))
                        
                        for idx, device in enumerate(devices_ordenados_checkboxes):
                            col_idx = idx % len(cols_checkbox)
                            with cols_checkbox[col_idx]:
                                selecionado = st.checkbox(
                                    f"✅ {device}",
                                    value=device in st.session_state[key_selecionados],
                                    key=f"checkbox_device_{chip_atual}_{device}"
                                )
                                if selecionado:
                                    st.session_state[key_selecionados].add(device)
                                else:
                                    st.session_state[key_selecionados].discard(device)
                        
                        devices_selecionados_chip = list(st.session_state[key_selecionados])
                        
                        if devices_selecionados_chip:
                            st.success(f"✅ {len(devices_selecionados_chip)} device(s) selecionado(s)")
                        else:
                            st.info("👆 Selecione devices acima")
                        
                        st.markdown("---")
                        st.markdown("##### 🎯 PASSO 3: Gerar Grid dos Devices SELECIONADOS")
                        
                        if st.button(
                            f"📊 Gerar Grid (SELECIONADOS: {len(devices_selecionados_chip)})",
                            key=f"btn_grid_selecionados_{chip_atual}",
                            use_container_width=True,
                            disabled=(len(devices_selecionados_chip) == 0),
                            help="Mostra apenas os devices marcados acima"
                        ):
                            if dados_chip_completo and etapas_disponibles and devices_selecionados_chip:
                                with st.spinner(f"Gerando grid com {len(devices_selecionados_chip)} devices selecionados..."):
                                    try:
                                        # Ordenar devices selecionados numericamente
                                        devices_selecionados_chip_ordenados = sorted(
                                            devices_selecionados_chip,
                                            key=lambda x: int(x) if str(x).isdigit() else float('inf')
                                        )
                                        
                                        # Preparar dados para plotagem
                                        nrows_sel = int(np.ceil(len(devices_selecionados_chip_ordenados) / n_cols_grid))
                                        figsize_altura_sel = max(4 * nrows_sel, 12)
                                        
                                        fig_sel, axes_sel = plt.subplots(nrows_sel, n_cols_grid, 
                                                                        figsize=(3*n_cols_grid, figsize_altura_sel), 
                                                                        facecolor='white')
                                        axes_sel = np.array(axes_sel).flatten()
                                        
                                        for idx, device in enumerate(devices_selecionados_chip_ordenados):
                                            ax = axes_sel[idx]
                                            
                                            # Plotar device em todas as etapas
                                            for etapa in etapas_disponibles:
                                                if device in dados_chip_completo[etapa].columns:
                                                    df_etapa = dados_chip_completo[etapa]
                                                    cor = plotter_chip_analise.cores_etapas.get(etapa, 'black')
                                                    label = plotter_chip_analise.labels_etapas.get(etapa, etapa)
                                                    ax.plot(df_etapa['V_G'], df_etapa[device], 
                                                           linewidth=2, label=label, color=cor, alpha=0.85)
                                            
                                            ax.set_title(f"Device {device} (BOM)", fontsize=10, fontweight='bold', color='green')
                                            ax.set_xlabel("V$_{GS}$ (V)", fontsize=9)
                                            ax.set_ylabel("I$_{DS}$ (A)", fontsize=9)
                                            ax.set_yscale("log")
                                            ax.grid(True, alpha=0.3)
                                            ax.tick_params(labelsize=8)
                                            ax.legend(fontsize=7, loc='best')
                                        
                                        # Remover eixos extras
                                        for j in range(len(devices_selecionados_chip_ordenados), len(axes_sel)):
                                            fig_sel.delaxes(axes_sel[j])
                                        
                                        plt.tight_layout()
                                        st.pyplot(fig_sel, use_container_width=True)
                                        plt.close()
                                        
                                        st.success(f"✅ Grid com {len(devices_selecionados_chip_ordenados)} devices SELECIONADOS gerado!")
                                    except Exception as e:
                                        st.error(f"❌ Erro ao gerar grid selecionado: {e}")
                            else:
                                st.warning("⚠️ Nenhum device selecionado ou dados indisponíveis")
                
                st.markdown("---")
                st.markdown("### 📊 ETAPA 4: Consolidação e Gráfico Final (Devices Selecionados)")
                st.markdown("Os devices **BOM** de cada chip selecionado compõem o gráfico consolidado abaixo")
                
                # Resumo de seleções
                st.markdown("**📋 Resumo de Devices Selecionados:**")
                
                resumo_selecoes = []
                total_devices_selecionados = 0
                
                for chip_res in chips_selecionados_analise:
                    key_selecionados_res = f"selecionados_{chip_res}"
                    if key_selecionados_res in st.session_state:
                        devices_selecionados_res = list(st.session_state[key_selecionados_res])
                        n_selecionados = len(devices_selecionados_res)
                        total_devices_selecionados += n_selecionados
                        
                        n_total = len(df_consolidado_analise[df_consolidado_analise['chip'] == chip_res]['device'].unique())
                        
                        resumo_selecoes.append({
                            'Chip': chip_res,
                            'Selecionados': n_selecionados,
                            'Total': n_total,
                            'Taxa': f"{100*n_selecionados/n_total:.1f}%" if n_total > 0 else "0%",
                            'Devices': ', '.join(devices_selecionados_res[:5]) + ('...' if n_selecionados > 5 else '')
                        })
                
                if resumo_selecoes:
                    df_resumo_selecoes = pd.DataFrame(resumo_selecoes)
                    st.dataframe(df_resumo_selecoes, use_container_width=True, hide_index=True)
                
                if total_devices_selecionados == 0:
                    st.warning("⚠️ Nenhum device selecionado. Complete a ETAPA 3 primeiro.")
                else:
                    st.success(f"✅ Total de **{total_devices_selecionados}** devices selecionados para análise")
                
                st.markdown("---")
                
                col_btn_consolidar_1, col_btn_consolidar_2 = st.columns([1, 4])
                
                with col_btn_consolidar_1:
                    btn_gerar_consolidado = st.button(
                        "🔄 Gerar Gráfico Final",
                        key="btn_gerar_consolidado",
                        use_container_width=True,
                        disabled=(total_devices_selecionados == 0)
                    )
                
                if btn_gerar_consolidado:
                    with st.spinner("Consolidando dados selecionados e gerando análise..."):
                        try:
                            # Filtrar apenas devices SELECIONADOS
                            df_filtrado = df_consolidado_analise.copy()
                            
                            dfs_para_concat = []
                            
                            for chip_filtro in chips_selecionados_analise:
                                key_selecionados_filtro = f"selecionados_{chip_filtro}"
                                if key_selecionados_filtro in st.session_state:
                                    devices_selecionados_filtro = list(st.session_state[key_selecionados_filtro])
                                    
                                    if devices_selecionados_filtro:
                                        # Manter apenas devices selecionados deste chip
                                        df_chip_filtro = df_consolidado_analise[df_consolidado_analise['chip'] == chip_filtro]
                                        df_chip_filtrado = df_chip_filtro[df_chip_filtro['device'].isin(devices_selecionados_filtro)]
                                        dfs_para_concat.append(df_chip_filtrado)
                            
                            if dfs_para_concat:
                                df_filtrado = pd.concat(dfs_para_concat, ignore_index=True)
                            else:
                                df_filtrado = pd.DataFrame()
                            
                            if df_filtrado.empty:
                                st.error("❌ Nenhum device foi selecionado para análise")
                            else:
                                st.success(f"✅ Dados filtrados: {len(df_filtrado):,} pontos de {df_filtrado['device'].nunique()} devices selecionados")
                                
                                st.markdown("---")
                                st.markdown("#### 📈 V$_{Dirac}$ - Charge Neutrality Point")
                                
                                # Processar V_Dirac
                                try:
                                    df_vdirac_consolidado, stats_vdirac_consolidado = plotter.processar_vdirac_multiplos_chips(
                                        df_filtrado,
                                        etapas_ordem=['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'],
                                        devices_por_chip=None  # Usa todos os selecionados
                                    )
                                    
                                    if df_vdirac_consolidado.empty:
                                        st.warning("⚠️ Não foi possível calcular V_Dirac com os dados")
                                    else:
                                        # Gerar gráfico
                                        fig_consolidado = plotter.plot_vdirac_evolucao(
                                            df_vdirac_consolidado,
                                            stats_vdirac_consolidado,
                                            etapas_ordem=['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta'],
                                            figsize=(13, 7),
                                            titulo="V$_{Dirac}$ - Triagem Manual de Devices"
                                        )
                                        
                                        st.pyplot(fig_consolidado)
                                        
                                        # Download
                                        buf_consolidado = io.BytesIO()
                                        fig_consolidado.savefig(
                                            buf_consolidado, 
                                            format="png", 
                                            dpi=300, 
                                            facecolor="white", 
                                            bbox_inches="tight", 
                                            pad_inches=0.8
                                        )
                                        buf_consolidado.seek(0)
                                        st.download_button(
                                            "📥 Baixar Gráfico (PNG)",
                                            data=buf_consolidado,
                                            file_name=f"vdirac_consolidado_{data_selecionada_analise}.png",
                                            mime="image/png",
                                            key="download_consolidado_png"
                                        )
                                        
                                        plt.close(fig_consolidado)
                                        
                                        # Tabelas de resultados
                                        st.markdown("#### 📋 Estatísticas Consolidadas")
                                        
                                        stats_tabela_consolidada = []
                                        for etapa in ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']:
                                            if etapa in stats_vdirac_consolidado:
                                                stat = stats_vdirac_consolidado[etapa]
                                                stats_tabela_consolidada.append({
                                                    'Etapa': plotter.labels_etapas.get(etapa, etapa),
                                                    'V$_{Dirac}$ Médio (V)': f"{stat['media']:.4f}",
                                                    'SEM (V)': f"{stat['sem']:.4f}",
                                                    'Min (V)': f"{stat['min']:.4f}",
                                                    'Max (V)': f"{stat['max']:.4f}",
                                                    'N': stat['n_valores']
                                                })
                                        
                                        df_stats_consolidada = pd.DataFrame(stats_tabela_consolidada)
                                        st.dataframe(df_stats_consolidada, use_container_width=True, hide_index=True)
                                        
                                        # Dados brutos
                                        st.markdown("#### 🗃️ Dados Brutos (V$_{Dirac}$ por Device)")
                                        
                                        df_vdirac_pivot_consolidada = df_vdirac_consolidado.pivot_table(
                                            index=['chip', 'device'],
                                            columns='etapa',
                                            values='vdirac',
                                            aggfunc='mean'
                                        ).reset_index()
                                        
                                        etapas_colunas_consolidada = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
                                        cols_display_consolidada = ['chip', 'device'] + [e for e in etapas_colunas_consolidada if e in df_vdirac_pivot_consolidada.columns]
                                        df_vdirac_pivot_consolidada = df_vdirac_pivot_consolidada[cols_display_consolidada]
                                        
                                        for col in etapas_colunas_consolidada:
                                            if col in df_vdirac_pivot_consolidada.columns:
                                                df_vdirac_pivot_consolidada[col] = df_vdirac_pivot_consolidada[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
                                        
                                        st.dataframe(df_vdirac_pivot_consolidada, use_container_width=True, height=400)
                                        
                                        # CSV para download
                                        csv_consolidado = df_vdirac_consolidado.to_csv(index=False)
                                        st.download_button(
                                            "📥 Baixar Dados (CSV)",
                                            data=csv_consolidado,
                                            file_name=f"vdirac_consolidado_{data_selecionada_analise}.csv",
                                            mime="text/csv",
                                            key="download_consolidado_csv"
                                        )
                                        
                                        # Agrupamento
                                        st.markdown("#### 🎯 Agrupamento de Chips")
                                        
                                        try:
                                            grupos_consolidados = plotter.agrupar_chips_por_vdirac(df_vdirac_consolidado, stats_vdirac_consolidado)
                                            
                                            for grupo_nome_cons, chips_grupo_cons in grupos_consolidados.items():
                                                vdirac_grupo_cons = df_vdirac_consolidado[
                                                    (df_vdirac_consolidado['chip'].isin(chips_grupo_cons)) & 
                                                    (df_vdirac_consolidado['etapa'] == 'bare')
                                                ]['vdirac'].values
                                                
                                                if len(vdirac_grupo_cons) > 0:
                                                    vdirac_medio_grupo_cons = np.mean(vdirac_grupo_cons)
                                                    
                                                    col_grupo_cons_1, col_grupo_cons_2 = st.columns([2, 1])
                                                    with col_grupo_cons_1:
                                                        st.markdown(f"**{grupo_nome_cons}:** {', '.join(chips_grupo_cons)}")
                                                    with col_grupo_cons_2:
                                                        st.metric("V$_{Dirac}$ BARE", f"{vdirac_medio_grupo_cons:.4f} V")
                                        except:
                                            st.info("ℹ️ Agrupamento não disponível para estes dados")
                                except Exception as e:
                                    st.error(f"❌ Erro ao processar V_Dirac: {e}")
                                
                                # ---- Curvas médias por etapa ----
                                st.markdown("---")
                                st.markdown("#### 📉 Curvas Médias por Etapa")
                                st.markdown("Média de I$_{DS}$ sobre todos os devices selecionados, para cada etapa")
                                
                                try:
                                    etapas_ordem_cm = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
                                    etapas_presentes_cm = [e for e in etapas_ordem_cm if e in df_filtrado['etapa'].values]
                                    
                                    if not etapas_presentes_cm:
                                        st.warning("⚠️ Nenhuma etapa disponível para plotar curvas médias")
                                    else:
                                        df_media_cm = (
                                            df_filtrado[df_filtrado['etapa'].isin(etapas_presentes_cm)]
                                            .groupby(['etapa', 'V_G'], sort=False)['I_DS']
                                            .mean()
                                            .reset_index()
                                        )
                                        
                                        fig_cm, ax_cm = plt.subplots(figsize=(12, 7), facecolor='white')
                                        
                                        for etapa_cm in etapas_presentes_cm:
                                            df_et_cm = df_media_cm[df_media_cm['etapa'] == etapa_cm].sort_values('V_G')
                                            cor_cm = plotter.cores_etapas.get(etapa_cm, 'black')
                                            label_cm = plotter.labels_etapas.get(etapa_cm, etapa_cm)
                                            ax_cm.plot(df_et_cm['V_G'], df_et_cm['I_DS'],
                                                       linewidth=2.2, label=label_cm, color=cor_cm)
                                        
                                        ax_cm.set_xlabel("V$_{GS}$ (V)", fontsize=13)
                                        ax_cm.set_ylabel("I$_{DS}$ Médio (A)", fontsize=13)
                                        ax_cm.set_yscale("log")
                                        ax_cm.set_title(
                                            f"Curvas Médias por Etapa — {total_devices_selecionados} device(s) selecionado(s)",
                                            fontsize=14, fontweight='bold'
                                        )
                                        ax_cm.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
                                        ax_cm.legend(fontsize=11, loc='best', frameon=False)
                                        plt.tight_layout()
                                        
                                        st.pyplot(fig_cm)
                                        
                                        buf_cm = io.BytesIO()
                                        fig_cm.savefig(buf_cm, format="png", dpi=300,
                                                       facecolor="white", bbox_inches="tight", pad_inches=0.5)
                                        buf_cm.seek(0)
                                        st.download_button(
                                            "📥 Baixar Curvas Médias (PNG)",
                                            data=buf_cm,
                                            file_name=f"curvas_medias_{data_selecionada_analise}.png",
                                            mime="image/png",
                                            key="download_curvas_medias_png"
                                        )
                                        plt.close(fig_cm)
                                except Exception as e:
                                    st.error(f"❌ Erro ao gerar curvas médias: {e}")
                                
                                # ---- Curvas médias: BLANKs + concentrações ng/mL ----
                                st.markdown("---")
                                st.markdown("#### 🧪 Curvas Médias — BLANK + Concentrações (ng/mL)")
                                st.markdown("b1, b2 e b3 são combinados em uma única curva **BLANK**; demais etapas plotadas individualmente")
                                
                                try:
                                    etapas_blanks = ['b1', 'b2', 'b3']
                                    etapas_concs  = ['c10ng', 'c25ng', 'c50ng', 'c75ng', 'c100ng']
                                    
                                    etapas_blanks_presentes = [e for e in etapas_blanks if e in df_filtrado['etapa'].values]
                                    etapas_concs_presentes  = [e for e in etapas_concs  if e in df_filtrado['etapa'].values]
                                    
                                    if not etapas_blanks_presentes and not etapas_concs_presentes:
                                        st.warning("⚠️ Nenhuma etapa de BLANK ou concentração disponível nos dados selecionados")
                                    else:
                                        fig_ng, ax_ng = plt.subplots(figsize=(12, 7), facecolor='white')
                                        
                                        # Curva BLANK: média de b1+b2+b3 juntos por V_G
                                        if etapas_blanks_presentes:
                                            df_blanks = (
                                                df_filtrado[df_filtrado['etapa'].isin(etapas_blanks_presentes)]
                                                .groupby('V_G', sort=False)['I_DS']
                                                .mean()
                                                .reset_index()
                                                .sort_values('V_G')
                                            )
                                            cor_blank = plotter.cores_etapas.get('b_avg', '#FF1493')
                                            ax_ng.plot(df_blanks['V_G'], df_blanks['I_DS'],
                                                       linewidth=2.5, label='BLANK', color=cor_blank,
                                                       linestyle='--')
                                        
                                        # Curvas de concentração: média por V_G para cada etapa
                                        for etapa_ng in etapas_concs_presentes:
                                            df_et_ng = (
                                                df_filtrado[df_filtrado['etapa'] == etapa_ng]
                                                .groupby('V_G', sort=False)['I_DS']
                                                .mean()
                                                .reset_index()
                                                .sort_values('V_G')
                                            )
                                            cor_ng    = plotter.cores_etapas.get(etapa_ng, 'black')
                                            label_ng  = plotter.labels_etapas.get(etapa_ng, etapa_ng)
                                            ax_ng.plot(df_et_ng['V_G'], df_et_ng['I_DS'],
                                                       linewidth=2.2, label=label_ng, color=cor_ng)
                                        
                                        ax_ng.set_xlabel("V$_{GS}$ (V)", fontsize=13)
                                        ax_ng.set_ylabel("I$_{DS}$ Médio (A)", fontsize=13)
                                        ax_ng.set_yscale("log")
                                        ax_ng.set_title(
                                            f"Curvas Médias — BLANK + Concentrações — {total_devices_selecionados} device(s)",
                                            fontsize=14, fontweight='bold'
                                        )
                                        ax_ng.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
                                        ax_ng.legend(fontsize=11, loc='best', frameon=False)
                                        plt.tight_layout()
                                        
                                        st.pyplot(fig_ng)
                                        
                                        buf_ng = io.BytesIO()
                                        fig_ng.savefig(buf_ng, format="png", dpi=300,
                                                       facecolor="white", bbox_inches="tight", pad_inches=0.5)
                                        buf_ng.seek(0)
                                        st.download_button(
                                            "📥 Baixar Curvas ng/mL (PNG)",
                                            data=buf_ng,
                                            file_name=f"curvas_ng_{data_selecionada_analise}.png",
                                            mime="image/png",
                                            key="download_curvas_ng_png"
                                        )
                                        plt.close(fig_ng)
                                except Exception as e:
                                    st.error(f"❌ Erro ao gerar curvas ng/mL: {e}")
                                
                                # ---- Curvas médias: BLANKs + série aM/fM/pM ----
                                st.markdown("---")
                                st.markdown("#### ⚗️ Curvas Médias — BLANK + Série de Diluição (aM → pM)")
                                st.markdown("b1, b2 e b3 são combinados em uma única curva **BLANK**; concentrações plotadas individualmente")
                                
                                try:
                                    etapas_blanks_m = ['b1', 'b2', 'b3']
                                    etapas_menos    = ['menos18', 'menos17', 'menos16',
                                                       'menos15', 'menos14', 'menos13',
                                                       'menos12', 'menos11', 'menos10']
                                    
                                    labels_menos = {
                                        'menos18': '1 aM',
                                        'menos17': '10 aM',
                                        'menos16': '100 aM',
                                        'menos15': '1 fM',
                                        'menos14': '10 fM',
                                        'menos13': '100 fM',
                                        'menos12': '1 pM',
                                        'menos11': '10 pM',
                                        'menos10': '100 pM',
                                    }
                                    
                                    etapas_blanks_m_presentes = [e for e in etapas_blanks_m if e in df_filtrado['etapa'].values]
                                    etapas_menos_presentes    = [e for e in etapas_menos    if e in df_filtrado['etapa'].values]
                                    
                                    if not etapas_blanks_m_presentes and not etapas_menos_presentes:
                                        st.warning("⚠️ Nenhuma etapa de BLANK ou diluição disponível nos dados selecionados")
                                    else:
                                        fig_m, ax_m = plt.subplots(figsize=(12, 7), facecolor='white')
                                        
                                        # Curva BLANK: média de b1+b2+b3 juntos por V_G
                                        if etapas_blanks_m_presentes:
                                            df_blanks_m = (
                                                df_filtrado[df_filtrado['etapa'].isin(etapas_blanks_m_presentes)]
                                                .groupby('V_G', sort=False)['I_DS']
                                                .mean()
                                                .reset_index()
                                                .sort_values('V_G')
                                            )
                                            cor_blank_m = plotter.cores_etapas.get('b_avg', '#FF1493')
                                            ax_m.plot(df_blanks_m['V_G'], df_blanks_m['I_DS'],
                                                      linewidth=2.5, label='BLANK', color=cor_blank_m,
                                                      linestyle='--')
                                        
                                        # Curvas de concentração por V_G
                                        for etapa_m in etapas_menos_presentes:
                                            df_et_m = (
                                                df_filtrado[df_filtrado['etapa'] == etapa_m]
                                                .groupby('V_G', sort=False)['I_DS']
                                                .mean()
                                                .reset_index()
                                                .sort_values('V_G')
                                            )
                                            cor_m   = plotter.cores_concentracoes.get(etapa_m, 'black')
                                            label_m = labels_menos.get(etapa_m, etapa_m)
                                            ax_m.plot(df_et_m['V_G'], df_et_m['I_DS'],
                                                      linewidth=2.2, label=label_m, color=cor_m)
                                        
                                        ax_m.set_xlabel("V$_{GS}$ (V)", fontsize=13)
                                        ax_m.set_ylabel("I$_{DS}$ Médio (A)", fontsize=13)
                                        ax_m.set_yscale("log")
                                        ax_m.set_title(
                                            f"Curvas Médias — BLANK + Diluição (aM→pM) — {total_devices_selecionados} device(s)",
                                            fontsize=14, fontweight='bold'
                                        )
                                        ax_m.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)
                                        ax_m.legend(fontsize=11, loc='best', frameon=False)
                                        plt.tight_layout()
                                        
                                        st.pyplot(fig_m)
                                        
                                        buf_m = io.BytesIO()
                                        fig_m.savefig(buf_m, format="png", dpi=300,
                                                      facecolor="white", bbox_inches="tight", pad_inches=0.5)
                                        buf_m.seek(0)
                                        st.download_button(
                                            "📥 Baixar Curvas Diluição (PNG)",
                                            data=buf_m,
                                            file_name=f"curvas_diluicao_{data_selecionada_analise}.png",
                                            mime="image/png",
                                            key="download_curvas_diluicao_png"
                                        )
                                        plt.close(fig_m)
                                except Exception as e:
                                    st.error(f"❌ Erro ao gerar curvas de diluição: {e}")
                                
                                # ---- Metadados da sessão de análise ----
                                st.markdown("---")
                                st.markdown("#### 🗂️ Metadados da Análise")
                                
                                # --- Chips e devices selecionados ---
                                meta_chips = []
                                for chip_m in chips_selecionados_analise:
                                    key_dev_m = f"selecionados_{chip_m}"
                                    devs_m = sorted(
                                        list(st.session_state.get(key_dev_m, set())),
                                        key=lambda x: int(x) if str(x).isdigit() else float('inf')
                                    )
                                    n_total_m = len(df_consolidado_analise[
                                        df_consolidado_analise['chip'] == chip_m
                                    ]['device'].unique())
                                    meta_chips.append({
                                        'Chip': chip_m,
                                        'Devices selecionados': ', '.join(devs_m) if devs_m else '—',
                                        'N selecionados': len(devs_m),
                                        'N total': n_total_m,
                                    })
                                
                                st.markdown("**Chips e devices incluídos na análise:**")
                                st.dataframe(pd.DataFrame(meta_chips), use_container_width=True, hide_index=True)
                                
                                # --- Etapas por gráfico ---
                                etapas_ordem_ref   = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
                                etapas_blanks_ref  = ['b1', 'b2', 'b3']
                                etapas_ng_ref      = ['c10ng', 'c25ng', 'c50ng', 'c75ng', 'c100ng']
                                etapas_menos_ref   = ['menos18', 'menos17', 'menos16',
                                                      'menos15', 'menos14', 'menos13',
                                                      'menos12', 'menos11', 'menos10']
                                labels_meta = {
                                    'bare': 'BARE', 'etoh': 'ETOH', 'ddt': 'DDT',
                                    'pbse': 'PBSE', 'apt': 'APT', 'eta': 'ETA',
                                    'b1': 'BLANK1', 'b2': 'BLANK2', 'b3': 'BLANK3',
                                    'c10ng': '10 ng/mL', 'c25ng': '25 ng/mL',
                                    'c50ng': '50 ng/mL', 'c75ng': '75 ng/mL', 'c100ng': '100 ng/mL',
                                    'menos18': '1 aM', 'menos17': '10 aM', 'menos16': '100 aM',
                                    'menos15': '1 fM', 'menos14': '10 fM', 'menos13': '100 fM',
                                    'menos12': '1 pM', 'menos11': '10 pM', 'menos10': '100 pM',
                                }
                                
                                etapas_presentes = set(df_filtrado['etapa'].unique())
                                
                                def fmt_etapas(lista):
                                    presentes = [e for e in lista if e in etapas_presentes]
                                    return ', '.join(labels_meta.get(e, e) for e in presentes) if presentes else '(nenhuma)'
                                
                                meta_graficos = [
                                    {
                                        'Gráfico': 'V_Dirac — evolução por etapa',
                                        'Etapas usadas': fmt_etapas(etapas_ordem_ref),
                                        'Critério da média': 'Média do V_Dirac (mínimo de I_DS) por device; barra de erro = SEM entre devices',
                                    },
                                    {
                                        'Gráfico': 'Curvas médias — bare/etoh/ddt/pbse/apt/eta',
                                        'Etapas usadas': fmt_etapas(etapas_ordem_ref),
                                        'Critério da média': 'Média de I_DS agrupada por (etapa, V_G) sobre todos os devices selecionados',
                                    },
                                    {
                                        'Gráfico': 'Curvas médias — BLANK + concentrações ng/mL',
                                        'Etapas usadas': f"BLANK ← {fmt_etapas(etapas_blanks_ref)} (média conjunta); {fmt_etapas(etapas_ng_ref)}",
                                        'Critério da média': 'BLANK: média de I_DS de b1+b2+b3 juntos por V_G; demais: média por (etapa, V_G)',
                                    },
                                    {
                                        'Gráfico': 'Curvas médias — BLANK + série diluição (aM→pM)',
                                        'Etapas usadas': f"BLANK ← {fmt_etapas(etapas_blanks_ref)} (média conjunta); {fmt_etapas(etapas_menos_ref)}",
                                        'Critério da média': 'BLANK: média de I_DS de b1+b2+b3 juntos por V_G; demais: média por (etapa, V_G)',
                                    },
                                ]
                                
                                st.markdown("**Critério de média e etapas por gráfico:**")
                                st.dataframe(pd.DataFrame(meta_graficos), use_container_width=True, hide_index=True)
                                
                                # --- Resumo numérico geral ---
                                n_chips_meta   = len(chips_selecionados_analise)
                                n_devs_meta    = total_devices_selecionados
                                n_pontos_meta  = len(df_filtrado)
                                etapas_meta    = sorted(etapas_presentes)
                                
                                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                                col_m1.metric("Chips", n_chips_meta)
                                col_m2.metric("Devices", n_devs_meta)
                                col_m3.metric("Etapas presentes", len(etapas_meta))
                                col_m4.metric("Pontos totais", f"{n_pontos_meta:,}")
                                
                                with st.expander("📋 Lista completa de etapas presentes nos dados"):
                                    st.write(', '.join(labels_meta.get(e, e) for e in etapas_meta))
                                
                                # ---- Personalização via HTML auto-suficiente ----
                                st.markdown("---")
                                st.markdown("#### 🎨 Exportar Gráfico Interativo (HTML)")
                                st.markdown("Escolha o gráfico, clique em **Gerar HTML** e abra o arquivo para personalizar cores, estilos, labels e título — tudo no navegador, sem recarregar nada")
                                
                                import matplotlib.colors as _mcolors
                                import json as _json
                                
                                def _to_hex(c):
                                    try:
                                        return _mcolors.to_hex(_mcolors.to_rgba(c))
                                    except Exception:
                                        return '#000000'
                                
                                def _gerar_html_customizavel(curvas_data, titulo_default):
                                    """
                                    curvas_data: lista de dicts
                                        { id, label, color (hex), linestyle (plotly), linewidth, x: [], y: [] }
                                    Retorna string HTML auto-suficiente com painel de edição + Plotly.
                                    """
                                    data_js  = _json.dumps(curvas_data, ensure_ascii=False)
                                    titulo_js = _json.dumps(titulo_default, ensure_ascii=False)
                                    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Gráfico GFET — Personalização</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#f4f4f4;display:flex;height:100vh;overflow:hidden}}
#sidebar{{width:310px;min-width:260px;background:#fff;border-right:1px solid #dde;overflow-y:auto;
          padding:14px 12px;display:flex;flex-direction:column;gap:10px}}
#main{{flex:1;display:flex;flex-direction:column;padding:10px;gap:8px;min-width:0}}
h3{{font-size:13px;font-weight:700;color:#333;border-bottom:1px solid #eee;padding-bottom:5px;margin-bottom:2px}}
.block{{background:#f8f8fb;border:1px solid #e0e4ee;border-radius:6px;padding:9px 10px}}
.bname{{font-weight:600;font-size:12px;color:#333;margin-bottom:6px}}
label{{font-size:11px;color:#555;display:block;margin-bottom:2px;margin-top:5px}}
input[type=text],select{{width:100%;padding:4px 6px;border:1px solid #ccc;border-radius:4px;font-size:12px}}
input[type=color]{{width:44px;height:26px;border:none;border-radius:4px;padding:1px;cursor:pointer}}
.row{{display:flex;gap:7px;align-items:flex-end}}
.row>div{{flex:1}}
#titulo-input{{width:100%;padding:6px 8px;font-size:13px;border:1px solid #ccc;border-radius:4px}}
.btn{{padding:8px 12px;border:none;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600}}
#btn-apply{{background:#1976d2;color:#fff;width:100%}}
#btn-apply:hover{{background:#1255a0}}
#btn-png{{background:#388e3c;color:#fff}}
#btn-png:hover{{background:#276228}}
.toolbar{{display:flex;gap:8px;flex-wrap:wrap}}
#chart{{flex:1;min-height:0}}
</style>
</head>
<body>
<div id="sidebar">
  <h3>⚙️ Personalizar</h3>
  <div>
    <label>Título</label>
    <input type="text" id="titulo-input">
  </div>
  <div id="curves-panel"></div>
  <button class="btn" id="btn-apply" onclick="aplicar()">▶ Aplicar</button>
</div>
<div id="main">
  <div class="toolbar">
    <button class="btn" id="btn-png" onclick="baixarPNG()">📥 Baixar PNG</button>
  </div>
  <div id="chart"></div>
</div>
<script>
const DADOS = {data_js};
const TITULO_DEFAULT = {titulo_js};
document.getElementById('titulo-input').value = TITULO_DEFAULT;

function buildPanel(){{
  const p = document.getElementById('curves-panel');
  p.innerHTML = '';
  DADOS.forEach((c,i)=>{{
    const d = document.createElement('div');
    d.className = 'block';
    d.innerHTML = `
      <div class="bname">${{c.label}}</div>
      <div><label>Label</label>
        <input type="text" id="lbl-${{i}}" value="${{c.label}}">
      </div>
      <div class="row" style="margin-top:4px">
        <div><label>Cor</label><br>
          <input type="color" id="cor-${{i}}" value="${{c.color}}">
        </div>
        <div><label>Estilo</label>
          <select id="est-${{i}}">
            <option value="solid"   ${{c.linestyle==='solid'   ?'selected':''}}>Sólida</option>
            <option value="dash"    ${{c.linestyle==='dash'    ?'selected':''}}>Tracejada</option>
            <option value="dashdot" ${{c.linestyle==='dashdot' ?'selected':''}}>Traço-ponto</option>
            <option value="dot"     ${{c.linestyle==='dot'     ?'selected':''}}>Pontilhada</option>
          </select>
        </div>
        <div style="max-width:58px"><label>Espessura</label>
          <input type="text" id="lw-${{i}}" value="${{c.linewidth}}">
        </div>
      </div>`;
    p.appendChild(d);
  }});
}}

function aplicar(){{
  const titulo = document.getElementById('titulo-input').value;
  const traces = DADOS.map((c,i)=>{{
    const lbl = document.getElementById(`lbl-${{i}}`).value;
    const cor  = document.getElementById(`cor-${{i}}`).value;
    const est  = document.getElementById(`est-${{i}}`).value;
    const lw   = parseFloat(document.getElementById(`lw-${{i}}`).value)||2;
    return {{x:c.x, y:c.y, mode:'lines', name:lbl,
             line:{{color:cor, dash:est, width:lw}}}};
  }});
  const layout={{
    title:{{text:titulo, font:{{size:16}}}},
    xaxis:{{title:'V\u209A\u2091\u209C\u00a0(V)', showgrid:true, gridcolor:'#e0e0e0', zeroline:false}},
    yaxis:{{title:'I_DS M\u00e9dio (A)', type:'log', showgrid:true, gridcolor:'#e0e0e0', zeroline:false}},
    plot_bgcolor:'white', paper_bgcolor:'white',
    font:{{size:13}}, legend:{{font:{{size:11}}}},
    margin:{{l:75,r:25,t:60,b:60}}
  }};
  Plotly.react('chart', traces, layout, {{responsive:true}});
}}

function baixarPNG(){{
  Plotly.downloadImage('chart',{{format:'png',width:1400,height:800,filename:'grafico_gfet'}});
}}

buildPanel();
aplicar();
</script>
</body>
</html>"""
                                
                                # --- Catálogo de gráficos ---
                                _etapas_ord_h  = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
                                _etapas_bk_h   = ['b1', 'b2', 'b3']
                                _etapas_ng_h   = ['c10ng', 'c25ng', 'c50ng', 'c75ng', 'c100ng']
                                _etapas_am_h   = ['menos18', 'menos17', 'menos16',
                                                  'menos15', 'menos14', 'menos13',
                                                  'menos12', 'menos11', 'menos10']
                                _labels_h = {
                                    'bare':'BARE','etoh':'ETOH','ddt':'DDT','pbse':'PBSE','apt':'APT','eta':'ETA',
                                    'b1':'BLANK1','b2':'BLANK2','b3':'BLANK3',
                                    'c10ng':'10 ng/mL','c25ng':'25 ng/mL','c50ng':'50 ng/mL',
                                    'c75ng':'75 ng/mL','c100ng':'100 ng/mL',
                                    'menos18':'1 aM','menos17':'10 aM','menos16':'100 aM',
                                    'menos15':'1 fM','menos14':'10 fM','menos13':'100 fM',
                                    'menos12':'1 pM','menos11':'10 pM','menos10':'100 pM',
                                }
                                
                                _graficos_h = {}
                                if any(e in etapas_presentes for e in _etapas_ord_h):
                                    _graficos_h["Curvas médias — bare/etoh/ddt/pbse/apt/eta"] = {
                                        'tipo':'simples','curvas':_etapas_ord_h,
                                        'titulo': f"Curvas Médias por Etapa — {total_devices_selecionados} devices"
                                    }
                                if any(e in etapas_presentes for e in _etapas_bk_h + _etapas_ng_h):
                                    _graficos_h["Curvas médias — BLANK + concentrações (ng/mL)"] = {
                                        'tipo':'blank+concs','blanks':_etapas_bk_h,'curvas':_etapas_ng_h,
                                        'titulo': f"Curvas Médias — BLANK + ng/mL — {total_devices_selecionados} devices"
                                    }
                                if any(e in etapas_presentes for e in _etapas_bk_h + _etapas_am_h):
                                    _graficos_h["Curvas médias — BLANK + diluição (aM → pM)"] = {
                                        'tipo':'blank+concs','blanks':_etapas_bk_h,'curvas':_etapas_am_h,
                                        'titulo': f"Curvas Médias — BLANK + Diluição — {total_devices_selecionados} devices"
                                    }
                                
                                if not _graficos_h:
                                    st.warning("⚠️ Nenhum dado disponível para exportar")
                                else:
                                    _sel_h = st.selectbox(
                                        "Gráfico para exportar:",
                                        list(_graficos_h.keys()),
                                        key="html_graf_sel"
                                    )
                                    
                                    if st.button("🔄 Gerar HTML", key="btn_gerar_html", use_container_width=True):
                                        try:
                                            _info_h = _graficos_h[_sel_h]
                                            
                                            def _media_vg(etapa_k):
                                                return (df_filtrado[df_filtrado['etapa'] == etapa_k]
                                                        .groupby('V_G', sort=False)['I_DS'].mean()
                                                        .reset_index().sort_values('V_G'))
                                            
                                            def _media_bks(blist):
                                                pres = [e for e in blist if e in etapas_presentes]
                                                return (df_filtrado[df_filtrado['etapa'].isin(pres)]
                                                        .groupby('V_G', sort=False)['I_DS'].mean()
                                                        .reset_index().sort_values('V_G'))
                                            
                                            _curvas_h = []
                                            
                                            if _info_h['tipo'] == 'blank+concs':
                                                if any(e in etapas_presentes for e in _info_h['blanks']):
                                                    df_bk = _media_bks(_info_h['blanks'])
                                                    _curvas_h.append({
                                                        'id': '__blank__', 'label': 'BLANK',
                                                        'color': _to_hex(plotter.cores_etapas.get('b_avg','#FF1493')),
                                                        'linestyle': 'dash', 'linewidth': 2.5,
                                                        'x': df_bk['V_G'].tolist(),
                                                        'y': df_bk['I_DS'].tolist()
                                                    })
                                                for _e in _info_h['curvas']:
                                                    if _e not in etapas_presentes:
                                                        continue
                                                    df_e = _media_vg(_e)
                                                    _cor_e = _to_hex(plotter.cores_etapas.get(
                                                        _e, plotter.cores_concentracoes.get(_e, '#000000')))
                                                    _curvas_h.append({
                                                        'id': _e,
                                                        'label': _labels_h.get(_e, _e),
                                                        'color': _cor_e,
                                                        'linestyle': 'solid', 'linewidth': 2.2,
                                                        'x': df_e['V_G'].tolist(),
                                                        'y': df_e['I_DS'].tolist()
                                                    })
                                            else:
                                                for _e in _info_h['curvas']:
                                                    if _e not in etapas_presentes:
                                                        continue
                                                    df_e = _media_vg(_e)
                                                    _cor_e = _to_hex(plotter.cores_etapas.get(_e, '#000000'))
                                                    _curvas_h.append({
                                                        'id': _e,
                                                        'label': _labels_h.get(_e, _e),
                                                        'color': _cor_e,
                                                        'linestyle': 'solid', 'linewidth': 2.2,
                                                        'x': df_e['V_G'].tolist(),
                                                        'y': df_e['I_DS'].tolist()
                                                    })
                                            
                                            if not _curvas_h:
                                                st.warning("⚠️ Nenhuma curva disponível para este gráfico")
                                            else:
                                                _html_out = _gerar_html_customizavel(_curvas_h, _info_h['titulo'])
                                                st.session_state['_html_exportar'] = _html_out
                                                st.session_state['_html_exportar_nome'] = _sel_h
                                                # Salvar diretamente na pasta local
                                                import pathlib as _pl, re as _re
                                                _slug = _re.sub(r'[^a-zA-Z0-9_-]', '_', _sel_h)[:60]
                                                _pasta_exp = _pl.Path(__file__).parent / "exports"
                                                _pasta_exp.mkdir(exist_ok=True)
                                                _caminho_html = _pasta_exp / f"{_slug}.html"
                                                _caminho_html.write_text(_html_out, encoding='utf-8')
                                                st.session_state['_html_exportar_caminho'] = str(_caminho_html)
                                                st.success(f"✅ HTML salvo em `{_caminho_html}`  — e o botão de download aparece abaixo.")
                                        
                                        except Exception as e:
                                            st.error(f"❌ Erro ao gerar HTML: {e}")
                                            import traceback
                                            st.error(traceback.format_exc())
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar análise consolidada: {e}")
                            import traceback
                            st.error(traceback.format_exc())
                
                # --- Download HTML persistente (fora do if btn_gerar_consolidado) ---
                if '_html_exportar' in st.session_state:
                    st.markdown("---")
                    nome_graf = st.session_state.get('_html_exportar_nome', 'gráfico')
                    st.info(f"📄 HTML pronto: **{nome_graf}**")
                    st.download_button(
                        "📥 Baixar HTML interativo",
                        data=st.session_state['_html_exportar'],
                        file_name="grafico_personalizado.html",
                        mime="text/html",
                        key="download_html_persistente",
                        use_container_width=True
                    )

# ==================== RODAPÉ ====================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>📊 GFET Curves Analysis Tool | Desenvolvido com Streamlit</p>
    </div>
""", unsafe_allow_html=True)