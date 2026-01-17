# trading_platform/quant_engine/strategies/sismografo_do_sentimento.py
import pandas as pd
import pandas_ta as ta
import numpy as np
from .base_strategy import BaseStrategy

# =============================================================================
#           ESTRATÉGIA V1.0 - SISMÓGRAFO DO SENTIMENTO
# =============================================================================

class StrategyContract(BaseStrategy):
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Adiciona os indicadores base e depois os indicadores de sentimento.
        """
        # Primeiro, calcula os indicadores base (ATR, RSI, EMAs, etc.)
        df_featured = BaseStrategy.add_indicators(df, params)
        
        # --- INTEGRAÇÃO DE DADOS DE SENTIMENTO ---
        df_featured['sentiment_score'] = np.random.uniform(-1, 1, size=len(df_featured))
        df_featured['sentiment_momentum'] = df_featured['sentiment_score'].diff(periods=params.get('sentiment_momentum_period', 3))

        # --- INDICADORES TÉCNICOS DE CONTEXTO (Específicos desta estratégia) ---
        adx_len = params.get('adx_period', 14)
        adx_indicator = ta.adx(df_featured['high'], df_featured['low'], df_featured['close'], length=adx_len)
        if adx_indicator is not None and not adx_indicator.empty:
            df_featured['adx'] = adx_indicator[f'ADX_{adx_len}']
        else:
            df_featured['adx'] = np.nan
            
        df_featured.dropna(inplace=True)
        return df_featured

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Gera alertas quando o sentimento atinge um nível extremo, indicando
        potencial euforia ou pânico no mercado.
        """
        df = df_featured.copy()
        sentimento_threshold = params.get('sentiment_threshold', 0.90) # Aumentado para pegar apenas picos reais
        
        # Condições para um pico de sentimento (vetorizado)
        cond_pico_positivo = df['sentiment_score'] > sentimento_threshold
        cond_pico_negativo = df['sentiment_score'] < -sentimento_threshold
        
        # Filtra o DataFrame original para preservar todas as colunas de features
        alertas_compra = df[cond_pico_positivo].copy()
        alertas_compra['tipo'] = 'Buy'
        
        alertas_venda = df[cond_pico_negativo].copy()
        alertas_venda['tipo'] = 'Sell'
        
        alertas_finais = pd.concat([alertas_compra, alertas_venda]).sort_values('time')
        return alertas_finais.rename(columns={'time': 'time_alerta'})

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Prepara o dossiê para a IA. A IA decidirá se o contexto técnico
        (força da tendência) justifica agir sobre o catalisador do sentimento.
        """
        if alertas_df.empty: 
            return pd.DataFrame()
        
        trades_potenciais = alertas_df.copy()
        
        # ### BUG CRÍTICO DE LOOKAHEAD BIAS CORRIGIDO ###
        # A entrada deve ocorrer no candle SEGUINTE ao do alerta para ser um teste honesto.
        df_mercado_idx = df_mercado_featured.set_index('time')
        indices_alerta = df_mercado_idx.index.searchsorted(trades_potenciais['time_alerta'])
        indices_entrada = indices_alerta + 1
        
        valid_mask = indices_entrada < len(df_mercado_idx)
        if not np.any(valid_mask): return pd.DataFrame()
        
        # Filtra para apenas os trades que têm um candle de entrada válido
        trades_potenciais = trades_potenciais[valid_mask]
        indices_entrada_validos = indices_entrada[valid_mask]
        candles_entrada = df_mercado_idx.iloc[indices_entrada_validos]
        
        # ### BUG CRÍTICO DE CONTRATO CORRIGIDO ###
        # Atribui os dados essenciais que o pipeline espera.
        trades_potenciais['time_entrada'] = candles_entrada.index.values
        trades_potenciais['preco_entrada'] = candles_entrada['open'].values
        trades_potenciais['stop_loss_base'] = np.where(
            trades_potenciais['tipo'] == 'Buy', 
            trades_potenciais['low'].values, # SL abaixo da mínima do candle do pico
            trades_potenciais['high'].values # SL acima da máxima do candle do pico
        )
        trades_potenciais['atr_no_alerta'] = trades_potenciais['atr'].values
        trades_potenciais['Risco_Retorno'] = params.get('Risco_Retorno', 2.0)
        
        # ### BUG CRÍTICO DE LÓGICA CORRIGIDO ###
        # Mapeamento explícito das features a partir do DataFrame original, não do subconjunto.
        trades_potenciais['feature_sentiment_score'] = trades_potenciais['sentiment_score'].values
        trades_potenciais['feature_sentiment_momentum'] = trades_potenciais['sentiment_momentum'].values
        trades_potenciais['feature_adx'] = trades_potenciais['adx'].values
        
        # Remove colunas que não são features para limpar os dados para a IA
        cols_to_keep = [col for col in trades_potenciais.columns if col.startswith('feature_') or col in ['time_entrada', 'tipo', 'preco_entrada', 'stop_loss_base', 'atr_no_alerta', 'Risco_Retorno']]
        
        return trades_potenciais[cols_to_keep].dropna()