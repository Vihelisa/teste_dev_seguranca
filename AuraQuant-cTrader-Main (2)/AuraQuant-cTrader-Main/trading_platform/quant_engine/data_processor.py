import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Union, Dict, Optional
# Importa nosso gerenciador de conexão e a flag de disponibilidade
from ..utils.mt5_connector import mt5_connection, MT5_AVAILABLE

# Configura o logger
logger = logging.getLogger(__name__)

# =============================================================================
#           FUNÇÕES INTERNAS (PRIVADAS)
# =============================================================================

def _prepare_single_asset_df(df_exec: pd.DataFrame, df_liq: pd.DataFrame) -> pd.DataFrame:
    """(PRIVADO) Processa e enriquece dados para um ativo único, alinhando timeframes."""
    df_exec['time'] = pd.to_datetime(df_exec['time'], unit='s')
    df_liq['time'] = pd.to_datetime(df_liq['time'], unit='s')
    df_exec.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    # Prepara os níveis de liquidez D1 antes do merge
    df_liq['nivel_liquidez_sup'] = df_liq['high'].shift(1)
    df_liq['nivel_liquidez_inf'] = df_liq['low'].shift(1)
    df_liq.dropna(subset=['nivel_liquidez_sup', 'nivel_liquidez_inf'], inplace=True)
    
    # Alinha os dois timeframes de forma eficiente
    df_final = pd.merge_asof(
        df_exec.sort_values('time'),
        df_liq[['time', 'nivel_liquidez_sup', 'nivel_liquidez_inf']].sort_values('time'),
        on='time',
        direction='backward'
    )
    df_final.dropna(inplace=True)
    return df_final

# =============================================================================
#           FUNÇÃO PÚBLICA PRINCIPAL
# =============================================================================

def prepare_data_for_assets(assets: list, dias: int = 365, account=None) -> Optional[Union[Dict[str, pd.DataFrame], pd.DataFrame]]:
    """
    Motor Universal de Coleta de Dados V4.1 (Portátil e Seguro).
    Usa o mt5_connector para gerenciar conexões e só executa se o MT5 estiver disponível.
    """
    if not MT5_AVAILABLE:
        logger.warning("[DATA_PROC_V4]: Biblioteca MetaTrader5 não disponível. Coleta de dados pulada.")
        return None

    logger.info(f"  [DATA_PROC_V4]: Iniciando coleta para os ativos: {assets}...")
    
    # [MELHORIA] Usa o mt5_connector para uma conexão segura e centralizada.
    # Opcionalmente, pode receber um objeto de conta para usar em conexões de usuário.
    # Se nenhuma conta for passada, ele pode tentar uma conexão padrão (se configurada).
    with mt5_connection(account) as mt5:
        if not mt5:
            logger.error("[DATA_PROC_V4]: Falha na conexão com o MT5. Verifique as credenciais e se o terminal está rodando.")
            return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=dias)
        timeframe_exec = mt5.TIMEFRAME_M15
        timeframe_liq = mt5.TIMEFRAME_D1
        
        # --- LÓGICA PARA PAIRS TRADING ---
        if len(assets) == 2:
            logger.info(f"    - Modo Pairs Trading detectado. Alinhando {assets[0]} e {assets[1]}...")
            
            df1_raw = pd.DataFrame(mt5.copy_rates_range(assets[0], timeframe_exec, start_date, end_date))
            df2_raw = pd.DataFrame(mt5.copy_rates_range(assets[1], timeframe_exec, start_date, end_date))
            
            if df1_raw.empty or df2_raw.empty:
                logger.warning(f"    - Dados insuficientes para um ou ambos os ativos no par {assets}.")
                return None

            cols_to_keep = ['time', 'open', 'high', 'low', 'close', 'tick_volume']
            df1 = df1_raw[cols_to_keep].copy(); df1['time'] = pd.to_datetime(df1['time'], unit='s')
            df2 = df2_raw[cols_to_keep].copy(); df2['time'] = pd.to_datetime(df2['time'], unit='s')
            
            # O `inner join` no índice de tempo garante a honestidade estatística.
            merged_df = pd.merge(df1.set_index('time'), df2.set_index('time'), left_index=True, right_index=True, how='inner', suffixes=('_1', '_2'))
            merged_df.dropna(inplace=True)
            
            logger.info(f"    - Dados de par alinhados. {len(merged_df)} candles finais.")
            return merged_df.reset_index()

        # --- LÓGICA PARA ATIVO ÚNICO OU PORTFÓLIO ---
        else:
            logger.info(f"    - Modo Ativo Único/Portfólio detectado...")
            portfolio_data = {}
            for ativo in assets:
                ativo_clean = ativo.strip()
                logger.info(f"    - Processando: {ativo_clean}")
                
                df_exec = pd.DataFrame(mt5.copy_rates_range(ativo_clean, timeframe_exec, start_date, end_date))
                df_liq = pd.DataFrame(mt5.copy_rates_range(ativo_clean, timeframe_liq, start_date, end_date))

                if df_exec.empty or df_liq.empty:
                    logger.warning(f"    - Dados insuficientes para {ativo_clean}. Ativo será pulado.");
                    continue
                    
                df_processed = _prepare_single_asset_df(df_exec, df_liq)
                if not df_processed.empty:
                    portfolio_data[ativo_clean] = df_processed
                    logger.info(f"    - Preparação concluída para {ativo_clean}. Total de {len(df_processed)} candles.")
            
            return portfolio_data if portfolio_data else None