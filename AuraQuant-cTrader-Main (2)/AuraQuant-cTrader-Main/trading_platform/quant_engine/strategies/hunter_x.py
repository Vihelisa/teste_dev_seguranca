# trading_platform/quant_engine/strategies/hunter_x.py
import pandas as pd
import numpy as np
import pandas_ta as ta
from .base_strategy import BaseStrategy # Importa a classe base

# =============================================================================
#           ESTRATÉGIA V3.0 - HUNTER X (FRAMEWORK DE PESQUISA QUANTITATIVA)
# =============================================================================

class StrategyContract(BaseStrategy): # Herda da classe base
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Adiciona os indicadores base. Esta estratégia não precisa de indicadores adicionais.
        """
        return BaseStrategy.add_indicators(df, params)

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Geração de alertas V3.0 (VETORIZADA e agnóstica). 
        Ela não presume reversão ou continuação, apenas identifica um 
        evento de interesse (primeiro toque diário na liquidez).
        """
        df = df_featured.copy()
        df['dia'] = pd.to_datetime(df['time']).dt.date

        # Condições de alerta de toque (sem loop for)
        condicao_toque_superior = (df['high'] >= df['nivel_liquidez_sup'])
        condicao_toque_inferior = (df['low'] <= df['nivel_liquidez_inf'])
        
        # Filtro vetorizado para pegar apenas o PRIMEIRO alerta de cada tipo por dia
        df['venda_potencial'] = condicao_toque_superior
        df['compra_potencial'] = condicao_toque_inferior
        
        # O `groupby('dia').transform(lambda x: x.cumsum() == 1)` cria uma máscara
        # booleana que é verdadeira apenas para a primeira ocorrência em cada dia.
        df['primeira_venda'] = df.groupby('dia')['venda_potencial'].transform(lambda x: x.cumsum() == 1) & condicao_toque_superior
        df['primeira_compra'] = df.groupby('dia')['compra_potencial'].transform(lambda x: x.cumsum() == 1) & condicao_toque_inferior

        # Cria os DataFrames de alertas, usando .copy() para evitar warnings
        alertas_venda = df.loc[df['primeira_venda']].copy()
        alertas_venda['tipo'] = 'Sell'
        
        alertas_compra = df.loc[df['primeira_compra']].copy()
        alertas_compra['tipo'] = 'Buy'
        
        # Concatena e ordena por tempo para ter uma lista cronológica de sinais brutos
        alertas_finais = pd.concat([alertas_venda, alertas_compra]).sort_index()
        # O reset_index é crucial para que o DataFrame retornado seja fácil de iterar
        return alertas_finais.reset_index().rename(columns={'time': 'time_alerta'})

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Constrói o "dossiê de inteligência" para a IA a partir de cada evento de interesse.
        Versão vetorizada para melhor performance.
        """
        if alertas_df.empty:
            return pd.DataFrame()

        trades_potenciais = alertas_df.copy()
        df_mercado_idx = df_mercado_featured.set_index('time')

        # Encontra os candles de entrada (o candle seguinte ao do alerta)
        indices_alerta = df_mercado_idx.index.searchsorted(trades_potenciais['time_alerta'])
        indices_entrada = indices_alerta + 1
        
        valid_mask = indices_entrada < len(df_mercado_idx)
        if not np.any(valid_mask):
            return pd.DataFrame()

        # Filtra para apenas os trades que têm um candle de entrada válido
        trades_potenciais = trades_potenciais[valid_mask].copy()
        indices_entrada_validos = indices_entrada[valid_mask]
        candles_entrada = df_mercado_idx.iloc[indices_entrada_validos]

        # Atribui os dados essenciais que o pipeline espera
        trades_potenciais['time_entrada'] = candles_entrada.index.values
        trades_potenciais['preco_entrada'] = candles_entrada['open'].values
        trades_potenciais['stop_loss_base'] = np.where(
            trades_potenciais['tipo'] == 'Buy',
            trades_potenciais['low'].values,
            trades_potenciais['high'].values
        )
        trades_potenciais['atr_no_alerta'] = trades_potenciais['atr'].values
        trades_potenciais['Risco_Retorno'] = params.get('Risco_Retorno', 1.5)

        # --- Análise Anatômica do Candle de Alerta (Vetorizada) ---
        atr_do_candle = trades_potenciais['atr'].values
        atr_do_candle[atr_do_candle < 1e-9] = 1.0 # Evita divisão por zero

        sombra = np.where(
            trades_potenciais['tipo'] == 'Sell',
            trades_potenciais['high'].values - trades_potenciais['close'].values,
            trades_potenciais['close'].values - trades_potenciais['low'].values
        )
        hora_do_dia = pd.to_datetime(trades_potenciais['time_alerta']).hour.values

        atr_media_100_safe = trades_potenciais['atr_media_100'].values
        atr_media_100_safe[atr_media_100_safe <= 0] = 1.0 # Evita divisão por zero

        # ### ARSENAL DE INTELIGÊNCIA PARA A IA (Vetorizado) ###
        trades_potenciais['feature_rsi'] = trades_potenciais['rsi'].values
        trades_potenciais['feature_explosao_vol'] = atr_do_candle / atr_media_100_safe
        trades_potenciais['feature_forca_rejeicao'] = sombra / atr_do_candle
        trades_potenciais['feature_sessao'] = np.select(
            [hora_do_dia < 8, (hora_do_dia >= 8) & (hora_do_dia < 16)],
            [0, 1],
            default=2
        )
        trades_potenciais['feature_exaustao_curta'] = (trades_potenciais['close'].values - trades_potenciais['ema_curta'].values) / atr_do_candle
        trades_potenciais['feature_exaustao_longa'] = (trades_potenciais['close'].values - trades_potenciais['ema_longa'].values) / atr_do_candle

        # Remove colunas que não são features para limpar os dados para a IA
        cols_to_keep = [col for col in trades_potenciais.columns if col.startswith('feature_') or col in ['time_entrada', 'tipo', 'preco_entrada', 'stop_loss_base', 'atr_no_alerta', 'Risco_Retorno']]

        return trades_potenciais[cols_to_keep].dropna()