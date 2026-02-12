# 🚀 Aplicativo Streamlit - Controle Financeiro

Aplicativo web interativo para visualização e gerenciamento das finanças mensais.

## 📋 Funcionalidades

### 📊 Dashboard
- Métricas principais (Total do Mês, Total Pago, Total a Pagar)
- Totais por categoria (CASA, V, M)
- Gráficos de distribuição por status e categoria
- Lista de contas em aberto

### 📈 Análises
- **Status**: Distribuição por status (valor e quantidade)
- **Categorias**: Distribuição por categoria com gráficos
- **Top 10**: Maiores contas com visualização horizontal
- **Vencimentos**: Calendário de vencimentos por dia

### 📋 Tabelas
- Todas as contas ordenadas por vencimento
- Contas em aberto com destaque
- Resumo por categoria e status

### 🔧 Gerenciar
- **Marcar como Pago**: Atualizar status de contas
- **Atualizar Valor**: Modificar valor de qualquer conta
- **Buscar Conta**: Sistema de busca por nome

### 📤 Exportar
- Gerar CSV detalhado com todas as contas
- Gerar resumo mensal em CSV
- Download direto dos arquivos

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install streamlit pandas matplotlib seaborn
```

### 2. Executar o Aplicativo

```bash
streamlit run streamlit_app.py
```

O aplicativo abrirá automaticamente no seu navegador em `http://localhost:8501`

## 💡 Dicas de Uso

### Navegação
Use o menu lateral para navegar entre as diferentes seções:
- 📊 Dashboard - Visão geral rápida
- 📈 Análises - Análises detalhadas com gráficos
- 📋 Tabelas - Visualização tabular dos dados
- 🔧 Gerenciar - Editar contas
- 📤 Exportar - Gerar relatórios

### Marcando Contas como Pagas
1. Vá em **🔧 Gerenciar**
2. Selecione a aba **✅ Marcar como Pago**
3. Escolha a conta
4. Clique em **Marcar como PAGA**

### Atualizando Valores
1. Vá em **🔧 Gerenciar**
2. Selecione a aba **💵 Atualizar Valor**
3. Escolha a conta
4. Digite o novo valor
5. Clique em **Atualizar Valor**

### Exportando Dados
1. Vá em **📤 Exportar**
2. Escolha o tipo de relatório
3. Clique em **Gerar**
4. Use o botão de download para baixar o arquivo

## 🎨 Recursos Visuais

- **Código de cores por status**:
  - 🟢 Verde: Pago
  - 🟡 Amarelo: Aberto
  - 🔴 Vermelho: Atrasado

- **Código de cores por categoria**:
  - 🔵 Azul: CASA
  - 🟣 Roxo: V
  - 🟠 Laranja: M

## 📁 Arquivos

- `streamlit_app.py` - Aplicativo principal
- `financas_casa.json` - Dados de entrada
- `financas_casa.csv` - CSV gerado (após exportação)
- `resumo_mensal.csv` - Resumo gerado (após exportação)

## 🔄 Atualização Automática

O aplicativo recarrega automaticamente os dados após qualquer modificação (marcar como pago, atualizar valor).

## ⚙️ Configurações

O aplicativo está configurado para:
- Layout wide (usa toda a largura da tela)
- Sidebar expandida por padrão
- Cache de dados para melhor performance

## 🐛 Resolução de Problemas

### Erro de NumPy
Se encontrar erros relacionados ao NumPy 2.0, instale a versão compatível:

```bash
pip install "numpy<2"
```

### Arquivo não encontrado
Certifique-se de estar executando o comando na pasta `/home/v/Documents/contas/`

### Dados não atualizam
Clique no botão **⚙️ Rerun** no canto superior direito do Streamlit

## 📞 Scripts do Terminal

Além do aplicativo web, você pode usar os scripts via terminal:

```bash
# Modo interativo completo
python update.py -i

# Calcular resumo mensal
python maths_month.py

# Resetar mês
python reset_month.py
```

---

**Versão:** 1.0  
**Criado:** Fevereiro/2026
