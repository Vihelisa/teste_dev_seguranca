# trading_platform/quant_engine/strategies/sentinela_da_liquidez.py
import pandas as pd
import numpy as np
import pandas_ta as ta
from ..strategy_interface import StrategyInterface # Importa o contrato formal

# =============================================================================
#           ESTRATÉGIA V2.0 - SENTINELA DA LIQUIDEZ
# =============================================================================

class StrategyContract(StrategyInterface): # Herda formalmente da Interface
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Adiciona os "sensores" da estratégia, criando um dossiê completo sobre
        a tendência, volatilidade e momentum do mercado.
        """
        df_featured = df.copy()
        
        # Parâmetros lidos do JSON, com fallbacks seguros
        ema_curta_len = params.get('EMA_Curta_Periodo', 21)
        ema_longa_len = params.get('EMA_Longa_Periodo', 200)
        atr_len = params.get('ATR_Periodo', 14)
        atr_media_len = params.get('ATR_Media_Periodo', 100)
        adx_len = params.get('ADX_Periodo', 14)
        rsi_len = params.get('RSI_Periodo', 14)

        # Sensores de Tendência
        df_featured['ema_curta'] = ta.ema(df_featured['close'], length=ema_curta_len)
        df_featured['ema_longa'] = ta.ema(df_featured['close'], length=ema_longa_len)

        # Sensores de Volatilidade e Momentum
        # Calcula o ATR primeiro
        atr_indicator = ta.atr(df_featured['high'], df_featured['low'], df_featured['close'], length=atr_len)
        if atr_indicator is not None and not atr_indicator.empty:
            df_featured['atr'] = atr_indicator
        else:
            df_featured['atr'] = np.nan

        # Agora calcula a média do ATR
        df_featured['atr_media'] = df_featured['atr'].rolling(window=atr_media_len, min_periods=1).mean()
        
        # Calcula o RSI
        df_featured['rsi'] = ta.rsi(df_featured['close'], length=rsi_len)

        # Sensor de Força da Tendência
        adx_indicator = ta.adx(df_featured['high'], df_featured['low'], df_featured['close'], length=adx_len)
        if adx_indicator is not None and not adx_indicator.empty:
            df_featured['adx'] = adx_indicator[f'ADX_{adx_len}']
        else:
            df_featured['adx'] = np.nan # Preenche com NaN se não puder ser calculado

        df_featured.dropna(inplace=True)
        return df_featured

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Geração de alertas VETORIZADA e agnóstica. Identifica o PRIMEIRO toque
        diário em um nível de liquidez, tratando-o como um "evento de interesse".
        """
        df = df_featured.copy()
        df['dia'] = pd.to_datetime(df['time']).dt.date

        cond_toque_sup = (df['high'] >= df['nivel_liquidez_sup'])
        cond_toque_inf = (df['low'] <= df['nivel_liquidez_inf'])
        
        df['venda_potencial'] = cond_toque_sup
        df['compra_potencial'] = cond_toque_inf
        
        # Filtro vetorizado para a primeira ocorrência do dia
        df['primeira_venda'] = df.groupby('dia')['venda_potencial'].transform(lambda x: x.cumsum() == 1) & cond_toque_sup
        df['primeira_compra'] = df.groupby('dia')['compra_potencial'].transform(lambda x: x.cumsum() == 1) & cond_toque_inf

        alertas_venda = df.loc[df['primeira_venda']].copy(); alertas_venda['tipo'] = 'Sell'
        alertas_compra = df.loc[df['primeira_compra']].copy(); alertas_compra['tipo'] = 'Buy'
        
        alertas_finais = pd.concat([alertas_venda, alertas_compra]).sort_index()
        return alertas_finais.rename(columns={'time': 'time_alerta'})

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Versão V2.0 (Tipo-Segura e Vetorizada). Constrói o dossiê de inteligência
        para a IA de forma performática e robusta.
        """
        if alertas_df.empty:
            return pd.DataFrame()
        
        df_mercado_idx = df_mercado_featured.set_index('time')
        
        # Encontra as posições (índices inteiros) dos alertas e das entradas.
        indices_alerta = df_mercado_idx.index.searchsorted(alertas_df['time_alerta'])
        indices_entrada = indices_alerta + 1

        # Filtro de segurança para remover alertas cuja entrada estaria "fora do tempo".
        valid_mask = indices_entrada < len(df_mercado_idx)
        if not np.any(valid_mask):
            return pd.DataFrame()

        alertas_validos = alertas_df[valid_mask]
        indices_alerta_validos = indices_alerta[valid_mask]
        indices_entrada_validos = indices_entrada[valid_mask]

        # Seleciona os candles de contexto usando os índices de POSIÇÃO (.iloc).
        candles_alerta_contexto = df_mercado_idx.iloc[indices_alerta_validos]
        candles_entrada_contexto = df_mercado_idx.iloc[indices_entrada_validos]
        
        # Cria o DataFrame final, alinhado com os alertas que sobreviveram ao filtro.
        trades_potenciais = pd.DataFrame(index=alertas_validos.index)

        # ATRIBUIÇÃO DE DADOS ESSENCIAIS (O Contrato)
        trades_potenciais['time_entrada'] = candles_entrada_contexto.index.values
        trades_potenciais['tipo'] = alertas_validos['tipo'].values
        trades_potenciais['preco_entrada'] = candles_entrada_contexto['open'].values
        trades_potenciais['stop_loss_base'] = np.where(trades_potenciais['tipo'] == 'Sell', candles_alerta_contexto['high'].values, candles_alerta_contexto['low'].values)
        trades_potenciais['atr_no_alerta'] = candles_alerta_contexto['atr'].values
        trades_potenciais['Risco_Retorno'] = params.get('Risco_Retorno', 1.5)
        
        # ATRIBUIÇÃO DE FEATURES PARA A IA (Vetorizada)
        # Prepara vetores seguros para os cálculos
        atr_safe = pd.Series(candles_alerta_contexto['atr'].values).replace(0, 1e-9).values
        atr_media_safe = pd.Series(candles_alerta_contexto['atr_media'].values).replace(0, 1e-9).values
        
        trades_potenciais['feature_rsi'] = candles_alerta_contexto['rsi'].values
        trades_potenciais['feature_adx'] = candles_alerta_contexto['adx'].values
        trades_potenciais['feature_explosao_vol'] = atr_safe / atr_media_safe
        
        sombra_superior = candles_alerta_contexto['high'].values - np.maximum(candles_alerta_contexto['open'].values, candles_alerta_contexto['close'].values)
        sombra_inferior = np.minimum(candles_alerta_contexto['open'].values, candles_alerta_contexto['close'].values) - candles_alerta_contexto['low'].values
        trades_potenciais['feature_forca_rejeicao'] = np.where(trades_potenciais['tipo'] == 'Sell', sombra_superior / atr_safe, sombra_inferior / atr_safe)
        
        trades_potenciais['feature_sessao'] = pd.to_datetime(alertas_validos['time_alerta']).dt.hour.apply(
            lambda h: 0 if 0 <= h < 8 else (1 if 8 <= h < 16 else 2)
        ).values

        trades_potenciais['feature_exaustao_curta'] = (candles_alerta_contexto['close'].values - candles_alerta_contexto['ema_curta'].values) / atr_safe
        trades_potenciais['feature_exaustao_longa'] = (candles_alerta_contexto['close'].values - candles_alerta_contexto['ema_longa'].values) / atr_safe

        # Limpa o DataFrame de quaisquer trades que não puderam ter todas as features calculadas
        return trades_potenciais.dropna(subset=[col for col in trades_potenciais.columns if col.startswith('feature_')])