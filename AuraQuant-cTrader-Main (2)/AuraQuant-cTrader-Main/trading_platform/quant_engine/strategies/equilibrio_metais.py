import pandas as pd
import numpy as np
import pandas_ta as ta
from statsmodels.tsa.stattools import coint

class StrategyContract:
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calcula os indicadores de cointegração e z-score de forma vetorizada e eficiente.
        """
        df_featured = df.copy()
        # Garante que os nomes das colunas estejam em minúsculas para consistência.
        df_featured.columns = [col.lower().replace(df.columns[0].lower(), '1').replace(df.columns[1].lower(), '2') for col in df_featured.columns]

        # Extração de parâmetros com valores padrão
        coint_period = params.get('coint_period', 252)
        zscore_period = params.get('zscore_period', 60)
        
        # --- Cálculo de Cointegração Rolante (Implementação Corrigida) ---
        # A abordagem anterior com .rolling().apply() estava incorreta, pois a função
        # era chamada para cada coluna individualmente. A abordagem correta e segura,
        # embora mais lenta, é iterar e aplicar o teste na janela de ambos os ativos.
        p_values = [np.nan] * len(df_featured) # Pré-aloca a lista com NaNs
        
        # Itera apenas a partir do ponto em que temos uma janela completa de dados.
        for i in range(coint_period, len(df_featured)):
            # Extrai as janelas de dados para os dois ativos.
            window_close_1 = df_featured['close_1'].iloc[i - coint_period : i]
            window_close_2 = df_featured['close_2'].iloc[i - coint_period : i]
            
            # Checagem de segurança para evitar erro no teste estatístico
            if window_close_1.var() < 1e-10 or window_close_2.var() < 1e-10:
                p_values[i] = np.nan
            else:
                # Aplica o teste de cointegração na janela atual
                _, p_value, _ = coint(window_close_1, window_close_2, trend='c')
                p_values[i] = p_value
        
        df_featured['p_value_coint'] = p_values
        df_featured['p_value_coint'].ffill(inplace=True) # Preenche para frente para garantir que não haja NaNs

        # --- Cálculo do Z-Score e seus componentes ---
        df_featured['spread_ratio'] = df_featured['close_1'] / df_featured['close_2']
        spread_ma = df_featured['spread_ratio'].rolling(window=zscore_period).mean()
        spread_std = df_featured['spread_ratio'].rolling(window=zscore_period).std()
        
        df_featured['zscore'] = (df_featured['spread_ratio'] - spread_ma) / spread_std
        df_featured['spread_std'] = spread_std # Mantido para usar como feature

        # --- Indicadores Adicionais ---
        df_featured['zscore_momentum'] = df_featured['zscore'].diff(5)
        df_featured['atr_1'] = ta.atr(df_featured['high_1'], df_featured['low_1'], df_featured['close_1'], length=14)
        df_featured['atr_2'] = ta.atr(df_featured['high_2'], df_featured['low_2'], df_featured['close_2'], length=14)

        df_featured.dropna(inplace=True)
        return df_featured.reset_index()

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Gera alertas quando o z-score cruza um limiar e a cointegração é válida."""
        df = df_featured.copy()
        
        # Extração de parâmetros
        z_entry_threshold = params.get('z_entry_threshold', 2.0)
        coint_p_value_threshold = params.get('coint_p_value_threshold', 0.05)
        
        # Condições para o alerta (vetorizadas)
        cond_z_cross = (df['zscore'].abs() > z_entry_threshold) & (df['zscore'].abs().shift(1) <= z_entry_threshold)
        cond_coint_valid = df['p_value_coint'] < coint_p_value_threshold
        
        alertas = df[cond_z_cross & cond_coint_valid].copy()
        
        # Define o tipo de operação com base no sinal do z-score
        alertas['tipo'] = np.where(alertas['zscore'] > 0, 'Sell', 'Buy')
        
        return alertas.rename(columns={'time': 'time_alerta'})

    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Prepara o DataFrame final para o ml_trainer com as features necessárias."""
        if alertas_df.empty:
            return pd.DataFrame()
        
        # A lógica para encontrar candles de entrada é mantida, mas pode ser simplificada no futuro.
        # Por enquanto, a sua lógica é funcional.
        # Apenas garantimos que os dados necessários são passados adiante.
        trades_potenciais = alertas_df.copy()
        
        # Junta os dados de alerta com os dados do mercado para obter os preços de entrada
        # Usamos merge_asof para encontrar o próximo candle de mercado após cada alerta.
        trades_potenciais = pd.merge_asof(
            trades_potenciais.sort_values('time_alerta'),
            df_mercado_featured.sort_values('time'),
            left_on='time_alerta',
            right_on='time',
            direction='forward' # Pega o próximo candle
        )
        trades_potenciais.dropna(subset=['time'], inplace=True)
        
        trades_potenciais['time_entrada'] = trades_potenciais['time']
        trades_potenciais['preco_entrada_1'] = trades_potenciais['open_1']
        trades_potenciais['preco_entrada_2'] = trades_potenciais['open_2']
        trades_potenciais['zscore_entrada'] = trades_potenciais['zscore_x'] # z-score no momento do alerta
        
        # Mapeamento explícito para features
        trades_potenciais['feature_zscore'] = trades_potenciais['zscore_x']
        trades_potenciais['feature_p_value_coint'] = trades_potenciais['p_value_coint_x']
        trades_potenciais['feature_spread_volatility'] = trades_potenciais['spread_std_x']
        trades_potenciais['feature_zscore_momentum'] = trades_potenciais['zscore_momentum_x']
        
        # Calcula a razão dos ATRs de forma segura (evitando divisão por zero)
        atr2_safe = trades_potenciais['atr_2_x'].replace(0, np.nan)
        trades_potenciais['feature_atr_ratio'] = trades_potenciais['atr_1_x'] / atr2_safe

        # Limpa qualquer linha que não tenha todas as features
        feature_cols = [col for col in trades_potenciais.columns if col.startswith('feature_')]
        return trades_potenciais.dropna(subset=feature_cols)