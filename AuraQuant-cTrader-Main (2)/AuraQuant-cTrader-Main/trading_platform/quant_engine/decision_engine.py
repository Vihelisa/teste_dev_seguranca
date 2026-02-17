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
#DEFAULT_VALUE_PER_LOT = Decimal('10.0')  # USD per pip for 1 standard lot
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


def get_trade_signal(instance, StrategyContract, saved_ia, log_prefix, fix_current_price=None):
    """
    Core logic for analyzing a strategy signal. Returns a trade request dictionary if a trade is approved.
    Esta é uma versão modificada de analyze_and_trade para o motor FIX.
    """
    return analyze_and_get_signal(instance, StrategyContract, saved_ia, log_prefix, fix_current_price=fix_current_price)

# =============================================================================
#           FUNÇÃO AUXILIAR: CÁLCULO CORRETO DE LOTE
# =============================================================================

def calculate_lot_size_for_risk(symbol_info, entry_price, sl_price, risk_amount):
    """
    Calcula o tamanho do lote baseado no risco monetário desejado.
    
    POR QUE ESTA FUNÇÃO É NECESSÁRIA:
    O cálculo anterior usava uma fórmula simplificada que não considerava
    o tamanho real do contrato nem o valor real do tick do ativo.
    
    PROBLEMA DO CÁLCULO ANTIGO:
    - Usava valor fixo de $10 por pip (não funciona para todos os pares)
    - Multiplicava distância em PREÇO diretamente (ex: 0.0050)
    - Resultado: $0.05 em vez de $500 (erro de 10.000x!)
    
    SOLUÇÃO:
    Usar dados reais do MT5 (symbol_info) para calcular corretamente.
    
    Args:
        symbol_info: Objeto do MT5 com informações do símbolo
        entry_price (Decimal): Preço de entrada planejado
        sl_price (Decimal): Preço do Stop Loss
        risk_amount (Decimal): Quanto $ queremos arriscar neste trade
    
    Returns:
        Decimal: Tamanho do lote calculado e validado
    """
    from decimal import Decimal, ROUND_DOWN
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # =====================================================================
        # PASSO 1: Calcular distância até Stop Loss (em preço)
        # =====================================================================
        # Exemplo: Entry=1.2000, SL=1.1950 → distância=0.0050
        sl_distance = abs(entry_price - sl_price)
        
        # Validação: distância deve ser > 0
        if sl_distance <= Decimal('0'):
            logger.error(
                f"[LOT_CALC] ❌ Distância SL inválida: {sl_distance}. "
                f"Entry={entry_price}, SL={sl_price}"
            )
            # Retorna lote mínimo em caso de erro
            return Decimal('0.01')
        
        logger.info(f"[LOT_CALC] Distância SL: {sl_distance}")
        
        # =====================================================================
        # PASSO 2: Obter informações REAIS do símbolo do MT5
        # =====================================================================
        
        # trade_tick_size: Qual é o tamanho de 1 tick (menor variação)?
        # - EURUSD: 0.00001 (5 dígitos) ou 0.0001 (4 dígitos)
        # - USDJPY: 0.001 (3 dígitos)
        # - XAUUSD: 0.01
        # POR QUE PRECISAMOS: Para converter distância de PREÇO para TICKS
        tick_size = Decimal(str(symbol_info.trade_tick_size))
        
        # trade_tick_value: Quanto vale 1 tick em USD?
        # - EURUSD 1 lote: ~$10/tick (mas varia ligeiramente)
        # - USDJPY 1 lote: ~$9.13/tick (depende da cotação atual)
        # - XAUUSD 1 lote: ~$1/tick
        # POR QUE PRECISAMOS: Valor NÃO é fixo $10 para todos os pares!
        tick_value = Decimal(str(symbol_info.trade_tick_value))
        
        # volume_step: Qual o incremento mínimo de lote aceito?
        # - Maioria dos pares: 0.01 (pode fazer 0.01, 0.02, 0.03...)
        # - Alguns índices: 0.1 ou 1.0
        # POR QUE PRECISAMOS: Broker rejeita se enviarmos 0.237 quando só aceita 0.01
        volume_step = Decimal(str(symbol_info.volume_step))
        
        # volume_min e volume_max: Limites do broker
        # - Típico: min=0.01, max=100 ou 500
        # POR QUE PRECISAMOS: Proteger contra lotes impossíveis
        volume_min = Decimal(str(symbol_info.volume_min))
        volume_max = Decimal(str(symbol_info.volume_max))
        
        logger.info(
            f"[LOT_CALC] Symbol Info: "
            f"TickSize={tick_size}, "
            f"TickValue=${tick_value}, "
            f"VolumeStep={volume_step}, "
            f"Min={volume_min}, Max={volume_max}"
        )
        
        # =====================================================================
        # PASSO 3: Converter distância de PREÇO para TICKS
        # =====================================================================
        
        # Exemplo EURUSD:
        # - Distância: 0.0050 (50 pips)
        # - Tick Size: 0.0001 (1 pip)
        # - Cálculo: 0.0050 / 0.0001 = 50 ticks
        #
        # POR QUE ISSO É IMPORTANTE:
        # Precisamos saber QUANTOS ticks há na distância do SL
        # para poder calcular o valor em dinheiro
        ticks_in_sl = sl_distance / tick_size
        
        logger.info(
            f"[LOT_CALC] SL em ticks: {ticks_in_sl} "
            f"({sl_distance} / {tick_size})"
        )
        
        # =====================================================================
        # PASSO 4: Calcular quanto vale o SL em $ por lote
        # =====================================================================
        
        # Fórmula: Ticks × Valor_por_Tick
        #
        # Exemplo EURUSD com 50 pips de SL:
        # - Ticks: 50
        # - Tick Value: $10
        # - Cálculo: 50 × $10 = $500 por lote
        #
        # ISTO É O QUE ESTAVA FALTANDO NO CÓDIGO ANTIGO!
        # O código antigo fazia: 0.0050 × $10 = $0.05 ❌
        # O correto é: 50 ticks × $10/tick = $500 ✅
        sl_value_per_lot = ticks_in_sl * tick_value
        
        logger.info(
            f"[LOT_CALC] Valor do SL por lote: ${sl_value_per_lot}"
        )
        
        # Validação: deve ser > 0
        if sl_value_per_lot <= Decimal('0'):
            logger.error(
                f"[LOT_CALC] ❌ Valor SL por lote inválido: {sl_value_per_lot}"
            )
            return Decimal('0.01')
        
        # =====================================================================
        # PASSO 5: Calcular tamanho do lote para atingir risco desejado
        # =====================================================================
        
        # Fórmula: Lote = Risco_Desejado / Valor_SL_por_Lote
        #
        # Exemplo: Quero arriscar $100
        # - Risco desejado: $100
        # - SL vale por lote: $500
        # - Cálculo: $100 / $500 = 0.2 lotes
        #
        # LÓGICA: Se 1 lote arrisca $500, então para arriscar só $100
        # preciso de 1/5 de lote (0.2)
        calculated_lot_size = risk_amount / sl_value_per_lot
        
        logger.info(
            f"[LOT_CALC] Lote calculado (bruto): {calculated_lot_size} "
            f"(${risk_amount} / ${sl_value_per_lot})"
        )
        
        # =====================================================================
        # PASSO 6: Arredondar para o volume_step aceito pelo broker
        # =====================================================================
        
        # PROBLEMA: Calculamos 0.237 lotes, mas broker só aceita 0.01, 0.02...
        #
        # SOLUÇÃO: Arredondar para BAIXO no incremento correto
        # - Calculado: 0.237
        # - Volume step: 0.01
        # - Divisão: 0.237 / 0.01 = 23.7 steps
        # - Arredondar para baixo: 23 steps
        # - Multiplicar de volta: 23 × 0.01 = 0.23 lotes
        #
        # POR QUE ARREDONDAR PARA BAIXO (ROUND_DOWN):
        # - Segurança: melhor arriscar um pouco MENOS do que planejado
        # - Evita rejeição: 0.237 seria rejeitado, 0.23 é aceito
        steps = (calculated_lot_size / volume_step).quantize(
            Decimal('1'),  # Arredondar para inteiro (número de steps)
            rounding=ROUND_DOWN  # Sempre para baixo (conservador)
        )
        
        final_lot_size = steps * volume_step
        
        logger.info(
            f"[LOT_CALC] Após arredondamento: {final_lot_size} "
            f"({steps} steps de {volume_step})"
        )
        
        # =====================================================================
        # PASSO 7: Validar limites do broker
        # =====================================================================
        
        # Se ficou menor que o mínimo, usar o mínimo
        if final_lot_size < volume_min:
            logger.warning(
                f"[LOT_CALC] ⚠️ Lote {final_lot_size} < mínimo {volume_min}. "
                f"Usando mínimo."
            )
            final_lot_size = volume_min
        
        # Se ficou maior que o máximo, usar o máximo
        elif final_lot_size > volume_max:
            logger.warning(
                f"[LOT_CALC] ⚠️ Lote {final_lot_size} > máximo {volume_max}. "
                f"Usando máximo."
            )
            final_lot_size = volume_max
        
        # =====================================================================
        # RESULTADO FINAL
        # =====================================================================
        
        logger.info(
            f"[LOT_CALC] ✅ Lote FINAL: {final_lot_size} "
            f"(arriscando ~${sl_value_per_lot * final_lot_size:.2f})"
        )
        
        return final_lot_size
        
    except Exception as e:
        # Em caso de QUALQUER erro, retornar lote mínimo seguro
        logger.error(
            f"[LOT_CALC] ❌ ERRO ao calcular lote: {e}",
            exc_info=True
        )
        return Decimal('0.01')


