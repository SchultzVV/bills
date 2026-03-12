"""
App Streamlit para análise interativa de curvas GFET
Versão Estendida - Suporta todas as corridas e filtros avançados
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

# Importar módulo estendido
from dataprep_extended import (
    BronzeDataExtractor,
    ConsolidatedDataAnalyzer,
    create_consolidated_dataframe
)

# Configuração da página
st.set_page_config(
    page_title="📊 GFET Curves - Análise Avançada",
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
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================

@st.cache_data(show_spinner=False)
def carregar_dados_consolidados(base_path="data/bronze/GFETS"):
    """Carrega e cache o DataFrame consolidado"""
    extractor = BronzeDataExtractor(base_path)
    return extractor.create_consolidated_dataframe(verbose=False)


def converter_decimal_europeu(df, colunas):
    """Converte vírgulas para pontos em colunas específicas"""
    df_conv = df.copy()
    for col in colunas:
        if col in df_conv.columns:
            df_conv[col] = df_conv[col].astype(str).str.replace(',', '.')
            df_conv[col] = pd.to_numeric(df_conv[col], errors='coerce')
    return df_conv


def plot_curvas_comparacao(data_dict, titulo, x_col='Variable Source', y_col='dev1', 
                           log_scale=True, cores=None):
    """Plota múltiplas curvas de comparação"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if cores is None:
        cores = sns.color_palette('husl', len(data_dict))
    
    for idx, (label, df) in enumerate(data_dict.items()):
        if df is not None and len(df) > 0:
            ax.plot(df[x_col], df[y_col], 
                   label=label,
                   linewidth=2.5,
                   alpha=0.8,
                   color=cores[idx])
    
    ax.set_xlabel('Voltage (V)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Current (A)', fontsize=14, fontweight='bold')
    ax.set_title(titulo, fontsize=16, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    if log_scale:
        ax.set_yscale('symlog')
    
    plt.tight_layout()
    return fig


# ==================== INTERFACE PRINCIPAL ====================

st.title("📊 Análise Avançada de Curvas GFET")
st.markdown("**Sistema com suporte a múltiplas corridas e filtros avançados**")
st.markdown("---")

# Carregar dados consolidados
with st.spinner("🔄 Carregando dados consolidados (pode levar alguns segundos na primeira vez)..."):
    try:
        df_consolidated = carregar_dados_consolidados()
        analyzer = ConsolidatedDataAnalyzer(df_consolidated)
        st.success(f"✅ Dados carregados: {len(df_consolidated):,} linhas")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        st.stop()

# ==================== SIDEBAR: FILTROS ====================

st.sidebar.header("⚙️ Filtros de Dados")

# 1. Experimento
experimentos = analyzer.list_experiments()
experimento = st.sidebar.selectbox(
    "📅 Experimento:",
    experimentos,
    help="Selecione o experimento/data"
)

# 2. Pasta
pastas = analyzer.list_folders(experiment=experimento)
pasta = st.sidebar.selectbox(
    "📁 Pasta:",
    pastas,
    help="Selecione a pasta de dados"
)

# 3. Chip
chips = analyzer.list_chips(experiment=experimento, folder=pasta)
chip = st.sidebar.selectbox(
    "💾 Chip:",
    chips,
    help="Selecione o chip"
)

# 4. Etapas disponíveis para o chip selecionado
df_chip = analyzer.filter_data(experiment=experimento, folder=pasta, chip=chip)
etapas_disponiveis = sorted(df_chip['_etapa'].unique())

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estatísticas")
st.sidebar.info(f"🎯 Etapas disponíveis: **{len(etapas_disponiveis)}**")

# Mostrar etapas disponíveis
with st.sidebar.expander("📋 Ver Etapas Disponíveis"):
    for etapa in etapas_disponiveis:
        # Contar corridas para esta etapa
        df_etapa = analyzer.filter_data(
            experiment=experimento,
            folder=pasta,
            chip=chip,
            stage=etapa
        )
        num_corridas = df_etapa['_sweep_idx'].nunique()
        st.markdown(f"- **{etapa}** ({num_corridas} corridas)")

st.sidebar.markdown("---")

# ==================== TABS PRINCIPAIS ====================

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Comparar Etapas",
    "🔄 Comparar Corridas",
    "📊 Visualização Custom",
    "ℹ️ Info dos Dados"
])

