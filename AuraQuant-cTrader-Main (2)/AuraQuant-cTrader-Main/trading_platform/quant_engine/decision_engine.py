#core.py
import logging
import pandas as pd

from django.conf import settings
from django.core.cache import cache
from decimal import Decimal

from .. import trader_engine
from . import data_processor

# Trading constants
MIN_LOT_SIZE = Decimal('0.01')
MAX_LOT_SIZE = Decimal('100.0')
DEFAULT_VALUE_PER_LOT = Decimal('10.0')  # USD per pip for 1 standard lot
FALLBACK_DIVISOR = Decimal('1000.0')

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

        # Tamanho de lote padrão (fixo)
        fixed_lot_size = Decimal(str(instance.lot_size))
        final_lot_size = fixed_lot_size  # Valor inicial/fallback

        if instance.risk_mode == 'DYNAMIC':
            try:
                current_balance = Decimal(str(current_balance))
                # Obter saldo da conta de trading
                #É necessário definir o account para que o current_balance possa existir do jeito antigo ele nao existia
                account = instance.trading_account
                if hasattr(account, 'current_balance'):
                    current_balance = Decimal(str(account.current_balance))
                elif hasattr(account, 'balance'):
                    current_balance = Decimal(str(account.balance))
                else:
                    current_balance = Decimal('0')
                    logger.warning(f"{log_prefix} Não foi possível obter saldo da conta.")

                risk_percent = Decimal(str(instance.risk_percent))

                if current_balance > 0:
                    # Calcular risco monetário
                    risco_monetario = current_balance * (risk_percent / Decimal('100.0'))
                    # Obter preços para cálculo de lote
                    entry_price = Decimal(str(trade_details.get('entry_price', 0)))
                    sl_price = Decimal(str(trade_details.get('sl_price', 0)))

                    # Calcular tamanho do lote baseado no risco
                    if sl_price > 0 and entry_price > 0:
                        sl_distance = abs(entry_price - sl_price)
                        valor_por_lote = Decimal('10.0')  # USD por pip para 1 lote padrão

                        if sl_distance > 0:
                            # Calcular risco monetário permitido
                            calculated_lot_size = risco_monetario / (sl_distance * valor_por_lote)
                        else:
                            # Fallback se distância for zero
                            calculated_lot_size = Decimal('0.01')
                    else:
                        # Fallback: usar cálculo simples
                        # Fallback se não tem SL/Entry definidos
                        calculated_lot_size = risco_monetario / Decimal('1000.0')
                    
                    # Arredondar para 2 casas decimais (padrão forex)
                    calculated_lot_size_round = round(calculated_lot_size, 2)

                    # aplicar limites
                    quantity_max = max(MIN_LOT_SIZE, calculated_lot_size_round)
                    final_lot_size = min(quantity_max, MAX_LOT_SIZE)  # Limite máximo
                    
                    logger.info(
                        f"{log_prefix} DYNAMIC sizing calculado: "
                        f"Saldo={current_balance}, "
                        f"Risco%={risk_percent}%, "
                        f"RiscoMoney={risco_monetario}, "
                        f"Calculado={calculated_lot_size}, "
                        f"Final={final_lot_size} lotes"
                    )
                else:
                    logger.warning(f"{log_prefix} Saldo zero ou inválido, usando lote fixo.")
                    final_lot_size = Decimal(str(instance.lot_size))

            except Exception as e:
                logger.error(f"{log_prefix} Erro no cálculo dinâmico de lote: {e}")
                final_lot_size = Decimal(str(instance.lot_size))  # Fallback to fixed lot

        trade_request = {
            'symbol_id': assets[0] if strategy_obj.strategy_type != 'PAIRS' else assets, # tasks.py uses symbol_id
            'comment': f"BS-{strategy_obj.id}-{instance.id}",
            'side': trade_details['trade_type_str'],
            'quantity_in_lots': final_lot_size,
            **trade_details
        }
        return trade_request
    else:
        logger.info(f"{log_prefix} SINAL REPROVADO. Prob. ({best_decision['prediction_proba']:.2%}) < Limiar ({limiar_otimo:.2f}).")
        return None
