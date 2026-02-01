# ============================================================================
# IMPORTS PADRÃO DO PYTHON
# ============================================================================
import logging
import pandas as pd
import traceback  # Para logging detalhado de erros

# ============================================================================
# IMPORTS DO DJANGO
# ============================================================================
from django.conf import settings
from django.core.cache import cache

# ============================================================================
# IMPORTS PARA CÁLCULOS FINANCEIROS (DECIMAL)
# ============================================================================
from decimal import Decimal, ROUND_HALF_UP

# ============================================================================
# IMPORTS INTERNOS DO PROJETO
# ============================================================================
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
        logger.info(f"{log_prefix} -> Dados de mercado insuficientes para análise.")
        return None

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
        logger.info(f"{log_prefix} -> DataFrame para análise está vazio ou nulo.")
        return None

    params = strategy_obj.portfolio_composition.get(params_key, {})
    df_featured = StrategyContract.add_indicators(df_para_analise, params)

    alert_candidate = df_featured.tail(1)
    alerts = StrategyContract.generate_alerts(alert_candidate, params)
    if alerts.empty:
        logger.info(f"{log_prefix} -> Nenhuma condição de alerta encontrada.")
        return None

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

        # ============================================================================
        # CORREÇÃO: CÁLCULO DINÂMICO DE LOTE COM DECIMAL
        # ============================================================================

        if instance.risk_mode == 'DYNAMIC':
            try:
                # ============================================================================
                # PASSO 1: OBTER SALDO DA CONTA DE TRADING
                # ============================================================================
                # Referência à conta de trading vinculada a esta instância do robô
                account = instance.trading_account

                # Inicializa saldo como Decimal zero (valor padrão seguro)
                current_balance = Decimal('0')

                # Obter saldo da conta de trading
                #É necessário definir o account para que o current_balance possa existir do jeito antigo ele nao existia
                # Verifica primeiro se existe o atributo 'current_balance' (nome mais recente)
                if hasattr(account, 'current_balance'):
                    # Converte o valor do banco para Decimal de forma segura
                    # str() garante que não haverá erros de conversão de float
                    current_balance = Decimal(str(account.current_balance))

                # Se não existir 'current_balance', tenta 'balance' (nome antigo/alternativo)
                elif hasattr(account, 'balance'):
                    current_balance = Decimal(str(account.balance))

                # Se nenhum dos dois existir, mantém zero e registra aviso
                else:
                    logger.warning(f"{log_prefix} Conta {account.account_login} não possui campo de saldo definido.")

                # ---------------------------------------------------------------------
                # PASSO 2: OBTER PERCENTUAL DE RISCO CONFIGURADO
                # ---------------------------------------------------------------------
                # Converte o risk_percent da instância para Decimal
                # Este é o percentual do saldo que o trader está disposto a arriscar por trade
                # Exemplo: 2.5 significa 2.5% do saldo total
                risk_percent = Decimal(str(instance.risk_percent))

                #---------------------------------------------------------------------
                # PASSO 3: VALIDAR SE HÁ SALDO SUFICIENTE PARA OPERAR
                # ---------------------------------------------------------------------
                
                # Só calcula lote dinâmico se houver saldo positivo
                if current_balance > Decimal('0'):
                    # -----------------------------------------------------------------
                    # PASSO 4: CALCULAR O VALOR MONETÁRIO QUE SERÁ ARRISCADO
                    # -----------------------------------------------------------------

                    # Fórmula: Saldo × (Percentual ÷ 100)
                    # Exemplo: $10,000 × (2.5 ÷ 100) = $10,000 × 0.025 = $250
                    # Resultado: Trader está disposto a perder até $250 neste trade
                    risco_monetario = current_balance * (risk_percent / Decimal('100')) # Calcular risco monetário
                    logger.info(
                        f"{log_prefix} Saldo disponível: ${current_balance}, "
                        f"Risco configurado: {risk_percent}%, "
                        f"Valor em risco: ${risco_monetario}"
                    )

                    # -----------------------------------------------------------------
                    # PASSO 5: OBTER PREÇOS DE ENTRADA E STOP LOSS DO SINAL
                    # -----------------------------------------------------------------
                    
                    # Preço onde a ordem será executada
                    # get() retorna 0 se a chave não existir (fallback seguro)
                    entry_price = Decimal(str(trade_details.get('entry_price', 0))) # Obter preços para cálculo de lote
                    # Preço de stop loss (onde a posição será fechada se der errado)
                    sl_price = Decimal(str(trade_details.get('sl_price', 0)))

                    # -----------------------------------------------------------------
                    # PASSO 6: VALIDAR SE OS PREÇOS SÃO VÁLIDOS
                    # -----------------------------------------------------------------
                    
                    # Só calcula se ambos os preços forem maiores que zero
                    # Se não forem, usa fallback (método simplificado)
                    # Calcular tamanho do lote baseado no risco
                    if sl_price > Decimal('0') and entry_price > Decimal('0'):
                        # -------------------------------------------------------------
                        # PASSO 7: CALCULAR DISTÂNCIA ATÉ O STOP LOSS
                        # -------------------------------------------------------------
                        # abs() garante valor positivo independente da direção (compra/venda)
                        # Exemplo: Entry=$1.2000, SL=$1.1950 → Distância=0.0050
                        sl_distance = abs(entry_price - sl_price)
                        # Valor em USD que 1 lote padrão movimenta por ponto (pip)
                        # Para Forex: 1 lote = 100,000 unidades = $10/pip geralmente
                        valor_por_lote = DEFAULT_VALUE_PER_LOT  # USD por pip para 1 lote padrão

                        # Valida se a distância é válida (maior que zero)
                        if sl_distance > Decimal('0'):
                            # ---------------------------------------------------------
                            # PASSO 8: CALCULAR TAMANHO DO LOTE
                            # ---------------------------------------------------------
                            
                            # Fórmula: Risco Monetário ÷ (Distância SL × Valor por Lote)
                            # Exemplo:
                            #   Risco: $250
                            #   Distância SL: 0.0050 (50 pips)
                            #   Valor/lote: $10/pip
                            # Cálculo: $250 ÷ (0.0050 × $10) = $250 ÷ $50 = 5 lotes
                            # Calcular risco monetário permitido
                            calculated_lot_size = risco_monetario / (sl_distance * valor_por_lote)
                            logger.info(
                                f"{log_prefix} Entry: {entry_price}, SL: {sl_price}, "
                                f"Distância SL: {sl_distance}, "
                                f"Lote calculado: {calculated_lot_size}"
                            )
                        # Se distância for zero (erro nos dados), usa fallback
                        else:
                            logger.warning(f"{log_prefix} Distância de SL é zero. Usando cálculo simplificado.")
                            # Fallback: divide risco monetário por divisor fixo
                            calculated_lot_size = risco_monetario / FALLBACK_DIVISOR # Decimal('1000.0')
                    # Se preços forem inválidos (zero ou negativos), usa fallback
                    else:
                        logger.warning(
                            f"{log_prefix} Preços inválidos (Entry: {entry_price}, SL: {sl_price}). "
                            f"Usando cálculo simplificado."
                        )
                        # Fallback: usar cálculo simples
                        # Fallback se não tem SL/Entry definidos
                        calculated_lot_size = risco_monetario / FALLBACK_DIVISOR

                    # -----------------------------------------------------------------
                    # PASSO 9: ARREDONDAR PARA FORMATO VÁLIDO DE FOREX
                    # -----------------------------------------------------------------
                    
                    # quantize() é o método CORRETO do Decimal para arredondamento
                    # ROUND_HALF_UP: arredonda 0.125 → 0.13 (sempre para cima em 0.5)
                    # Decimal('0.01') define 2 casas decimais (padrão Forex)
                            
                    # Arredondar para 2 casas decimais (padrão forex)
                    calculated_lot_size_round = calculated_lot_size.quantize(
                        Decimal('0.01'),  # Precisão: 2 casas decimais
                        rounding=ROUND_HALF_UP  # Método de arredondamento
                    )
                    logger.info(f"{log_prefix} Lote após arredondamento: {calculated_lot_size_round}")

                    # -----------------------------------------------------------------
                    # PASSO 10: APLICAR LIMITES DE SEGURANÇA (MIN/MAX)
                    # -----------------------------------------------------------------
                    # Garante que o lote não seja menor que o mínimo permitido
                    # Exemplo: se calculou 0.005, ajusta para 0.01 (mínimo)
                    # aplicar limites
                    quantity_after_min = max(MIN_LOT_SIZE, calculated_lot_size_round)

                    # Garante que o lote não seja maior que o máximo permitido
                    # Exemplo: se calculou 150 lotes, limita a 100 lotes (máximo)
                    final_lot_size = min(quantity_after_min, MAX_LOT_SIZE)  # Limite máximo

                    # -----------------------------------------------------------------
                    # PASSO 11: REGISTRAR DETALHES DO CÁLCULO NO LOG
                    # -----------------------------------------------------------------
                    logger.info(
                        f"{log_prefix} DYNAMIC sizing calculado: "
                        f"Saldo={current_balance}, "
                        f"Risco%={risk_percent}%, "
                        f"RiscoMoney={risco_monetario}, "
                        f"Calculado={calculated_lot_size}, "
                        f"Arredondado={calculated_lot_size_round}, "
                        f"Final={final_lot_size} lotes"
                    )
                # ---------------------------------------------------------------------
                # SE NÃO HÁ SALDO, USA LOTE FIXO COMO FALLBACK
                # ---------------------------------------------------------------------
                else:
                    # Converte o lote fixo da instância para Decimal
                    final_lot_size = Decimal(str(instance.lot_size))
                    logger.warning(
                        f"{log_prefix} Saldo da conta é zero ou negativo (${current_balance}). "
                        f"Usando lote fixo configurado."
                    )              

            # -------------------------------------------------------------------------
            # TRATAMENTO DE ERROS: SE QUALQUER COISA FALHAR, USA LOTE FIXO
            # -------------------------------------------------------------------------
            except Exception as e:
                logger.error(
                    f"{log_prefix} ERRO no cálculo dinâmico de lote: {e}. "
                    f"Traceback: {traceback.format_exc()}"
                )
                # Em caso de erro, sempre usa o lote fixo como fallback de segurança
                final_lot_size = Decimal(str(instance.lot_size))

        trade_request = {
            'symbol_id': assets[0] if strategy_obj.strategy_type != 'PAIRS' else assets, # tasks.py uses symbol_id
            'comment': f"BS-{strategy_obj.id}-{instance.id}",
            'side': trade_details['trade_type_str'],
            'quantity_in_lots': final_lot_size,
            **trade_details # Inclui entry_price, sl_price, tp_price, etc
        }
        return trade_request
    
    # =========================================================================
    # SE PROBABILIDADE < LIMIAR, REJEITA O SINAL
    # =========================================================================
    else:
        logger.info(
            f"{log_prefix} SINAL REPROVADO. "
            f"Prob. ({best_decision['prediction_proba']:.2%}) < Limiar ({limiar_otimo:.2f})."
        )
        return None  # ← RETORNA None se sinal foi reprovado