def analyze_and_get_signal(instance, StrategyContract, saved_ia, log_prefix, fix_current_price=None):
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

                    # Inicializa calculated_lot_size com FALLBACK desde o início
                    # MOTIVO: Garante que a variável SEMPRE existe, mesmo se
                    # qualquer validação abaixo falhar silenciosamente.
                    # Sem isso, o Passo 10 quebraria com NameError!
                    calculated_lot_size = risco_monetario / FALLBACK_DIVISOR

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
                        # Valida se a distância é válida (maior que zero)
                        if sl_distance > Decimal('0'):
                            # ---------------------------------------------------------
                            # PASSO 8: BUSCAR SYMBOL_INFO REAL DO MT5
                            # ---------------------------------------------------------

                            # POR QUE CONECTAR AO MT5 AQUI:
                            # O cliente não quer valores fixos/estimados.
                            # Precisamos dos dados REAIS do símbolo para calcular
                            # corretamente para QUALQUER ativo:
                            # - Forex (EURUSD, GBPUSD, USDJPY)
                            # - Metais (XAUUSD, XAGUSD)
                            # - Índices (US30, NAS100)
                            # - Cripto (BTCUSD)
        
                            # Nome do símbolo que estamos analisando
                            symbol_name = assets[0] #if strategy_obj.strategy_type != 'PAIRS' else assets[0]
                            # symbol_info será None se falhar (tratamos abaixo)
                            symbol_info_mt5 = None
                            try:
                                # Só precisamos do context manager mt5_connection
                                # O import do MetaTrader5 diretamente não é necessário aqui
                                # pois usamos o wrapper mt5_connection que já gerencia a conexão
                                from trading_platform.utils.mt5_connection import mt5_connection
                                
                                # Abrir conexão com MT5 usando as credenciais da conta
                                with mt5_connection(instance.trading_account) as mt5_conn:
                                    if mt5_conn:
                                        # Garantir que o símbolo está visível no Market Watch
                                        # (necessário para obter informações)
                                        mt5_conn.symbol_select(symbol_name, True)
                                        # Buscar informações completas do símbolo
                                        # Contém: tick_size, tick_value, volume_step, etc.
                                        symbol_info_mt5 = mt5_conn.symbol_info(symbol_name)
                                        if symbol_info_mt5:
                                            logger.info(
                                                f"{log_prefix} [LOT_CALC] symbol_info obtido: "
                                                f"Symbol={symbol_name}, "
                                                f"TickSize={symbol_info_mt5.trade_tick_size}, "
                                                f"TickValue={symbol_info_mt5.trade_tick_value}, "
                                                f"VolumeStep={symbol_info_mt5.volume_step}"
                                            )
                                        else:
                                            logger.warning(
                                                f"{log_prefix} [LOT_CALC] ⚠️ symbol_info retornou None "
                                                f"para {symbol_name}. Usando FALLBACK."
                                            )
                                    else:
                                        logger.warning(
                                            f"{log_prefix} [LOT_CALC] ⚠️ Falha ao conectar MT5 "
                                            f"para obter symbol_info. Usando FALLBACK."
                                        )
                            except Exception as e:
                                logger.error(
                                    f"{log_prefix} [LOT_CALC] ❌ Erro ao buscar symbol_info: {e}",
                                    exc_info=True
                                )
                                symbol_info_mt5 = None

                            # ---------------------------------------------------------
                            # PASSO 9: CALCULAR LOTE COM DADOS REAIS OU FALLBACK
                            # ---------------------------------------------------------

                            if symbol_info_mt5:
                                # ✅ CAMINHO IDEAL: Dados reais do MT5
                                # Chama a função que usa symbol_info real
                                # (tick_size, tick_value, volume_step corretos!)
                                calculated_lot_size = calculate_lot_size_for_risk(
                                    symbol_info=symbol_info_mt5,
                                    entry_price=entry_price,
                                    sl_price=sl_price,
                                    risk_amount=risco_monetario  # ← Nome correto!
                                )
                                
                                logger.info(
                                    f"{log_prefix} [LOT_CALC] ✅ Lote calculado com dados REAIS: "
                                    f"{calculated_lot_size} lotes "
                                    f"para risco de ${risco_monetario}"
                                )
                            else:
                                # ⚠️ CAMINHO FALLBACK: symbol_info não disponível
                                # Usa FALLBACK_DIVISOR (configurado no topo do arquivo)
                                # Trader_engine ainda vai validar o risco final!
                                calculated_lot_size = risco_monetario / FALLBACK_DIVISOR
                                
                                logger.warning(
                                    f"{log_prefix} [LOT_CALC] ⚠️ Usando FALLBACK: "
                                    f"{risco_monetario} / {FALLBACK_DIVISOR} = "
                                    f"{calculated_lot_size} lotes. "
                                    f"Validação final no trader_engine."
                                )

                            
                        # Se distância for zero (erro nos dados), usa fallback
                        else:
                            logger.warning(
                                f"{log_prefix} Distância de SL é zero. "
                                f"Usando FALLBACK_DIVISOR."
                            )
                            calculated_lot_size = risco_monetario / FALLBACK_DIVISOR
                    
                    else: # Se preços forem inválidos (zero ou negativos), usa fallback
                        logger.warning(
                            f"{log_prefix} Preços inválidos (Entry: {entry_price}, SL: {sl_price}). "
                            f"Usando FALLBACK_DIVISOR"
                        )
                        # Fallback: usar cálculo simples
                        # Fallback se não tem SL/Entry definidos
                        calculated_lot_size = risco_monetario / FALLBACK_DIVISOR

                    # -----------------------------------------------------------------
                    # PASSO 10: ARREDONDAR PARA FORMATO VÁLIDO DE FOREX
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
                    # PASSO 11: APLICAR LIMITES DE SEGURANÇA (MIN/MAX)
                    # -----------------------------------------------------------------
                    # Garante que o lote não seja menor que o mínimo permitido
                    # Exemplo: se calculou 0.005, ajusta para 0.01 (mínimo)
                    # aplicar limites
                    quantity_after_min = max(MIN_LOT_SIZE, calculated_lot_size_round)

                    # Garante que o lote não seja maior que o máximo permitido
                    # Exemplo: se calculou 150 lotes, limita a 100 lotes (máximo)
                    final_lot_size = min(quantity_after_min, MAX_LOT_SIZE)  # Limite máximo

                    # -----------------------------------------------------------------
                    # PASSO 12: REGISTRAR DETALHES DO CÁLCULO NO LOG
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

        # =====================================================================
        # ANTI SPLIT-BRAIN: substituir entry_price pelo preço real do FIX
        # =====================================================================
        # O sinal foi gerado com dados históricos do MT5 (data_processor).
        # Se o tasks.py injetou o preço atual do feed FIX, usamos ele
        # para garantir que decisão e execução ocorrem na mesma realidade
        # de mercado — eliminando o risco de slippage fantasma.
        if fix_current_price is not None:
            old_price = trade_details.get('entry_price', 'N/A')
            trade_details['entry_price'] = fix_current_price
            logger.info(
                f"{log_prefix} [SPLIT-BRAIN CORRIGIDO] "
                f"entry_price substituido: {old_price} (MT5) → {fix_current_price} (FIX)"
            )
        else:
            logger.warning(
                f"{log_prefix} [SPLIT-BRAIN] fix_current_price nao disponivel. "
                f"Usando entry_price do sinal MT5. Risco de divergencia de preco!"
            )

        trade_request = {
            'symbol_id': assets[0] if strategy_obj.strategy_type != 'PAIRS' else assets,
            'comment': f"BS-{strategy_obj.id}-{instance.id}",
            'side': trade_details['trade_type_str'],
            'quantity_in_lots': final_lot_size,
            **trade_details
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
