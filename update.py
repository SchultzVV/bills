import json
import csv
from datetime import datetime
from maths_month import calcular_resumo_mensal

INPUT_JSON = "financas_casa.json"
TEMPLATE_JSON = "template_contas.json"
OUTPUT_CSV = "financas_casa.csv"

STATUS_LABELS = {
    "pago": "PAGO",
    "aberto": "EM ABERTO",
    "atrasado": "ATRASADO"
}

def carregar_template():
    """Carrega contas fixas do template"""
    try:
        with open(TEMPLATE_JSON, "r", encoding="utf-8") as f:
            template = json.load(f)
        return template["contas_fixas"]
    except FileNotFoundError:
        print(f"⚠️  Template não encontrado: {TEMPLATE_JSON}")
        return []

def perguntar_valor(nome, valor_base=0.0):
    """Pergunta o valor de uma conta"""
    while True:
        if valor_base > 0:
            resposta = input(f"  {nome} [R$ {valor_base:.2f}]: ").strip()
            if not resposta:
                return valor_base
        else:
            resposta = input(f"  {nome}: ").strip()
            if not resposta:
                return 0.0
        
        try:
            return float(resposta)
        except ValueError:
            print("    ❌ Valor inválido, digite apenas números (ex: 230.50)")
            print("    💡 Se quer informar status, aguarde a próxima pergunta")

def perguntar_status():
    """Pergunta o status de uma conta"""
    while True:
        status = input("  Status (pago/aberto) [aberto]: ").strip().lower()
        if not status:
            return "aberto"
        if status in ["pago", "aberto", "atrasado"]:
            return status
        print("    ❌ Status inválido. Use: pago, aberto ou atrasado")

def adicionar_contas_categoria(categoria, contas_existentes=None):
    """Adiciona contas de uma categoria específica"""
    contas = []
    
    print(f"\n{'='*50}")
    print(f"📋 CATEGORIA: {categoria}")
    print(f"{'='*50}")
    
    if contas_existentes:
        usar = input(f"Usar contas anteriores de {categoria}? (s/n) [s]: ").strip().lower()
        if usar != 'n':
            print(f"✅ Atualizando {len(contas_existentes)} contas anteriores\n")
            
            # Atualizar cada conta existente
            for conta_antiga in contas_existentes:
                print(f"\n📝 {conta_antiga['nome']}")
                
                # Valor
                valor_base = conta_antiga.get('valor', 0.0)
                valor = perguntar_valor("Valor", valor_base)
                
                # Parcelas (se existir)
                parcela_atual = conta_antiga.get('parcela_atual')
                total_parcelas = conta_antiga.get('total_parcelas')
                
                if parcela_atual and total_parcelas:
                    print(f"  Parcelas anteriores: {parcela_atual}/{total_parcelas}")
                    atualizar_parcelas = input("  Atualizar parcelas? (s/n) [n]: ").strip().lower()
                    if atualizar_parcelas == 's':
                        while True:
                            try:
                                parcela_atual = int(input(f"  Parcela atual [{parcela_atual}]: ") or parcela_atual)
                                total_parcelas = int(input(f"  Total de parcelas [{total_parcelas}]: ") or total_parcelas)
                                if parcela_atual > 0 and total_parcelas > 0 and parcela_atual <= total_parcelas:
                                    break
                                else:
                                    print("    ❌ Valores inválidos. Parcela atual deve ser <= total de parcelas")
                            except ValueError:
                                print("    ❌ Digite apenas números inteiros")
                
                # Status
                status = perguntar_status()
                
                # Criar conta atualizada
                conta = {
                    "categoria": categoria,
                    "nome": conta_antiga['nome'],
                    "vencimento": conta_antiga['vencimento'],
                    "valor": valor,
                    "status_code": status
                }
                
                if parcela_atual and total_parcelas:
                    conta["parcela_atual"] = parcela_atual
                    conta["total_parcelas"] = total_parcelas
                
                contas.append(conta)
            
            # Perguntar se quer adicionar mais contas
            print(f"\n{'='*50}")
            adicionar_mais = input(f"Quer adicionar outra conta {categoria}? (s/n) [n]: ").strip().lower()
            if adicionar_mais != 's':
                return contas
    else:
        tem_contas = input(f"Tem contas da categoria {categoria}? (s/n): ").strip().lower()
        
        if tem_contas != 's':
            return contas
    
    # Adicionar novas contas
    while True:
        print(f"\n➕ Nova conta {categoria}")
        nome = input("  Nome: ").strip()
        if not nome:
            break
        
        # Vencimento
        while True:
            try:
                vencimento_input = input("  Vencimento (dd/mm/aaaa ou apenas dd): ").strip()
                if '/' in vencimento_input:
                    vencimento = vencimento_input
                    break
                else:
                    vencimento = int(vencimento_input)
                    break
            except ValueError:
                print("    ❌ Vencimento inválido, use apenas números (ex: 15 ou 15/01/2026)")
        
        valor = perguntar_valor("Valor")
        
        # Parcelas (se aplicável)
        parcela_atual = None
        total_parcelas = None
        if categoria in ["V", "M"]:
            tem_parcelas = input("  Tem parcelas? (s/n) [n]: ").strip().lower()
            if tem_parcelas == 's':
                while True:
                    try:
                        parcela_atual = int(input("  Parcela atual: "))
                        total_parcelas = int(input("  Total de parcelas: "))
                        if parcela_atual > 0 and total_parcelas > 0 and parcela_atual <= total_parcelas:
                            break
                        else:
                            print("    ❌ Valores inválidos. Parcela atual deve ser <= total de parcelas")
                    except ValueError:
                        print("    ❌ Digite apenas números inteiros")
        
        status = perguntar_status()
        
        conta = {
            "categoria": categoria,
            "nome": nome,
            "vencimento": vencimento,
            "valor": valor,
            "status_code": status
        }
        
        if parcela_atual and total_parcelas:
            conta["parcela_atual"] = parcela_atual
            conta["total_parcelas"] = total_parcelas
        
        contas.append(conta)
        
        continuar = input(f"\n  Adicionar outra conta {categoria}? (s/n) [n]: ").strip().lower()
        if continuar != 's':
            break
    
    return contas

