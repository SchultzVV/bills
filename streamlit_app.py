import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="💰 Controle Financeiro",
    page_icon="💰",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_dados():
    """Carrega dados do JSON"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    metadata = dados['metadata']
    df = pd.DataFrame(dados['contas'])
    
    # Normalizar campos
    if 'status' in df.columns and 'status_code' not in df.columns:
        df['status_code'] = df['status']
    elif 'status_code' not in df.columns:
        df['status_code'] = 'aberto'
    
    return metadata, df


def salvar_dados(dados):
    """Salva dados no JSON"""
    with open('financas_casa.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    st.cache_data.clear()


def calcular_totais(df):
    """Calcula todos os totais"""
    total_mes = df['valor'].sum()
    total_pago = df[df['status_code'] == 'pago']['valor'].sum()
    total_a_pagar = df[df['status_code'].isin(['aberto', 'atrasado'])]['valor'].sum()
    
    total_casa = df[df['categoria'] == 'CASA']['valor'].sum()
    total_v = df[df['categoria'] == 'V']['valor'].sum()
    total_m = df[df['categoria'] == 'M']['valor'].sum()
    
    return {
        'total_mes': total_mes,
        'total_pago': total_pago,
        'total_a_pagar': total_a_pagar,
        'total_casa': total_casa,
        'total_v': total_v,
        'total_m': total_m
    }


def marcar_como_pago(nome_conta):
    """Marca uma conta como paga"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    encontrado = False
    for conta in dados['contas']:
        if conta['nome'].lower() == nome_conta.lower():
            conta['status_code'] = 'pago'
            if 'status' in conta:
                conta['status'] = 'pago'
            encontrado = True
            break
    
    if encontrado:
        salvar_dados(dados)
        return True
    return False


def atualizar_valor_conta(nome_conta, novo_valor):
    """Atualiza o valor de uma conta"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    encontrado = False
    valor_antigo = 0
    for conta in dados['contas']:
        if conta['nome'].lower() == nome_conta.lower():
            valor_antigo = conta['valor']
            conta['valor'] = float(novo_valor)
            encontrado = True
            break
    
    if encontrado:
        salvar_dados(dados)
        return True, valor_antigo
    return False, 0


def listar_meses_anteriores():
    """Lista todos os arquivos de meses anteriores"""
    import os
    import glob
    
    if not os.path.exists('olds'):
        return []
    
    arquivos = glob.glob('olds/financas_casa *.json')
    meses = []
    
    for arquivo in arquivos:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                metadata = dados.get('metadata', {})
                mes = metadata.get('mes', '?')
                ano = metadata.get('ano', '?')
                nome_arquivo = os.path.basename(arquivo)
                meses.append({
                    'arquivo': arquivo,
                    'nome': nome_arquivo.replace('financas_casa ', '').replace('.json', ''),
                    'mes': mes,
                    'ano': ano,
                    'display': f"{nome_arquivo.replace('financas_casa ', '').replace('.json', '').title()} {ano}"
                })
        except:
            continue
    
    # Ordenar por ano e mês
    meses.sort(key=lambda x: (int(x['ano']), int(x['mes'])), reverse=True)
    return meses


def carregar_mes_anterior(arquivo):
    """Carrega dados de um mês anterior"""
    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    metadata = dados['metadata']
    df = pd.DataFrame(dados['contas'])
    
    if 'status' in df.columns and 'status_code' not in df.columns:
        df['status_code'] = df['status']
    elif 'status_code' not in df.columns:
        df['status_code'] = 'aberto'
    
    return metadata, df


def adicionar_conta(nome, categoria, vencimento, valor, status, parcela_atual=None, total_parcelas=None):
    """Adiciona uma nova conta"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    nova_conta = {
        "categoria": categoria,
        "nome": nome,
        "vencimento": int(vencimento),
        "valor": float(valor),
        "status_code": status
    }
    
    if parcela_atual and total_parcelas:
        nova_conta['parcela_atual'] = int(parcela_atual)
        nova_conta['total_parcelas'] = int(total_parcelas)
    
    dados['contas'].append(nova_conta)
    salvar_dados(dados)
    return True


def remover_conta(nome):
    """Remove uma conta"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    dados['contas'] = [c for c in dados['contas'] if c['nome'] != nome]
    salvar_dados(dados)
    return True


def atualizar_contas_em_lote(df_editado):
    """Atualiza todas as contas de uma vez a partir do DataFrame editado"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    # Reconstruir lista de contas a partir do DataFrame editado
    novas_contas = []
    
    for _, row in df_editado.iterrows():
        conta = {
            "categoria": row['categoria'],
            "nome": row['nome'],
            "vencimento": int(row['vencimento']),
            "valor": float(row['valor']),
            "status_code": row['status_code']
        }
        
        # Adicionar parcelas se existirem
        if 'parcela_atual' in row and pd.notna(row['parcela_atual']):
            conta['parcela_atual'] = int(row['parcela_atual'])
        if 'total_parcelas' in row and pd.notna(row['total_parcelas']):
            conta['total_parcelas'] = int(row['total_parcelas'])
        
        novas_contas.append(conta)
    
    dados['contas'] = novas_contas
    salvar_dados(dados)
    return True


