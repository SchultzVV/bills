# 💰 Sistema de Controle Financeiro

Sistema automatizado para gerenciar as finanças mensais da casa com modo interativo.

## 📁 Arquivos

### Arquivos Principais
- **`financas_casa.json`** - Dados do mês atual
- **`template_contas.json`** - Template com contas fixas da categoria CASA
- **`update.py`** - Atualiza dados e gera CSVs
- **`maths_month.py`** - Calcula resumo mensal
- **`reset_month.py`** - Reseta o mês automaticamente

### Arquivos Gerados (não edite)
- **`financas_casa.csv`** - Tabela detalhada das contas
- **`resumo_mensal.csv`** - Resumo com totais

## 🚀 Como Usar

### 🆕 Modo Interativo (Recomendado)
```bash
python update.py --interativo
# ou
python update.py -i
```

O sistema vai perguntar:
1. **Mês e Ano** - Para qual período você está registrando
2. **Contas CASA** - Reseta automaticamente do template, pergunta valores
3. **Contas V** - Pergunta se tem contas da categoria V
4. **Contas M** - Pergunta se tem contas da categoria M

Para cada conta, você informa:
- Nome
- Vencimento (dia ou dd/mm/aaaa)
- Valor
- Parcelas (se aplicável para V e M)
- Status (pago/aberto)

### 📝 Modo Normal
```bash
python update.py
```

Apenas gera os CSVs a partir do JSON existente.

## 📋 Estrutura das Categorias

### 🏠 CASA (Mensais)
Contas fixas da casa, resetadas automaticamente do template todo mês:
- Aluguel, Condomínio, Luz, Internet, etc.
- Sempre perguntadas no modo interativo

### 👤 V e M (Opcionais)
Contas pessoais, podem ter parcelas:
- Cartões de crédito
- Compras parceladas
- Empréstimos
- Etc.

## 📊 Formato do CSV

```csv
Categoria,Conta,Vencimento,Valor,Parcelas,Status_Code
CASA,Aluguel,10/01/2026,1325.00,-,pago
V,Apocalipse,16/01/2026,1260.29,12/32,aberto
M,Mercado Livre,21/01/2026,628.28,3/10,pago
```

**Colunas:**
- **Categoria**: CASA, V ou M
- **Conta**: Nome da conta
- **Vencimento**: Data dd/mm/aaaa
- **Valor**: Valor em reais
- **Parcelas**: atual/total ou "-" se não parcelado
- **Status_Code**: pago, aberto ou atrasado

## 🔄 Workflow Mensal

### Opção 1: Modo Interativo Completo
```bash
python update.py --interativo
```

Responda as perguntas interativas e pronto!

### Opção 2: Edição Manual + Update
```bash
# 1. Editar JSON manualmente
code financas_casa.json

# 2. Gerar relatórios
python update.py
```

## 📝 Formato do JSON

```json
{
  "metadata": {
    "mes": "1",
    "ano": "2026",
    "descricao": "Controle financeiro da casa"
  },
  "contas": [
    {
      "categoria": "CASA",
      "nome": "Aluguel",
      "vencimento": 10,
      "valor": 1325.00,
      "status_code": "pago"
    },
    {
      "categoria": "V",
      "nome": "Apocalipse",
      "vencimento": 16,
      "valor": 1260.29,
      "status_code": "aberto",
      "parcela_atual": 12,
      "total_parcelas": 32
    }
  ]
}
```

### Campos Obrigatórios
- `categoria`: "CASA", "V" ou "M"
- `nome`: Nome da conta
- `vencimento`: Dia (int) ou data completa "dd/mm/aaaa"
- `valor`: Valor numérico
- `status_code`: "pago", "aberto" ou "atrasado"

### Campos Opcionais
- `parcela_atual`: Número da parcela atual
- `total_parcelas`: Total de parcelas

## 🎯 Exemplos

### Exemplo 1: Início do Mês Interativo
```bash
$ python update.py -i

💰 ATUALIZAÇÃO DE FINANÇAS
==================================================

Mês [1-12] [1]: 2
Ano [2026]: 2026

==================================================
🏠 CONTAS DA CASA - Mês 02/2026
==================================================

📝 Aluguel
  Valor [R$ 1325.00]: 
  Status (pago/aberto) [aberto]: pago

📝 Luz
  Valor [R$ 0.00]: 230.50
  Status (pago/aberto) [aberto]: 

...

==================================================
📋 CATEGORIA: V
==================================================
Usar contas anteriores de V? (s/n) [s]: n
Tem contas da categoria V? (s/n): s

➕ Nova conta V
  Nome: Apocalipse
  Vencimento (dd/mm/aaaa ou apenas dd): 16
  Valor: 1260.29
  Tem parcelas? (s/n) [n]: s
  Parcela atual: 12
  Total de parcelas: 32
  Status (pago/aberto) [aberto]: 

  Adicionar outra conta V? (s/n) [n]: n
```

### Exemplo 2: Conta com Parcelas no JSON
```json
{
  "categoria": "M",
  "nome": "Notebook",
  "vencimento": 15,
  "valor": 450.00,
  "status_code": "pago",
  "parcela_atual": 3,
  "total_parcelas": 10
}
```

### Exemplo 3: Reuso de Contas Anteriores
```bash
==================================================
📋 CATEGORIA: V
==================================================
Usar contas anteriores de V? (s/n) [s]: s
✅ Usando 7 contas anteriores
```

## ⚙️ Status Automático

O sistema calcula automaticamente o status "atrasado":
- Se `vencimento < data_atual` e `status != "pago"` → `status = "atrasado"`

## 💡 Dicas

### Parcelas
Para controle de parcelas, use `parcela_atual/total_parcelas`:
- Apocalipse: 12/32 (já pagou 11, está na parcela 12)
- No próximo mês: Edite manualmente para 13/32

### Contas Recorrentes
Mantenha no template (`template_contas.json`) apenas contas da categoria CASA que se repetem todo mês.

### Workflow Rápido
```bash
# Uma vez por mês
python update.py -i

# Sempre que pagar conta, edite o JSON e rode:
python update.py
```

### Template
O template é usado apenas para contas CASA. Contas V e M você informa no modo interativo ou edita direto no JSON.

## 🔧 Scripts Auxiliares

### Reset Month
```bash
python reset_month.py 2 2026        # Mês específico
python reset_month.py proximo       # Próximo mês
python reset_month.py adicionar     # Adicionar conta extra
```

## 📊 Resumo Mensal

O `resumo_mensal.csv` mostra:
- Total do Mês
- Total Pago  
- Total a Pagar
- Total por categoria (CASA, V, M)
