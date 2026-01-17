# trading_platform/quant_engine/strategies/sincronizador_quantico.py
import pandas as pd
import pandas_ta as ta
import numpy as np
from ..strategy_interface import StrategyInterface # Importa o contrato formal

# =============================================================================
#           ESTRATÉGIA V1.0 - SINCRONIZADOR QUÂNTICO
# =============================================================================

class StrategyContract(StrategyInterface): # Herda formalmente da Interface
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calcula os dois pilares da estratégia: o filtro de regime (correlação rolante)
        e o indicador de desvio (Z-score do spread).
        """
        df_featured = df.copy()
        df_featured.columns = df_featured.columns.str.lower()
        
        # Parâmetros lidos do JSON
        corr_period = params.get('corr_period', 96)
        zscore_period = params.get('zscore_period', 24)
        
        # 1. Filtro de Regime: Calcula a correlação dos retornos em uma janela móvel.
        #    `pct_change()` calcula o retorno percentual de um candle para o outro.
        retornos_1 = df_featured['close_1'].pct_change()
        retornos_2 = df_featured['close_2'].pct_change()
        df_featured['feature_correlacao_curta'] = retornos_1.rolling(window=corr_period).corr(retornos_2)

        # 2. Indicador de Desvio: Calcula o Z-Score da razão dos preços.
        df_featured['spread_ratio'] = df_featured['close_1'] / df_featured['close_2']
        spread_ma = ta.sma(df_featured['spread_ratio'], length=zscore_period)
        spread_std = df_featured['spread_ratio'].rolling(window=zscore_period).std()
        
        # A coluna de Z-Score é padronizada para 'zscore' para compatibilidade
        # com o `portfolio_analyzer`.
        df_featured['zscore'] = (df_featured['spread_ratio'] - spread_ma) / spread_std
        
        df_featured.dropna(inplace=True)
        # Retorna o DataFrame com o 'time' como uma coluna normal.
        return df_featured.reset_index(drop=True)

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Gera alertas apenas quando AMBAS as condições são atendidas:
        1. O mercado está em um regime de alta correlação.
        2. O Z-score do spread cruza o limiar de entrada.
        """
        df = df_featured.copy()
        
        # Condições de filtro e gatilho (vetorizadas)
        cond_regime_correlacionado = df['feature_correlacao_curta'] > params.get('corr_threshold', 0.85)
        
        z_entry_threshold = params.get('z_entry_threshold', 2.5)
        z_abs = df['zscore'].abs()
        cond_desvio_zscore = (z_abs > z_entry_threshold) & (z_abs.shift(1) <= z_entry_threshold)

        # Filtra o DataFrame original para preservar todas as colunas
        alertas = df[cond_regime_correlacionado & cond_desvio_zscore].copy()
        alertas['tipo'] = np.where(alertas['zscore'] > 0, 'Sell', 'Buy')
        
        return alertas.rename(columns={'time': 'time_alerta'})

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Prepara os dados para a IA. Para esta estratégia, as features já estão
        nos alertas, então esta função é principalmente para formatação e
        cumprimento do contrato de dados.
        """
        if alertas_df.empty: 
            return pd.DataFrame()
        
        trades_potenciais = alertas_df.copy()
        df_mercado_idx = df_mercado_featured.set_index('time')
        
        # Vetorização para encontrar os candles de entrada de forma performática
        indices_alerta = df_mercado_idx.index.searchsorted(trades_potenciais['time_alerta'])
        indices_entrada = indices_alerta + 1

        # Filtro de segurança para remover alertas no final da série de dados
        valid_mask = indices_entrada < len(df_mercado_idx)
        if not np.any(valid_mask): return pd.DataFrame()
        
        trades_potenciais = trades_potenciais[valid_mask]
        indices_entrada_validos = indices_entrada[valid_mask]
        candles_entrada = df_mercado_idx.iloc[indices_entrada_validos]

        # Atribuição de dados essenciais (O Contrato)
        trades_potenciais['time_entrada'] = candles_entrada.index.values
        trades_potenciais['preco_entrada_1'] = candles_entrada['open_1'].values
        trades_potenciais['preco_entrada_2'] = candles_entrada['open_2'].values
        trades_potenciais['zscore_entrada'] = trades_potenciais['zscore'].values
        
        # As colunas de 'feature_*' já existem e serão passadas adiante.
        
        # [SUGESTÃO] Adicionar Volatilidade como Feature
        # atr_1 = ta.atr(df_mercado_featured['high_1'], df_mercado_featured['low_1'], df_mercado_featured['close_1'], 14)
        # trades_potenciais['feature_volatility'] = atr_1.loc[trades_potenciais.index]

        return trades_potenciais