def verificar_mes_atual():
    """Verifica se o mês atual é diferente do mês registrado"""
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    mes_registro = int(dados['metadata']['mes'])
    ano_registro = int(dados['metadata']['ano'])
    
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    return mes_atual != mes_registro or ano_atual != ano_registro


def obter_nome_mes(numero_mes):
    """Retorna o nome do mês em português"""
    meses = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    return meses.get(int(numero_mes), "desconhecido")


def fechar_mes_e_avancar():
    """Fecha o mês atual e cria o próximo com contas resetadas"""
    # Carregar dados atuais
    with open('financas_casa.json', 'r', encoding='utf-8') as f:
        dados_atuais = json.load(f)
    
    # Fazer backup do mês anterior com nome por extenso
    mes_anterior = int(dados_atuais['metadata']['mes'])
    ano_anterior = dados_atuais['metadata']['ano']
    nome_mes = obter_nome_mes(mes_anterior)
    backup_filename = f"olds/financas_casa {nome_mes}.json"
    
    import os
    os.makedirs('olds', exist_ok=True)
    
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(dados_atuais, f, ensure_ascii=False, indent=2)
    
    # Calcular próximo mês
    mes_atual = int(dados_atuais['metadata']['mes'])
    ano_atual = int(dados_atuais['metadata']['ano'])
    
    if mes_atual == 12:
        proximo_mes = 1
        proximo_ano = ano_atual + 1
    else:
        proximo_mes = mes_atual + 1
        proximo_ano = ano_atual
    
    # Carregar template ou usar contas CASA
    try:
        with open('template_contas.json', 'r', encoding='utf-8') as f:
            template = json.load(f)
        contas_template = template['contas_fixas']
    except FileNotFoundError:
        # Usar contas CASA do mês atual como template
        contas_template = [c for c in dados_atuais['contas'] if c['categoria'] == 'CASA']
    
    # Criar novo mês
    novo_json = {
        "metadata": {
            "mes": str(proximo_mes),
            "ano": str(proximo_ano),
            "descricao": "Controle financeiro da casa"
        },
        "contas": []
    }
    
    # Adicionar contas do template resetadas
    for conta in contas_template:
        nova_conta = {
            "categoria": conta["categoria"],
            "nome": conta["nome"],
            "vencimento": conta["vencimento"],
            "valor": conta.get("valor", 0.0),
            "status_code": "aberto"
        }
        # Manter parcelas se existir e avançar
        if 'parcela_atual' in conta and 'total_parcelas' in conta:
            if conta['parcela_atual'] < conta['total_parcelas']:
                nova_conta['parcela_atual'] = conta['parcela_atual'] + 1
                nova_conta['total_parcelas'] = conta['total_parcelas']
        
        novo_json["contas"].append(nova_conta)
    
    # Salvar novo mês
    salvar_dados(novo_json)
    
    return backup_filename, proximo_mes, proximo_ano


