import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import glob
import io

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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Curvas de Transferência", 
    "🔄 Curvas Normalizadas",
    "🎯 Device Individual",
    "💧 Curvas de Concentração",
    "🗃️ Tabelão"
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

# ==================== RODAPÉ ====================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>📊 GFET Curves Analysis Tool | Desenvolvido com Streamlit</p>
    </div>
""", unsafe_allow_html=True)