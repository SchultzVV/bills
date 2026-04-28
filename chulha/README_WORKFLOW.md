# 📊 GFET Curves Analysis - Workflow Modular

Sistema modular para análise de curvas de transferência de transistores de grafeno (GFET).

## 📁 Estrutura do Projeto

```
chulha/
├── data/
│   └── GFETS/
│       ├── 19abr/
│       │   ├── raw/          # 📥 Arquivos CSV originais
│       │   └── silver/       # 💎 Arquivos processados
│       ├── 19mar/
│       └── 03abr/
├── resultados/               # 📊 Figuras exportadas
├── dataprep.py              # 🔧 Preparação de dados (Raw → Silver)
├── plot_utils.py            # 📈 Funções de plotagem
├── streamlit_app_plots.py   # 🌐 Interface web
├── exemplo_workflow.ipynb   # 📓 Exemplo de uso
└── General_curves.ipynb     # 📓 Notebook original
```

## 🚀 Componentes

### 1️⃣ dataprep.py - Preparação de Dados

Responsável por processar arquivos CSV brutos e salvá-los na camada silver.

**Classes principais:**
- `DataPreparation`: Processa CSVs brutos
- `DataLoader`: Carrega dados processados

**Funções convenientes:**
- `processar_experimento()`: Processa todos os CSVs de uma pasta
- `carregar_experimento()`: Carrega dados de um chip

**Exemplo:**
```python
from dataprep import DataPreparation

# Processar dados
prep = DataPreparation(
    pasta_raw="data/GFETS/19abr/raw",
    pasta_silver="data/GFETS/19abr/silver",
    skiprows=16,
    linha_inicio=9574,
    linha_fim=10074
)

resultados = prep.processar_todos()
```

### 2️⃣ plot_utils.py - Funções de Plotagem

Biblioteca de funções para criar gráficos reutilizáveis.

**Classe principal:**
- `PlotterGFET`: Plotter completo para análise GFET

**Métodos disponíveis:**
- `plot_curvas_transferencia_grid()`: Grid com todos os devices
- `plot_curvas_normalizadas_grid()`: Grid normalizado
- `plot_device_individual()`: Curva de um device específico
- `plot_concentracoes()`: Curvas de concentração
- `salvar_figura()`: Salva figura em arquivo

**Exemplo:**
```python
from plot_utils import PlotterGFET
from dataprep import carregar_experimento

# Carregar dados
dados = carregar_experimento("data/GFETS/19abr/silver", "C1")

# Criar plotter
plotter = PlotterGFET(chip_name="C1")

# Plotar curvas
fig = plotter.plot_curvas_transferencia_grid(dados)
plotter.salvar_figura(fig, "resultados/C1_grid.png")
```

### 3️⃣ streamlit_app_plots.py - Interface Web

Aplicação web interativa para visualização de dados.

**Recursos:**
- Seleção de chip e device
- 4 abas de visualização:
  - 📈 Curvas de Transferência
  - 🔄 Curvas Normalizadas
  - 🎯 Device Individual
  - 💧 Curvas de Concentração

**Executar:**
```bash
cd chulha
streamlit run streamlit_app_plots.py
```

### 4️⃣ exemplo_workflow.ipynb - Notebook de Exemplo

Notebook demonstrando o uso completo dos scripts.

**Seções:**
1. Preparação dos Dados (Raw → Silver)
2. Carregar Dados Processados
3. Visualização de Dados
4. Análise Exploratória
5. Exportar Resultados

## 📋 Workflow Completo

### Passo 1: Organizar Dados

```
data/GFETS/19abr/
├── raw/                 # Colocar CSVs originais aqui
│   ├── C1 - BARE.csv
│   ├── C1 - ETOH.csv
│   └── ...
└── silver/              # Arquivos processados (gerados automaticamente)
```

### Passo 2: Processar Dados

```python
from dataprep import processar_experimento

# Processar todos os arquivos
resultados = processar_experimento(
    pasta_raw="data/GFETS/19abr/raw",
    pasta_silver="data/GFETS/19abr/silver"
)
```

### Passo 3: Analisar e Plotar

```python
from dataprep import carregar_experimento
from plot_utils import PlotterGFET

# Carregar dados
dados = carregar_experimento("data/GFETS/19abr/silver", "C1")

# Plotar
plotter = PlotterGFET(chip_name="C1")
fig = plotter.plot_device_individual(dados, device="1")
```

### Passo 4: Visualizar no Streamlit

```bash
streamlit run streamlit_app_plots.py
```

## 🎨 Personalização

### Ajustar Processamento

Modifique os parâmetros no `DataPreparation`:

```python
prep = DataPreparation(
    pasta_raw="...",
    pasta_silver="...",
    skiprows=16,          # Linhas para pular no início
    linha_inicio=9574,    # Início do recorte
    linha_fim=10074       # Fim do recorte
)
```

### Customizar Cores

Edite os dicionários no `PlotterGFET`:

```python
plotter.cores_etapas = {
    'bare': 'black',
    'etoh': 'grey',
    'ddt': '#FFC000',
    # ...
}
```

### Adicionar Novas Etapas

No `DataLoader.carregar_chip()`, adicione ao mapeamento:

```python
mapeamento_etapas = {
    "nova_etapa": f"{chip} - NOVA_ajustado.csv",
    # ...
}
```

## 📊 Tipos de Gráficos

### 1. Curvas de Transferência
- Escala logarítmica no eixo Y
- Múltiplas etapas (BARE, ETOH, DDT, PBSE, APT, ETA)
- Grid 4x5 com 20 devices

### 2. Curvas Normalizadas
- Normalização pelo valor máximo
- Comparação visual facilitada
- Mesmo layout do grid

### 3. Curvas de Concentração
- Diferentes concentrações (1 aM, 1 fM, 1 pM, etc.)
- Inclui curva "Branca" (média dos BLANKs)
- Mostra valor mínimo e V_GS na legenda
- Opção normalizada ou absoluta

## 🔧 Requisitos

```bash
pip install pandas numpy matplotlib streamlit
```

## 📝 Notas Importantes

- **Raw**: Sempre mantenha os arquivos originais intactos
- **Silver**: Dados processados, prontos para análise
- **Resultados**: Figuras exportadas em alta resolução (400 DPI)
- **Cache**: O Streamlit usa cache para melhor performance

## 🐛 Troubleshooting

### Erro ao carregar CSV
- Verifique o separador (`;` ou `,`)
- Ajuste `skiprows` se necessário
- Confirme o decimal (`,` ou `.`)

### Device não encontrado
- Verifique o nome do device (case-sensitive)
- Confirme que o arquivo foi processado corretamente
- Use `loader.obter_colunas_disponiveis()` para listar devices

### Gráfico vazio
- Verifique se a etapa existe em `dados`
- Confirme que o device existe naquela etapa
- Use `print(dados.keys())` para ver etapas disponíveis

## 📚 Exemplos Práticos

Ver [exemplo_workflow.ipynb](exemplo_workflow.ipynb) para exemplos completos de uso.

## 🤝 Contribuindo

Para adicionar novos tipos de gráficos:
1. Crie método na classe `PlotterGFET` em `plot_utils.py`
2. Adicione aba no `streamlit_app_plots.py`
3. Documente no README

## 📄 Licença

Este projeto é de código aberto e livre para uso acadêmico.

---

**Desenvolvido para análise de curvas GFET** 🔬📊
