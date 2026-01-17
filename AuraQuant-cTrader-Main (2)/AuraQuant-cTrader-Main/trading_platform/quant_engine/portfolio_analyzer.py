# trading_platform/quant_engine/portfolio_analyzer.py
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
#           FERRAMENTA 1: O SIMULADOR (PARA ESTRATÉGIAS COM REGRAS FIXAS)
# =============================================================================

def label_trades_with_fixed_targets(trades_potenciais_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Função Oráculo-Simulador V13.1 (Simulador).
    Simula CADA trade com alvos e stops pré-definidos (pela estratégia)
    para obter o P/L Ratio REAL, baseado em preço.
    """
    print(f"    [ANALYZER_V13.1]: Iniciando simulação com alvos fixos...")
    trades_com_resultados = trades_potenciais_df.copy()
    
    pnl_ratio_list = []
    
    dados_mercado_idx = df_mercado_featured.set_index('time')
    is_pairs_trading = 'zscore_entrada' in trades_com_resultados.columns

    for _, trade in trades_com_resultados.iterrows():
        entry_time = trade['time_entrada']
        dados_futuros = dados_mercado_idx.loc[dados_mercado_idx.index > entry_time].head(params.get('Max_Candles_Hold', 96))
        
        pnl_ratio = -1.0
        
        if dados_futuros.empty:
            pnl_ratio_list.append(pnl_ratio); continue

        if is_pairs_trading:
            entry_price_1, entry_price_2 = trade['preco_entrada_1'], trade['preco_entrada_2']
            z_entry, z_stop, z_target = trade['zscore_entrada'], params.get('z_stop_loss', 3.5), params.get('z_exit_target', 0.0)
            ponto_de_saida = "Timeout"
            vela_de_saida = None
            
            for _, vela in dados_futuros.iterrows():
                if (trade['tipo'] == 'Buy' and vela['zscore'] >= z_target) or (trade['tipo'] == 'Sell' and vela['zscore'] <= z_target):
                    ponto_de_saida, vela_de_saida = "Alvo", vela; break
                if (trade['tipo'] == 'Buy' and vela['zscore'] < -z_stop) or (trade['tipo'] == 'Sell' and vela['zscore'] > z_stop):
                    ponto_de_saida, vela_de_saida = "Stop Loss", vela; break
            
            if ponto_de_saida == "Timeout": vela_de_saida = dados_futuros.iloc[-1]
            
            exit_price_1, exit_price_2 = vela_de_saida['close_1'], vela_de_saida['close_2']
            pnl_perna_1 = exit_price_1 - entry_price_1
            pnl_perna_2 = exit_price_2 - entry_price_2
            lucro_em_preco = (pnl_perna_1 - pnl_perna_2) if trade['tipo'] == 'Buy' else (pnl_perna_2 - pnl_perna_1)
            
            spread_std = trade.get('spread_std', 0.001)
            z_dist_ao_stop = abs(z_stop - abs(z_entry))
            risco_em_preco_estimado = z_dist_ao_stop * spread_std * entry_price_2
            if risco_em_preco_estimado < 1e-9: risco_em_preco_estimado = 1e-9
            pnl_ratio = lucro_em_preco / risco_em_preco_estimado
        
        else: # Estratégias de ativo único
            entry_price, sl_base, atr, rr = trade['preco_entrada'], trade['stop_loss_base'], trade['atr_no_alerta'], trade.get('Risco_Retorno', 1.5)
            sl_dinamico = sl_base + (atr * params.get('Stop_Loss_ATR_Mult', 1.0)) if trade['tipo'] == 'Sell' else sl_base - (atr * params.get('Stop_Loss_ATR_Mult', 1.0))
            dist_sl = abs(entry_price - sl_dinamico)

            if dist_sl > 1e-9:
                take_profit = entry_price - (dist_sl * rr) if trade['tipo'] == 'Sell' else entry_price + (dist_sl * rr)
                ponto_de_saida = "Timeout"
                for _, vela in dados_futuros.iterrows():
                    if (trade['tipo'] == 'Sell' and vela['high'] >= sl_dinamico) or (trade['tipo'] == 'Buy' and vela['low'] <= sl_dinamico):
                        ponto_de_saida = "Stop Loss"; pnl_ratio = -1.0; break
                    if (trade['tipo'] == 'Sell' and vela['low'] <= take_profit) or (trade['tipo'] == 'Buy' and vela['high'] >= take_profit):
                        ponto_de_saida = "Alvo"; pnl_ratio = rr; break
                if ponto_de_saida == "Timeout":
                    pnl_em_preco = dados_futuros.iloc[-1]['close'] - entry_price
                    if trade['tipo'] == 'Sell': pnl_em_preco *= -1
                    pnl_ratio = pnl_em_preco / dist_sl
        
        pnl_ratio_list.append(pnl_ratio)
            
    trades_com_resultados['pnl_ratio'] = pnl_ratio_list
    trades_com_resultados['target'] = np.where(trades_com_resultados['pnl_ratio'] > 0, 1, 0)
    print(f"    [ANALYZER_V13.1]: Rotulagem completa. Taxa de acerto base: {trades_com_resultados['target'].mean():.2%}")
    return trades_com_resultados

# =============================================================================
#           FERRAMENTA 2: O MESTRE ESTRATEGISTA (PARA IA DINÂMICA)
# =============================================================================

def discover_trade_potential_for_ai(trades_potenciais_df: pd.DataFrame, df_mercado_featured: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Função Oráculo V13.2 (A Estrategista).
    Analisa o futuro de cada trade para DESCOBRIR o drawdown e o lucro máximos.
    """
    print(f"    [ANALYZER_V13.2]: Descobrindo potencial de trades para IA Estrategista...")
    trades_rotulados = trades_potenciais_df.copy()
    target_max_drawdown_list, target_max_profit_list = [], []
    dados_mercado_idx = df_mercado_featured.set_index('time')
    is_pairs_trading = 'zscore_entrada' in trades_rotulados.columns

    for _, trade in trades_rotulados.iterrows():
        entry_time = trade['time_entrada']
        dados_futuros = dados_mercado_idx.loc[dados_mercado_idx.index > entry_time].head(params.get('Max_Candles_Hold', 96))
        
        if dados_futuros.empty:
            dd_val = trade.get('zscore_entrada', 0) if is_pairs_trading else 0
            profit_val = trade.get('zscore_entrada', 0) if is_pairs_trading else 0
            target_max_drawdown_list.append(dd_val); target_max_profit_list.append(profit_val)
            continue

        if is_pairs_trading:
            if trade['tipo'] == 'Buy':
                target_max_drawdown_list.append(dados_futuros['zscore'].min())
                target_max_profit_list.append(dados_futuros['zscore'].max())
            else: # Sell
                target_max_drawdown_list.append(dados_futuros['zscore'].max())
                target_max_profit_list.append(dados_futuros['zscore'].min())
        else:
            entry_price, sl_base, atr = trade['preco_entrada'], trade['stop_loss_base'], trade['atr_no_alerta']
            sl_dinamico = sl_base + (atr * params.get('Stop_Loss_ATR_Mult', 1.0)) if trade['tipo'] == 'Sell' else sl_base - (atr * params.get('Stop_Loss_ATR_Mult', 1.0))
            dist_sl = abs(entry_price - sl_dinamico)
            if dist_sl < 1e-9: dist_sl = 1e-9
            
            pnl_em_preco_series = (dados_futuros['close'] - entry_price)
            if trade['tipo'] == 'Sell': pnl_em_preco_series *= -1
            
            pnl_ratio_series = pnl_em_preco_series / dist_sl
            target_max_drawdown_list.append(pnl_ratio_series.min())
            target_max_profit_list.append(pnl_ratio_series.max())

    trades_rotulados['target_max_drawdown'] = target_max_drawdown_list
    trades_rotulados['target_max_profit'] = target_max_profit_list
    trades_rotulados['target'] = np.where(np.array(target_max_profit_list) > 0, 1, 0)
    trades_rotulados['pnl_ratio'] = np.where(trades_rotulados['target'] == 1, trades_rotulados['target_max_profit'], -1.0)

    print(f"    [ANALYZER_V13.2]: Descoberta de potencial completa.")
    return trades_rotulados

# =============================================================================
#           FUNÇÃO DE SIMULAÇÃO FINANCEIRA (COMPLETA E CORRIGIDA)
# =============================================================================
def run_financial_simulation(all_trades_df: pd.DataFrame, capital_inicial: float, dias_backtest: int) -> dict:
    if all_trades_df.empty: return {}
    df = all_trades_df.sort_values('time_entrada').reset_index(drop=True)
    capital, equity_curve = capital_inicial, [capital_inicial]
    risco_por_trade_pct = 0.015
    returns_list = []
    
    for _, trade in df.iterrows():
        risco_monetario = capital * risco_por_trade_pct
        retorno_real = risco_monetario * trade['pnl_ratio']
        capital += retorno_real
        if capital < 0: capital = 0
        equity_curve.append(capital)
        returns_list.append(retorno_real)
        
    df['Return'] = returns_list
    
    # --- ### O CÓDIGO QUE FALTAVA ### ---
    capital_series = pd.Series(equity_curve)
    peak = capital_series.cummax()
    drawdown = (capital_series - peak) / peak if peak.all() > 0 else pd.Series([0.0])
    max_dd = abs(drawdown.min()) * 100 if not drawdown.empty else 0.0
    capital_final = capital_series.iloc[-1]
    net_profit = capital_final - capital_inicial
    total_trades = len(df)
    meses_no_backtest = dias_backtest / 30.44 if dias_backtest > 0 else 1.0
    trades_por_mes = total_trades / meses_no_backtest
    win_rate = (df['Return'] > 0).mean() * 100 if total_trades > 0 else 0.0
    gross_profit = df['Return'][df['Return'] > 0].sum()
    gross_loss = abs(df['Return'][df['Return'] < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    media_ganho = df['Return'][df['Return'] > 0].mean() if (df['Return'] > 0).any() else 0.0
    media_perda = abs(df['Return'][df['Return'] < 0].mean()) if (df['Return'] < 0).any() else 0.0
    df['Win'] = (df['Return'] > 0).astype(int)
    df['Streak'] = (df['Win'] != df['Win'].shift()).cumsum()
    streaks = df.groupby(['Win', 'Streak']).size()
    max_win_streak = streaks.get(1, pd.Series([0])).max()
    max_loss_streak = streaks.get(0, pd.Series([0])).max()
    start_date = pd.to_datetime(df['time_entrada'].iloc[0]) if total_trades > 0 else pd.NaT

    stats = {
        "Capital Inicial": capital_inicial, "Capital Final": capital_final,
        "Lucro Líquido ($)": net_profit, "Retorno Total [%]": (net_profit / capital_inicial) * 100 if capital_inicial > 0 else 0.0,
        "Nº de Trades Total": total_trades, "Média de Trades/Mês": trades_por_mes,
        "Taxa de Acerto (Win Rate) [%]": win_rate, "Fator de Lucro": profit_factor,
        "Drawdown Máximo [%]": max_dd, "Média de Ganho ($)": media_ganho,
        "Média de Perda ($)": media_perda, "Maior Sequência de Ganhos": int(max_win_streak),
        "Maior Sequência de Perdas": int(max_loss_streak),
        "Start": start_date.isoformat() if pd.notna(start_date) else None, 
        "_equity_curve": {"Equity": equity_curve}
    }
    
    final_stats = {}
    for key, value in stats.items():
        if isinstance(value, (float, np.floating)): final_stats[key] = round(value, 2)
        elif isinstance(value, (int, np.integer)): final_stats[key] = int(value)
        elif value == float('inf'): final_stats[key] = 999.0
        else: final_stats[key] = value
            
    return final_stats

# =============================================================================
#           EXPORTAÇÃO E COMPATIBILIDADE
# =============================================================================

label_trades = label_trades_with_fixed_targets