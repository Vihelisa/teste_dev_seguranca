import pandas as pd
import pandas_ta as ta
# A interface pode ser removida se não for usada, mas a mantemos por boa prática de design
# from ..strategy_interface import StrategyInterface 

# class BaseStrategy(StrategyInterface):
class BaseStrategy: # Simplificado se a interface não estiver em uso ativo
    """
    Classe base V2.0 para estratégias, com cálculo de indicadores comuns e robustos.
    As estratégias individuais herdam desta classe para reutilizar a lógica.
    """

    @staticmethod
    def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Adiciona um conjunto padrão de indicadores técnicos, incluindo níveis de
        liquidez diários calculados corretamente.
        """
        df_featured = df.copy()

        # --- Indicadores Padrões ---
        ema_curta_periodo = params.get('EMA_Curta_Periodo', 21)
        ema_longa_periodo = params.get('EMA_Longa_Periodo', 200)
        atr_periodo = params.get('atr_period', 14)
        rsi_periodo = params.get('rsi_period', 14)

        df_featured['ema_curta'] = ta.ema(df_featured['close'], length=ema_curta_periodo)
        df_featured['ema_longa'] = ta.ema(df_featured['close'], length=ema_longa_periodo)
        df_featured['atr'] = ta.atr(df_featured['high'], df_featured['low'], df_featured['close'], length=atr_periodo)
        df_featured['rsi'] = ta.rsi(df_featured['close'], length=rsi_periodo)

        # --- [CORREÇÃO CRÍTICA] Cálculo dos Níveis de Liquidez do Dia Anterior ---
        df_featured['dia'] = pd.to_datetime(df_featured['time']).dt.date
        
        # 1. Agrupa por dia e encontra a máxima e a mínima de cada dia.
        daily_levels = df_featured.groupby('dia').agg(
            high_d1=('high', 'max'),
            low_d1=('low', 'min')
        )
        
        # 2. Usa .shift(1) para mover os valores para o dia seguinte.
        #    Agora, cada linha representa um dia e contém a máxima/mínima do dia anterior.
        daily_levels['nivel_liquidez_sup'] = daily_levels['high_d1'].shift(1)
        daily_levels['nivel_liquidez_inf'] = daily_levels['low_d1'].shift(1)
        
        # 3. Junta (merge) esta informação diária de volta ao DataFrame original.
        #    Isso mapeia a máxima/mínima do dia anterior para cada candle do dia atual.
        df_featured = pd.merge(df_featured, daily_levels[['nivel_liquidez_sup', 'nivel_liquidez_inf']], on='dia', how='left')
        
        # Remove a coluna 'dia' auxiliar se não for mais necessária
        # df_featured.drop(columns=['dia'], inplace=True)
        
        # Adiciona a Média Móvel do ATR, útil para normalização
        df_featured['atr_media_100'] = df_featured['atr'].rolling(window=100).mean()

        # Remove linhas com valores NaN resultantes dos cálculos de indicadores
        df_featured.dropna(inplace=True)
        
        return df_featured