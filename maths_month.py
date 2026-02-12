import json
import csv
from datetime import datetime

INPUT_JSON = "financas_casa.json"
OUTPUT_CSV = "resumo_mensal.csv"

def calcular_resumo_mensal():
    """Calcula o resumo mensal das finanças"""
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extrair mês e ano dos metadados
    mes = data["metadata"]["mes"]
    ano = data["metadata"]["ano"]
    
    # Inicializar contadores
    total_mes = 0.0
    total_pago = 0.0
    total_a_pagar = 0.0
    total_casa = 0.0
    total_v = 0.0
    total_m = 0.0

    # Processar cada conta
    for conta in data["contas"]:
        valor = conta["valor"]
        categoria = conta["categoria"]
        status = conta.get("status_code", conta.get("status", "aberto"))
        
        # Normaliza status (aceita formato antigo e novo)
        status_aliases = {
            "paid": "pago",
            "due": "aberto",
            "overdue": "atrasado"
        }
        if status in status_aliases:
            status = status_aliases[status]

        # Total do mês
        total_mes += valor

        # Total por status
        if status == "pago":
            total_pago += valor
        else:
            total_a_pagar += valor

        # Total por categoria
        if categoria == "CASA":
            total_casa += valor
        elif categoria == "V":
            total_v += valor
        elif categoria == "M":
            total_m += valor

    # Criar linha de resumo
    resumo = {
        "Mês": f"{mes}/{ano}",
        "Total do Mês": f"{total_mes:.2f}",
        "Total Pago": f"{total_pago:.2f}",
        "Total a Pagar": f"{total_a_pagar:.2f}",
        "Total CASA": f"{total_casa:.2f}",
        "Total V": f"{total_v:.2f}",
        "Total M": f"{total_m:.2f}"
    }

    # Escrever CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Mês",
                "Total do Mês",
                "Total Pago",
                "Total a Pagar",
                "Total CASA",
                "Total V",
                "Total M"
            ]
        )
        writer.writeheader()
        writer.writerow(resumo)

    print(f"✅ Resumo mensal gerado com sucesso: {OUTPUT_CSV}")
    print(f"   📊 Total do mês: R$ {total_mes:.2f}")
    print(f"   ✅ Pago: R$ {total_pago:.2f}")
    print(f"   ⏰ A pagar: R$ {total_a_pagar:.2f}")
    print(f"   🏠 CASA: R$ {total_casa:.2f}")
    print(f"   👤 V: R$ {total_v:.2f}")
    print(f"   👤 M: R$ {total_m:.2f}")

if __name__ == "__main__":
    calcular_resumo_mensal()
