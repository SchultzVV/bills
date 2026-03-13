# 📊 Sistema Estendido de Análise de Curvas GFET

Sistema completo para análise interativa de curvas de transferência de sensores GFET, com suporte a **todas as corridas** e filtros avançados.

## 🚀 Início Rápido

### 1. Instalar dependências (se necessário)

```bash
pip install streamlit pandas numpy matplotlib seaborn
```

### 2. Executar o App Streamlit

**Entre na pasta `chulha` antes de rodar:**
```bash
cd /home/v/Documents/contas/chulha
```

**Opção 1 - App estendido (corridas e filtros avançados):**
```bash
streamlit run streamlit_app_extended.py
```

**Opção 2 - App novo com aba de Tabelão:**
```bash
streamlit run streamlit_app_plots.py
```

> Se quiser escolher outra porta: `streamlit run streamlit_app_plots.py --server.port 8502`

**Opção A - Usando o script:**
```bash
./run_streamlit.sh
```

**Opção B - Comando direto (versão estendida):**
```bash
streamlit run streamlit_app_extended.py
```

O app será aberto automaticamente em: **http://localhost:8501**

## 📋 Estrutura do Projeto

```
chulha/
├── dataprep_extended.py          # Sistema de extração de dados (todas as corridas)
├── streamlit_app_extended.py     # App Streamlit interativo
├── run_streamlit.sh              # Script para executar o app
├── run.ipynb                     # Notebook de testes e exemplos
├── data/
│   ├── bronze/GFETS/            # Dados brutos (múltiplas corridas)
│   │   ├── 19abr/
│   │   ├── 03abr/
│   │   └── ...
│   └── gold/                    # Dados consolidados
└── README_STREAMLIT.md          # Este arquivo
```

## 🎯 Funcionalidades do App

### 1. 📈 Comparar Etapas
- Compare diferentes etapas de um chip
- Selecione múltiplas etapas (ex: BARE, DDT, 1ato, 1fento)
- Escolha qual device plotar (dev1-dev20)
- Alterne entre escala linear/logarítmica

**Exemplo de uso:**
- Chip: C1
- Etapas: 1ato, 1fento, 1pico
- Device: dev1
- Resultado: Gráfico comparando as 3 etapas

### 2. 🔄 Comparar Corridas
**Esta é a funcionalidade principal solicitada!**

- Selecione uma etapa (ex: 1ato)
- Escolha múltiplas corridas para comparar
- Veja análise de reprodutibilidade automática
- Coeficiente de variação (CV) entre corridas

**Exemplo de uso:**
- Chip: C1
- Etapa: 1ato
- Corridas: 0, 5, 10, 15, 18
- Resultado: Gráfico com 5 curvas + análise de CV

### 3. 📊 Visualização Custom
- Controle total sobre eixos X e Y
- Escolha qualquer coluna de dados
- 3 modos de seleção:
  - Etapas específicas
  - Todas as etapas
  - Corridas específicas
- Opção de mostrar pontos

### 4. ℹ️ Info dos Dados
- Estatísticas gerais
- Número de corridas por etapa
- Download dos dados em CSV
- Visualização de dados brutos

## 💡 Exemplos de Casos de Uso

### Caso 1: Comparar reprodutibilidade de corridas
```
1. Abrir app
2. Selecionar: Experimento=19abr, Chip=C1
3. Ir para aba "Comparar Corridas"
4. Escolher etapa: 1ato
5. Selecionar corridas: 0, 5, 10, 15, 18
6. Clicar em "Gerar Gráfico"
7. Ver CV médio e gráfico de comparação
```

### Caso 2: Comparar diferentes concentrações
```
1. Selecionar: Experimento=19abr, Chip=C1
2. Ir para aba "Comparar Etapas"
3. Selecionar etapas: 1ato, 1fento, 1pico, 100fento
4. Device: dev1
5. Gerar gráfico de comparação
```

### Caso 3: Análise custom
```
1. Ir para aba "Visualização Custom"
2. Definir: X=Variable Source, Y=dev3
3. Modo: "Todas as etapas"
4. Ativar escala log
5. Gerar visualização completa
```

## 🔧 Sistema de Preparação de Dados

### Novidades do `dataprep_extended.py`:

