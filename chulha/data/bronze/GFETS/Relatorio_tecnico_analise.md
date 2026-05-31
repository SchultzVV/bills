# Relatório Técnico — Tratamento e Análise de Dados de Biossensores GFET

**Projeto:** Análise de Curvas de Transferência de Transistores de Efeito de Campo Baseados em Grafeno (GFETs)
**Formato:** Relatório técnico resumido para adaptação em artigo científico

---

## 1. Bibliotecas e Ferramentas Utilizadas

O fluxo de análise foi implementado integralmente em linguagem Python, com uso das seguintes bibliotecas principais:

**pandas** — biblioteca central para manipulação tabular de dados. Foi utilizada em todas as etapas do fluxo: leitura dos arquivos CSV brutos, seleção de intervalos de linhas, renomeação de colunas, conversão de tipos numéricos, reestruturação entre formatos wide e long (`melt`, `pivot_table`) e exportação dos dados processados. A escolha do pandas se justifica pela sua capacidade de representar séries temporais e matrizes de medição de forma eficiente, com operações vetorizadas de alto desempenho.

**NumPy** — utilizado para operações numéricas de baixo nível, incluindo cálculo de mínimos (`nanargmin`, `nanmin`), normalização vetorial e formatação de valores em notação científica. Complementa o pandas em operações que exigem controle explícito sobre arrays numéricos.

**Matplotlib** — biblioteca responsável pela geração de todos os gráficos do projeto. Foram utilizados layouts em grade (*subplots*) para exibição simultânea de múltiplos dispositivos, escala logarítmica no eixo de corrente, configuração personalizada de marcações de eixo e salvamento de figuras em alta resolução. A escolha do Matplotlib garantiu controle total sobre a aparência dos gráficos, essencial para adequação às normas de publicação científica.

**OS e Glob** — módulos da biblioteca padrão do Python utilizados para varredura automática de diretórios, listagem de arquivos CSV e construção de caminhos de forma independente do sistema operacional. Dispensaram a necessidade de especificação manual dos arquivos a processar, tornando o pipeline adaptável a qualquer estrutura de pastas.

**Streamlit** — framework utilizado para construção da interface interativa de análise e visualização. Permitiu transformar os scripts Python de análise em uma aplicação web local, com controles de seleção, filtros dinâmicos, exibição de tabelas e renderização de gráficos, sem necessidade de desenvolvimento web. O sistema de cache nativo do Streamlit (`@st.cache_data`) foi empregado para evitar reprocessamento redundante dos dados a cada interação do usuário.

---

## 2. Fluxo de Tratamento e Análise de Dados

O pipeline de dados foi organizado em três camadas sequenciais, inspiradas na arquitetura Medallion de engenharia de dados, em que cada camada recebe os dados da anterior e os entrega em estado progressivamente mais limpo e estruturado.

### 2.1 Leitura e Extração dos Dados Brutos (Camada Bronze)

Os dados brutos são arquivos CSV exportados diretamente pelo sistema de medição elétrica. Cada arquivo corresponde a uma etapa de funcionalização de um chip e contém um cabeçalho instrumental de 16 linhas, seguido de múltiplas varreduras consecutivas de tensão de porta ($V_{GS}$), cada uma registrando a corrente dreno-fonte ($I_{DS}$) em até 20 dispositivos simultâneos.

A leitura dos arquivos foi implementada com separador de colunas ponto-e-vírgula (`;`) e supressão automática do cabeçalho:

```python
df = pd.read_csv(caminho, sep=";", skiprows=16)
```

Uma etapa relevante nesta fase foi a identificação do intervalo correspondente à **última varredura completa** de cada arquivo. Por se tratar do ciclo de medição com o dispositivo em equilíbrio térmico e elétrico, essa varredura é a mais representativa do estado estacionário do sensor. O recorte foi definido nas linhas 9574 a 10074 de cada arquivo (500 pontos de medição), e aplicado sistematicamente a todos os arquivos processados.

