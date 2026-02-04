import logging
import traceback
import json
import decimal
import numpy as np
import pandas as pd
import traceback  # Para logging detalhado de erros (se ainda não estiver importado)
from decimal import Decimal, ROUND_HALF_UP  # Para cálculos financeiros precisos

from decimal import Decimal
from datetime import datetime
from django.contrib.auth.models import User
from django.conf import settings
from .models import TradingAccount, Notification, TradeLog, ActiveRobotInstance

# Handle optional MetaTrader5 import for non-Windows environments
try:
    import MetaTrader5 as mt5
    from .utils.mt5_connector import mt5_connection
except (ImportError, ModuleNotFoundError):
    mt5 = None
    mt5_connection = None
    logging.warning("MetaTrader5 module not found. Trading engine will be disabled.")

# Serializador JSON robusto para logging, garantindo que nada quebre a serialização.
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '_asdict'): return obj._asdict()
        if isinstance(obj, (np.integer, np.floating, decimal.Decimal)): return float(obj)
        if isinstance(obj, (datetime, pd.Timestamp)): return obj.isoformat()
        if isinstance(obj, np.ndarray): return obj.tolist()
        if pd.isna(obj): return None
        # Para qualquer outro objeto não serializável, retorna sua representação em string.
        try:
            return super(ComplexEncoder, self).default(obj)
        except TypeError:
            return str(obj)

logger = logging.getLogger(__name__)
MAGIC_NUMBER_BASE = settings.MAGIC_NUMBER_BASE

# =============================================================================
#           FUNÇÕES INTERNAS (PRIVADAS)
# =============================================================================

def _get_active_position(symbol: str, magic: int, mt5_conn):
    """(PRIVADO) Verifica se JÁ EXISTE uma posição aberta PELA ESTRATÉGIA ESPECÍFICA."""
    positions = mt5_conn.positions_get(symbol=symbol)
    if not positions: return None
    for pos in positions:
        if pos.magic == magic: return pos
    return None