✅ **Extrai TODAS as corridas** (não apenas a última)
✅ **Detecta automaticamente** blocos de sweeps
✅ **Metadados completos**: experimento, pasta, chip, etapa, corrida, timestamp
✅ **DataFrame consolidado** com todos os dados
✅ **Filtros fáceis** por qualquer combinação

### Estrutura do DataFrame Consolidado:

**Colunas de dados:**
- `Variable Source`: Voltagem
- `dev1`, `dev2`, ..., `dev20`: Correntes dos devices

**Colunas de metadados:**
- `_data_experimento`: ex: "19abr", "03abr"
- `_pasta_dados`: ex: "19abr_curves"
- `_chip`: ex: "C1", "C2", "C3"
- `_etapa`: ex: "1ato", "BARE", "DDT"
- `_sweep_idx`: índice da corrida (0, 1, 2, ...)
- `_timestamp`: timestamp da medição
- `_arquivo`: nome do arquivo original
- `_caminho_relativo`: caminho completo

## 📊 Formato dos Dados

### Dados Bronze (Raw)
```
data/bronze/GFETS/19abr/19abr_curves/C1 - 1ato.csv
```

Cada arquivo contém **múltiplas corridas** separadas por timestamps.

### Dados Consolidados
```python
# Criar DataFrame consolidado
from dataprep_extended import create_consolidated_dataframe

df = create_consolidated_dataframe("data/bronze/GFETS")
# Resultado: DataFrame com TODAS as corridas de TODOS os arquivos
```

## 🎨 Customização

### Modificar cores:
Edite `streamlit_app_extended.py`, função `plot_curvas_comparacao`:
```python
cores = sns.color_palette('seu_palette', n_cores)
```

### Adicionar novos filtros:
No sidebar, adicione novos seletores:
```python
novo_filtro = st.sidebar.selectbox("Filtro:", opcoes)
```

### Modificar resolução dos gráficos:
```python
fig, ax = plt.subplots(figsize=(largura, altura))
```

## 🐛 Troubleshooting

### Problema: "ImportError: pyarrow"
**Solução:** Não é necessário. O sistema salva em CSV automaticamente.
```bash
# Opcional: para formato Parquet
pip install pyarrow
```

### Problema: "Nenhum dado encontrado"
**Solução:** Verifique:
1. Pasta `data/bronze/GFETS/` existe?
2. Há arquivos CSV dentro?
3. Execute o notebook `run.ipynb` para verificar

### Problema: "Gráficos vazios"
**Solução:** O sistema converte vírgulas decimais automaticamente. Se ainda assim vazio:
1. Verifique formato dos CSVs
2. Teste com célula de debug no notebook

## 📈 Performance

- **Primeira execução**: ~10-30s (carrega todos os dados)
- **Depois**: Instantâneo (usa cache do Streamlit)
- **114 arquivos CSV** processados automaticamente
- **~250k+ linhas** de dados consolidados

## 🔐 Controle de Versão

### Arquivos importantes:
- ✅ `dataprep_extended.py`: Sistema principal
- ✅ `streamlit_app_extended.py`: Interface
- ✅ `run.ipynb`: Testes e exemplos
- ❌ `data/gold/*.csv`: Não commitar (muito grande)
- ❌ `data/gold/*.parquet`: Não commitar

## 📝 Changelog

### v2.0 (Atual)
- ✅ Extração de todas as corridas
- ✅ App Streamlit interativo
- ✅ Comparação de corridas
- ✅ Análise de reprodutibilidade
- ✅ Filtros avançados

### v1.0 (Anterior)
- ❌ Apenas última corrida
- ❌ Sem interface interativa

## 🤝 Contribuindo

Para adicionar novas funcionalidades:
1. Modifique `dataprep_extended.py` para novos filtros
2. Adicione nova aba no `streamlit_app_extended.py`
3. Teste no `run.ipynb`
4. Documente aqui

## 📧 Suporte

Em caso de dúvidas ou problemas:
1. Verifique o notebook `run.ipynb` - tem células de debug
2. Execute célula 6.6 (DEBUG) para inspecionar dados
3. Verifique console do Streamlit para erros

## 🎉 Pronto para Usar!

Execute agora:
```bash
./run_streamlit.sh
```

E comece a explorar seus dados de forma interativa! 🚀
