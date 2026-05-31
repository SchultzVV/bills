# 🔍 Análise Manual - Nova Aba de Curadoria de Dados

## Resumo das Alterações

A aplicação Streamlit foi reorganizada com uma **nova aba dedicada à análise manual** (Tab 6: "🔍 Análise Manual"), permitindo curadoria interativa dos dados experimentais antes da geração das médias finais.

---

## Estrutura Anterior vs Nova

### ❌ Antes
- Tab 5 (Tabelão) continha tanto a visualização de dados quanto a análise de V_Dirac
- Seleção era feita por data/chip/device de forma não-hierárquica
- Falta de visualização prévia para validação dos devices

### ✅ Agora

| Tab | Nome | Função |
|-----|------|--------|
| 1 | 📈 Curvas de Transferência | Visualização padrão de curvas |
| 2 | 🔄 Curvas Normalizadas | Curvas normalizadas |
| 3 | 🎯 Device Individual | Análise de device único |
| 4 | 💧 Curvas de Concentração | Análise de concentração |
| 5 | 🗃️ Tabelão | **Apenas visualização de dados consolidados** (sem V_Dirac) |
| **6** | **🔍 Análise Manual** | **NOVA - Curadoria hierárquica com aprovação manual** |

---

## Pipeline Hierárquico da Nova Aba

```
📅 ETAPA 1: Seleção de Data
   ↓
🔬 ETAPA 2: Seleção de Chips
   ↓
🎯 ETAPA 3: Inspeção Visual e Aprovação de Devices
   ├─ Visualização em grid de devices
   ├─ Checkboxes para aprovação/rejeição
   └─ Gráficos individuais para cada device
   ↓
📊 ETAPA 4: Consolidação e Gráfico Final
   ├─ Usa APENAS dados aprovados
   ├─ Calcula V_Dirac
   ├─ Gera gráfico consolidado
   └─ Agrupa chips por similaridade
```

---

## Como Usar a Nova Aba

### 1️⃣ **ETAPA 1: Selecionar Data de Aquisição**

Na parte superior da aba, você verá:
- **Seletor de Data**: Escolha a data (ex: "19abr", "03abr", etc.)
- **Seletor de Subpasta**: Se houver subpastas dentro da data
- **Estatísticas**: Total de chips, devices e pontos

```
📂 Pasta: data/silver/19abr/
📊 Total Chips: 3
🎯 Total Devices: 20
📈 Total Pontos: 1000
```

### 2️⃣ **ETAPA 2: Selecionar Chips**

Use o **multiselect** para escolher quais chips incluir:
- Selecione todos (default) ou apenas alguns
- Cada chip selecionado terá sua própria aba para inspeção

### 3️⃣ **ETAPA 3: Inspeção Visual e Aprovação**

Para cada chip, você verá:

#### a) **Grid de Checkboxes**
```
Aprovação de Devices:
☑️ Device 1    ☑️ Device 2    ☑️ Device 3
☑️ Device 4    ☐ Device 5    ☑️ Device 6
```

- **Marque ☑️** para incluir na análise final
- **Desmarque ☐** para rejeitar (transistor queimado, etc.)

#### b) **Visualização de Curvas**
- Escolha um device no seletor
- Selecione quais etapas visualizar (BARE, ETOH, DDT, etc.)
- Opção para normalizar a curva
- Clique em "📊 Visualizar Curva" para ver o gráfico

**Por que visualizar?**
- Identificar devices com comportamento anômalo
- Detectar transistores queimados
- Validar qualidade dos dados experimentais

### 4️⃣ **ETAPA 4: Consolidação e Gráfico Final**

Após revisar todos os chips:

#### a) **Resumo de Aprovações**
Tabela mostrando:
- Quantos devices foram aprovados por chip
- Taxa de aprovação (ex: 18/20 = 90%)

#### b) **Botão "🔄 Gerar Gráfico Final"**
Clique para consolidar os dados e gerar:

**📊 Gráfico V_Dirac Consolidado**
- Usa APENAS devices aprovados
- Mostra evolução através das etapas
- Cores em arco-íris (BARE → ETA)
- Barras de erro (±SEM)

**📋 Tabela de Estatísticas**
- V_Dirac médio por etapa
- SEM (Standard Error of Mean)
- Min/Max
- N (número de valores)