def _build_trade_request(symbol: str, trade_type: int, volume: float, price: float, sl: float, tp: float, comment: str, digits: int, magic_number: int) -> dict:
    """(PRIVADO) Constrói o dicionário de requisição com arredondamento dinâmico."""
    return { "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": float(volume), "type": trade_type,
             "price": round(price, digits), "sl": round(sl, digits), "tp": round(tp, digits), "deviation": 20, "magic": magic_number,
             "comment": comment, "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC }

# =============================================================================
#           API PÚBLICA DE EXECUÇÃO DE ORDENS
# =============================================================================

def execute_trade_from_signal(instance: ActiveRobotInstance, signal_details: dict):
    """
    Função Mestra de Execução V15.0. Versão final com logging completo e robusto.
    """
    if not mt5 or not mt5_connection:
        logger.error("MT5 not available. Cannot execute trade.")
        return
    account, user = instance.trading_account, instance.user
    symbol = signal_details.get("symbol")
    request, result, price, stop_loss_final, take_profit = None, None, 0.0, 0.0, 0.0 # Inicializa para o bloco finally

    try:
        # Validação de contrato clara e explícita
        required_keys = ["symbol", "trade_type_str", "stop_loss_base"]
        if not all(key in signal_details for key in required_keys):
            raise ValueError(f"Sinal inválido. Chaves faltando: {[k for k in required_keys if k not in signal_details]}")

        current_magic_number = MAGIC_NUMBER_BASE + instance.strategy.id

        with mt5_connection(account) as mt5_conn:
            if not mt5_conn:
                raise ConnectionError(f"Falha ao conectar MT5 para {account.account_login}")

            # Risk Management Check 1: Max Open Positions
            user_positions = mt5_conn.positions_get()
            if len(user_positions) >= user.profile.max_open_positions:
                logger.warning(f"[RISK_MG] Trade para {symbol} bloqueado. Limite de posições abertas ({user.profile.max_open_positions}) atingido.")
                return

            if _get_active_position(symbol, current_magic_number, mt5_conn):
                logger.info(f"[TRADER_ENGINE] Posição para {symbol} (magic: {current_magic_number}) já existe.")
                return

            # Garante que o símbolo está visível no Market Watch para evitar erros.
            if not mt5_conn.symbol_select(symbol, True):
                # Se mesmo assim não for possível selecionar, lança um erro claro.
                raise ConnectionError(f"Falha ao selecionar/habilitar o símbolo {symbol} no terminal MT5.")

            symbol_info = mt5_conn.symbol_info(symbol)
            if not symbol_info: raise ValueError(f"Não foi possível obter symbol_info para {symbol}")
            tick = mt5_conn.symbol_info_tick(symbol)
            if not tick: raise ValueError(f"Não foi possível obter o tick para {symbol}")

            # =========================================================================
            # OBTER PREÇO ATUAL E INFORMAÇÕES DO SÍMBOLO
            # =========================================================================
            trade_type = mt5.ORDER_TYPE_BUY if signal_details['trade_type_str'].lower() == 'buy' else mt5.ORDER_TYPE_SELL
            price = tick.ask if trade_type == mt5.ORDER_TYPE_BUY else tick.bid
            point, digits = symbol_info.point, symbol_info.digits

            # =========================================================================
            # CALCULAR STOP LOSS
            # =========================================================================
            stop_loss_proposto = signal_details.get("stop_loss_base", 0.0)

            # Lógica para SL de segurança em ordens de teste
            if stop_loss_proposto == 0.0 and signal_details.get('comment', '').startswith('BS-TEST-'):
                distancia_segura = max(symbol_info.trade_stops_level, 50) * point
                stop_loss_proposto = price - distancia_segura if trade_type == mt5.ORDER_TYPE_BUY else price + distancia_segura

            sl_reference_price = tick.bid if trade_type == mt5.ORDER_TYPE_BUY else tick.ask
            distancia_minima_corretora = symbol_info.trade_stops_level * point

            stop_loss_final = stop_loss_proposto
            if abs(sl_reference_price - stop_loss_proposto) < distancia_minima_corretora:
                offset = distancia_minima_corretora * 1.05
                stop_loss_final = sl_reference_price - offset if trade_type == mt5.ORDER_TYPE_BUY else sl_reference_price + offset
            
            # Calcula a distância final até o SL (será usada para cálculo de risco)
            sl_distance_final = abs(price - stop_loss_final)

            #============================================================================
            # CORREÇÃO: VALIDAÇÃO DE RISCO POR TRADE (Risk Management Check 2)
            # ============================================================================

            # Obtém informações atualizadas da conta (saldo, margem, etc)
            account_info = mt5_conn.account_info()

            # Valida se conseguiu obter as informações E se há saldo positivo
            if account_info and account_info.balance > 0:
                # -------------------------------------------------------------------------
                # PASSO 1: CONVERTER SALDO PARA DECIMAL
                # -------------------------------------------------------------------------
                # Converte o saldo da conta (que vem como float do MT5) para Decimal
                # Isso garante precisão nos cálculos financeiros
                balance = Decimal(str(account_info.balance))
                logger.info(f"[RISK_MG] Saldo da conta: ${balance}")

                # -------------------------------------------------------------------------
                # PASSO 2: OBTER TAMANHO DO LOTE (JÁ É DECIMAL)
                # -------------------------------------------------------------------------
                # instance.lot_size JÁ É Decimal (vem do banco de dados como DecimalField)
                # NÃO precisa converter! Usar diretamente
                lot_size = instance.lot_size

                # -------------------------------------------------------------------------
                # PASSO 3: CALCULAR PERDA POTENCIAL SE O STOP LOSS FOR ATINGIDO
                # -------------------------------------------------------------------------
                # sl_distance_final foi calculado anteriormente (distância até o SL em preço)
                # Exemplo: Entry=$1.2000, SL=$1.1950 → sl_distance_final=0.0050
                # Converte para Decimal de forma segura
                sl_distance = Decimal(str(sl_distance_final))

                # Valor em USD que cada pip movimenta por lote
                # Para 1 lote padrão Forex: geralmente $10/pip
                # Para mini-lote (0.1): $1/pip
                # Para micro-lote (0.01): $0.10/pip
                value_per_pip = Decimal('10.0')

                # Fórmula: Perda Potencial = Distância SL × Valor por pip × Quantidade de lotes
                # Exemplo:
                #   sl_distance = 0.0050 (50 pips)
                #   value_per_pip = $10
                #   lot_size = 2.0 lotes
                # Cálculo: 0.0050 × $10 × 2.0 = $100 de perda potencial
                potential_loss = sl_distance * value_per_pip * lot_size
                logger.info(
                    f"[RISK_MG] Cálculo de perda potencial: "
                    f"SL Distance={sl_distance}, "
                    f"Value/pip=${value_per_pip}, "
                    f"Lot Size={lot_size}, "
                    f"Potential Loss=${potential_loss}"
                )

                # -------------------------------------------------------------------------
                # PASSO 4: CALCULAR PERCENTUAL DE RISCO EM RELAÇÃO AO SALDO
                # -------------------------------------------------------------------------
                # Fórmula: (Perda Potencial ÷ Saldo) × 100
                # Exemplo: ($100 ÷ $10,000) × 100 = 1%
                # Isso indica que este trade arrisca 1% do saldo total
                risk_percent = (potential_loss / balance) * Decimal('100')

                # Arredonda para 2 casas decimais para comparação
                risk_percent_rounded = risk_percent.quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP
                )
                logger.info(
                    f"[RISK_MG] Trade arrisca {risk_percent_rounded}% do saldo "
                    f"(${potential_loss} de ${balance})"
                )

                # -------------------------------------------------------------------------
                # PASSO 5: VALIDAR SE O RISCO ESTÁ DENTRO DO LIMITE CONFIGURADO
                # -------------------------------------------------------------------------
                # Converte o limite máximo de risco do perfil do usuário para Decimal
                max_risk_allowed = Decimal(str(user.profile.max_risk_per_trade))

                # Compara o risco calculado com o limite configurado
                if risk_percent_rounded > max_risk_allowed:
                    # BLOQUEIO: Trade excede o limite de risco permitido
                    logger.warning(
                        f"[RISK_MG] ⚠️ TRADE BLOQUEADO! "
                        f"Símbolo: {symbol}, "
                        f"Risco calculado: {risk_percent_rounded}%, "
                        f"Limite permitido: {max_risk_allowed}%, "
                        f"Perda potencial: ${potential_loss}"
                    )
                    # Retorna imediatamente sem executar a ordem
                    # Isso protege a conta de trades com risco excessivo                  
                    return
                
                else:
                    # Trade aprovado: risco está dentro dos limites
                    logger.info(
                        f"[RISK_MG] ✅ Trade aprovado. "
                        f"Risco {risk_percent_rounded}% está dentro do limite de {max_risk_allowed}%"
                    )

            # =========================================================================
            # CALCULAR TAKE PROFIT
            # ========================================================================= 


            # Obtém a relação risco/retorno configurada (padrão: 1.5)
            # Exemplo: se SL = 50 pips, TP = 75 pips (1.5x)
            risco_retorno = signal_details.get('risco_retorno', 1.5)

            # Calcula o preço de take profit baseado na distância do SL
            # Para COMPRA: TP fica ACIMA do preço de entrada
            # Para VENDA: TP fica ABAIXO do preço de entrada
            if trade_type == mt5.ORDER_TYPE_BUY:
                take_profit = price + (sl_distance_final * risco_retorno)
            else:  # SELL
                take_profit = price - (sl_distance_final * risco_retorno)

            logger.info(
                f"[TRADER_ENGINE] Preços calculados: "
                f"Entry={price}, SL={stop_loss_final}, TP={take_profit}, "
                f"Risk/Reward={risco_retorno}"
            )

            # =========================================================================
            # CONSTRUIR REQUISIÇÃO DE ORDEM
            # =========================================================================
            request = _build_trade_request(
                symbol=symbol, 
                trade_type=trade_type, 
                volume=float(instance.lot_size), # MT5 exige float aqui
                price=price,
                sl=stop_loss_final, 
                tp=take_profit, 
                comment=signal_details.get('comment', 'BS-Trade')[:31],
                digits=digits, 
                magic_number=current_magic_number
            )
            logger.info(f"[TRADER_ENGINE] Enviando ordem: {request}")

            # =========================================================================
            # ENVIAR ORDEM PARA O BROKER
            # =========================================================================
            result = mt5_conn.order_send(request)

    except Exception as e:
        logger.critical(f"[TRADER_ENGINE] EXCEÇÃO CRÍTICA para {account.account_login}: {traceback.format_exc()}")
        TradeLog.objects.create(
            instance=instance, user=user, trading_account=account, status=TradeLog.TradeStatus.EXCEPTION,
            request_data=json.loads(json.dumps(request or signal_details, cls=ComplexEncoder)),
            comment=traceback.format_exc(), symbol=symbol
        )
        Notification.objects.create(user=user, message=f"Erro interno no robô {instance.strategy.name}.", notification_type='ERROR')

    finally:
        if request and result:
            status_log = TradeLog.TradeStatus.SUCCESS if result.retcode == mt5.TRADE_RETCODE_DONE else TradeLog.TradeStatus.FAILED
            message = f"{request['comment']} abriu ordem em {symbol}." if status_log == 'SUCCESS' else f"Falha na ordem em {symbol}: {result.comment}"
            
            TradeLog.objects.create(
                instance=instance, user=user, trading_account=account, status=status_log,
                request_data=json.loads(json.dumps(request, cls=ComplexEncoder)),
                response_data=json.loads(json.dumps(result, cls=ComplexEncoder)),
                retcode=result.retcode, comment=result.comment,
                order_ticket=result.order if status_log == 'SUCCESS' else None,
                symbol=symbol, trade_type=signal_details.get("trade_type_str").upper(),
                volume=instance.lot_size, price_entry=price,
                sl_price=stop_loss_final, tp_price=take_profit # [MELHORIA] Preenche os campos que faltavam
            )
            Notification.objects.create(user=user, message=message,
                                        notification_type=Notification.NotificationType.SUCCESS if status_log == 'SUCCESS' else Notification.NotificationType.ERROR)
        
        elif request and not result:
            TradeLog.objects.create(
                instance=instance, user=user, trading_account=account, status=TradeLog.TradeStatus.FAILED,
                request_data=json.loads(json.dumps(request, cls=ComplexEncoder)),
                comment="order_send() retornou None.", symbol=symbol
            )
            Notification.objects.create(user=user, message=f"Falha de comunicação para ordem em {symbol}.", notification_type='ERROR')