# ==================== TAB 1: COMPARAR ETAPAS ====================
with tab1:
    st.header("📈 Comparação entre Etapas")
    st.markdown("Compare diferentes etapas de um mesmo chip")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        etapas_selecionadas = st.multiselect(
            "Selecione as etapas para comparar:",
            etapas_disponiveis,
            default=etapas_disponiveis[:min(3, len(etapas_disponiveis))],
            help="Escolha até 10 etapas"
        )
    
    with col2:
        device_col = st.selectbox(
            "Device:",
            ['dev1', 'dev2', 'dev3', 'dev4', 'dev5', 'dev6', 'dev7', 'dev8'],
            help="Selecione qual device plotar"
        )
        
        usar_log = st.checkbox("Escala logarítmica (Y)", value=True)
    
    if etapas_selecionadas:
        # Botão para gerar gráfico
        if st.button("🎨 Gerar Gráfico", key="btn_etapas"):
            with st.spinner("Preparando dados..."):
                plot_data = {}
                
                for etapa in etapas_selecionadas:
                    df_filtrado = analyzer.filter_data(
                        experiment=experimento,
                        folder=pasta,
                        chip=chip,
                        stage=etapa
                    )
                    
                    if len(df_filtrado) > 0:
                        # Usar última corrida
                        sweep_idx = df_filtrado['_sweep_idx'].max()
                        df_sweep = df_filtrado[df_filtrado['_sweep_idx'] == sweep_idx]
                        
                        # Converter formato decimal
                        df_sweep = converter_decimal_europeu(
                            df_sweep, 
                            ['Variable Source', device_col]
                        )
                        
                        # Preparar dados
                        df_plot = df_sweep[['Variable Source', device_col]].dropna()
                        
                        if len(df_plot) > 0:
                            plot_data[f"{chip} - {etapa}"] = df_plot
                
                if plot_data:
                    fig = plot_curvas_comparacao(
                        plot_data,
                        f"Comparação de Etapas - {chip} ({device_col})",
                        x_col='Variable Source',
                        y_col=device_col,
                        log_scale=usar_log
                    )
                    st.pyplot(fig)
                    
                    # Estatísticas
                    st.markdown("### 📊 Estatísticas")
                    stats_data = []
                    for label, df in plot_data.items():
                        stats_data.append({
                            'Etapa': label,
                            'Pontos': len(df),
                            'V_min': f"{df['Variable Source'].min():.3f}",
                            'V_max': f"{df['Variable Source'].max():.3f}",
                            'I_min': f"{df[device_col].min():.2e}",
                            'I_max': f"{df[device_col].max():.2e}"
                        })
                    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
                else:
                    st.warning("⚠️ Nenhum dado disponível para as etapas selecionadas")
    else:
        st.info("👆 Selecione pelo menos uma etapa para visualizar")


