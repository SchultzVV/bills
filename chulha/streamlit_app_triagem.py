"""
TRIAGEM INTERATIVA DE DEVICES - GFET
Página para seleção progressiva com múltiplas datas/chips
Grid de devices com sobreposição de datas
Gera super-gráfico consolidado com todas as seleções
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from dataprep import DataLoader
from plot_utils import PlotterGFET

# ==================== CONFIGURAÇÃO PÁGINA ====================
st.set_page_config(
    page_title="🔍 Triagem GFET - Seleção Multi-Data",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .stButton>button { width: 100%; }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .stats-box {
        background-color: #f0f2f6;
        padding: 12px;
        border-radius: 8px;
        margin: 5px 0;
    }
    .device-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== INICIALIZAR SESSION STATE ====================
if 'selecoes_multi' not in st.session_state:
    st.session_state.selecoes_multi = {}  # {chave_unica: {devices_selecionados, dados_associados}}

if 'dados_consolidados' not in st.session_state:
    st.session_state.dados_consolidados = {}

# ==================== FUNÇÕES AUXILIARES ====================

@st.cache_data
def listar_datas_disponiveis():
    """Lista todas as datas/experimentos em data/silver"""
    base_path = "data/silver"
    if not os.path.exists(base_path):
        return []
    datas = [d for d in os.listdir(base_path) 
             if os.path.isdir(os.path.join(base_path, d)) and not d.startswith('.')]
    return sorted(datas, reverse=True)


@st.cache_data
def carregar_dados_data(data, chip):
    """Carrega dados de um chip em uma data específica"""
    pasta_dados = os.path.join("data/silver", data)
    loader = DataLoader(pasta_dados)
    return loader.carregar_chip(chip)


def listar_chips_data(data):
    """Lista chips disponíveis em uma data"""
    pasta_dados = os.path.join("data/silver", data)
    if not os.path.exists(pasta_dados):
        return []
    loader = DataLoader(pasta_dados)
    return sorted(loader.listar_chips_disponiveis())


def obter_devices_etapa(dados, etapa):
    """Retorna lista de devices de uma etapa"""
    if etapa not in dados:
        return []
    df = dados[etapa]
    return sorted([col for col in df.columns if col != 'V_G'])


def calcular_stats_device(dados, etapa, device):
    """Calcula estatísticas de um device"""
    if etapa not in dados or device not in dados[etapa].columns:
        return None
    
    df = dados[etapa]
    valores = df[device].dropna()
    
    return {
        'count': len(valores),
        'mean': valores.mean(),
        'std': valores.std(),
        'min': valores.min(),
        'max': valores.max()
    }


def plotar_device_multi_data(dados_dict, etapa, device, ax, cores_datas=None):
    """
    Plota um device com múltiplas datas sobrepostas
    
    Args:
        dados_dict: {data: dados_carregados, ...}
        etapa: etapa para plotar
        device: device para plotar
        ax: eixo matplotlib
        cores_datas: {data: cor, ...}
    
    Returns:
        bool sucesso
    """
    encontrou_algo = False
    
    if cores_datas is None:
        cores_datas = {}
        cores = plt.cm.tab10(np.linspace(0, 1, len(dados_dict)))
        for idx, data in enumerate(sorted(dados_dict.keys())):
            cores_datas[data] = cores[idx]
    
    for data, dados in dados_dict.items():
        if etapa not in dados or device not in dados[etapa].columns:
            continue
        
        df = dados[etapa]
        if 'V_G' not in df.columns:
            continue
        
        cor = cores_datas[data]
        ax.plot(df['V_G'], df[device], linewidth=2, label=data, color=cor, alpha=0.8)
        encontrou_algo = True
    
    if encontrou_algo:
        ax.set_xlabel("V$_{GS}$ (V)")
        ax.set_ylabel("I$_{DS}$ (A)")
        ax.set_title(f"Device {device}", fontweight='bold', fontsize=10)
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc='best')
    
    return encontrou_algo


def calcular_media_devices_multi(dados_dict, etapa, devices_list):
    """Calcula média de múltiplos devices considerando múltiplas datas"""
    media_consolidada = {}
    
    for data, dados in dados_dict.items():
        if etapa not in dados:
            continue
        
        df = dados[etapa].copy()
        devices_validos = [d for d in devices_list if d in df.columns]
        
        if not devices_validos:
            continue
        
        media_df = df[['V_G'] + devices_validos].copy()
        media_df['Media'] = media_df[devices_validos].mean(axis=1)
        media_consolidada[data] = media_df
    
    return media_consolidada


# ==================== TÍTULO PRINCIPAL ====================
st.title("🔍 Triagem Interativa Multi-Data de Devices - GFET")
st.markdown("---")
st.markdown("""
**Fluxo Completo:**
1. **Selecione MÚLTIPLAS DATAS** (checkbox)
2. **Escolha um CHIP** comum às datas
3. **Escolha a ETAPA**
4. Veja o **GRID com todos os DEVICES** (múltiplas datas sobrepostas em cada)
5. **Selecione os devices BOM** (checkboxes)
6. Visualize a **MÉDIA dos selecionados** (com datas separadas)
7. **SUPER-GRÁFICO final** consolidado
""")
st.markdown("---")

# ==================== CARREGAR ESTRUTURA ====================
datas_disponiveis = listar_datas_disponiveis()

if not datas_disponiveis:
    st.error("❌ Nenhuma data encontrada em `data/silver/`")
    st.stop()

# ==================== ETAPA 1: SELECIONAR DATAS ====================
st.subheader("📅 ETAPA 1: Selecione as Datas para Análise")

col_toggle_all, col_space = st.columns([1, 4])
with col_toggle_all:
    selecionar_todas = st.checkbox("Selecionar TODAS", value=False, key="sel_todas")

datas_selecionadas = []
cols_dates = st.columns(4)

for idx, data in enumerate(datas_disponiveis):
    col = cols_dates[idx % 4]
    with col:
        if selecionar_todas:
            selecionada = st.checkbox(data, value=True, key=f"data_check_{data}")
        else:
            selecionada = st.checkbox(data, value=False, key=f"data_check_{data}")
        if selecionada:
            datas_selecionadas.append(data)

if not datas_selecionadas:
    st.warning("⚠️ Selecione pelo menos uma data acima")
    st.stop()

st.success(f"✅ {len(datas_selecionadas)} data(s) selecionada(s): {', '.join(datas_selecionadas)}")
st.markdown("---")

# ==================== ETAPA 2: SELECIONAR CHIP ====================
st.subheader("🔬 ETAPA 2: Selecione o Chip")

# Encontrar chips comuns a todas as datas selecionadas
chips_comuns = None
for data in datas_selecionadas:
    chips_data = set(listar_chips_data(data))
    if chips_comuns is None:
        chips_comuns = chips_data
    else:
        chips_comuns = chips_comuns.intersection(chips_data)

chips_comuns = sorted(list(chips_comuns))

if not chips_comuns:
    st.error("❌ Nenhum chip encontrado em TODAS as datas selecionadas")
    st.stop()

chip_selecionado = st.selectbox(
    "Escolha o Chip:",
    chips_comuns,
    help="Mostram apenas chips presentes em TODAS as datas selecionadas"
)

st.info(f"✅ Chip selecionado: **{chip_selecionado}**")
st.markdown("---")

# ==================== ETAPA 3: SELECIONAR ETAPA ====================
st.subheader("📍 ETAPA 3: Selecione a Etapa")

# Carregar dados de todas as datas
dados_multi_data = {}
try:
    for data in datas_selecionadas:
        dados_multi_data[data] = carregar_dados_data(data, chip_selecionado)
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {e}")
    st.stop()

# Encontrar etapas comuns
etapas_comuns = None
for data, dados in dados_multi_data.items():
    etapas_data = set(dados.keys())
    if etapas_comuns is None:
        etapas_comuns = etapas_data
    else:
        etapas_comuns = etapas_comuns.intersection(etapas_data)

etapas_comuns = sorted(list(etapas_comuns))

if not etapas_comuns:
    st.error("❌ Nenhuma etapa encontrada em TODAS as datas selecionadas")
    st.stop()

etapa_selecionada = st.selectbox(
    "Escolha a Etapa:",
    etapas_comuns,
    help="Mostram apenas etapas presentes em TODAS as datas"
)

st.info(f"✅ Etapa selecionada: **{etapa_selecionada}**")
st.markdown("---")

# ==================== OBTER DEVICES ====================
devices_comuns = None
for data, dados in dados_multi_data.items():
    devices_data = set(obter_devices_etapa(dados, etapa_selecionada))
    if devices_comuns is None:
        devices_comuns = devices_data
    else:
        devices_comuns = devices_comuns.intersection(devices_data)

devices_comuns = sorted(list(devices_comuns))

if not devices_comuns:
    st.error("❌ Nenhum device encontrado")
    st.stop()

# ==================== ESTATÍSTICAS GERAIS ====================
st.subheader("📊 Estatísticas Gerais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='stats-box'>
        <strong>📅 Datas:</strong><br>
        <h2>{len(datas_selecionadas)}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stats-box'>
        <strong>🔬 Chip:</strong><br>
        <h2>{chip_selecionado}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stats-box'>
        <strong>📍 Etapa:</strong><br>
        <h2>{etapa_selecionada.upper()}</h2>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='stats-box'>
        <strong>🎯 Total de Devices:</strong><br>
        <h2>{len(devices_comuns)}</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== ETAPA 4: GRID DE DEVICES COM MÚLTIPLAS DATAS ====================
st.subheader("🎯 ETAPA 4: Grid de Devices (múltiplas datas sobrepostas)")

# Cores para as datas
cores_datas = {}
cores = plt.cm.tab10(np.linspace(0, 1, len(datas_selecionadas)))
for idx, data in enumerate(sorted(datas_selecionadas)):
    cores_datas[data] = cores[idx]

# Criar grid de subplots
ncols = 4
nrows = int(np.ceil(len(devices_comuns) / ncols))

fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4*nrows), facecolor='white')
axes = np.array(axes).flatten()

# Plotar cada device com todas as datas
for idx, device in enumerate(devices_comuns):
    ax = axes[idx]
    plotar_device_multi_data(dados_multi_data, etapa_selecionada, device, ax, cores_datas)

# Remover eixos extras
for j in range(len(devices_comuns), len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
st.pyplot(fig)

st.markdown("---")

# ==================== ETAPA 5: SELEÇÃO DE DEVICES ====================
st.subheader("✅ ETAPA 5: Selecione os Devices BOM")

chave_analise = f"{'-'.join(datas_selecionadas)}_{chip_selecionado}_{etapa_selecionada}"

if chave_analise not in st.session_state.selecoes_multi:
    st.session_state.selecoes_multi[chave_analise] = {'devices': set(), 'chave': chave_analise}

# Checkboxes para seleção em grid
cols_devices = st.columns(5)

for idx, device in enumerate(devices_comuns):
    col = cols_devices[idx % 5]
    with col:
        selecionado = st.checkbox(
            f"✅ {device}",
            value=device in st.session_state.selecoes_multi[chave_analise]['devices'],
            key=f"dev_sel_{chave_analise}_{device}"
        )
        if selecionado:
            st.session_state.selecoes_multi[chave_analise]['devices'].add(device)
        else:
            st.session_state.selecoes_multi[chave_analise]['devices'].discard(device)

devices_selecionados = list(st.session_state.selecoes_multi[chave_analise]['devices'])

if devices_selecionados:
    st.success(f"✅ {len(devices_selecionados)} device(s) selecionado(s)")
else:
    st.info("👈 Selecione devices acima")

st.markdown("---")

# ==================== ETAPA 6: MÉDIA DOS SELECIONADOS ====================
if devices_selecionados:
    st.subheader(f"📊 ETAPA 6: Média dos {len(devices_selecionados)} Devices Selecionados")
    
    media_multi = calcular_media_devices_multi(dados_multi_data, etapa_selecionada, devices_selecionados)
    
    if media_multi:
        # Plotar médias com datas separadas
        fig_media, ax_media = plt.subplots(figsize=(14, 7))
        
        for data in sorted(media_multi.keys()):
            media_df = media_multi[data]
            cor = cores_datas[data]
            ax_media.plot(media_df['V_G'], media_df['Media'], linewidth=3, label=f"Média - {data}", color=cor)
        
        ax_media.set_xlabel("V$_{GS}$ (V)", fontsize=12)
        ax_media.set_ylabel("I$_{DS}$ (A)", fontsize=12)
        ax_media.set_title(f"Média - {chip_selecionado} ({etapa_selecionada.upper()}) | {len(devices_selecionados)} devices | {len(datas_selecionadas)} datas", fontsize=13, fontweight='bold')
        ax_media.set_yscale("log")
        ax_media.grid(True, alpha=0.3)
        ax_media.legend(fontsize=10)
        
        plt.tight_layout()
        st.pyplot(fig_media)
        
        # Armazenar para super-gráfico
        st.session_state.dados_consolidados[chave_analise] = {
            'datas': datas_selecionadas,
            'chip': chip_selecionado,
            'etapa': etapa_selecionada,
            'devices': devices_selecionados,
            'medias': media_multi,
            'cores': cores_datas
        }
        
        st.success("✅ Dados salvos para o super-gráfico!")
    else:
        st.warning("⚠️ Erro ao calcular médias")

st.markdown("---\n")

# ==================== ETAPA 7: SUPER-GRÁFICO FINAL ====================
st.markdown("## 🚀 ETAPA 7: SUPER-GRÁFICO CONSOLIDADO")
st.markdown("""
Clique no botão abaixo para gerar um gráfico com **TODA** a triagem realizada
""")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn1:
    if st.button("📈 Gerar Super-Gráfico", use_container_width=True):
        if st.session_state.dados_consolidados:
            fig_super = plt.figure(figsize=(16, 9))
            
            line_idx = 0
            for chave, info in st.session_state.dados_consolidados.items():
                medias = info['medias']
                cores = info['cores']
                
                for data in sorted(medias.keys()):
                    media_df = medias[data]
                    label = f"{data} - {info['chip']} ({info['etapa'].upper()}) | {len(info['devices'])} dev"
                    cor = cores[data]
                    plt.plot(media_df['V_G'], media_df['Media'], 
                            linewidth=2.5, label=label, color=cor, alpha=0.85)
                    line_idx += 1
            
            plt.xlabel("V$_{GS}$ (V)", fontsize=13)
            plt.ylabel("I$_{DS}$ (A)", fontsize=13)
            plt.title("🎯 SUPER-GRÁFICO - Consolidação de Todas as Triagens", fontsize=15, fontweight='bold')
            plt.yscale("log")
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best', fontsize=9, ncol=2)
            plt.tight_layout()
            
            st.pyplot(fig_super)
            
            st.success(f"✅ Super-gráfico gerado com {line_idx} curvas consolidadas!")
        else:
            st.warning("⚠️ Nenhuma triagem realizada. Complete a análise acima primeiro.")

with col_btn2:
    if st.button("💾 Salvar Seleções (JSON)", use_container_width=True):
        st.info("💾 Função de salvamento será implementada em breve!")

with col_btn3:
    if st.button("🔄 Limpar Tudo", use_container_width=True):
        st.session_state.selecoes_multi = {}
        st.session_state.dados_consolidados = {}
        st.success("✅ Tudo limpo!")
        st.rerun()

# ==================== RESUMO FINAL ====================
st.markdown("---")
st.subheader("📋 Resumo de Triagens Realizadas")

if st.session_state.dados_consolidados:
    st.markdown(f"**Total de triagens:** `{len(st.session_state.dados_consolidados)}`")
    
    with st.expander("Ver detalhes"):
        for chave, info in st.session_state.dados_consolidados.items():
            st.markdown(f"""
            - **{chave}**
              - Datas: {len(info['datas'])}
              - Chip: {info['chip']}
              - Etapa: {info['etapa']}
              - Devices: {len(info['devices'])}
            """)
else:
    st.info("Nenhuma triagem realizada ainda.")