### 2.2 Limpeza e Padronização (Camada Silver)

Os dados extraídos foram padronizados e salvos em novos arquivos CSV com nomenclatura estruturada (`{chip} - {etapa}_ajustado.csv`). As operações realizadas nesta etapa foram:

- Renomeação das colunas para identificadores padronizados: a primeira coluna recebeu o nome `V_G` (tensão de porta) e as demais foram numeradas sequencialmente como `1`, `2`, ..., `20` (identificadores de dispositivo);
- Conversão da coluna `V_G` para tipo numérico de ponto flutuante;
- Na leitura posterior para análise, o separador decimal vírgula (`,`) foi tratado automaticamente via parâmetro `decimal=","`, corrigindo um ponto frequente de incompatibilidade entre a formatação regional do instrumento e o padrão de análise em Python.

O carregamento dos arquivos processados foi centralizado na classe `DataLoader`, que implementa um mapeamento entre rótulos semânticos de etapa (como `"bare"`, `"apt"`, `"menos15"`) e os respectivos nomes de arquivo no diretório silver. Esse mapeamento abstrai do código de análise qualquer dependência direta dos nomes de arquivo, tornando o pipeline robusto a variações de nomenclatura e facilitando a manutenção.

### 2.3 Consolidação e Reestruturação (Camada Gold — Tabelão)

A etapa mais significativa de transformação foi a construção do **tabelão** — um DataFrame consolidado em formato *tidy* (long format), em que cada linha representa uma única observação: o valor de corrente de um dispositivo específico, em uma tensão de porta específica, para uma etapa e chip específicos.

A reestruturação foi realizada pela operação `melt`, que converte o formato original matricial (colunas = dispositivos) para o formato analítico (uma linha por valor de corrente):

```
Formato original (wide):  V_G | dev1 | dev2 | ... | dev20
Formato tabelão (long):   chip | etapa | V_G | device | I_DS
```

Essa transformação teve impacto direto na qualidade da análise: o formato tidy permitiu aplicar filtros arbitrários por qualquer combinação de chip, etapa e dispositivo com operações simples do pandas, e habilitou a reconstrução dinâmica de subconjuntos de dados para plotagem via `pivot_table`. A consistência entre as representações foi validada verificando que a operação melt seguida de pivot_table produz exatamente os dados originais.

### 2.4 Normalização

Para comparação entre dispositivos com amplitudes absolutas distintas de corrente — variação decorrente de diferenças de resistência de contato e mobilidade local — as curvas de transferência foram normalizadas pelo valor máximo de cada curva:

$$I_{DS}^{\text{norm}}(V_{GS}) = \frac{I_{DS}(V_{GS})}{\max\left[I_{DS}(V_{GS})\right]}$$

A normalização preserva a posição do ponto de mínimo (ponto de Dirac) e o formato relativo da curva, desacoplando a comparação visual entre etapas da variabilidade absoluta de condutividade entre dispositivos.

### 2.5 Análise de Concentrações e Referência Branca

Para a análise de resposta ao analito em função da concentração, foi calculada a **curva de referência branca** como a média aritmética das três medições BLANK (realizadas em solução tampão antes da exposição ao analito). Essa média reduz a influência de flutuações instrumentais na definição da linha de base e foi utilizada como referência visual em todos os gráficos de concentração.

Em cada curva de concentração, a posição do mínimo de corrente e a tensão de porta correspondente foram calculadas e incluídas automaticamente nos rótulos do gráfico, permitindo rastrear quantitativamente o deslocamento do ponto de Dirac em função da concentração sem necessidade de inspeção manual dos dados.

---

## 3. Desenvolvimento da Interface e Visualização dos Resultados

A interface de análise foi desenvolvida em Streamlit e organizada em cinco abas temáticas, cada uma orientada a uma perspectiva analítica distinta:

