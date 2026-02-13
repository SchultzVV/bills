"""
Utilitários para plotagem de curvas GFET
Funções reutilizáveis para criar gráficos de análise
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Optional, Tuple


class PlotterGFET:
    """
    Classe para plotar curvas GFET
    """
    
    def __init__(self, chip_name: str = ""):
        """
        Inicializa o plotter
        
        Args:
            chip_name: Nome do chip para incluir nos títulos
        """
        self.chip_name = chip_name
        
        # Configurações de cores para etapas
        self.cores_etapas = {
            'bare': 'black',
            'etoh': 'grey',
            'ddt': '#FFC000',
            'pbse': '#00D023',
            'apt': '#B038FA',
            'eta': '#F86226'
        }
        
        self.labels_etapas = {
            'bare': 'BARE',
            'etoh': 'ETOH',
            'ddt': 'DDT',
            'pbse': 'PBSE',
            'apt': 'APT',
            'eta': 'ETA'
        }
        
        # Configurações para concentrações
        self.cores_concentracoes = {
            'branca': 'black',
            'menos18': 'red',
            'menos17': 'brown',
            'menos16': 'orange',
            'menos15': 'yellow',
            'menos14': 'yellowgreen',
            'menos13': 'green',
            'menos12': 'blue',
            'menos11': 'purple',
            'menos10': 'magenta',
            'menos9': 'pink',
            'menos8': 'black'
        }
        
        self.labels_concentracoes = {
            'branca': 'Branca',
            'menos18': '1 aM',
            'menos17': '10 aM',
            'menos16': '100 aM',
            'menos15': '1 fM',
            'menos14': '10 fM',
            'menos13': '100 fM',
            'menos12': '1 pM',
            'menos11': '10 pM',
            'menos10': '100 pM',
            'menos9': '1 nM',
            'menos8': '10 nM'
        }
    
    @staticmethod
    def formatar_exponencial(valor: float) -> str:
        """Formata valor em notação científica com potência elevada"""
        if valor == 0 or np.isnan(valor):
            return "0"
        try:
            base = f"{valor:.2g}".split("e")
            mantissa = base[0]
            expoente = int(base[1])
            expoente_formatado = ''.join({
                "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³",
                "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
            }[c] for c in str(expoente))
            return f"{mantissa} × 10{expoente_formatado}"
        except:
            return f"{valor:.2e}"
    
    @staticmethod
    def calcular_media_blanks(dados: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Calcula média dos BLANKs"""
        if 'b1' not in dados or 'b2' not in dados or 'b3' not in dados:
            return None
        
        b_avg = dados['b1'].copy()
        colunas_numericas = [col for col in b_avg.columns if col != 'V_G']
        
        for col in colunas_numericas:
            b_avg[col] = (dados['b1'][col] + dados['b2'][col] + dados['b3'][col]) / 3
        
        return b_avg
    
    def plot_curvas_transferencia_grid(self, dados: Dict[str, pd.DataFrame], 
                                       etapas: Optional[List[str]] = None,
                                       figsize: Tuple[int, int] = (20, 16)) -> plt.Figure:
        """
        Plota grid com curvas de transferência de todos os devices
        
        Args:
            dados: Dicionário com DataFrames das etapas
            etapas: Lista de etapas para plotar (default: bare, etoh, ddt, pbse, apt, eta)
            figsize: Tamanho da figura
            
        Returns:
            Figure do matplotlib
        """
        if etapas is None:
            etapas = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
        
        # Filtrar etapas disponíveis
        etapas_disponiveis = [e for e in etapas if e in dados]
        
        if not etapas_disponiveis:
            raise ValueError("Nenhuma etapa disponível nos dados")
        
        # Obter colunas (devices)
        primeira_etapa = etapas_disponiveis[0]
        colunas = [col for col in dados[primeira_etapa].columns if col != 'V_G']
        
        # Criar subplots
        fig, axes = plt.subplots(4, 5, figsize=figsize, facecolor="white")
        axes = axes.flatten()
        
        for idx, coluna in enumerate(colunas[:20]):
            ax = axes[idx]
            
            for etapa in etapas_disponiveis:
                if coluna in dados[etapa].columns:
                    cor = self.cores_etapas.get(etapa, 'gray')
                    label = self.labels_etapas.get(etapa, etapa.upper())
                    ax.plot(dados[etapa]["V_G"], dados[etapa][coluna],
                           color=cor, linestyle='-', label=label, linewidth=1.5)
            
            ax.set_xlabel("V$_{GS}$ (V)")
            ax.set_ylabel("I$_{DS}$ (A)")
            ax.set_title(f"Device {coluna}")
            ax.set_yscale("log")
            ax.grid(True)
            
            x_ticks = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]
            ax.set_xticks(x_ticks)
            ax.set_xticklabels([str(x) for x in x_ticks])
            ax.legend(fontsize=8)
        
        plt.tight_layout()
        return fig
    
    def plot_curvas_normalizadas_grid(self, dados: Dict[str, pd.DataFrame],
                                      etapas: Optional[List[str]] = None,
                                      figsize: Tuple[int, int] = (20, 16)) -> plt.Figure:
        """
        Plota grid com curvas normalizadas de todos os devices
        
        Args:
            dados: Dicionário com DataFrames das etapas
            etapas: Lista de etapas para plotar
            figsize: Tamanho da figura
            
        Returns:
            Figure do matplotlib
        """
        if etapas is None:
            etapas = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
        
        etapas_disponiveis = [e for e in etapas if e in dados]
        
        if not etapas_disponiveis:
            raise ValueError("Nenhuma etapa disponível nos dados")
        
        primeira_etapa = etapas_disponiveis[0]
        colunas = [col for col in dados[primeira_etapa].columns if col != 'V_G']
        
        fig, axes = plt.subplots(4, 5, figsize=figsize, facecolor="white")
        axes = axes.flatten()
        
        for idx, coluna in enumerate(colunas[:20]):
            ax = axes[idx]
            
            for etapa in etapas_disponiveis:
                if coluna in dados[etapa].columns:
                    valores = dados[etapa][coluna]
                    valores_norm = valores / valores.max()
                    
                    cor = self.cores_etapas.get(etapa, 'gray')
                    label = self.labels_etapas.get(etapa, etapa.upper())
                    ax.plot(dados[etapa]["V_G"], valores_norm,
                           color=cor, linestyle='-', label=label, linewidth=1.5)
            
            ax.set_xlabel("V$_{GS}$ (V)")
            ax.set_ylabel("I$_{DS}$ Normalizado")
            ax.set_title(f"Device {coluna}")
            ax.grid(True)
            
            x_ticks = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]
            ax.set_xticks(x_ticks)
            ax.set_xticklabels([str(x) for x in x_ticks])
            ax.legend(fontsize=8)
        
        plt.tight_layout()
        return fig
    
    def plot_device_individual(self, dados: Dict[str, pd.DataFrame],
                              device: str,
                              etapas: Optional[List[str]] = None,
                              normalizado: bool = False,
                              figsize: Tuple[int, int] = (10, 7)) -> plt.Figure:
        """
        Plota curva individual de um device
        
        Args:
            dados: Dicionário com DataFrames das etapas
            device: Nome do device
            etapas: Lista de etapas para plotar
            normalizado: Se True, normaliza as curvas
            figsize: Tamanho da figura
            
        Returns:
            Figure do matplotlib
        """
        if etapas is None:
            etapas = ['bare', 'etoh', 'ddt', 'pbse', 'apt', 'eta']
        
        etapas_disponiveis = [e for e in etapas if e in dados and device in dados[e].columns]
        
        if not etapas_disponiveis:
            raise ValueError(f"Device {device} não encontrado em nenhuma etapa")
        
        fig, ax = plt.subplots(figsize=figsize, facecolor="white")
        
        for etapa in etapas_disponiveis:
            valores = dados[etapa][device]
            vg = dados[etapa]["V_G"]
            
            if normalizado:
                valores = valores / valores.max()
            
            cor = self.cores_etapas.get(etapa, 'gray')
            label = self.labels_etapas.get(etapa, etapa.upper())
            ax.plot(vg, valores, color=cor, linestyle='-', label=label, linewidth=2)
        
        ax.set_xlabel(f"V$_{{GS}}$ (V)\n({self.chip_name})", fontsize=12)
        
        if normalizado:
            ax.set_ylabel("I$_{DS}$ Normalizado", fontsize=12)
            titulo = f"Curva de Transferência Normalizada - Device {device}"
        else:
            ax.set_ylabel("I$_{DS}$ (A)", fontsize=12)
            titulo = f"Curva de Transferência do GFET - Device {device}"
            ax.set_yscale("log")
        
        ax.set_title(titulo, fontsize=14, fontweight='bold')
        ax.grid(True)
        
        x_ticks = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([str(x) for x in x_ticks])
        ax.legend(fontsize=10)
        
        plt.tight_layout()
        return fig
    
    def plot_concentracoes(self, dados: Dict[str, pd.DataFrame],
                          device: str,
                          concentracoes: Optional[List[str]] = None,
                          incluir_branca: bool = True,
                          normalizado: bool = False,
                          x_range: Tuple[float, float] = (-0.4, 0.4),
                          figsize: Tuple[int, int] = (10, 7)) -> plt.Figure:
        """
        Plota curvas de concentração para um device
        
        Args:
            dados: Dicionário com DataFrames
            device: Nome do device
            concentracoes: Lista de concentrações para plotar
            incluir_branca: Se True, inclui curva branca (média dos blanks)
            normalizado: Se True, normaliza as curvas
            x_range: Range do eixo X (V_GS)
            figsize: Tamanho da figura
            
        Returns:
            Figure do matplotlib
        """
        if concentracoes is None:
            concentracoes = ['menos18', 'menos15', 'menos12']
        
        fig, ax = plt.subplots(figsize=figsize, facecolor="white")
        
        # Plot branca (média dos blanks)
        if incluir_branca:
            b_avg = self.calcular_media_blanks(dados)
            if b_avg is not None and device in b_avg.columns:
                valores = b_avg[device]
                vg = b_avg["V_G"]
                
                if normalizado:
                    valores = valores / valores.max()
                
                ax.plot(vg, valores, color='black', linestyle='--',
                       linewidth=2, label='Branca')
        
        # Plot concentrações
        for conc in concentracoes:
            if conc in dados and device in dados[conc].columns:
                valores = dados[conc][device]
                vg = dados[conc]["V_G"]
                
                if normalizado:
                    maximo = np.nanmax(valores)
                    if maximo > 0:
                        valores = valores / maximo
                        idx_min = np.nanargmin(valores)
                        vmin = valores.iloc[idx_min]
                        vg_min = vg.iloc[idx_min]
                        label = f"{self.labels_concentracoes.get(conc, conc)} (min = {vmin:.2e} @ {vg_min:.3f} V)"
                    else:
                        label = self.labels_concentracoes.get(conc, conc)
                else:
                    idx_min = np.nanargmin(valores)
                    corrente_min = valores.iloc[idx_min]
                    vg_min = vg.iloc[idx_min]
                    corrente_fmt = self.formatar_exponencial(corrente_min)
                    label = f"{self.labels_concentracoes.get(conc, conc)} (min = {corrente_fmt} @ {vg_min:.3f} V)"
                
                cor = self.cores_concentracoes.get(conc, 'gray')
                ax.plot(vg, valores, color=cor, linestyle='-',
                       linewidth=2, label=label)
        
        ax.set_xlim(x_range)
        ax.set_xlabel(f"V$_{{GS}}$ (V)\n({self.chip_name})", fontsize=12)
        
        if normalizado:
            ax.set_ylabel("I$_{DS}$ Normalizado (a.u.)", fontsize=12)
            ax.set_ylim(-0.05, 1.05)
            titulo = f"Curva de Concentrações - Device {device} (Normalizada)"
        else:
            ax.set_ylabel("I$_{DS}$ (A)", fontsize=12)
            titulo = f"Curva de Concentrações - Device {device}"
            formatter = mticker.ScalarFormatter(useMathText=True)
            formatter.set_scientific(True)
            ax.yaxis.set_major_formatter(formatter)
        
        ax.set_title(titulo, fontsize=14, fontweight='bold')
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        ax.legend(loc='best', fontsize=10)
        
        plt.tight_layout()
        return fig
    
    def salvar_figura(self, fig: plt.Figure, caminho: str, dpi: int = 400):
        """
        Salva figura em arquivo
        
        Args:
            fig: Figure do matplotlib
            caminho: Caminho para salvar
            dpi: Resolução da imagem
        """
        fig.savefig(caminho, dpi=dpi, bbox_inches='tight')
        print(f"✅ Figura salva: {caminho}")


# Exemplo de uso
if __name__ == "__main__":
    from dataprep import carregar_experimento
    
    # Carregar dados
    pasta_silver = "data/GFETS/19abr/silver"
    chip = "C1"
    dados = carregar_experimento(pasta_silver, chip)
    
    # Criar plotter
    plotter = PlotterGFET(chip_name=chip)
    
    # Plotar curvas de transferência
    fig = plotter.plot_curvas_transferencia_grid(dados)
    plotter.salvar_figura(fig, f"resultados/{chip}_transferencia_grid.png")
    
    # Plotar device individual
    fig = plotter.plot_device_individual(dados, device="1")
    plotter.salvar_figura(fig, f"resultados/{chip}_device_1.png")
    
    # Plotar concentrações
    fig = plotter.plot_concentracoes(dados, device="1", normalizado=True)
    plotter.salvar_figura(fig, f"resultados/{chip}_concentracoes_device_1.png")