def resetar_contas_casa(mes, ano):
    """Reseta contas da categoria CASA do template"""
    contas_template = carregar_template()
    contas_casa = []
    
    print(f"\n{'='*50}")
    print(f"🏠 CONTAS DA CASA - Mês {mes:02d}/{ano}")
    print(f"{'='*50}")
    
    for conta_base in contas_template:
        if conta_base["categoria"] != "CASA":
            continue
        
        nome = conta_base["nome"]
        valor_base = conta_base.get("valor", 0.0)
        vencimento = conta_base.get("vencimento")
        
        print(f"\n📝 {nome}")
        valor = perguntar_valor("Valor", valor_base)
        status = perguntar_status()
        
        conta = {
            "categoria": "CASA",
            "nome": nome,
            "vencimento": vencimento,
            "valor": valor,
            "status_code": status
        }
        
        contas_casa.append(conta)
    
    return contas_casa

def carregar_contas_anteriores():
    """Carrega contas V e M do JSON anterior se existir"""
    try:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        contas_v = [c for c in data.get("contas", []) if c["categoria"] == "V"]
        contas_m = [c for c in data.get("contas", []) if c["categoria"] == "M"]
        
        return contas_v, contas_m
    except FileNotFoundError:
        return [], []

def atualizar_dados_interativo():
    """Atualiza os dados de forma interativa"""
    print("\n" + "="*50)
    print("💰 ATUALIZAÇÃO DE FINANÇAS")
    print("="*50)
    
    # Perguntar mês/ano
    hoje = datetime.today()
    
    while True:
        try:
            mes_input = input(f"\nMês [1-12] [{hoje.month}]: ").strip()
            mes = int(mes_input) if mes_input else hoje.month
            if 1 <= mes <= 12:
                break
            else:
                print("    ❌ Mês inválido. Digite um número entre 1 e 12")
        except ValueError:
            print("    ❌ Digite apenas números")
    
    while True:
        try:
            ano_input = input(f"Ano [{hoje.year}]: ").strip()
            ano = int(ano_input) if ano_input else hoje.year
            if 2000 <= ano <= 2100:
                break
            else:
                print("    ❌ Ano inválido. Digite um ano entre 2000 e 2100")
        except ValueError:
            print("    ❌ Digite apenas números")
    
    # Carregar contas anteriores
    contas_v_anteriores, contas_m_anteriores = carregar_contas_anteriores()
    
    # Resetar contas CASA
    contas_casa = resetar_contas_casa(mes, ano)
    
    # Perguntar contas V
    contas_v = adicionar_contas_categoria("V", contas_v_anteriores)
    
    # Perguntar contas M
    contas_m = adicionar_contas_categoria("M", contas_m_anteriores)
    
    # Criar JSON
    todas_contas = contas_casa + contas_v + contas_m
    
    data = {
        "metadata": {
            "mes": str(mes),
            "ano": str(ano),
            "descricao": "Controle financeiro da casa"
        },
        "contas": todas_contas
    }
    
    # Salvar JSON
    with open(INPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ JSON atualizado: {INPUT_JSON}")
    print(f"   �� Total de contas: {len(todas_contas)}")
    print(f"   🏠 CASA: {len(contas_casa)}")
    print(f"   👤 V: {len(contas_v)}")
    print(f"   👤 M: {len(contas_m)}")
    
    return data

def gerar_csv(data):
    """Gera o CSV a partir dos dados"""
    mes = int(data["metadata"]["mes"])
    ano = int(data["metadata"]["ano"])
    today = datetime.today().date()
    
    rows = []
    for conta in data["contas"]:
        vencimento_raw = conta["vencimento"]
        
        # Processar vencimento
        if isinstance(vencimento_raw, int):
            dia = vencimento_raw
            vencimento = datetime(ano, mes, dia).date()
            vencimento_str = vencimento.strftime("%d/%m/%Y")
        elif '/' in str(vencimento_raw):
            vencimento_str = vencimento_raw
            try:
                vencimento = datetime.strptime(vencimento_raw, "%d/%m/%Y").date()
            except:
                partes = vencimento_raw.split('/')
                vencimento = datetime(int(partes[2]), int(partes[1]), int(partes[0])).date()
        else:
            dia = int(vencimento_raw)
            vencimento = datetime(ano, mes, dia).date()
            vencimento_str = vencimento.strftime("%d/%m/%Y")
        
        # Normalizar status
        status = conta.get("status_code", conta.get("status", "aberto"))
        status_aliases = {
            "paid": "pago",
            "due": "aberto",
            "overdue": "atrasado"
        }
        if status in status_aliases:
            status = status_aliases[status]
        
        # Calcular atraso automaticamente
        if status != "pago" and vencimento < today:
            status = "atrasado"
        
        # Montar linha
        row = {
            "Categoria": conta["categoria"],
            "Conta": conta["nome"],
            "Vencimento": vencimento_str,
            "Valor": f"{conta['valor']:.2f}",
            "Status_Code": status
        }
        
        # Adicionar parcelas se existir
        if "parcela_atual" in conta and "total_parcelas" in conta:
            row["Parcelas"] = f"{conta['parcela_atual']}/{conta['total_parcelas']}"
        else:
            row["Parcelas"] = "-"
        
        rows.append(row)
    
    # Escrever CSV
    fieldnames = [
        "Categoria",
        "Conta",
        "Vencimento",
        "Valor",
        "Parcelas",
        "Status_Code"
    ]
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ CSV gerado com sucesso: {OUTPUT_CSV}")

def main():
    import sys
    
    # Verificar se deve rodar modo interativo
    if "--interativo" in sys.argv or "-i" in sys.argv:
        data = atualizar_dados_interativo()
    else:
        # Modo normal: apenas gera CSV do JSON existente
        try:
            with open(INPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {INPUT_JSON}")
            print("💡 Use: python update.py --interativo para criar")
            return
    
    # Gerar CSV
    gerar_csv(data)
    
    # Gerar resumo mensal
    print()
    calcular_resumo_mensal()

if __name__ == "__main__":
    main()