# ==================== TAB 2: COMPARAR CORRIDAS ====================
with tab2:
    st.header("🔄 Comparação entre Corridas")
    st.markdown("Compare diferentes corridas (sweeps) de uma mesma etapa")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        etapa_corridas = st.selectbox(
            "Selecione a etapa:",
            etapas_disponiveis,
            key="etapa_corridas",
            help="Escolha a etapa para comparar corridas"
        )
    
    with col2:
        device_col_corridas = st.selectbox(
            "Device:",
            ['dev1', 'dev2', 'dev3', 'dev4', 'dev5', 'dev6', 'dev7', 'dev8'],
            key="device_corridas",
            help="Selecione qual device plotar"
        )
        
        usar_log_corridas = st.checkbox("Escala logarítmica (Y)", value=True, key="log_corridas")
    
    if etapa_corridas:
        # Obter corridas disponíveis
        df_etapa_corridas = analyzer.filter_data(
            experiment=experimento,
            folder=pasta,
            chip=chip,
            stage=etapa_corridas
        )
        
        corridas_disponiveis = sorted(df_etapa_corridas['_sweep_idx'].unique())
        
        st.info(f"📊 **{len(corridas_disponiveis)}** corridas disponíveis para **{etapa_corridas}**")
        
        # Seletor de corridas
        corridas_selecionadas = st.multiselect(
            "Selecione as corridas para comparar:",
            corridas_disponiveis,
            default=corridas_disponiveis[-min(5, len(corridas_disponiveis)):],  # Últimas 5
            help="Escolha quais corridas comparar",
            key="corridas_sel"
        )
        
        if corridas_selecionadas:
            if st.button("🎨 Gerar Gráfico", key="btn_corridas"):
                with st.spinner("Preparando dados..."):
                    plot_data_corridas = {}
                    
                    for sweep_idx in corridas_selecionadas:
                        df_sweep = df_etapa_corridas[df_etapa_corridas['_sweep_idx'] == sweep_idx]
                        
                        # Converter formato decimal
                        df_sweep = converter_decimal_europeu(
                            df_sweep,
                            ['Variable Source', device_col_corridas]
                        )
                        
                        # Preparar dados
                        df_plot = df_sweep[['Variable Source', device_col_corridas]].dropna()
                        
                        if len(df_plot) > 0:
                            # Pegar timestamp se disponível
                            if '_timestamp' in df_sweep.columns:
                                timestamp = df_sweep['_timestamp'].iloc[0]
                                label = f"Corrida {sweep_idx} ({timestamp})"
                            else:
                                label = f"Corrida {sweep_idx}"
                            
                            plot_data_corridas[label] = df_plot
                    
                    if plot_data_corridas:
                        cores_corridas = sns.color_palette('viridis', len(plot_data_corridas))
                        fig = plot_curvas_comparacao(
                            plot_data_corridas,
                            f"Comparação de Corridas - {chip} - {etapa_corridas} ({device_col_corridas})",
                            x_col='Variable Source',
                            y_col=device_col_corridas,
                            log_scale=usar_log_corridas,
                            cores=cores_corridas
                        )
                        st.pyplot(fig)
                        
                        # Análise de reprodutibilidade
                        st.markdown("### 📊 Análise de Reprodutibilidade")
                        
                        # Calcular desvio padrão entre corridas em pontos comuns
                        col_rep1, col_rep2 = st.columns(2)
                        
                        with col_rep1:
                            st.metric("Corridas Comparadas", len(plot_data_corridas))
                            st.metric("Pontos por Corrida", 
                                     f"~{np.mean([len(df) for df in plot_data_corridas.values()]):.0f}")
                        
                        with col_rep2:
                            # Calcular coeficiente de variação médio
                            if len(plot_data_corridas) > 1:
                                valores_corridas = [df[device_col_corridas].values 
                                                   for df in plot_data_corridas.values()]
                                # Pegar apenas o tamanho mínimo comum
                                min_len = min([len(v) for v in valores_corridas])
                                valores_truncados = [v[:min_len] for v in valores_corridas]
                                valores_array = np.array(valores_truncados)
                                
                                cv_medio = np.mean(np.std(valores_array, axis=0) / 
                                                  (np.mean(valores_array, axis=0) + 1e-15)) * 100
                                st.metric("CV Médio", f"{cv_medio:.2f}%", 
                                         help="Coeficiente de variação médio entre corridas")
                    else:
                        st.warning("⚠️ Nenhum dado disponível para as corridas selecionadas")
        else:
            st.info("👆 Selecione pelo menos uma corrida para visualizar")


