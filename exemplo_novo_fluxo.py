#!/usr/bin/env python3
"""
Exemplo do novo fluxo interativo
"""

print("""
==================================================
📋 CATEGORIA: V
==================================================
Usar contas anteriores de V? (s/n) [s]: s
✅ Atualizando 7 contas anteriores

📝 Apocalipse
  Valor [R$ 1260.29]: 
  Parcelas anteriores: 12/32
  Atualizar parcelas? (s/n) [n]: s
  Parcela atual [12]: 13
  Total de parcelas [32]: 
  Status (pago/aberto) [aberto]: pago

📝 PJ
  Valor [R$ 3954.00]: 4100.50
  Status (pago/aberto) [aberto]: 

📝 PF
  Valor [R$ 2595.64]: 
  Status (pago/aberto) [aberto]: 

... (continua para todas as 7 contas)

==================================================
Quer adicionar outra conta V? (s/n) [n]: s

➕ Nova conta V
  Nome: Empréstimo Novo
  Vencimento (dd/mm/aaaa ou apenas dd): 20
  Valor: 500.00
  Tem parcelas? (s/n) [n]: s
  Parcela atual: 1
  Total de parcelas: 6
  Status (pago/aberto) [aberto]: 

  Adicionar outra conta V? (s/n) [n]: n

==================================================
📋 CATEGORIA: M
==================================================
...
""")

print("\n✅ Novo fluxo implementado!")
print("\n📋 Melhorias:")
print("  1. Ao reusar contas, pergunta item por item")
print("  2. Permite atualizar valor de cada conta")
print("  3. Permite atualizar parcelas (se tiver)")
print("  4. Pergunta status de cada conta")
print("  5. Depois pergunta se quer adicionar mais contas")
print("  6. Mantém validações para evitar erros")