# =============================================================================
#           API PÚBLICA DE FECHAMENTO DE ORDENS (COM AUDITORIA)
# =============================================================================

def close_all_positions_for_strategy(account: TradingAccount, strategy_id: int, user: User):
    """Fecha todas as posições que pertencem a UMA ESTRATÉGIA ESPECÍFICA."""
    if not mt5 or not mt5_connection:
        logger.error("MT5 not available. Cannot close positions.")
        return {"success": False, "closed_count": 0, "error": "MT5 not available"}
    logger.info(f"Iniciando fechamento de posições para estratégia ID {strategy_id} na conta {account.account_login}")
    
    closed_count = 0
    with mt5_connection(account) as mt5_conn:
        if not mt5_conn:
            return {"success": False, "closed_count": 0, "error": "Connection failed"}

        current_magic_number = MAGIC_NUMBER_BASE + strategy_id
        positions = mt5_conn.positions_get()

        if not positions:
            return {"success": True, "closed_count": 0}

        for pos in positions:
            if pos.magic == current_magic_number:
                try:
                    tick = mt5_conn.symbol_info_tick(pos.symbol)
                    if not tick: continue

                    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL, "position": pos.ticket, "symbol": pos.symbol,
                        "volume": pos.volume, "type": close_type, "price": close_price, "deviation": 20,
                        "magic": current_magic_number, "comment": f"Closed by user",
                    }
                    result = mt5_conn.order_send(close_request)

                    status_log = TradeLog.TradeStatus.FAILED
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        status_log = TradeLog.TradeStatus.CLOSED
                        closed_count += 1

                    # [REFACTOR] Update the original TradeLog entry instead of creating a new one.
                    try:
                        trade_log_entry = TradeLog.objects.get(order_ticket=pos.ticket)

                        trade_log_entry.status = status_log
                        trade_log_entry.price_exit = close_price
                        trade_log_entry.profit_loss = pos.profit
                        # Append closing data to response_data for a complete audit trail
                        if trade_log_entry.response_data:
                            trade_log_entry.response_data['close_request'] = json.loads(json.dumps(close_request, cls=ComplexEncoder))
                            trade_log_entry.response_data['close_result'] = json.loads(json.dumps(result, cls=ComplexEncoder)) if result else {}
                        else:
                            trade_log_entry.response_data = {
                                'close_request': json.loads(json.dumps(close_request, cls=ComplexEncoder)),
                                'close_result': json.loads(json.dumps(result, cls=ComplexEncoder)) if result else {}
                            }

                        trade_log_entry.comment = f"{trade_log_entry.comment} | Closed by user. Close comment: {result.comment if result else 'N/A'}"
                        trade_log_entry.save()

                        Notification.objects.create(user=user, message=f"Posição {pos.symbol} (Ticket: {pos.ticket}) fechada.", notification_type='INFO')

                    except TradeLog.DoesNotExist:
                        logger.error(f"Could not find original TradeLog for order ticket {pos.ticket} to update on close.")
                    except Exception as log_e:
                        logger.error(f"Error updating TradeLog for ticket {pos.ticket}: {log_e}")

                except Exception as e:
                     logger.error(f"Erro durante o fechamento da posição {pos.ticket}: {traceback.format_exc()}")

    return {"success": True, "closed_count": closed_count}