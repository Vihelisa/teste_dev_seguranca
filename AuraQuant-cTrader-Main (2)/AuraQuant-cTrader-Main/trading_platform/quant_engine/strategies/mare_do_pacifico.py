import pandas as pd
import numpy as np
import pandas_ta as ta
from statsmodels.tsa.stattools import coint

# --- FUNÇÃO AUXILIAR OTIMIZADA PARA CÁLCULO DE COINTEGRAÇÃO ROLANTE ---
# Esta função pode ser movida para um arquivo de utilitários comum no futuro.
def rolling_coint(series_tuple, trend='c'):
    """Aplica o teste de cointegração em duas séries."""
    series1, series2 = series_tuple
    if series1.var() < 1e-10 or series2.var() < 1e-10:
        return np.nan
    _, p_value, _ = coint(series1, series2, trend=trend)
    return p_value

class StrategyContract:
    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calcula os indicadores para a estratégia Maré do Pacífico de forma vetorizada.
        """
        df_featured = df.copy()
        df_featured.columns = [col.lower().replace(df.columns[0].lower(), '1').replace(df.columns[1].lower(), '2') for col in df_featured.columns]

        # Extração de parâmetros específicos para esta estratégia
        coint_period = params.get('coint_period', 120)
        zscore_period = params.get('zscore_period', 40)
        
        # --- [OTIMIZAÇÃO] Cálculo de Cointegração Vetorizado ---
        p_values = df_featured[['close_1', 'close_2']].rolling(window=coint_period).apply(
            rolling_coint, 
            raw=False
        )
        df_featured['p_value_coint'] = p_values.ffill()

        # --- Cálculo do Z-Score e seus componentes ---
        df_featured['spread_ratio'] = df_featured['close_1'] / df_featured['close_2']
        spread_ma = df_featured['spread_ratio'].rolling(window=zscore_period).mean()
        spread_std = df_featured['spread_ratio'].rolling(window=zscore_period).std()
        
        df_featured['zscore'] = (df_featured['spread_ratio'] - spread_ma) / spread_std
        df_featured['spread_std'] = spread_std

        # --- Indicadores Adicionais ---
        df_featured['zscore_momentum'] = df_featured['zscore'].diff(5)
        df_featured['atr_1'] = ta.atr(df_featured['high_1'], df_featured['low_1'], df_featured['close_1'], length=14)
        df_featured['atr_2'] = ta.atr(df_featured['high_2'], df_featured['low_2'], df_featured['close_2'], length=14)

        df_featured.dropna(inplace=True)
        return df_featured.reset_index()

    @staticmethod
    def generate_alerts(df_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Gera alertas com base nos parâmetros específicos da Maré do Pacífico."""
        df = df_featured.copy()
        
        # Extração de parâmetros com os padrões desta estratégia
        z_entry_threshold = params.get('z_entry_threshold', 1.9)
        coint_p_value_threshold = params.get('coint_p_value_threshold', 0.05)
        
        cond_z_cross = (df['zscore'].abs() > z_entry_threshold) & (df['zscore'].abs().shift(1) <= z_entry_threshold)
        cond_coint_valid = df['p_value_coint'] < coint_p_value_threshold
        
        alertas = df[cond_z_cross & cond_coint_valid].copy()
        alertas['tipo'] = np.where(alertas['zscore'] > 0, 'Sell', 'Buy')
        
        return alertas.rename(columns={'time': 'time_alerta'})
    
    @staticmethod
    def define_decision_points_and_features(alertas_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
        """Prepara o DataFrame final para o ml_trainer (lógica idêntica a outras estratégias de pares)."""
        if alertas_df.empty:
            return pd.DataFrame()
        
        trades_potenciais = pd.merge_asof(
            alertas_df.sort_values('time_alerta'),
            df_mercado_featured.sort_values('time'),
            left_on='time_alerta',
            right_on='time',
            direction='forward'
        )
        trades_potenciais.dropna(subset=['time'], inplace=True)
        
        trades_potenciais['time_entrada'] = trades_potenciais['time']
        trades_potenciais['preco_entrada_1'] = trades_potenciais['open_1']
        trades_potenciais['preco_entrada_2'] = trades_potenciais['open_2']
        trades_potenciais['zscore_entrada'] = trades_potenciais['zscore_x']
        
        # Mapeamento explícito para features
        trades_potenciais['feature_zscore'] = trades_potenciais['zscore_x']
        trades_potenciais['feature_p_value_coint'] = trades_potenciais['p_value_coint_x']
        trades_potenciais['feature_spread_volatility'] = trades_potenciais['spread_std_x']
        trades_potenciais['feature_zscore_momentum'] = trades_potenciais['zscore_momentum_x']
        
        atr2_safe = trades_potenciais['atr_2_x'].replace(0, np.nan)
        trades_potenciais['feature_atr_ratio'] = trades_potenciais['atr_1_x'] / atr2_safe

        feature_cols = [col for col in trades_potenciais.columns if col.startswith('feature_')]
        return trades_potenciais.dropna(subset=feature_cols)