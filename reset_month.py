#!/usr/bin/env python3
"""
Script para resetar o mês automaticamente.
Cria um novo financas_casa.json baseado no template, com todas as contas em 'aberto'.
"""

import json
from datetime import datetime

TEMPLATE_FILE = "template_contas.json"
OUTPUT_FILE = "financas_casa.json"

def resetar_mes(mes=None, ano=None):
    """
    Reseta o mês criando um novo JSON a partir do template.
    
    Args:
        mes: Mês (1-12). Se None, usa o mês atual.
        ano: Ano (ex: 2026). Se None, usa o ano atual.
    """
    # Se não especificado, usa data atual
    if mes is None or ano is None:
        hoje = datetime.today()
        mes = mes or hoje.month
        ano = ano or hoje.year
    
    # Carregar template
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = json.load(f)
    
    # Criar novo JSON
    novo_json = {
        "metadata": {
            "mes": str(mes),
            "ano": str(ano),
            "descricao": "Controle financeiro da casa"
        },
        "contas": []
    }
    
    # Adicionar contas do template com status 'aberto'
    for conta in template["contas_fixas"]:
        nova_conta = {
            "categoria": conta["categoria"],
            "nome": conta["nome"],
            "vencimento": conta["vencimento"],
            "valor": conta["valor"],
            "status": "aberto"
        }
        novo_json["contas"].append(nova_conta)
    
    # Salvar arquivo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(novo_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Mês {mes:02d}/{ano} resetado com sucesso!")
    print(f"   📄 Arquivo criado: {OUTPUT_FILE}")
    print(f"   📝 {len(novo_json['contas'])} contas carregadas do template")
    print(f"   💡 Todas as contas estão com status 'aberto'")
    print(f"\n🔧 Próximos passos:")
    print(f"   1. Edite {OUTPUT_FILE} e atualize os valores das contas variáveis")
    print(f"   2. Marque como 'pago' as contas já pagas")
    print(f"   3. Execute 'python update.py' para gerar os CSVs")

def adicionar_conta_extra():
    """Adiciona uma conta extra ao JSON atual (para contas não-recorrentes)"""
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("\n➕ Adicionar conta extra")
    categoria = input("Categoria (CASA/V/M): ").upper()
    nome = input("Nome da conta: ")
    vencimento = int(input("Dia do vencimento: "))
    valor = float(input("Valor: "))
    status = input("Status (aberto/pago/atrasado) [aberto]: ") or "aberto"
    
    nova_conta = {
        "categoria": categoria,
        "nome": nome,
        "vencimento": vencimento,
        "valor": valor,
        "status": status
    }
    
    data["contas"].append(nova_conta)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Conta '{nome}' adicionada com sucesso!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "adicionar":
            adicionar_conta_extra()
        elif sys.argv[1] == "proximo":
            # Reseta para o próximo mês
            hoje = datetime.today()
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
            if proximo_mes > 12:
                proximo_mes = 1
                proximo_ano += 1
            resetar_mes(proximo_mes, proximo_ano)
        else:
            try:
                mes = int(sys.argv[1])
                ano = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.today().year
                resetar_mes(mes, ano)
            except:
                print("Uso: python reset_month.py [mes] [ano]")
                print("     python reset_month.py proximo")
                print("     python reset_month.py adicionar")
    else:
        # Reseta para o mês atual
        resetar_mes()
