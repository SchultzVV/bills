"""
Script de preparação estendida de dados para análise de curvas GFET
Lê TODOS os dados da camada bronze (todas as corridas) e cria um DataFrame consolidado
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime


class BronzeDataExtractor:
    """
    Extrai TODAS as corridas de arquivos CSV da camada bronze
    """
    
    def __init__(self, base_path: str = "data/bronze/GFETS", skiprows: int = 16):
        """
        Inicializa o extrator de dados bronze
        
        Args:
            base_path: Caminho base para os dados bronze
            skiprows: Número de linhas de cabeçalho para pular
        """
        self.base_path = Path(base_path)
        self.skiprows = skiprows
        
    def find_all_csv_files(self) -> List[Dict[str, str]]:
        """
        Encontra todos os arquivos CSV na estrutura bronze
        
        Returns:
            Lista de dicionários com metadados dos arquivos
        """
        csv_files = []
        
        if not self.base_path.exists():
            print(f"⚠️ Pasta {self.base_path} não encontrada!")
            return csv_files
        
        # Procurar recursivamente por arquivos CSV
        for csv_path in self.base_path.rglob("*.csv"):
            # Extrair metadados do caminho
            relative_path = csv_path.relative_to(self.base_path)
            parts = relative_path.parts
            
            # Estrutura esperada: data/experimento/pasta_curves/arquivo.csv
            if len(parts) >= 3:
                data_experimento = parts[0]  # ex: 03abr, 19abr
                pasta_dados = parts[1]  # ex: 03abr_curves
                arquivo = parts[2]  # ex: C1 - 100pico.csv
                
                # Extrair chip e etapa do nome do arquivo
                if " - " in arquivo:
                    chip, etapa = arquivo.replace(".csv", "").split(" - ", 1)
                    
                    csv_files.append({
                        "caminho_completo": str(csv_path),
                        "caminho_relativo": str(relative_path),
                        "data_experimento": data_experimento,
                        "pasta_dados": pasta_dados,
                        "chip": chip,
                        "etapa": etapa,
                        "arquivo": arquivo
                    })
        
        return sorted(csv_files, key=lambda x: (x["data_experimento"], x["chip"], x["etapa"]))
    
    def detect_sweep_blocks(self, df: pd.DataFrame) -> List[Tuple[int, int, str]]:
        """
        Detecta blocos de corridas (sweeps) no DataFrame
        
        Args:
            df: DataFrame lido do CSV
            
        Returns:
            Lista de tuplas (inicio, fim, timestamp)
        """
        sweeps = []
        
        # Procurar por linhas que começam com um timestamp (formato de data)
        # Padrão: YYYY-MM-DD_HHhMMmSSs
        timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}h\d{2}m\d{2}s')
        
        for idx, row in df.iterrows():
            first_val = str(row.iloc[0])
            if timestamp_pattern.match(first_val):
                # Encontramos o início de um sweep
                timestamp = first_val.split(',')[0]  # Pegar só o timestamp
                sweeps.append((idx, timestamp))
        
        # Criar tuplas (inicio, fim, timestamp)
        blocks = []
        for i in range(len(sweeps)):
            start_idx = sweeps[i][0] + 1  # +1 para pular linha do timestamp
            timestamp = sweeps[i][1]
            
            # Fim é o início do próximo sweep ou fim do dataframe
            if i < len(sweeps) - 1:
                end_idx = sweeps[i + 1][0]
            else:
                end_idx = len(df)
            
            # Só adicionar se tiver dados suficientes (pelo menos 100 linhas)
            if end_idx - start_idx >= 100:
                blocks.append((start_idx, end_idx, timestamp))
        
        return blocks
    
    def extract_all_sweeps(self, caminho_arquivo: str, verbose: bool = False) -> List[pd.DataFrame]:
        """
        Extrai todas as corridas de um arquivo CSV
        
        Args:
            caminho_arquivo: Caminho completo do arquivo
            verbose: Se True, imprime informações
            
        Returns:
            Lista de DataFrames, um para cada corrida
        """
        sweeps_data = []
        
        try:
            # Ler CSV
            df = pd.read_csv(caminho_arquivo, sep=";", skiprows=self.skiprows, header=None)
            
            # Detectar blocos de corridas
            blocks = self.detect_sweep_blocks(df)
            
            if verbose:
                nome = os.path.basename(caminho_arquivo)
                print(f"📂 {nome}: {len(blocks)} corridas detectadas")
            
            # Extrair cada bloco
            for block_idx, (start, end, timestamp) in enumerate(blocks):
                # Pegar dados do bloco
                block_df = df.iloc[start:end, :].copy()
                
                # Primeira linha tem os nomes das colunas
                if len(block_df) > 0:
                    # Usar primeira linha como header
                    first_row = block_df.iloc[0]
                    block_df = block_df.iloc[1:, :]
                    block_df.columns = first_row.values
                    
                    # Resetar índice
                    block_df = block_df.reset_index(drop=True)
                    
                    # Adicionar metadados
                    block_df["_timestamp"] = timestamp
                    block_df["_sweep_idx"] = block_idx
                    
                    sweeps_data.append(block_df)
            
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao processar {caminho_arquivo}: {e}")
        
        return sweeps_data
    
    def create_consolidated_dataframe(self, verbose: bool = True) -> pd.DataFrame:
        """
        Cria DataFrame consolidado com TODOS os dados da camada bronze
        
        Args:
            verbose: Se True, imprime progresso
            
        Returns:
            DataFrame consolidado com todos os dados
        """
        all_data = []
        
        # Encontrar todos os arquivos
        csv_files = self.find_all_csv_files()
        
        if verbose:
            print(f"🔍 Encontrados {len(csv_files)} arquivos CSV")
            print("="*80)
        
        # Processar cada arquivo
        for file_info in csv_files:
            caminho = file_info["caminho_completo"]
            
            # Extrair todas as corridas
            sweeps = self.extract_all_sweeps(caminho, verbose=verbose)
            
            # Adicionar metadados a cada corrida
            for sweep_df in sweeps:
                # Adicionar colunas de metadados
                sweep_df["_data_experimento"] = file_info["data_experimento"]
                sweep_df["_pasta_dados"] = file_info["pasta_dados"]
                sweep_df["_chip"] = file_info["chip"]
                sweep_df["_etapa"] = file_info["etapa"]
                sweep_df["_arquivo"] = file_info["arquivo"]
                sweep_df["_caminho_relativo"] = file_info["caminho_relativo"]
                
                all_data.append(sweep_df)
        
        if not all_data:
            if verbose:
                print("⚠️ Nenhum dado extraído!")
            return pd.DataFrame()
        
        # Concatenar todos os dados
        if verbose:
            print("="*80)
            print("🔄 Concatenando todos os dados...")
        
        df_consolidated = pd.concat(all_data, ignore_index=True)
        
        if verbose:
            print(f"✅ DataFrame consolidado criado!")
            print(f"   📊 Total de linhas: {len(df_consolidated):,}")
            print(f"   📋 Colunas: {len(df_consolidated.columns)}")
            print(f"   🗂️  Experimentos: {df_consolidated['_data_experimento'].nunique()}")
            print(f"   💾 Chips: {df_consolidated['_chip'].nunique()}")
            print(f"   📈 Etapas: {df_consolidated['_etapa'].nunique()}")
            print(f"   🔄 Total de corridas: {len(df_consolidated.groupby(['_arquivo', '_sweep_idx']))}")
        
        return df_consolidated


class ConsolidatedDataAnalyzer:
    """
    Analisador de dados consolidados
    """
    
    def __init__(self, df_consolidated: pd.DataFrame):
        """
        Inicializa o analisador
        
        Args:
            df_consolidated: DataFrame consolidado
        """
        self.df = df_consolidated
        
    def list_experiments(self) -> List[str]:
        """Lista experimentos disponíveis"""
        return sorted(self.df["_data_experimento"].unique().tolist())
    
    def list_folders(self, experiment: Optional[str] = None) -> List[str]:
        """Lista pastas disponíveis"""
        df = self.df
        if experiment:
            df = df[df["_data_experimento"] == experiment]
        return sorted(df["_pasta_dados"].unique().tolist())
    
    def list_chips(self, experiment: Optional[str] = None, folder: Optional[str] = None) -> List[str]:
        """Lista chips disponíveis"""
        df = self.df
        if experiment:
            df = df[df["_data_experimento"] == experiment]
        if folder:
            df = df[df["_pasta_dados"] == folder]
        return sorted(df["_chip"].unique().tolist())
    
    def list_stages(self, chip: Optional[str] = None) -> List[str]:
        """Lista etapas disponíveis"""
        df = self.df
        if chip:
            df = df[df["_chip"] == chip]
        return sorted(df["_etapa"].unique().tolist())
    
    def filter_data(self, 
                    experiment: Optional[str] = None,
                    folder: Optional[str] = None,
                    chip: Optional[str] = None,
                    stage: Optional[str] = None,
                    sweep_idx: Optional[int] = None) -> pd.DataFrame:
        """
        Filtra dados consolidados
        
        Args:
            experiment: Data do experimento (ex: "19abr")
            folder: Pasta de dados (ex: "19abr_curves")
            chip: Chip (ex: "C1")
            stage: Etapa (ex: "1ato")
            sweep_idx: Índice da corrida
            
        Returns:
            DataFrame filtrado
        """
        df = self.df
        
        if experiment:
            df = df[df["_data_experimento"] == experiment]
        if folder:
            df = df[df["_pasta_dados"] == folder]
        if chip:
            df = df[df["_chip"] == chip]
        if stage:
            df = df[df["_etapa"] == stage]
        if sweep_idx is not None:
            df = df[df["_sweep_idx"] == sweep_idx]
        
        return df
    
    def get_plot_data(self, 
                      experiment: str,
                      folder: str,
                      chip: str,
                      stages: List[str],
                      x_col: str = "Variable Source",
                      y_col: str = "dev1",
                      sweep_idx: int = -1) -> Dict[str, pd.DataFrame]:
        """
        Obtém dados prontos para plotagem
        
        Args:
            experiment: Data do experimento
            folder: Pasta de dados
            chip: Chip
            stages: Lista de etapas
            x_col: Coluna X para plot
            y_col: Coluna Y para plot
            sweep_idx: Índice da corrida (-1 para última)
            
        Returns:
            Dicionário com {etapa: DataFrame} com colunas x e y
        """
        plot_data = {}
        
        for stage in stages:
            # Filtrar dados
            df_filtered = self.filter_data(
                experiment=experiment,
                folder=folder,
                chip=chip,
                stage=stage
            )
            
            if df_filtered.empty:
                continue
            
            # Se sweep_idx = -1, pegar última corrida
            if sweep_idx == -1:
                sweep_idx_val = df_filtered["_sweep_idx"].max()
            else:
                sweep_idx_val = sweep_idx
            
            df_sweep = df_filtered[df_filtered["_sweep_idx"] == sweep_idx_val]
            
            # Verificar se colunas existem
            if x_col not in df_sweep.columns or y_col not in df_sweep.columns:
                continue
            
            # Preparar dados para plot
            df_plot = df_sweep[[x_col, y_col]].copy()
            
            # Converter vírgulas para pontos (formato europeu)
            df_plot[x_col] = df_plot[x_col].astype(str).str.replace(',', '.')
            df_plot[y_col] = df_plot[y_col].astype(str).str.replace(',', '.')
            
            # Converter para numérico
            df_plot[x_col] = pd.to_numeric(df_plot[x_col], errors='coerce')
            df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors='coerce')
            
            # Remover NaN
            df_plot = df_plot.dropna()
            
            plot_data[stage] = df_plot
        
        return plot_data
    
    def save_consolidated(self, output_path: str):
        """
        Salva DataFrame consolidado
        
        Args:
            output_path: Caminho para salvar (CSV ou Parquet)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == ".parquet":
            self.df.to_parquet(output_path, index=False)
            print(f"✅ Dados salvos em: {output_path} (formato Parquet)")
        else:
            self.df.to_csv(output_path, index=False)
            print(f"✅ Dados salvos em: {output_path} (formato CSV)")


