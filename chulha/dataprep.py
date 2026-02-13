"""
Script de preparação de dados para análise de curvas GFET
Lê arquivos CSV brutos e salva na camada silver processados
"""

import os
import pandas as pd
import glob
from typing import List, Dict, Optional


class DataPreparation:
    """
    Classe para preparar dados de curvas GFET
    """
    
    def __init__(self, pasta_raw: str, pasta_silver: str, 
                 skiprows: int = 16, 
                 linha_inicio: int = 9574, 
                 linha_fim: int = 10074):
        """
        Inicializa o preparador de dados
        
        Args:
            pasta_raw: Pasta com arquivos CSV originais
            pasta_silver: Pasta onde salvar arquivos processados
            skiprows: Número de linhas para pular no início do CSV
            linha_inicio: Índice inicial para recorte dos dados
            linha_fim: Índice final para recorte dos dados
        """
        self.pasta_raw = pasta_raw
        self.pasta_silver = pasta_silver
        self.skiprows = skiprows
        self.linha_inicio = linha_inicio
        self.linha_fim = linha_fim
        
        # Criar pasta silver se não existir
        os.makedirs(self.pasta_silver, exist_ok=True)
    
    def listar_arquivos_csv(self) -> List[str]:
        """Lista todos os arquivos CSV na pasta raw"""
        if not os.path.exists(self.pasta_raw):
            print(f"⚠️ Pasta {self.pasta_raw} não encontrada!")
            return []
        
        arquivos = [f for f in os.listdir(self.pasta_raw) if f.endswith(".csv")]
        return sorted(arquivos)
    
    def processar_arquivo(self, caminho_arquivo: str, verbose: bool = True) -> Optional[pd.DataFrame]:
        """
        Processa um único arquivo CSV
        
        Args:
            caminho_arquivo: Caminho completo do arquivo
            verbose: Se True, imprime logs do processamento
            
        Returns:
            DataFrame processado ou None em caso de erro
        """
        nome_arquivo = os.path.basename(caminho_arquivo)
        
        try:
            # Ler o CSV
            df = pd.read_csv(caminho_arquivo, sep=";", skiprows=self.skiprows)
            
            if verbose:
                print("\n" + "="*60)
                print(f" 📂 Processando: {nome_arquivo}")
                print("="*60)
                print(f"🔍 Antes do ajuste: {df.shape[0]:,} linhas | {df.shape[1]} colunas")
            
            # Ajustar linhas (última corrida)
            df = df.iloc[self.linha_inicio:self.linha_fim, :]
            
            if verbose:
                print("-"*60)
                print(f"✅ Após o ajuste: {df.shape[0]:,} linhas | {df.shape[1]} colunas")
                print("-"*60)
            
            # Criar nome do arquivo processado
            novo_nome = nome_arquivo.replace(".csv", "_ajustado.csv")
            caminho_salvar = os.path.join(self.pasta_silver, novo_nome)
            
            # Salvar CSV processado
            df.to_csv(caminho_salvar, index=False)
            
            if verbose:
                print("📁 Arquivo salvo com sucesso! ✅")
                print(f"📍 Local: {caminho_salvar}")
                print("="*60)
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao processar {nome_arquivo}: {e}")
            return None
    
    def processar_todos(self, verbose: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Processa todos os arquivos CSV da pasta raw
        
        Args:
            verbose: Se True, imprime logs do processamento
            
        Returns:
            Dicionário com nome_arquivo: DataFrame
        """
        arquivos = self.listar_arquivos_csv()
        
        if not arquivos:
            print("⚠️ Nenhum arquivo CSV encontrado!")
            return {}
        
        print(f"📊 Encontrados {len(arquivos)} arquivos CSV")
        print(f"📂 Pasta origem: {self.pasta_raw}")
        print(f"📂 Pasta destino: {self.pasta_silver}")
        
        resultados = {}
        
        for arquivo in arquivos:
            caminho_completo = os.path.join(self.pasta_raw, arquivo)
            df = self.processar_arquivo(caminho_completo, verbose=verbose)
            
            if df is not None:
                resultados[arquivo] = df
        
        print(f"\n✅ Processo finalizado! {len(resultados)}/{len(arquivos)} arquivos processados com sucesso")
        return resultados


class DataLoader:
    """
    Classe para carregar dados processados da camada silver
    """
    
    def __init__(self, pasta_silver: str):
        """
        Inicializa o carregador de dados
        
        Args:
            pasta_silver: Pasta com arquivos CSV processados
        """
        self.pasta_silver = pasta_silver
    
    def listar_chips_disponiveis(self) -> List[str]:
        """Lista chips disponíveis na pasta silver"""
        if not os.path.exists(self.pasta_silver):
            return []
        
        arquivos = [f for f in os.listdir(self.pasta_silver) if f.endswith("_ajustado.csv")]
        chips = sorted(list(set([f.split(" - ")[0] for f in arquivos if " - " in f])))
        return chips
    
    def carregar_chip(self, chip: str) -> Dict[str, pd.DataFrame]:
        """
        Carrega todos os dados de um chip específico
        
        Args:
            chip: Nome do chip (ex: "C1", "C2", etc.)
            
        Returns:
            Dicionário com etapa: DataFrame
        """
        # Mapeamento de etapas
        mapeamento_etapas = {
            "bare": f"{chip} - BARE_ajustado.csv",
            "etoh": f"{chip} - ETOH_ajustado.csv",
            "ddt": f"{chip} - DDT_ajustado.csv",
            "pbse": f"{chip} - PBSE_ajustado.csv",
            "apt": f"{chip} - APT_ajustado.csv",
            "eta": f"{chip} - ETA_ajustado.csv",
            "b1": f"{chip} - BLANK1_ajustado.csv",
            "b2": f"{chip} - BLANK2_ajustado.csv",
            "b3": f"{chip} - BLANK3_ajustado.csv",
            "menos18": f"{chip} - 1ato_ajustado.csv",
            "menos17": f"{chip} - 10ato_ajustado.csv",
            "menos16": f"{chip} - 100ato_ajustado.csv",
            "menos15": f"{chip} - 1fento_ajustado.csv",
            "menos14": f"{chip} - 10fento_ajustado.csv",
            "menos13": f"{chip} - 100fento_ajustado.csv",
            "menos12": f"{chip} - 1pico_ajustado.csv",
            "menos11": f"{chip} - 10pico_ajustado.csv",
            "menos10": f"{chip} - 100pico_ajustado.csv",
            "menos9": f"{chip} - 1nano_ajustado.csv",
            "menos8": f"{chip} - 10nano_ajustado.csv",
            "menos7": f"{chip} - 100nano_ajustado.csv",
            "menos6": f"{chip} - 1micro_ajustado.csv",
            "c10ng": f"{chip} - 74pico_ajustado.csv",
            "c25ng": f"{chip} - 185pico_ajustado.csv",
            "c50ng": f"{chip} - 370pico_ajustado.csv",
            "c75ng": f"{chip} - 556pico_ajustado.csv",
            "c100ng": f"{chip} - 741pico_ajustado.csv"
        }
        
        dados = {}
        arquivos_disponiveis = set(os.listdir(self.pasta_silver))
        
        for etapa, arquivo in mapeamento_etapas.items():
            if arquivo in arquivos_disponiveis:
                try:
                    caminho = os.path.join(self.pasta_silver, arquivo)
                    df = pd.read_csv(caminho, sep=",", decimal=",", skipfooter=1, engine='python')
                    
                    # Renomear colunas
                    colunas = ['V_G'] + [str(i) for i in range(1, len(df.columns))]
                    df.columns = colunas[:len(df.columns)]
                    
                    # Converter V_G para float
                    df["V_G"] = df["V_G"].astype(float)
                    
                    dados[etapa] = df
                    print(f"✅ {arquivo} carregado como '{etapa}'")
                    
                except Exception as e:
                    print(f"❌ Erro ao carregar {arquivo}: {e}")
        
        if dados:
            print(f"\n📊 Total de etapas carregadas: {len(dados)}")
        else:
            print(f"⚠️ Nenhum dado encontrado para chip {chip}")
        
        return dados
    
    def obter_colunas_disponiveis(self, dados: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Obtém lista de colunas (devices) disponíveis
        
        Args:
            dados: Dicionário com DataFrames carregados
            
        Returns:
            Lista de nomes de colunas (devices)
        """
        if not dados:
            return []
        
        primeira_etapa = list(dados.values())[0]
        colunas = [col for col in primeira_etapa.columns if col != 'V_G']
        return colunas


def processar_experimento(pasta_raw: str, pasta_silver: str, 
                          skiprows: int = 16,
                          linha_inicio: int = 9574,
                          linha_fim: int = 10074,
                          verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Função conveniente para processar um experimento completo
    
    Args:
        pasta_raw: Pasta com arquivos CSV originais
        pasta_silver: Pasta para salvar arquivos processados
        skiprows: Número de linhas para pular no início
        linha_inicio: Índice inicial para recorte
        linha_fim: Índice final para recorte
        verbose: Se True, imprime logs
        
    Returns:
        Dicionário com resultados processados
    """
    prep = DataPreparation(pasta_raw, pasta_silver, skiprows, linha_inicio, linha_fim)
    return prep.processar_todos(verbose=verbose)


def carregar_experimento(pasta_silver: str, chip: str) -> Dict[str, pd.DataFrame]:
    """
    Função conveniente para carregar dados de um chip
    
    Args:
        pasta_silver: Pasta com arquivos processados
        chip: Nome do chip
        
    Returns:
        Dicionário com dados carregados
    """
    loader = DataLoader(pasta_silver)
    return loader.carregar_chip(chip)


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de processamento
    pasta_raw = "data/GFETS/19abr/raw"
    pasta_silver = "data/GFETS/19abr/silver"
    
    # Processar todos os arquivos
    prep = DataPreparation(pasta_raw, pasta_silver)
    resultados = prep.processar_todos()
    
    # Carregar dados processados
    loader = DataLoader(pasta_silver)
    chips = loader.listar_chips_disponiveis()
    print(f"\nChips disponíveis: {chips}")
    
    if chips:
        dados = loader.carregar_chip(chips[0])
        colunas = loader.obter_colunas_disponiveis(dados)
        print(f"Devices disponíveis: {colunas}")
