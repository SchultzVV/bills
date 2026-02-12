#!/usr/bin/env python3
"""Script de teste para validações"""

# Teste 1: Valor inválido
print("Teste 1: Digite 'pago' quando pedir valor")
print("Esperado: Mensagem de erro e pedir novamente")
print()

# Teste 2: Mês inválido
print("Teste 2: Digite '15' quando pedir mês")
print("Esperado: Mensagem de erro e pedir novamente")
print()

# Teste 3: Parcelas inválidas
print("Teste 3: Digite parcela 15/10 (parcela > total)")
print("Esperado: Mensagem de erro e pedir novamente")
print()

print("✅ Validações implementadas:")
print("  - Valor: Aceita apenas números")
print("  - Mês: Entre 1 e 12")
print("  - Ano: Entre 2000 e 2100")
print("  - Vencimento: Apenas números ou formato dd/mm/aaaa")
print("  - Parcelas: Números inteiros, parcela_atual <= total")
print("  - Status: Apenas pago, aberto ou atrasado")