**🗃️ Dados Brutos**
- V_Dirac para cada chip/device/etapa
- Formato tabular

**🎯 Agrupamento Automático**
- Chips organizados por similaridade de V_Dirac
- 3 grupos: Baixo V_D, Médio V_D, Alto V_D

---

## Dados Armazenados em Session State

O Streamlit mantém automaticamente o estado das suas seleções:
- **Data selecionada**
- **Chips selecionados**
- **Approval status** de cada device (checkbox)

Isso significa: se você recarregar a página, suas seleções **não são perdidas** (dentro da sessão).

---

## Fluxo de Filtragem de Dados

```
DataFrame Original (todos os dados)
        ↓
   ETAPA 1: Filtrar por Data
        ↓
   ETAPA 2: Filtrar por Chips selecionados
        ↓
   ETAPA 3: Filtrar por Devices aprovados
        ↓
DataFrame Filtrado (apenas dados curados)
        ↓
   Calcular V_Dirac
        ↓
   Gerar Gráfico + Tabelas
```

---

## Características da Nova Aba

✅ **Hierarquia Clara**: Data → Chip → Device  
✅ **Aprovação Manual**: Checkboxes para cada device  
✅ **Visualização Prévia**: Gráficos de cada device antes de aprovar  
✅ **Consolidação Automática**: Usa apenas dados aprovados  
✅ **Sem Alteração Matemática**: Mesmos cálculos de V_Dirac  
✅ **Agrupamento Inteligente**: Chips organizados por similaridade  
✅ **Download de Resultados**: PNG + CSV dos dados finais  

---

## Exemplo de Uso Prático

### Cenário: Analisar experimento de 19 de Abril

1. Seleciono **Data: 19abr**
2. Vejo que há **3 chips: C1, C2, C3**
3. Seleciono **Todos os chips** (default)

4. **Inspeção do Chip C1:**
   - Vejo 6 devices
   - Visualizo Device 1 → OK ✅
   - Visualizo Device 2 → Queimado ❌ → Desmarco
   - Visualizo Device 3 → OK ✅
   - ...continuo para C2 e C3

5. **Resumo de Aprovações:**
   - C1: 5/6 aprovados (83%)
   - C2: 6/6 aprovados (100%)
   - C3: 4/6 aprovados (67%)

6. **Clico em "🔄 Gerar Gráfico Final"**
   - Dados consolidados: 15 devices aprovados
   - V_Dirac calculado apenas desses 15
   - Gráfico mostra evolução BARE → ETA

---

## Comparação com Tabelão

| Aspecto | Tabelão (Tab 5) | Análise Manual (Tab 6) |
|--------|-----------------|----------------------|
| Propósito | Exploração geral de dados | Curadoria com aprovação |
| Seleção | Manual por chip/device | Hierárquica: Data→Chip→Device |
| Visualização | Gráficos ad-hoc | Inspeção com checkboxes |
| Filtragem | Filtros gerais | Aprovação/rejeição por device |
| Saída | Tabelão + plots isolados | Gráfico consolidado curado |

---

## Notas Técnicas

### State Management
```python
st.session_state['aprovado_{chip}'] = {device: bool}
```

### Filtragem
```python
devices_aprovados = [d for d, aprovado in st.session_state[key].items() if aprovado]
df_filtrado = df_consolidado[df_consolidado['device'].isin(devices_aprovados)]
```

### Matemática (Inalterada)
- V_Dirac = ponto de mínima corrente (I_DS)
- Média = np.mean(valores)
- SEM = std / √n
- Agrupamento = percentis de V_Dirac em BARE

---

## Arquivos Modificados

- **streamlit_app_plots.py**: Adição de Tab 6 + reorganização
- **plot_utils.py**: Sem alterações (mantém mesmos métodos)
- **dataprep.py**: Sem alterações

---

## Próximos Passos (Opcional)

Possíveis melhorias futuras:
- Salvar estado de aprovações em arquivo (para recarregar depois)
- Gráfico comparativo antes/depois da curadoria
- Relatório em PDF dos dados aprovados
- Integração com banco de dados para rastreabilidade

---

Tudo pronto! 🎉 A nova aba está funcional e mantém a lógica matemática original!
