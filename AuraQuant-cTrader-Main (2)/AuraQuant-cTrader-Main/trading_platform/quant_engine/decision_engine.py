#core.py
import logging
import pandas as pd
from django.conf import settings
from django.core.cache import cache

from .. import trader_engine
from . import data_processor

logger = logging.getLogger(__name__)

def analyze_and_trade(instance, StrategyContract, saved_ia, log_prefix):
    """
    Core logic for analyzing a strategy signal and potentially executing a trade.
    Moved from tasks.py for better separation of concerns.
    """
    strategy_obj = instance.strategy
    model, features = saved_ia['model'], saved_ia['features']
    limiar_otimo = strategy_obj.ml_threshold # Use the configurable threshold from the model

    assets = [asset.strip() for asset in strategy_obj.assets.split(',')]

    market_data = data_processor.prepare_data_for_assets(assets, dias=60, account=instance.trading_account)
    if market_data is None:
        logger.info(f"{log_prefix} -> Dados de mercado insuficientes."); return

    df_para_analise = None
    if strategy_obj.strategy_type == 'PAIRS':
        if not market_data.empty:
            df_para_analise = market_data
        params_key = ','.join(assets)
    else: # SINGLE_PORTFOLIO
        asset_principal = assets[0]
        if isinstance(market_data, dict) and market_data.get(asset_principal) is not None and not market_data[asset_principal].empty:
            df_para_analise = market_data[asset_principal]
        params_key = asset_principal

    if df_para_analise is None:
        logger.info(f"{log_prefix} -> DataFrame para análise está vazio ou nulo."); return

    params = strategy_obj.portfolio_composition.get(params_key, {})
    df_featured = StrategyContract.add_indicators(df_para_analise, params)

    alert_candidate = df_featured.tail(1)
    alerts = StrategyContract.generate_alerts(alert_candidate, params)
    if alerts.empty:
        logger.info(f"{log_prefix} -> Nenhuma condição de alerta encontrada no último candle."); return

    logger.info(f"{log_prefix} ALERTA GERADO! Tipo: {alerts.iloc[0].get('tipo', 'N/A')} @ {alerts.iloc[0]['time_alerta']}.")

    potential_trade = StrategyContract.define_decision_points_and_features(alerts, df_featured, params)
    if potential_trade.empty: return

    sinal_timestamp = pd.to_datetime(potential_trade.iloc[0]['time_entrada']).timestamp()
    lock_key = f"lock_signal_{instance.id}_{int(sinal_timestamp)}"
    if not cache.add(lock_key, 'locked', timeout=settings.SIGNAL_LOCK_TIMEOUT):
        logger.info(f"{log_prefix} Sinal para candle {sinal_timestamp} já processado recentemente. Ignorando.")
        return

    trades_to_predict_df = potential_trade[features]
    predictions_proba = model.predict_proba(trades_to_predict_df)[:, 1]
    potential_trade['prediction_proba'] = predictions_proba

    best_decision = potential_trade.loc[potential_trade['prediction_proba'].idxmax()]

    if best_decision['prediction_proba'] >= limiar_otimo:
        logger.info(f"{log_prefix} APROVADO! Prob. ({best_decision['prediction_proba']:.2%}) >= Limiar ({limiar_otimo:.2f}).")

        trade_details = best_decision.to_dict()
        trade_details['trade_type_str'] = trade_details.pop('tipo')

        trade_request = {
            'symbol': assets[0] if strategy_obj.strategy_type != 'PAIRS' else assets,
            'comment': f"BS-{strategy_obj.id}-{instance.id}",
            **trade_details
        }

        trader_engine.execute_trade_from_signal(instance, trade_request)
    else:
        logger.info(f"{log_prefix} REPROVADO. Prob. ({best_decision['prediction_proba']:.2%}) < Limiar ({limiar_otimo:.2f}).")


def get_trade_signal(instance, StrategyContract, saved_ia, log_prefix):
    """
    Core logic for analyzing a strategy signal. Returns a trade request dictionary if a trade is approved.
    Esta é uma versão modificada de analyze_and_trade para o motor FIX.
    """
    return analyze_and_get_signal(instance, StrategyContract, saved_ia, log_prefix)

