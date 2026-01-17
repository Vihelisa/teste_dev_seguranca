# trading_platform/quant_engine/strategy_interface.py
from abc import ABC, abstractmethod
import pandas as pd

# =============================================================================
#           A CONSTITUIÇÃO DA ALPHA FACTORY: O CONTRATO DE ESTRATÉGIA
# =============================================================================

class StrategyInterface(ABC):
    """
    Define o "Contrato" abstrato que TODAS as estratégias de trading na
    Plataforma Birdstone DEVEM seguir.
    
    Esta classe usa o `ABC` (Abstract Base Class) do Python para garantir que
    qualquer classe que herde dela seja OBRIGADA a implementar os três
    métodos principais do nosso pipeline quantitativo.
    
    Isso garante a uniformidade, a modularidade e a estabilidade do nosso
    motor de backtest (`backtester.py`) e do motor de execução em tempo real
    (`tasks.py`), pois eles podem confiar que qualquer estratégia sempre
    terá estes três "pontos de entrada" bem definidos.
    """

    @staticmethod
    @abstractmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        A primeira etapa do pipeline: Enriquecimento de Dados.
        
        Recebe um DataFrame de mercado bruto e os parâmetros da estratégia.
        Deve retornar um novo DataFrame com todas as colunas de indicadores
        necessárias para a geração de alertas e a extração de features
        (ex: EMAs, ATR, RSI, Z-Score, etc.).
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        A segunda etapa do pipeline: Identificação de Oportunidades.
        
        Recebe o DataFrame já enriquecido com indicadores.
        Deve retornar um DataFrame contendo apenas as linhas (candles) que
        representam um "evento de interesse" ou um sinal de trading bruto.
        Este DataFrame de alertas DEVE conter a coluna 'tipo' ('Buy' ou 'Sell')
        e a coluna 'time_alerta'.
        """
        pass

    @staticmethod
    @abstractmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        A terceira e última etapa: Preparação para a IA.
        
        Recebe o DataFrame de alertas e o DataFrame de mercado completo.
        Deve retornar um DataFrame final onde cada linha representa um trade
        potencial, pronto para ser enviado ao `portfolio_analyzer` e `ml_trainer`.
        
        Este DataFrame final DEVE conter:
        - 'time_entrada': O timestamp exato da entrada no trade.
        - 'tipo': 'Buy' ou 'Sell'.
        - 'preco_entrada': O preço de abertura do trade.
        - 'stop_loss_base': O preço de referência para o cálculo do stop loss.
        - 'atr_no_alerta': O valor do ATR no momento do alerta (para risco).
        - 'Risco_Retorno': (OBRIGATÓRIO para estratégias de ativo único).
        - Todas as colunas 'feature_...': Os dados que a IA usará para aprender.
        """
        pass