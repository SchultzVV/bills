"""
Pipeline para processar dados bronze → silver para TODOS os experimentos.
- Auto-detecta o último sweep (independente do número de corridas)
- Processa datas com CSVs diretos e com subpastas
- Ignora arquivos _overTime.csv
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path


BRONZE_BASE = Path("data/bronze/GFETS")
SILVER_BASE = Path("data/silver")
SKIPROWS = 16


def is_numeric_first_col(val):
    """Verifica se o valor parece um número float (linha de dados real)."""
    try:
        s = str(val).replace(",", ".").strip()
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def processar_csv(src_path: Path, dst_path: Path, verbose: bool = True):
    """
    Lê um CSV bruto, extrai o último sweep (últimas 500 linhas válidas)
    e salva no destino.
    """
    nome = src_path.name
    try:
        df = pd.read_csv(src_path, sep=";", skiprows=SKIPROWS, header=0,
                         low_memory=False)

        # Manter apenas linhas onde a primeira coluna é numérica (dados reais)
        col0 = df.columns[0]
        mascara = df[col0].apply(is_numeric_first_col)
        df_dados = df[mascara].copy()

        if len(df_dados) < 100:
            if verbose:
                print(f"  ⚠️  {nome}: poucas linhas válidas ({len(df_dados)}), pulando")
            return False

        # Pegar as últimas 500 (ou tudo se menos de 500)
        df_ultimo = df_dados.iloc[-500:].reset_index(drop=True)

        novo_nome = nome.replace(".csv", "_ajustado.csv")
        dst_path.mkdir(parents=True, exist_ok=True)
        df_ultimo.to_csv(dst_path / novo_nome, index=False)

        if verbose:
            print(f"  ✅ {nome}  →  {df_ultimo.shape[0]} linhas salvas")
        return True

    except Exception as e:
        if verbose:
            print(f"  ❌ {nome}: {e}")
        return False


def processar_pasta(src_dir: Path, dst_dir: Path, verbose: bool = True):
    """Processa todos os CSVs não-overTime de uma pasta."""
    csvs = sorted([
        f for f in src_dir.iterdir()
        if f.suffix.lower() == ".csv" and "_overTime" not in f.name
    ])

    if not csvs:
        return 0, 0

    ok = 0
    total = len(csvs)
    if verbose:
        print(f"\n📂 {src_dir}  →  {dst_dir}  ({total} arquivos)")

    for csv in csvs:
        if processar_csv(csv, dst_dir, verbose=verbose):
            ok += 1

    return ok, total


def main(verbose: bool = True):
    if not BRONZE_BASE.exists():
        print(f"❌ Pasta bronze não encontrada: {BRONZE_BASE}")
        return

    SILVER_BASE.mkdir(parents=True, exist_ok=True)

    total_ok = 0
    total_all = 0

    for date_dir in sorted(BRONZE_BASE.iterdir()):
        if not date_dir.is_dir():
            continue

        date_name = date_dir.name
        if verbose:
            print(f"\n{'='*60}")
            print(f"📅 Experimento: {date_name}")
            print('='*60)

        # CSVs diretos na pasta da data
        direct_csvs = [
            f for f in date_dir.iterdir()
            if f.suffix.lower() == ".csv" and "_overTime" not in f.name
        ]
        if direct_csvs:
            ok, total = processar_pasta(date_dir, SILVER_BASE / date_name, verbose)
            total_ok += ok
            total_all += total

        # Subpastas com CSVs
        for sub in sorted(date_dir.iterdir()):
            if not sub.is_dir():
                continue
            sub_csvs = [
                f for f in sub.iterdir()
                if f.suffix.lower() == ".csv" and "_overTime" not in f.name
            ]
            if sub_csvs:
                dst = SILVER_BASE / date_name / sub.name
                ok, total = processar_pasta(sub, dst, verbose)
                total_ok += ok
                total_all += total

    print(f"\n{'='*60}")
    print(f"✅ Pipeline finalizado: {total_ok}/{total_all} arquivos processados")
    print('='*60)


if __name__ == "__main__":
    main()