def main():
    # Header
    st.title("💰 Controle Financeiro da Casa")
    
    # Carregar dados
    metadata, df = carregar_dados()
    totais = calcular_totais(df)
    
    # Sidebar
    st.sidebar.title("📋 Menu")
    st.sidebar.markdown(f"**Mês:** {metadata['mes']}/{metadata['ano']}")
    st.sidebar.markdown(f"**Total de contas:** {len(df)}")
    
    # Verificar se o mês mudou
    mes_desatualizado = verificar_mes_atual()
    if mes_desatualizado:
        st.sidebar.warning("⚠️ Mês desatualizado! Feche o mês atual.")
    
    menu = st.sidebar.radio(
        "Navegação",
        ["📊 Dashboard", "📈 Análises", "📋 Tabelas", "🔧 Gerenciar", "📅 Fechar Mês", "� Meses Anteriores", "�📤 Exportar"]
    )
    
    # ==================== DASHBOARD ====================
    if menu == "📊 Dashboard":
        st.header(f"📊 Resumo Financeiro - {metadata['mes']}/{metadata['ano']}")
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="💰 Total do Mês",
                value=f"R$ {totais['total_mes']:,.2f}",
                delta=None
            )
        
        with col2:
            percentual_pago = (totais['total_pago']/totais['total_mes']*100) if totais['total_mes'] > 0 else 0
            st.metric(
                label="✅ Total Pago",
                value=f"R$ {totais['total_pago']:,.2f}",
                delta=f"{percentual_pago:.1f}%"
            )
        
        with col3:
            percentual_aberto = (totais['total_a_pagar']/totais['total_mes']*100) if totais['total_mes'] > 0 else 0
            st.metric(
                label="⏰ Total a Pagar",
                value=f"R$ {totais['total_a_pagar']:,.2f}",
                delta=f"{percentual_aberto:.1f}%",
                delta_color="inverse"
            )
        
        st.markdown("---")
        
        # Totais por categoria
        st.subheader("🏷️ Totais por Categoria")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🏠 CASA",
                value=f"R$ {totais['total_casa']:,.2f}",
                delta=f"{(totais['total_casa']/totais['total_mes']*100):.1f}%"
            )
        
        with col2:
            st.metric(
                label="👤 V",
                value=f"R$ {totais['total_v']:,.2f}",
                delta=f"{(totais['total_v']/totais['total_mes']*100):.1f}%"
            )
        
        with col3:
            st.metric(
                label="👤 M",
                value=f"R$ {totais['total_m']:,.2f}",
                delta=f"{(totais['total_m']/totais['total_mes']*100):.1f}%"
            )
        
        st.markdown("---")
        
        # Gráficos rápidos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Distribuição por Status")
            status_totais = df.groupby('status_code')['valor'].sum()
            cores_status = {'pago': '#4CAF50', 'aberto': '#FFC107', 'atrasado': '#F44336'}
            cores = [cores_status.get(s, '#9E9E9E') for s in status_totais.index]
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(status_totais.values, labels=status_totais.index.str.upper(), 
                   autopct='%1.1f%%', startangle=90, colors=cores, textprops={'size': 12})
            ax.set_title('Distribuição por Status (Valor)', fontsize=14, fontweight='bold')
            st.pyplot(fig)
        
        with col2:
            st.subheader("🏷️ Distribuição por Categoria")
            categoria_totais = df.groupby('categoria')['valor'].sum()
            cores_cat = {'CASA': '#2196F3', 'V': '#9C27B0', 'M': '#FF9800'}
            cores = [cores_cat.get(c, '#9E9E9E') for c in categoria_totais.index]
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(categoria_totais.values, labels=categoria_totais.index, 
                   autopct='%1.1f%%', startangle=90, colors=cores, textprops={'size': 12})
            ax.set_title('Distribuição por Categoria (Valor)', fontsize=14, fontweight='bold')
            st.pyplot(fig)
        
        # Contas em aberto - Destaque
        st.markdown("---")
        st.subheader("⚠️ Contas em Aberto")
        df_aberto = df[df['status_code'] == 'aberto'].copy()
        
        if len(df_aberto) > 0:
            df_aberto_display = df_aberto[['nome', 'categoria', 'vencimento', 'valor']].sort_values('vencimento')
            df_aberto_display['valor'] = df_aberto_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
            df_aberto_display.columns = ['Nome', 'Categoria', 'Vencimento', 'Valor']
            
            st.dataframe(df_aberto_display, use_container_width=True, hide_index=True)
            st.info(f"💡 Total em aberto: **R$ {df_aberto['valor'].sum():,.2f}**")
        else:
            st.success("✅ Nenhuma conta em aberto!")
    
    # ==================== ANÁLISES ====================
    elif menu == "📈 Análises":
        st.header("📈 Análises Detalhadas")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "🏷️ Categorias", "🏆 Top 10", "📅 Vencimentos"])
        
        # Tab 1: Distribuição por Status
        with tab1:
            st.subheader("Distribuição por Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Valor por Status")
                status_totais = df.groupby('status_code')['valor'].sum()
                cores_status = {'pago': '#4CAF50', 'aberto': '#FFC107', 'atrasado': '#F44336'}
                cores = [cores_status.get(s, '#9E9E9E') for s in status_totais.index]
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(status_totais.values, labels=status_totais.index.str.upper(), 
                       autopct='%1.1f%%', startangle=90, colors=cores, textprops={'size': 11})
                ax.set_title('Distribuição por Status (Valor)', fontsize=14, fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.markdown("#### Quantidade por Status")
                status_count = df['status_code'].value_counts()
                cores_count = [cores_status.get(s, '#9E9E9E') for s in status_count.index]
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(status_count.index.str.upper(), status_count.values, color=cores_count)
                ax.set_title('Quantidade de Contas por Status', fontsize=14, fontweight='bold')
                ax.set_ylabel('Quantidade')
                ax.grid(axis='y', alpha=0.3)
                st.pyplot(fig)
        
        # Tab 2: Distribuição por Categoria
        with tab2:
            st.subheader("Distribuição por Categoria")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Valor por Categoria")
                categoria_totais = df.groupby('categoria')['valor'].sum()
                cores_cat = {'CASA': '#2196F3', 'V': '#9C27B0', 'M': '#FF9800'}
                cores = [cores_cat.get(c, '#9E9E9E') for c in categoria_totais.index]
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(categoria_totais.values, labels=categoria_totais.index, 
                       autopct='%1.1f%%', startangle=90, colors=cores, textprops={'size': 11})
                ax.set_title('Distribuição por Categoria (Valor)', fontsize=14, fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.markdown("#### Total por Categoria (R$)")
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(categoria_totais.index, categoria_totais.values, color=cores)
                ax.set_title('Total por Categoria (R$)', fontsize=14, fontweight='bold')
                ax.set_ylabel('Valor (R$)')
                ax.grid(axis='y', alpha=0.3)
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
                st.pyplot(fig)
        
        # Tab 3: Top 10 Maiores Contas
        with tab3:
            st.subheader("🏆 Top 10 Maiores Contas")
            
            top10 = df.nlargest(10, 'valor')[['nome', 'valor', 'categoria', 'status_code']].copy()
            
            cores_status = {'pago': '#4CAF50', 'aberto': '#FFC107', 'atrasado': '#F44336'}
            cores_top = [cores_status.get(s, '#9E9E9E') for s in top10['status_code']]
            
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.barh(range(len(top10)), top10['valor'], color=cores_top)
            ax.set_yticks(range(len(top10)))
            ax.set_yticklabels([f"{row['nome']} ({row['categoria']})" for _, row in top10.iterrows()])
            ax.set_xlabel('Valor (R$)', fontsize=12)
            ax.set_title('Top 10 Maiores Contas', fontsize=14, fontweight='bold')
            ax.invert_yaxis()
            ax.grid(axis='x', alpha=0.3)
            
            for i, v in enumerate(top10['valor']):
                ax.text(v + 50, i, f'R$ {v:,.2f}', va='center', fontsize=10)
            
            st.pyplot(fig)
        
        # Tab 4: Calendário de Vencimentos
        with tab4:
            st.subheader("📅 Calendário de Vencimentos")
            
            df_venc = df.copy()
            df_venc['dia'] = df_venc['vencimento']
            vencimentos = df_venc.groupby('dia').agg({
                'valor': 'sum',
                'nome': 'count'
            }).rename(columns={'nome': 'quantidade'}).reset_index()
            
            col1, col2 = st.columns(1)
            
            with col1:
                st.markdown("#### Valor por Dia de Vencimento")
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.bar(vencimentos['dia'], vencimentos['valor'], color='#2196F3', alpha=0.7)
                ax.set_title('Valor Total por Dia de Vencimento', fontsize=14, fontweight='bold')
                ax.set_xlabel('Dia do Mês')
                ax.set_ylabel('Valor (R$)')
                ax.grid(axis='y', alpha=0.3)
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
                st.pyplot(fig)
                
                st.markdown("#### Quantidade por Dia de Vencimento")
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.bar(vencimentos['dia'], vencimentos['quantidade'], color='#FF9800', alpha=0.7)
                ax.set_title('Quantidade de Contas por Dia de Vencimento', fontsize=14, fontweight='bold')
                ax.set_xlabel('Dia do Mês')
                ax.set_ylabel('Quantidade')
                ax.grid(axis='y', alpha=0.3)
                st.pyplot(fig)
    
    # ==================== TABELAS ====================
    elif menu == "📋 Tabelas":
        st.header("📋 Tabelas Detalhadas")
        
        tab1, tab2, tab3 = st.tabs(["📑 Todas as Contas", "⏰ Contas em Aberto", "📊 Resumo por Categoria"])
        
        # Tab 1: Todas as Contas
        with tab1:
            st.subheader("Todas as Contas (Ordenadas por Vencimento)")
            
            df_display = df.copy()
            
            # Adicionar informação de parcelas
            if 'parcela_atual' in df_display.columns and 'total_parcelas' in df_display.columns:
                df_display['parcelas'] = df_display.apply(
                    lambda x: f"{int(x['parcela_atual'])}/{int(x['total_parcelas'])}" 
                    if pd.notna(x['parcela_atual']) and pd.notna(x['total_parcelas']) 
                    else '-', 
                    axis=1
                )
            else:
                df_display['parcelas'] = '-'
            
            df_display['valor_fmt'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            colunas_exibir = ['vencimento', 'nome', 'categoria', 'valor_fmt', 'parcelas', 'status_code']
            df_show = df_display[colunas_exibir].sort_values('vencimento')
            df_show.columns = ['Venc.', 'Nome', 'Cat.', 'Valor', 'Parcelas', 'Status']
            
            # Aplicar cores por status
            def colorir_linha(row):
                cores = {
                    'pago': 'background-color: #C8E6C9',
                    'aberto': 'background-color: #FFF9C4',
                    'atrasado': 'background-color: #FFCDD2'
                }
                cor = cores.get(row['Status'], '')
                return [cor] * len(row)
            
            st.dataframe(
                df_show.style.apply(colorir_linha, axis=1),
                use_container_width=True,
                height=600
            )
        
        # Tab 2: Contas em Aberto
        with tab2:
            st.subheader("⏰ Contas em Aberto")
            
            df_aberto = df[df['status_code'] == 'aberto'].copy()
            
            if len(df_aberto) > 0:
                df_aberto['valor_fmt'] = df_aberto['valor'].apply(lambda x: f"R$ {x:,.2f}")
                
                if 'parcela_atual' in df_aberto.columns:
                    df_aberto['parcelas'] = df_aberto.apply(
                        lambda x: f"{int(x['parcela_atual'])}/{int(x['total_parcelas'])}" 
                        if pd.notna(x.get('parcela_atual')) and pd.notna(x.get('total_parcelas')) 
                        else '-', 
                        axis=1
                    )
                else:
                    df_aberto['parcelas'] = '-'
                
                colunas = ['vencimento', 'nome', 'categoria', 'valor_fmt', 'parcelas']
                df_show = df_aberto[colunas].sort_values('vencimento')
                df_show.columns = ['Venc.', 'Nome', 'Cat.', 'Valor', 'Parcelas']
                
                st.info(f"⏰ **Total em aberto:** R$ {df_aberto['valor'].sum():,.2f}")
                st.dataframe(df_show, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhuma conta em aberto!")
        
        # Tab 3: Resumo por Categoria
        with tab3:
            st.subheader("📊 Resumo por Categoria e Status")
            
            resumo_cat = df.groupby(['categoria', 'status_code'])['valor'].sum().unstack(fill_value=0)
            resumo_cat['TOTAL'] = resumo_cat.sum(axis=1)
            resumo_cat.loc['TOTAL'] = resumo_cat.sum()
            
            # Formatar valores
            resumo_cat_fmt = resumo_cat.applymap(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(resumo_cat_fmt, use_container_width=True)
    
    # ==================== GERENCIAR ====================
    elif menu == "🔧 Gerenciar":
        st.header("🔧 Gerenciar Contas")
        
        tab1, tab2, tab3, tab4 = st.tabs(["✏️ Editar Tabela", "✅ Marcar como Pago", "💵 Atualizar Valor", "🔍 Buscar Conta"])
        
        # Tab 1: Editar Tabela Completa
        with tab1:
            st.subheader("✏️ Edição Avançada de Contas")
            st.write("Edite diretamente os valores na tabela abaixo. As alterações são salvas ao clicar em 'Salvar Alterações'.")
            
            # Preparar DataFrame para edição
            df_edit = df.copy()
            
            # Garantir que todas as colunas necessárias existam
            if 'parcela_atual' not in df_edit.columns:
                df_edit['parcela_atual'] = None
            if 'total_parcelas' not in df_edit.columns:
                df_edit['total_parcelas'] = None
            
            # Ordenar colunas para melhor visualização
            colunas_ordem = ['nome', 'categoria', 'vencimento', 'valor', 'status_code', 'parcela_atual', 'total_parcelas']
            colunas_existentes = [c for c in colunas_ordem if c in df_edit.columns]
            df_edit = df_edit[colunas_existentes]
            
            # Configurar editor de dados
            st.info("💡 Dica: Clique duas vezes em uma célula para editá-la.")
            
            df_editado = st.data_editor(
                df_edit,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "nome": st.column_config.TextColumn("Nome", required=True, max_chars=100),
                    "categoria": st.column_config.SelectboxColumn(
                        "Categoria",
                        options=["CASA", "V", "M"],
                        required=True
                    ),
                    "vencimento": st.column_config.NumberColumn(
                        "Vencimento",
                        min_value=1,
                        max_value=31,
                        step=1,
                        format="%d",
                        required=True
                    ),
                    "valor": st.column_config.NumberColumn(
                        "Valor (R$)",
                        min_value=0.0,
                        step=0.01,
                        format="R$ %.2f",
                        required=True
                    ),
                    "status_code": st.column_config.SelectboxColumn(
                        "Status",
                        options=["pago", "aberto", "atrasado"],
                        required=True
                    ),
                    "parcela_atual": st.column_config.NumberColumn(
                        "Parcela Atual",
                        min_value=0,
                        step=1,
                        format="%d"
                    ),
                    "total_parcelas": st.column_config.NumberColumn(
                        "Total Parcelas",
                        min_value=0,
                        step=1,
                        format="%d"
                    ),
                },
                hide_index=True,
                key="editor_contas"
            )
            
            # Botões de ação
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    try:
                        atualizar_contas_em_lote(df_editado)
                        st.success("✅ Todas as alterações foram salvas!")
                        st.balloons()
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {str(e)}")
            
            with col2:
                if st.button("🔄 Recarregar", use_container_width=True):
                    st.rerun()
            
            with col3:
                st.metric("Total de Contas", len(df_editado))
            
            st.markdown("---")
            
            # Seção: Adicionar Nova Conta
            st.subheader("➕ Adicionar Nova Conta")
            
            with st.form("form_adicionar_conta", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    novo_nome = st.text_input("Nome da Conta*", placeholder="Ex: Cartão de Crédito")
                    nova_categoria = st.selectbox("Categoria*", ["CASA", "V", "M"])
                
                with col2:
                    novo_vencimento = st.number_input("Vencimento (dia)*", min_value=1, max_value=31, value=10, step=1)
                    novo_valor = st.number_input("Valor (R$)*", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                
                with col3:
                    novo_status = st.selectbox("Status*", ["aberto", "pago", "atrasado"], index=0)
                    tem_parcelas = st.checkbox("Tem parcelas?")
                
                if tem_parcelas:
                    col1, col2 = st.columns(2)
                    with col1:
                        nova_parcela_atual = st.number_input("Parcela Atual", min_value=1, value=1, step=1)
                    with col2:
                        nova_total_parcelas = st.number_input("Total de Parcelas", min_value=1, value=1, step=1)
                else:
                    nova_parcela_atual = None
                    nova_total_parcelas = None
                
                submitted = st.form_submit_button("➕ Adicionar Conta", type="primary", use_container_width=True)
                
                if submitted:
                    if not novo_nome:
                        st.error("❌ O nome da conta é obrigatório!")
                    else:
                        try:
                            adicionar_conta(
                                novo_nome, nova_categoria, novo_vencimento, 
                                novo_valor, novo_status, nova_parcela_atual, nova_total_parcelas
                            )
                            st.success(f"✅ Conta '{novo_nome}' adicionada com sucesso!")
                            import time
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao adicionar conta: {str(e)}")
            
            st.markdown("---")
            
            # Seção: Remover Conta
            st.subheader("🗑️ Remover Conta")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                conta_remover = st.selectbox(
                    "Selecione a conta para remover:",
                    df['nome'].tolist(),
                    key="remover_conta"
                )
            
            with col2:
                st.write("")
                st.write("")
                if st.button("🗑️ Remover", type="secondary", use_container_width=True):
                    if st.session_state.get('confirmar_remocao') == conta_remover:
                        try:
                            remover_conta(conta_remover)
                            st.success(f"✅ Conta '{conta_remover}' removida!")
                            if 'confirmar_remocao' in st.session_state:
                                del st.session_state['confirmar_remocao']
                            import time
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao remover: {str(e)}")
                    else:
                        st.session_state['confirmar_remocao'] = conta_remover
                        st.warning("⚠️ Clique novamente para confirmar a remoção.")
        
        # Tab 2: Marcar como Pago
        with tab2:
            st.subheader("✅ Marcar Conta como Paga")
            
            contas_nao_pagas = df[df['status_code'] != 'pago']['nome'].tolist()
            
            if contas_nao_pagas:
                conta_selecionada = st.selectbox(
                    "Selecione a conta:",
                    contas_nao_pagas,
                    key="marcar_pago"
                )
                
                # Mostrar informações da conta
                info_conta = df[df['nome'] == conta_selecionada].iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Valor", f"R$ {info_conta['valor']:,.2f}")
                with col2:
                    st.metric("Vencimento", info_conta['vencimento'])
                with col3:
                    st.metric("Categoria", info_conta['categoria'])
                
                if st.button("✅ Marcar como PAGA", type="primary"):
                    if marcar_como_pago(conta_selecionada):
                        st.success(f"✅ Conta '{conta_selecionada}' marcada como PAGA!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao marcar conta como paga.")
            else:
                st.info("🎉 Todas as contas já estão pagas!")
        
        # Tab 3: Atualizar Valor
        with tab3:
            st.subheader("💵 Atualizar Valor de Conta")
            
            conta_atualizar = st.selectbox(
                "Selecione a conta:",
                df['nome'].tolist(),
                key="atualizar_valor"
            )
            
            info_conta = df[df['nome'] == conta_atualizar].iloc[0]
            st.info(f"Valor atual: **R$ {info_conta['valor']:,.2f}**")
            
            novo_valor = st.number_input(
                "Novo valor:",
                min_value=0.0,
                value=float(info_conta['valor']),
                step=0.01,
                format="%.2f"
            )
            
            if st.button("💾 Atualizar Valor", type="primary"):
                sucesso, valor_antigo = atualizar_valor_conta(conta_atualizar, novo_valor)
                if sucesso:
                    st.success(f"✅ Conta '{conta_atualizar}' atualizada!")
                    st.info(f"Valor antigo: R$ {valor_antigo:,.2f} → Valor novo: R$ {novo_valor:,.2f}")
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar valor.")
        
        # Tab 4: Buscar Conta
        with tab4:
            st.subheader("🔍 Buscar Conta")
            
            termo_busca = st.text_input("Digite o nome da conta:", key="buscar")
            
            if termo_busca:
                resultados = df[df['nome'].str.contains(termo_busca, case=False, na=False)].copy()
                
                if len(resultados) > 0:
                    resultados['valor_fmt'] = resultados['valor'].apply(lambda x: f"R$ {x:,.2f}")
                    
                    colunas = ['nome', 'categoria', 'vencimento', 'valor_fmt', 'status_code']
                    df_show = resultados[colunas]
                    df_show.columns = ['Nome', 'Cat.', 'Venc.', 'Valor', 'Status']
                    
                    st.success(f"🔍 Encontradas {len(resultados)} conta(s):")
                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"❌ Nenhuma conta encontrada com '{termo_busca}'")
    
    # ==================== FECHAR MÊS ====================
    elif menu == "📅 Fechar Mês":
        st.header("📅 Fechar Mês e Avançar")
        
        # Informações do mês atual
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📆 Mês Atual")
            st.info(f"**{metadata['mes']}/{metadata['ano']}**")
            
            hoje = datetime.now()
            st.write(f"Data atual: **{hoje.strftime('%d/%m/%Y')}**")
            
            if verificar_mes_atual():
                st.warning("⚠️ O mês registrado está desatualizado!")
                st.write("O sistema está em um mês anterior ao mês atual.")
        
        with col2:
            st.subheader("📊 Resumo")
            st.metric("Total de Contas", len(df))
            st.metric("Contas Pagas", len(df[df['status_code'] == 'pago']))
            st.metric("Contas em Aberto", len(df[df['status_code'] == 'aberto']))
        
        st.markdown("---")
        
        # Resumo financeiro final
        st.subheader("💰 Resumo Financeiro do Mês")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total do Mês", f"R$ {totais['total_mes']:,.2f}")
        with col2:
            st.metric("Total Pago", f"R$ {totais['total_pago']:,.2f}")
        with col3:
            st.metric("Total em Aberto", f"R$ {totais['total_a_pagar']:,.2f}")
        
        # Avisos
        if totais['total_a_pagar'] > 0:
            st.warning(f"⚠️ Ainda existem **R$ {totais['total_a_pagar']:,.2f}** em contas abertas!")
            
            df_pendentes = df[df['status_code'] != 'pago'][['nome', 'categoria', 'valor', 'status_code']].copy()
            df_pendentes['valor'] = df_pendentes['valor'].apply(lambda x: f"R$ {x:,.2f}")
            df_pendentes.columns = ['Nome', 'Categoria', 'Valor', 'Status']
            
            with st.expander("Ver contas pendentes"):
                st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todas as contas do mês foram pagas!")
        
        st.markdown("---")
        
        # Ação de fechar mês
        st.subheader("🔄 Fechar Mês e Criar Próximo")
        
        st.write("""
        **O que acontece ao fechar o mês:**
        1. Um backup do mês atual será salvo em `olds/`
        2. O sistema avançará para o próximo mês
        3. As contas fixas (CASA) serão replicadas
        4. Todas as contas serão marcadas como "aberto"
        5. Parcelas serão avançadas automaticamente
        """)
        
        # Calcular próximo mês
        mes_atual = int(metadata['mes'])
        ano_atual = int(metadata['ano'])
        
        if mes_atual == 12:
            proximo_mes = 1
            proximo_ano = ano_atual + 1
        else:
            proximo_mes = mes_atual + 1
            proximo_ano = ano_atual
        
        st.info(f"📅 Próximo mês: **{proximo_mes}/{proximo_ano}**")
        
        # Confirmação
        col1, col2 = st.columns([3, 1])
        
        with col1:
            confirmar = st.checkbox(
                "Confirmo que desejo fechar o mês atual e avançar para o próximo",
                key="confirmar_fechar"
            )
        
        with col2:
            if confirmar:
                if st.button("🔄 Fechar Mês", type="primary", use_container_width=True):
                    with st.spinner("Fechando mês e criando próximo..."):
                        try:
                            backup_file, novo_mes, novo_ano = fechar_mes_e_avancar()
                            st.success(f"✅ Mês fechado com sucesso!")
                            st.success(f"📁 Backup salvo: {backup_file}")
                            st.success(f"📅 Novo mês criado: {novo_mes}/{novo_ano}")
                            st.balloons()
                            
                            # Esperar 2 segundos e recarregar
                            import time
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao fechar mês: {str(e)}")
            else:
                st.button("🔄 Fechar Mês", type="primary", disabled=True, use_container_width=True)
    
    # ==================== MESES ANTERIORES ====================
    elif menu == "📚 Meses Anteriores":
        st.header("📚 Visualizar Meses Anteriores")
        
        meses_anteriores = listar_meses_anteriores()
        
        if not meses_anteriores:
            st.info("📭 Nenhum mês anterior encontrado.")
            st.write("Os meses fechados aparecerão aqui automaticamente após usar a função 'Fechar Mês'.")
        else:
            st.write(f"**{len(meses_anteriores)} mês(es) encontrado(s)**")
            
            # Seletor de mês
            opcoes_meses = [m['display'] for m in meses_anteriores]
            mes_selecionado_idx = st.selectbox(
                "Selecione o mês:",
                range(len(opcoes_meses)),
                format_func=lambda x: opcoes_meses[x],
                key="mes_anterior"
            )
            
            mes_dados = meses_anteriores[mes_selecionado_idx]
            
            st.markdown("---")
            
            # Carregar dados do mês selecionado
            metadata_ant, df_ant = carregar_mes_anterior(mes_dados['arquivo'])
            totais_ant = calcular_totais(df_ant)
            
            # Header do mês
            st.subheader(f"📅 {mes_dados['nome'].title()} / {mes_dados['ano']}")
            
            # Métricas principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Total do Mês", f"R$ {totais_ant['total_mes']:,.2f}")
            
            with col2:
                percentual_pago = (totais_ant['total_pago']/totais_ant['total_mes']*100) if totais_ant['total_mes'] > 0 else 0
                st.metric("✅ Total Pago", f"R$ {totais_ant['total_pago']:,.2f}", delta=f"{percentual_pago:.1f}%")
            
            with col3:
                percentual_aberto = (totais_ant['total_a_pagar']/totais_ant['total_mes']*100) if totais_ant['total_mes'] > 0 else 0
                st.metric("⏰ Total a Pagar", f"R$ {totais_ant['total_a_pagar']:,.2f}", delta=f"{percentual_aberto:.1f}%")
            
            st.markdown("---")
            
            # Totais por categoria
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🏠 CASA", f"R$ {totais_ant['total_casa']:,.2f}")
            
            with col2:
                st.metric("👤 V", f"R$ {totais_ant['total_v']:,.2f}")
            
            with col3:
                st.metric("👤 M", f"R$ {totais_ant['total_m']:,.2f}")
            
            st.markdown("---")
            
            # Tabs com análises
            tab1, tab2, tab3 = st.tabs(["📋 Todas as Contas", "📊 Gráficos", "📈 Resumo"])
            
            with tab1:
                st.subheader("Todas as Contas")
                
                df_display = df_ant.copy()
                
                # Adicionar informação de parcelas
                if 'parcela_atual' in df_display.columns and 'total_parcelas' in df_display.columns:
                    df_display['parcelas'] = df_display.apply(
                        lambda x: f"{int(x['parcela_atual'])}/{int(x['total_parcelas'])}" 
                        if pd.notna(x['parcela_atual']) and pd.notna(x['total_parcelas']) 
                        else '-', 
                        axis=1
                    )
                else:
                    df_display['parcelas'] = '-'
                
                df_display['valor_fmt'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
                
                colunas_exibir = ['vencimento', 'nome', 'categoria', 'valor_fmt', 'parcelas', 'status_code']
                df_show = df_display[colunas_exibir].sort_values('vencimento')
                df_show.columns = ['Venc.', 'Nome', 'Cat.', 'Valor', 'Parcelas', 'Status']
                
                # Aplicar cores por status
                def colorir_linha(row):
                    cores = {
                        'pago': 'background-color: #C8E6C9',
                        'aberto': 'background-color: #FFF9C4',
                        'atrasado': 'background-color: #FFCDD2'
                    }
                    cor = cores.get(row['Status'], '')
                    return [cor] * len(row)
                
                st.dataframe(
                    df_show.style.apply(colorir_linha, axis=1),
                    use_container_width=True,
                    height=500
                )
            
            with tab2:
                st.subheader("Distribuição")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Por Status")
                    status_totais = df_ant.groupby('status_code')['valor'].sum()
                    cores_status = {'pago': '#4CAF50', 'aberto': '#FFC107', 'atrasado': '#F44336'}
                    cores = [cores_status.get(s, '#9E9E9E') for s in status_totais.index]
                    
                    fig, ax = plt.subplots(figsize=(6, 5))
                    ax.pie(status_totais.values, labels=status_totais.index.str.upper(), 
                           autopct='%1.1f%%', startangle=90, colors=cores)
                    st.pyplot(fig)
                
                with col2:
                    st.markdown("#### Por Categoria")
                    categoria_totais = df_ant.groupby('categoria')['valor'].sum()
                    cores_cat = {'CASA': '#2196F3', 'V': '#9C27B0', 'M': '#FF9800'}
                    cores = [cores_cat.get(c, '#9E9E9E') for c in categoria_totais.index]
                    
                    fig, ax = plt.subplots(figsize=(6, 5))
                    ax.pie(categoria_totais.values, labels=categoria_totais.index, 
                           autopct='%1.1f%%', startangle=90, colors=cores)
                    st.pyplot(fig)
            
            with tab3:
                st.subheader("Resumo por Categoria e Status")
                
                resumo_cat = df_ant.groupby(['categoria', 'status_code'])['valor'].sum().unstack(fill_value=0)
                resumo_cat['TOTAL'] = resumo_cat.sum(axis=1)
                resumo_cat.loc['TOTAL'] = resumo_cat.sum()
                
                resumo_cat_fmt = resumo_cat.applymap(lambda x: f"R$ {x:,.2f}")
                
                st.dataframe(resumo_cat_fmt, use_container_width=True)
            
            # Botão de exportar
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("📥 Exportar CSV", use_container_width=True):
                    nome_arquivo_csv = f"financas_{mes_dados['nome']}_{mes_dados['ano']}.csv"
                    df_ant.to_csv(nome_arquivo_csv, index=False, encoding='utf-8')
                    st.success(f"✅ Exportado: {nome_arquivo_csv}")
            
            with col2:
                # Botão de download
                csv_data = df_ant.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"financas_{mes_dados['nome']}_{mes_dados['ano']}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # ==================== EXPORTAR ====================
    elif menu == "📤 Exportar":
        st.header("📤 Exportar Relatórios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 CSV Detalhado")
            st.write("Exporta todas as contas com informações completas.")
            
            if st.button("📥 Gerar CSV Detalhado", type="primary"):
                df_export = df.copy()
                df_export = df_export.sort_values(['categoria', 'vencimento'])
                df_export.to_csv('financas_casa.csv', index=False, encoding='utf-8')
                st.success("✅ CSV detalhado gerado: financas_casa.csv")
                
                with open('financas_casa.csv', 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="⬇️ Download CSV Detalhado",
                        data=f.read(),
                        file_name='financas_casa.csv',
                        mime='text/csv'
                    )
        
        with col2:
            st.subheader("📊 Resumo Mensal")
            st.write("Exporta resumo com totais do mês.")
            
            if st.button("📥 Gerar Resumo Mensal", type="primary"):
                resumo = {
                    'Mês': f"{metadata['mes']}/{metadata['ano']}",
                    'Total do Mês': f"{totais['total_mes']:.2f}",
                    'Total Pago': f"{totais['total_pago']:.2f}",
                    'Total a Pagar': f"{totais['total_a_pagar']:.2f}",
                    'Total CASA': f"{totais['total_casa']:.2f}",
                    'Total V': f"{totais['total_v']:.2f}",
                    'Total M': f"{totais['total_m']:.2f}"
                }
                
                df_resumo = pd.DataFrame([resumo])
                df_resumo.to_csv('resumo_mensal.csv', index=False, encoding='utf-8')
                
                st.success("✅ Resumo mensal gerado: resumo_mensal.csv")
                st.dataframe(df_resumo, use_container_width=True, hide_index=True)
                
                with open('resumo_mensal.csv', 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="⬇️ Download Resumo Mensal",
                        data=f.read(),
                        file_name='resumo_mensal.csv',
                        mime='text/csv'
                    )
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 Scripts Disponíveis")
    st.sidebar.code("python update.py -i", language="bash")
    st.sidebar.caption("Modo interativo completo")
    st.sidebar.code("python maths_month.py", language="bash")
    st.sidebar.caption("Calcular resumo mensal")
    st.sidebar.code("python reset_month.py", language="bash")
    st.sidebar.caption("Resetar mês")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("💰 Controle Financeiro v1.0")


if __name__ == "__main__":
    main()