A **primeira aba** exibe as curvas de transferência de todos os dispositivos de um chip em um layout de grade, com sobreposição das diferentes etapas de funcionalização em cores padronizadas. O eixo de corrente é apresentado em escala logarítmica, ressaltando variações em múltiplas ordens de magnitude e tornando visível a posição do ponto de Dirac em cada etapa. O número de dispositivos exibidos é controlável por slider, permitindo ajustar a visualização entre uma visão geral do chip e uma inspeção detalhada de subconjuntos de dispositivos.

A **segunda aba** apresenta o mesmo grid com as curvas normalizadas, em escala linear, focando na comparação da forma e posição relativa das curvas independentemente da amplitude absoluta de corrente.

A **terceira aba** isola um único dispositivo selecionado pelo usuário, gerando um gráfico de maior legibilidade com todas as etapas disponíveis. Suporta os modos de visualização normal e normalizado.

A **quarta aba** é dedicada à análise de resposta ao analito. Exibe as curvas de concentração de 1 aM a 10 nM sobre a curva branca de referência, com rótulos automáticos indicando o valor mínimo de corrente e a posição do ponto de Dirac para cada concentração. Essa aba foi projetada para facilitar a extração visual da curva analítica do sensor.

A **quinta aba** expõe o tabelão consolidado em formato tabular interativo, com filtros dinâmicos por chip e etapa. A partir dos dados filtrados, o usuário pode gerar três tipos de visualização diretamente: plot de dispositivo único, grid de múltiplos dispositivos e comparativo de dispositivos em uma única etapa. Essa aba concretiza a integração entre exploração tabular e visualização gráfica, permitindo que o pesquisador itere entre inspeção de dados brutos e geração de gráficos sem sair da interface.

A navegação lateral (sidebar) concentra os controles de escopo — seleção de experimento, subpasta e chip — e exibe estatísticas resumidas (número de etapas e dispositivos carregados) e a lista de etapas disponíveis, dando ao usuário visão imediata do conteúdo dos dados antes de qualquer interação com as abas.

---

## 4. Uso de Inteligência Artificial no Desenvolvimento

O desenvolvimento da infraestrutura computacional deste projeto contou com o suporte do modelo de linguagem **Claude Sonnet** (Anthropic), acessado pela extensão **GitHub Copilot** no editor Visual Studio Code.

A IA foi utilizada como ferramenta de apoio ao desenvolvimento de software, com foco nas seguintes contribuições:

**Refinamento de código:** sugestões de implementação para operações de transformação de dados (melt, pivot_table, mapeamento de etapas) e para a estruturação das classes de processamento, com ênfase em legibilidade e reutilização.

**Otimização da apresentação visual:** auxílio na configuração dos gráficos Matplotlib (escala de eixos, formatação de rótulos em notação científica com Unicode, layout de grades, gestão de legendas) e na organização da interface Streamlit (disposição de colunas, controles interativos, sistema de abas).

**Sugestões de estrutura lógica:** propostas de organização do fluxo de dados em camadas (bronze/silver/gold), separação entre classes de processamento e de carregamento, e modularização das funções de plotagem em classe dedicada (`PlotterGFET`), favorecendo a manutenção e extensão do código.

**Automação de tarefas repetitivas:** geração de mapeamentos extensos (como o dicionário de 27 etapas e seus respectivos arquivos), código boilerplate para componentes da interface Streamlit e tratamento padronizado de exceções na leitura de arquivos.

**Melhoria da organização do fluxo analítico:** sugestões sobre aplicação do decorador `@st.cache_data` para evitar reprocessamento redundante e sobre a arquitetura de reconstrução dinâmica do formato wide a partir do tabelão para alimentar os plotadores.

Em todos os casos, a interpretação dos resultados, as decisões metodológicas, a definição das etapas experimentais e os critérios de qualidade dos dados permaneceram sob responsabilidade exclusiva da pesquisadora. A IA atuou como ferramenta de produtividade no desenvolvimento técnico-computacional, sem interferência no conteúdo científico do trabalho.

---

*Relatório elaborado com base nos arquivos `dataprep.py`, `plot_utils.py` e `streamlit_app_plots.py` do projeto.*