# ==================== TAB 3: VISUALIZAÇÃO CUSTOM ====================
with tab3:
    st.header("📊 Visualização Customizada")
    st.markdown("Monte sua própria visualização com controle total")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Eixo X:**")
        x_col_custom = st.selectbox(
            "Coluna X:",
            ['Variable Source'],
            key="x_custom"
        )
    
    with col2:
        st.markdown("**🎯 Eixo Y:**")
        colunas_device = [f'dev{i}' for i in range(1, 21)]
        y_col_custom = st.selectbox(
            "Coluna Y:",
            colunas_device,
            key="y_custom"
        )
    
    with col3:
        st.markdown("**🎨 Estilo:**")
        usar_log_custom = st.checkbox("Log Y", value=True, key="log_custom")
        mostrar_pontos = st.checkbox("Mostrar pontos", value=False)
    
    # Seleção flexível
    st.markdown("---")
    st.markdown("### 🔧 Configuração de Dados")
    
    modo_selecao = st.radio(
        "Modo de seleção:",
        ["Etapas específicas", "Todas as etapas", "Corridas específicas"],
        horizontal=True
    )
    
    if modo_selecao == "Etapas específicas":
        etapas_custom = st.multiselect(
            "Etapas:",
            etapas_disponiveis,
            default=etapas_disponiveis[:3]
        )
        usar_ultima_corrida = st.checkbox("Usar última corrida de cada etapa", value=True)
        
    elif modo_selecao == "Todas as etapas":
        etapas_custom = etapas_disponiveis
        usar_ultima_corrida = True
        
    else:  # Corridas específicas
        etapa_custom = st.selectbox("Etapa:", etapas_disponiveis, key="etapa_custom_sel")
        df_custom = analyzer.filter_data(
            experiment=experimento,
            folder=pasta,
            chip=chip,
            stage=etapa_custom
        )
        corridas_custom = sorted(df_custom['_sweep_idx'].unique())
        corridas_selecionadas_custom = st.multiselect(
            "Corridas:",
            corridas_custom,
            default=corridas_custom[-3:] if len(corridas_custom) > 0 else []
        )
    
    if st.button("🎨 Gerar Visualização Custom", key="btn_custom"):
        with st.spinner("Gerando visualização..."):
            plot_data_custom = {}
            
            if modo_selecao in ["Etapas específicas", "Todas as etapas"]:
                for etapa in etapas_custom:
                    df_filt = analyzer.filter_data(
                        experiment=experimento,
                        folder=pasta,
                        chip=chip,
                        stage=etapa
                    )
                    
                    if len(df_filt) > 0:
                        if usar_ultima_corrida:
                            sweep_idx = df_filt['_sweep_idx'].max()
                            df_use = df_filt[df_filt['_sweep_idx'] == sweep_idx]
                        else:
                            df_use = df_filt
                        
                        df_use = converter_decimal_europeu(df_use, [x_col_custom, y_col_custom])
                        df_plot = df_use[[x_col_custom, y_col_custom]].dropna()
                        
                        if len(df_plot) > 0:
                            plot_data_custom[etapa] = df_plot
            
            else:  # Corridas específicas
                for sweep_idx in corridas_selecionadas_custom:
                    df_sweep = df_custom[df_custom['_sweep_idx'] == sweep_idx]
                    df_sweep = converter_decimal_europeu(df_sweep, [x_col_custom, y_col_custom])
                    df_plot = df_sweep[[x_col_custom, y_col_custom]].dropna()
                    
                    if len(df_plot) > 0:
                        plot_data_custom[f"Corrida {sweep_idx}"] = df_plot
            
            if plot_data_custom:
                fig, ax = plt.subplots(figsize=(14, 9))
                cores = sns.color_palette('tab10', len(plot_data_custom))
                
                for idx, (label, df) in enumerate(plot_data_custom.items()):
                    if mostrar_pontos:
                        ax.plot(df[x_col_custom], df[y_col_custom], 
                               'o-', label=label, linewidth=2, markersize=4,
                               alpha=0.7, color=cores[idx])
                    else:
                        ax.plot(df[x_col_custom], df[y_col_custom],
                               label=label, linewidth=2.5, alpha=0.8, color=cores[idx])
                
                ax.set_xlabel(x_col_custom, fontsize=14, fontweight='bold')
                ax.set_ylabel(y_col_custom, fontsize=14, fontweight='bold')
                ax.set_title(f"Visualização Custom - {chip}", fontsize=16, fontweight='bold')
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
                
                if usar_log_custom:
                    ax.set_yscale('symlog')
                
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.warning("⚠️ Nenhum dado disponível")


# ==================== TAB 4: INFO DOS DADOS ====================
with tab4:
    st.header("ℹ️ Informações dos Dados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Linhas", f"{len(df_consolidated):,}")
    
    with col2:
        st.metric("Experimentos", len(experimentos))
    
    with col3:
        st.metric("Chips", len(analyzer.list_chips()))
    
    st.markdown("---")
    
    # Dados do chip atual
    st.subheader(f"📊 Dados do Chip: {chip}")
    
    dados_chip_completos = analyzer.filter_data(
        experiment=experimento,
        folder=pasta,
        chip=chip
    )
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("**📈 Etapas:**")
        etapas_info = dados_chip_completos.groupby('_etapa')['_sweep_idx'].nunique().reset_index()
        etapas_info.columns = ['Etapa', 'Nº Corridas']
        st.dataframe(etapas_info, use_container_width=True)
    
    with col_info2:
        st.markdown("**📊 Resumo:**")
        st.write(f"- Total de etapas: **{len(etapas_disponiveis)}**")
        st.write(f"- Total de corridas: **{dados_chip_completos['_sweep_idx'].nunique()}**")
        st.write(f"- Total de pontos: **{len(dados_chip_completos):,}**")
        
        # Colunas disponíveis
        colunas_dados = [col for col in dados_chip_completos.columns if not col.startswith('_')]
        st.write(f"- Colunas de dados: **{len(colunas_dados)}**")
    
    st.markdown("---")
    
    # Amostra dos dados
    with st.expander("👀 Ver Amostra dos Dados Brutos"):
        st.dataframe(dados_chip_completos.head(20), use_container_width=True)
    
    # Download
    st.markdown("### 💾 Download dos Dados")
    csv_data = dados_chip_completos.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV (Chip Atual)",
        data=csv_data,
        file_name=f"{chip}_{experimento}_{pasta}_dados.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    📊 Sistema de Análise de Curvas GFET v2.0 (Estendido) | 
    Suporta múltiplas corridas e análise avançada
    </div>
    """,
    unsafe_allow_html=True
)