def create_consolidated_dataframe(base_path: str = "data/bronze/GFETS", 
                                  verbose: bool = True) -> pd.DataFrame:
    """
    Função conveniente para criar DataFrame consolidado
    
    Args:
        base_path: Caminho base para os dados bronze
        verbose: Se True, imprime progresso
        
    Returns:
        DataFrame consolidado
    """
    extractor = BronzeDataExtractor(base_path)
    return extractor.create_consolidated_dataframe(verbose=verbose)


def load_and_analyze(df_path: str) -> ConsolidatedDataAnalyzer:
    """
    Carrega DataFrame consolidado e retorna analisador
    
    Args:
        df_path: Caminho do arquivo consolidado
        
    Returns:
        Analisador de dados
    """
    df_path = Path(df_path)
    
    if df_path.suffix == ".parquet":
        df = pd.read_parquet(df_path)
    else:
        df = pd.read_csv(df_path)
    
    return ConsolidatedDataAnalyzer(df)


# Exemplo de uso
if __name__ == "__main__":
    # Criar DataFrame consolidado
    print("🚀 Criando DataFrame consolidado...")
    df_consolidated = create_consolidated_dataframe()
    
    # Criar analisador
    analyzer = ConsolidatedDataAnalyzer(df_consolidated)
    
    # Listar informações
    print("\n📊 INFORMAÇÕES DISPONÍVEIS:")
    print("="*80)
    print(f"Experimentos: {analyzer.list_experiments()}")
    print(f"Pastas: {analyzer.list_folders()}")
    print(f"Chips: {analyzer.list_chips()}")
    
    # Exemplo de filtro
    print("\n🔎 EXEMPLO DE FILTRO:")
    print("="*80)
    df_filtered = analyzer.filter_data(
        experiment="19abr",
        folder="19abr_curves",
        chip="C1"
    )
    print(f"Dados filtrados: {len(df_filtered)} linhas")
    print(f"Etapas disponíveis: {analyzer.list_stages(chip='C1')}")
    
    # Salvar
    analyzer.save_consolidated("data/gold/consolidated_all_data.parquet")