def analyze_and_get_signal(instance, StrategyContract, saved_ia, log_prefix):
    """
    The definitive Decision Engine logic (previously get_trade_signal).
    """
    strategy_obj = instance.strategy
    model, features = saved_ia['model'], saved_ia['features']
    limiar_otimo = strategy_obj.ml_threshold

    assets = [asset.strip() for asset in strategy_obj.assets.split(',')]

    # A obtenção de dados históricos ainda depende do pipeline existente (MT5).
    # O preço em tempo real para execução será obtido do feed FIX na tarefa.
    market_data = data_processor.prepare_data_for_assets(assets, dias=60, account=instance.trading_account)
    if market_data is None:
        logger.info(f"{log_prefix} -> Dados de mercado insuficientes para análise."); return None

    df_para_analise = None
    if strategy_obj.strategy_type == 'PAIRS':
        if not market_data.empty:
            df_para_analise = market_data
        params_key = ','.join(assets)
    else: # SINGLE_PORTFOLIO
        asset_principal = assets[0]
        if isinstance(market_data, dict) and market_data.get(asset_principal) is not None and not market_data[asset_principal].empty:
            df_para_analise = market_data[asset_principal]
        params_key = asset_principal

    if df_para_analise is None:
        logger.info(f"{log_prefix} -> DataFrame para análise está vazio ou nulo."); return None

    params = strategy_obj.portfolio_composition.get(params_key, {})
    df_featured = StrategyContract.add_indicators(df_para_analise, params)

    alert_candidate = df_featured.tail(1)
    alerts = StrategyContract.generate_alerts(alert_candidate, params)
    if alerts.empty:
        logger.info(f"{log_prefix} -> Nenhuma condição de alerta encontrada."); return None

    logger.info(f"{log_prefix} ALERTA GERADO! Tipo: {alerts.iloc[0].get('tipo', 'N/A')} @ {alerts.iloc[0]['time_alerta']}.")

    potential_trade = StrategyContract.define_decision_points_and_features(alerts, df_featured, params)
    if potential_trade.empty:
        return None

    sinal_timestamp = pd.to_datetime(potential_trade.iloc[0]['time_entrada']).timestamp()
    lock_key = f"lock_signal_{instance.id}_{int(sinal_timestamp)}"
    if not cache.add(lock_key, 'locked', timeout=settings.SIGNAL_LOCK_TIMEOUT):
        logger.info(f"{log_prefix} Sinal para candle {sinal_timestamp} já processado. Ignorando.")
        return None

    trades_to_predict_df = potential_trade[features]
    predictions_proba = model.predict_proba(trades_to_predict_df)[:, 1]
    potential_trade['prediction_proba'] = predictions_proba

    best_decision = potential_trade.loc[potential_trade['prediction_proba'].idxmax()]

    if best_decision['prediction_proba'] >= limiar_otimo:
        logger.info(f"{log_prefix} SINAL APROVADO! Prob. ({best_decision['prediction_proba']:.2%}) >= Limiar ({limiar_otimo:.2f}).")

        trade_details = best_decision.to_dict()
        trade_details['trade_type_str'] = trade_details.pop('tipo')

        # [DECISION ENGINE UPDATE] Calculates dynamic quantity if needed, or passes info for tasks.py to calculate.
        # Since risk calculation logic is in tasks.py (for dynamic balance access), we return the signal.
        # However, if we want 'quantity_in_lots' to be pre-calculated here, we'd need the balance.
        # For now, we return 'quantity_in_lots' as None or based on fixed lot if available,
        # but let tasks.py handle the final sizing based on the risk mode.
        # Actually, the new tasks.py expects 'quantity_in_lots' in the return.
        # But tasks.py *calculates* it if it's not there?
        # Let's look at the provided tasks.py code.
        # It calls `analyze_and_get_signal`.
        # Then: `success = fix_connector.send_market_order(..., quantity_in_lots=trade_request['quantity_in_lots'])`
        # So `analyze_and_get_signal` MUST return `quantity_in_lots`.

        # Calculating lots here:
        quantity = float(instance.lot_size)
        if instance.risk_mode == 'DYNAMIC':
             # Need current balance. 'instance' has 'trading_account', but is it up to date?
             # tasks.py refreshes it. Here we might use the one on instance.
             # If we want to be safe, we can use the one from instance if available.
             try:
                 current_balance = float(instance.trading_account.current_balance)
                 if current_balance > 0:
                     risco_monetario = current_balance * (instance.risk_percent / 100.0)
                     quantity = max(0.01, round(risco_monetario / 1000.0, 2))
             except:
                 pass # Fallback to fixed lot

        trade_request = {
            'symbol_id': assets[0] if strategy_obj.strategy_type != 'PAIRS' else assets, # tasks.py uses symbol_id
            'comment': f"BS-{strategy_obj.id}-{instance.id}",
            'side': trade_details['trade_type_str'],
            'quantity_in_lots': quantity,
            **trade_details
        }
        return trade_request
    else:
        logger.info(f"{log_prefix} SINAL REPROVADO. Prob. ({best_decision['prediction_proba']:.2%}) < Limiar ({limiar_otimo:.2f}).")
        return None
