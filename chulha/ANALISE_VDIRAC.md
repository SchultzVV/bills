# 📈 Análise de V_Dirac (Charge Neutrality Point)

## O que foi adicionado?

Uma nova seção na **aba "Tabelão"** (`Tab 5`) da aplicação Streamlit que permite visualizar e analisar a evolução do **V_Dirac** (ponto de neutralidade de carga) através das etapas de funcionalização (BARE → ETOH → DDT → PBSE → APT → ETA).

---

## Passo a Passo para Usar

### 1️⃣ Abrir a aplicação Streamlit

Na pasta `/home/mushulha/Bills/bills/chulha/`, execute:

```bash
streamlit run streamlit_app_plots.py
```

### 2️⃣ Navegar até a aba "Tabelão" (Tab 5)

Dentro da aplicação, clique na aba **"🗃️ Tabelão"** (quinta aba).

### 3️⃣ Rolar para a seção "📈 Análise de V_Dirac"

No final da aba Tabelão, você encontrará a nova seção com título:
```
📈 Análise de V_Dirac (Charge Neutrality Point)
```

### 4️⃣ Selecionar Devices por Chip

Você verá **abas para cada chip** (ex: "🔬 C1", "🔬 C2", etc.)

Em cada aba, você pode:
- Ver quantos **devices** o chip possui
- Ver quantas **etapas** estão disponíveis
- **Selecionar quais devices** incluir na análise

**Exemplo:**
- Se o chip C1 tem 20 devices, você pode escolher apenas alguns (ex: 1, 2, 3, 4, 5) ou todos

### 5️⃣ Clicar em "📊 Gerar Análise V_Dirac"

Isso vai:
1. ✅ Calcular V_Dirac para cada device selecionado em cada etapa
2. ✅ Calcular a **média ± SEM** (Standard Error of the Mean)
3. ✅ Gerar um **gráfico em arco-íris** mostrando a evolução

### 6️⃣ Visualizar os Resultados

O resultado inclui:

#### 📊 Gráfico Principal
- **Eixo X:** Etapas (BARE, ETOH, DDT, PBSE, APT, ETA)
- **Eixo Y:** V_Dirac (V)
- **Pontos coloridos:** Média de V_Dirac para cada etapa
- **Barras de erro:** ± SEM (mostra variabilidade)
- **Pontos pequenos:** Cada chip/device individual (levemente transparentes)
- **Linhas conexão:** Mostram a tendência geral

#### 📋 Tabela de Estatísticas
Mostra para cada etapa:
- V_Dirac Médio (V)
- SEM (erro padrão da média)
- Min e Max (range)
- N Valores (número de medições)

#### 🗃️ Dados Brutos de V_Dirac
Tabela com V_Dirac para cada combinação de chip/device em cada etapa

#### 🎯 Agrupamento de Chips
Agrupa chips em categorias:
- **Baixo V_D:** Chips com V_Dirac menor na etapa BARE
- **Médio V_D:** Chips com V_Dirac intermediário
- **Alto V_D:** Chips com V_Dirac maior

---

## O que é V_Dirac?

**V_Dirac** = Voltage onde a corrente de dreno (I_DS) é **mínima** no gráfico de transferência.

**Interpretação:**
- **Etapa BARE:** V_Dirac "natural" do dispositivo
- **Após cada funcionalização:** Mudança em V_Dirac indica dopagem da superfície
- **Exemplo:** Se V_Dirac muda de -0.2V → -0.1V → +0.1V, indica dopagem progressiva

---

## 💡 Dicas Importantes

### ✅ Melhor Prática
1. **Incluir vários devices por chip** para ter média mais robusta
2. **Incluir vários chips** para comparar comportamento geral vs outliers
3. **Comparar grupos** de chips similares (use o agrupamento automático)

### ⚠️ Se Não Conseguir Calcular
Se receber erro na geração:
- Certifique-se que selecionou pelo menos um device para cada chip
- Verifique se os dados estão em `data/silver/`
- Confirme que etapas esperadas (bare, etoh, etc.) estão presentes

### 📥 Download dos Resultados
- **PNG:** Clique em "📥 Baixar Gráfico V_Dirac (PNG)" para salvar a figura
- **CSV:** Clique em "📥 Baixar Dados V_Dirac (CSV)" para tabela completa

---

## 🎨 Interpretação das Cores

O gráfico usa **cores do arco-íris** para cada etapa:
- 🟣 **BARE** → Roxo
- 🔵 **ETOH** → Azul
- 🩵 **DDT** → Ciano
- 🟢 **PBSE** → Verde
- 🟡 **APT** → Amarelo
- 🟠 **ETA** → Laranja

A cor **muda gradualmente** de roxo (BARE) para laranja (ETA), visualizando a progressão.

---

## 📊 Exemplo de Análise Típica

**Cenário:** Você tem 3 chips (C1, C2, C3) com 5 devices cada

1. Na seção de seleção, você escolhe:
   - C1: devices [1, 2, 3, 4, 5]
   - C2: devices [1, 2, 3, 4, 5]
   - C3: devices [1, 2, 3, 4, 5]

2. Clica em "📊 Gerar Análise V_Dirac"

3. Resultado:
   - Calcula V_Dirac para 15 devices × 6 etapas = 90 valores
   - Agrupa por etapa e calcula: média, SEM, min, max
   - Mostra gráfico com 6 pontos (um por etapa) ± barras de erro

4. Você vê:
   - **Tendência geral:** Como V_Dirac evolui
   - **Variabilidade:** SEM mostra se resultado é estável
   - **Outliers:** Identificar chips diferentes

---

## 🔧 Código Técnico

As novas funções adicionadas são:

### Em `plot_utils.py`:
- `calcular_vdirac_device()` - Calcula V_Dirac para um device
- `processar_vdirac_multiplos_chips()` - Processa múltiplos chips/devices
- `plot_vdirac_evolucao()` - Gera o gráfico
- `agrupar_chips_por_vdirac()` - Agrupa chips por similaridade

### Em `streamlit_app_plots.py`:
- Nova seção na Tab 5 com interface interativa

---

## 📝 Notas

- V_Dirac é calculado como o **ponto de mínima corrente** (I_DS mínimo) em escala linear
- Se algum device não tiver dado suficiente em alguma etapa, é pulado automaticamente
- O SEM (Standard Error of Mean) = desvio padrão / √(n de valores)
- Chips são automaticamente agrupados em 3 grupos (terços) baseado em V_Dirac BARE

---

Aproveite a análise! 🎉
