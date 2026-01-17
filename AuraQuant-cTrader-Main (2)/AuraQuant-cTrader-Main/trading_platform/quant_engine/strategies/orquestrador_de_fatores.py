# trading_platform/quant_engine/strategies/orquestrador_de_fatores.py
import pandas as pd
import pandas_ta as ta
import numpy as np

class StrategyContract:
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calcula um painel de fatores ("features") que descrevem o estado
        do mercado de forma quantitativa.
        """
        df_factors = df.copy()
        
        # Fator de Momentum (Taxa de Variação)
        df_factors['feature_momentum'] = ta.roc(df_factors['close'], length=params.get('roc_period', 21))
        
        # Fator de Reversão à Média (Índice de Força Relativa)
        df_factors['feature_mean_reversion'] = ta.rsi(df_factors['close'], length=params.get('rsi_period', 14))
        
        # Fator de Baixa Volatilidade (ATR Normalizado pelo Preço)
        atr = ta.atr(df_factors['high'], df_factors['low'], df_factors['close'], length=params.get('atr_period', 14))
        # Adiciona a coluna ATR base para uso posterior
        df_factors['atr'] = atr
        df_factors['feature_low_volatility'] = atr / df_factors['close']
        
        # Fator de Qualidade/Força da Tendência (ADX)
        adx_indicator = ta.adx(df_factors['high'], df_factors['low'], df_factors['close'], length=params.get('adx_period', 14))
        if adx_indicator is not None and not adx_indicator.empty:
            df_factors['feature_trend_quality'] = adx_indicator[f'ADX_14']
        else:
            df_factors['feature_trend_quality'] = 0.0 # Valor neutro se não puder ser calculado
        
        df_factors.dropna(inplace=True)
        return df_factors

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Gera um "alerta de reavaliação" em intervalos regulares.
        NÃO há lógica de trading aqui, apenas um timer para a IA agir.
        """
        recalc_interval = params.get('recalc_interval', 6)
        
        # ### CORREÇÃO DO BUG DE LOOKAHEAD BIAS ###
        # Selecionamos os candles em intervalos regulares e, crucialmente,
        # renomeamos a coluna 'time' para 'time_alerta'.
        # O motor de backtest usará o 'open' do candle SEGUINTE para a entrada.
        # Isso garante que a IA tome a decisão com base nos dados do fechamento
        # do candle de alerta, e a operação ocorra no futuro, sem viés.
        alertas = df_featured.iloc[::recalc_interval, :].copy()
        return alertas.rename(columns={'time': 'time_alerta'})
        # ### FIM DA CORREÇÃO ###

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Para cada alerta, cria dois "cenários hipotéticos" (Compra e Venda)
        para a IA avaliar, cumprindo o contrato de dados do pipeline.
        """
        if alertas_df.empty:
            return pd.DataFrame()

        # O 'alertas_df' já contém todas as features que precisamos.
        
        # Cria os dois cenários: um para Compra e outro para Venda.
        trades_compra = alertas_df.copy(); trades_compra['tipo'] = 'Buy'
        trades_venda = alertas_df.copy(); trades_venda['tipo'] = 'Sell'
        trades_potenciais = pd.concat([trades_compra, trades_venda], ignore_index=True)
        
        # ### CORREÇÃO DO CONTRATO DE DADOS ###
        # Adiciona os campos essenciais que o `portfolio_analyzer` espera.
        # A entrada ocorre no 'time_alerta' porque a decisão é para o candle seguinte.
        trades_potenciais['time_entrada'] = trades_potenciais['time_alerta']
        trades_potenciais['preco_entrada'] = trades_potenciais['open']
        
        # O Stop Loss é definido com base na máxima/mínima do candle de alerta.
        trades_potenciais['stop_loss_base'] = np.where(
            trades_potenciais['tipo'] == 'Buy', 
            trades_potenciais['low'], 
            trades_potenciais['high']
        )
        trades_potenciais['atr_no_alerta'] = trades_potenciais['atr']
        
        # A estratégia CUMPRE o contrato ao fornecer o Risco/Retorno.
        trades_potenciais['Risco_Retorno'] = params.get('Risco_Retorno', 1.5)
        # ### FIM DA CORREÇÃO ###
        
        # As colunas de fatores já estão nomeadas como 'feature_*' e serão
        # automaticamente selecionadas pelo `ml_trainer`.
        return trades_potenciais