import logging
import json
import numpy as np
import pandas as pd
import traceback  # Para logging detalhado de erros (se ainda não estiver importado)

from decimal import Decimal, ROUND_HALF_UP  # Para cálculos financeiros precisos
from datetime import datetime
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone  # ← Para timestamp preciso
from trading_platform.models import TradeLog, Notification  # ← Para salvar logs
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


# =============================================================================
#           FUNÇÃO AUXILIAR PARA FIX PROTOCOL (NOVO)
# =============================================================================

def create_pending_trade_log(instance, signal_details, clordid, order_type='FIX'):
    """
    Cria um TradeLog com status PENDING para ordens FIX.
    
    Esta função é chamada IMEDIATAMENTE após enviar a ordem FIX.
    O TradeLog fica com status PENDING até que o ExecutionReport confirme.
    
    Args:
        instance (ActiveRobotInstance): Instância do robô que está operando
        signal_details (dict): Detalhes do sinal de trading
        clordid (str): ID único da ordem (ClOrdID) que foi enviado
        order_type (str): Tipo de ordem ('FIX' ou 'MT5')
    
    Returns:
        TradeLog: O objeto TradeLog criado (ou None se houver erro)
    
    Explicação:
        Quando usamos FIX Protocol, o fluxo é assíncrono:
        1. Enviamos a ordem → build_and_send_new_order_single()
        2. Criamos este TradeLog com status PENDING
        3. Sistema continua funcionando normalmente
        4. [... tempo passa ...]
        5. ExecutionReport chega (pode ser segundos depois)
        6. FIX Listener atualiza este TradeLog para SUCCESS ou FAILED
        
        O ClOrdID é a "chave" que conecta:
        - Este TradeLog (que estamos criando agora)
        - O ExecutionReport (que vai chegar depois)
    """
    try:
        # ---------------------------------------------------------------------
        # PASSO 1: Extrair dados do sinal
        # ---------------------------------------------------------------------
        
        # Símbolo do ativo (ex: EURUSD, GBPUSD)
        symbol = signal_details.get('symbol_id', 'UNKNOWN')
        
        # Lado da operação: 'buy' ou 'sell'
        side = signal_details.get('side', 'unknown')
        
        # Quantidade em lotes (ex: 0.01, 1.0, 5.0)
        quantity = signal_details.get('quantity_in_lots', 0)
        
        # Preço de entrada planejado (pode ser diferente do real)
        entry_price = signal_details.get('entry_price', 0)
        
        # Stop Loss planejado
        sl_price = signal_details.get('sl_price', 0)
        
        # Take Profit planejado
        tp_price = signal_details.get('tp_price', 0)
        
        # Comentário da ordem
        comment = signal_details.get('comment', f'FIX-{clordid}')
        
        # ---------------------------------------------------------------------
        # PASSO 2: Montar dados da requisição (para auditoria)
        # ---------------------------------------------------------------------
        
        # Este dicionário será salvo no campo request_data (JSON)
        # Ele contém TUDO que enviamos para o broker
        # Importante para:
        # - Auditoria (saber exatamente o que foi pedido)
        # - Debug (se algo der errado)
        # - Rastreamento (conectar com ExecutionReport)
        request_data = {
            'clordid': clordid,  # ← CHAVE MAIS IMPORTANTE!
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'order_type': order_type,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"Criando TradeLog PENDING: ClOrdID={clordid}, "
            f"Symbol={symbol}, Side={side}, Qty={quantity}"
        )
        
        # ---------------------------------------------------------------------
        # PASSO 3: Criar o TradeLog no banco de dados
        # ---------------------------------------------------------------------
        
        trade_log = TradeLog.objects.create(
            # Relacionamentos
            instance=instance,  # Qual robô está operando
            user=instance.user,  # Dono do robô
            trading_account=instance.trading_account,  # Conta de trading
            
            # Status CRÍTICO: PENDING!
            # Este status indica: "Ordem enviada, aguardando confirmação"
            status=TradeLog.TradeStatus.PENDING,
            
            # Dados da ordem
            symbol=symbol,
            trade_type=side.upper(),  # BUY ou SELL
            volume=Decimal(str(quantity)),  # Quantidade (Decimal para precisão!)
            
            # Preços planejados (podem mudar após confirmação)
            price_entry=Decimal(str(entry_price)) if entry_price else None,
            sl_price=Decimal(str(sl_price)) if sl_price else None,
            tp_price=Decimal(str(tp_price)) if tp_price else None,
            
            # Dados JSON para auditoria
            request_data=request_data,  # O que enviamos
            response_data={},  # Será preenchido quando ExecutionReport chegar
            
            # Comentários
            comment=f"Ordem FIX enviada. Aguardando confirmação. ClOrdID: {clordid}",
            
            # Ticket ainda não temos (só teremos quando broker confirmar)
            order_ticket=None  # Será preenchido pelo ExecutionReportHandler
        )
        
        logger.info(
            f"TradeLog ID={trade_log.id} criado com status PENDING. "
            f"ClOrdID={clordid}"
        )
        
        return trade_log
        
    except Exception as e:
        # Se der erro ao criar TradeLog, registra mas não quebra o sistema
        logger.error(
            f"Erro ao criar TradeLog PENDING para ClOrdID={clordid}: {e}",
            exc_info=True
        )
        return None



# ┌─────────────────────────────────────────────────────────────┐
# │ FUNÇÃO 2: Execução MT5 (RENOMEADA - código antigo)          │
# └─────────────────────────────────────────────────────────────┘

def _execute_via_mt5(instance, signal_details):
    """Executa via MT5"""
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

                # CORREÇÃO: Usar dados REAIS do symbol_info (já obtido acima nesta função!)
                # SOLUÇÃO: Converter distância de PREÇO para TICKS primeiro
                # trade_tick_size: tamanho de 1 tick (menor variação de preço)
                # trade_tick_value: quanto vale 1 tick em USD para 1 lote
                # Obtém tick_size e tick_value REAIS do symbol_info
                # (symbol_info já foi obtido algumas linhas acima nesta mesma função!)
                tick_size = Decimal(str(symbol_info.trade_tick_size))
                tick_value = Decimal(str(symbol_info.trade_tick_value))
                logger.info(
                    f"[RISK_MG] Dados reais do símbolo: "
                    f"TickSize={tick_size}, TickValue=${tick_value}"
                )

                # Converter distância de PREÇO para número de TICKS
                # Exemplo: 0.0050 / 0.0001 = 50 ticks
                ticks_in_sl = sl_distance / tick_size
                # Calcular perda potencial CORRETA
                # Fórmula: Ticks × Valor_por_Tick × Lotes
                # Exemplo: 50 ticks × $10/tick × 1 lote = $500
                potential_loss = ticks_in_sl * tick_value * lot_size
                logger.info(
                    f"[RISK_MG] Cálculo de perda potencial (CORRIGIDO): "
                    f"SL Distance={sl_distance}, "
                    f"Ticks={ticks_in_sl}, "
                    f"TickValue=${tick_value}, "
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




# ┌─────────────────────────────────────────────────────────────┐
# │ FUNÇÃO 3: Execução FIX (NOVA)                               │
# └─────────────────────────────────────────────────────────────┘
def _execute_via_fix(instance: ActiveRobotInstance, signal_details: dict):
    """
    Executa ordem via FIX Protocol (Assíncrono).
    
    Fluxo FIX:
    1. Valida campos obrigatórios
    2. Aplica gestão de risco (mesmas regras do MT5)
    3. Gera ClOrdID único
    4. Cria TradeLog com status PENDING
    5. Envia ordem via FIX
    6. Retorna imediatamente (não espera confirmação)
    7. ExecutionReportHandler atualiza TradeLog quando broker confirmar
    
    Diferença vs MT5:
    - MT5: Síncrono (espera resposta, status final imediato)
    - FIX: Assíncrono (retorna PENDING, atualizado depois)
    
    Args:
        instance: Instância do robô ativo
        signal_details: Detalhes do sinal de trading
        
    Returns:
        TradeLog: Log com status PENDING (ou None se erro antes de enviar)
    """
    import time
    import traceback
    from trading_platform.utils.fix_connection_manager import get_fix_connector
    
    account = instance.trading_account
    user = instance.user
    symbol = signal_details.get("symbol")
    
    try:
        # =====================================================================
        # VALIDAÇÃO 1: Campos Obrigatórios (IGUAL MT5)
        # =====================================================================
        required_keys = ["symbol", "trade_type_str", "stop_loss_base"]
        if not all(key in signal_details for key in required_keys):
            missing = [k for k in required_keys if k not in signal_details]
            raise ValueError(f"Sinal inválido. Chaves faltando: {missing}")
        
        logger.info(
            f"[FIX_ENGINE] Iniciando execução FIX para {symbol} "
            f"(Conta: {account.account_login})"
        )
        
        # =====================================================================
        # VALIDAÇÃO 2: Gestão de Risco - Max Open Positions
        # =====================================================================
        # TODO: Implementar consulta de posições via FIX
        # Por enquanto, apenas log
        logger.info(
            f"[FIX_ENGINE] Validação de max_open_positions "
            f"(TODO: implementar via FIX)"
        )
        
        # =====================================================================
        # VALIDAÇÃO 3: Gestão de Risco - Cálculo de Risco por Trade
        # =====================================================================
        # Mesma lógica do MT5, mas sem precisar conectar ao MT5
        
        # Obter saldo da conta (armazenado no banco)
        current_balance = account.current_balance
        
        if current_balance > Decimal('0'):
            # -----------------------------------------------------------------
            # Converter para Decimal
            # -----------------------------------------------------------------
            balance = Decimal(str(current_balance))
            lot_size = instance.lot_size  # Já é Decimal
            
            # -----------------------------------------------------------------
            # Calcular distância até Stop Loss
            # -----------------------------------------------------------------
            entry_price = Decimal(str(signal_details.get('entry_price', 0)))
            sl_price = Decimal(str(signal_details.get('stop_loss_base', 0)))
            
            if entry_price > Decimal('0') and sl_price > Decimal('0'):
                sl_distance = abs(entry_price - sl_price)
                
                # -----------------------------------------------------------------
                # CORREÇÃO: Cálculo de risco sem symbol_info do MT5
                #
                # PROBLEMA: No fluxo FIX não temos conexão MT5 aberta aqui.
                # Não podemos chamar symbol_info.trade_tick_size/trade_tick_value.
                #
                # SOLUÇÃO: Normalizar manualmente para pips usando o preço de entrada.
                # O preço de entrada já está disponível em 'entry_price' (calculado acima).
                #
                # LÓGICA DE DETECÇÃO AUTOMÁTICA:
                # - Pares JPY têm preço ALTO (ex: USDJPY = 155.00)
                #   → 1 pip = 0.01 → multiplicador = 100
                # - Pares normais têm preço BAIXO (ex: EURUSD = 1.0850)
                #   → 1 pip = 0.0001 → multiplicador = 10.000
                # -----------------------------------------------------------------
                
                # Detecta automaticamente o tipo de par pelo preço de entrada
                if entry_price > Decimal('10'):
                    # Par com JPY ou similar (preço > 10, menos casas decimais)
                    # Exemplo: USDJPY=155.00, EURJPY=168.00
                    # 1 pip = 0.01, então multiplicamos por 100
                    pip_multiplier = Decimal('100')
                else:
                    # Par Forex padrão (preço < 10, 4 ou 5 casas decimais)
                    # Exemplo: EURUSD=1.0850, GBPUSD=1.2700
                    # 1 pip = 0.0001, então multiplicamos por 10.000
                    pip_multiplier = Decimal('10000')
                
                # Converte distância de PREÇO para PIPS
                # Exemplo EURUSD: 0.0050 × 10.000 = 50 pips ✅
                # Exemplo USDJPY: 0.50 × 100 = 50 pips ✅
                # (vs código antigo: 0.0050 × $10 = $0.05 ❌)
                pips_in_sl = sl_distance * pip_multiplier
                
                # $10 por pip para 1 lote padrão (válido para pares USD cotados)
                # Funciona para: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, etc.
                value_per_pip = Decimal('10.0')
                
                # Calcula perda potencial CORRETA
                # Fórmula: Pips × Valor_por_Pip × Lotes
                # Exemplo: 50 pips × $10/pip × 1 lote = $500 ✅
                potential_loss = pips_in_sl * value_per_pip * lot_size
                
                logger.info(
                    f"[FIX_ENGINE][RISK_MG] Cálculo de risco: "
                    f"SL Distance={sl_distance}, "
                    f"Pip Multiplier={pip_multiplier}, "
                    f"Pips={pips_in_sl}, "
                    f"Value/pip=${value_per_pip}, "
                    f"Lot Size={lot_size}, "
                    f"Potential Loss=${potential_loss}"
                )
                
                # Calcular percentual de risco
                risk_percent = (potential_loss / balance) * Decimal('100')
                risk_percent_rounded = risk_percent.quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP
                )
                
                logger.info(
                    f"[FIX_ENGINE][RISK_MG] Risco calculado: {risk_percent_rounded}% "
                    f"(${potential_loss} de ${balance})"
                )
                
                # -----------------------------------------------------------------
                # Validar limite de risco
                # -----------------------------------------------------------------
                max_risk_allowed = Decimal(str(user.profile.max_risk_per_trade))
                
                if risk_percent_rounded > max_risk_allowed:
                    logger.warning(
                        f"[FIX_ENGINE][RISK_MG] ⚠️ TRADE BLOQUEADO! "
                        f"Risco {risk_percent_rounded}% > {max_risk_allowed}%"
                    )
                    
                    # Criar log de trade bloqueado
                    TradeLog.objects.create(
                        instance=instance,
                        user=user,
                        trading_account=account,
                        status=TradeLog.TradeStatus.FAILED,
                        request_data=signal_details,
                        comment=f"Trade bloqueado: Risco {risk_percent_rounded}% excede limite de {max_risk_allowed}%",
                        symbol=symbol
                    )
                    
                    # Notificar usuário
                    Notification.objects.create(
                        user=user,
                        message=f"Trade bloqueado por excesso de risco: {symbol} ({risk_percent_rounded}%)",
                        notification_type=Notification.NotificationType.WARNING
                    )
                    
                    # Retorna sem executar
                    return None
                
                else:
                    logger.info(
                        f"[FIX_ENGINE][RISK_MG] ✅ Trade aprovado. "
                        f"Risco {risk_percent_rounded}% <= {max_risk_allowed}%"
                    )
        
        # =====================================================================
        # PREPARAR DADOS DA ORDEM
        # =====================================================================
        
        # Lado da operação (FIX usa números: 1=Buy, 2=Sell)
        trade_type_str = signal_details['trade_type_str'].lower()
        side = 1 if trade_type_str == 'buy' else 2
        
        # Quantidade em lotes
        quantity = float(instance.lot_size)  # FIX aceita float
        
        # Preços
        entry_price_float = float(signal_details.get('entry_price', 0))
        sl_price_float = float(signal_details.get('stop_loss_base', 0))
        
        # Take Profit (calcular se não vier)
        tp_price_float = signal_details.get('take_profit', None)
        if not tp_price_float and sl_price_float and entry_price_float:
            risco_retorno = signal_details.get('risco_retorno', 1.5)
            sl_distance_float = abs(entry_price_float - sl_price_float)
            
            if trade_type_str == 'buy':
                tp_price_float = entry_price_float + (sl_distance_float * risco_retorno)
            else:
                tp_price_float = entry_price_float - (sl_distance_float * risco_retorno)
        
        # =====================================================================
        # GERAR CLORDID ÚNICO
        # =====================================================================
        # ClOrdID = Identificador único da nossa ordem
        # Formato: FIX_{instance_id}_{timestamp_milissegundos}
        # Exemplo: FIX_42_1738425678123
        
        timestamp_ms = int(time.time() * 1000)
        clordid = f"FIX_{instance.id}_{timestamp_ms}"
        
        logger.info(
            f"[FIX_ENGINE] Ordem preparada: "
            f"ClOrdID={clordid}, Symbol={symbol}, "
            f"Side={'BUY' if side == 1 else 'SELL'}, "
            f"Qty={quantity}, Entry={entry_price_float}, "
            f"SL={sl_price_float}, TP={tp_price_float}"
        )
        
        # =====================================================================
        # CRIAR TRADELOG COM STATUS PENDING
        # =====================================================================
        trade_log = create_pending_trade_log(
            instance=instance,
            signal_details=signal_details,
            clordid=clordid,
            order_type='FIX'
        )
        
        if not trade_log:
            logger.error(
                f"[FIX_ENGINE] ❌ Falha ao criar TradeLog PENDING "
                f"para ClOrdID={clordid}"
            )
            return None
        
        logger.info(
            f"[FIX_ENGINE] TradeLog ID={trade_log.id} criado com status PENDING"
        )
        
        # =====================================================================
        # OBTER CONECTOR FIX DO POOL
        # =====================================================================
        try:
            connector = get_fix_connector(account)
            
            if not connector:
                raise ConnectionError(
                    f"Não foi possível obter conector FIX para {account.account_login}"
                )
            
            logger.info(
                f"[FIX_ENGINE] Conector FIX obtido para {account.account_login}"
            )
        
        except Exception as e:
            logger.error(
                f"[FIX_ENGINE] ❌ Erro ao obter conector FIX: {e}",
                exc_info=True
            )
            
            # Atualizar TradeLog para FAILED
            trade_log.status = TradeLog.TradeStatus.FAILED
            trade_log.comment = f"Erro ao conectar FIX: {str(e)}"
            trade_log.save()
            
            # Notificar usuário
            Notification.objects.create(
                user=user,
                message=f"❌ Erro de conexão FIX: {symbol}",
                notification_type=Notification.NotificationType.ERROR
            )
            
            return None
        
        # =====================================================================
        # ENVIAR ORDEM VIA FIX PROTOCOL
        # =====================================================================
        try:
            success = connector.build_and_send_new_order_single(
                clordid=clordid,
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type='1',  # 1 = Market Order (ordem a mercado)
                sl_price=sl_price_float if sl_price_float else None,
                tp_price=tp_price_float if tp_price_float else None
            )
            
            if success:
                logger.info(
                    f"[FIX_ENGINE] ✅ Ordem FIX enviada com SUCESSO! "
                    f"ClOrdID={clordid}, Symbol={symbol}, "
                    f"TradeLog ID={trade_log.id}"
                )
                
                # Atualizar comentário do TradeLog
                trade_log.comment = (
                    f"Ordem FIX enviada com sucesso. "
                    f"Aguardando confirmação do broker. "
                    f"ClOrdID: {clordid}"
                )
                trade_log.save()
                
                # Notificar usuário
                Notification.objects.create(
                    user=user,
                    message=(
                        f"📤 Ordem FIX enviada: {symbol} "
                        f"({quantity} lotes - {'COMPRA' if side == 1 else 'VENDA'}). "
                        f"Aguardando confirmação..."
                    ),
                    notification_type=Notification.NotificationType.INFO
                )
                
                # Retornar TradeLog (ainda PENDING)
                # O ExecutionReportHandler vai atualizar quando confirmação chegar
                return trade_log
            
            else:
                # Falha ao enviar (função retornou False)
                logger.error(
                    f"[FIX_ENGINE] ❌ Falha ao enviar ordem FIX! "
                    f"ClOrdID={clordid}, Symbol={symbol}"
                )
                
                # Atualizar TradeLog para FAILED
                trade_log.status = TradeLog.TradeStatus.FAILED
                trade_log.comment = "Falha ao enviar ordem via FIX Protocol (função retornou False)"
                trade_log.save()
                
                # Notificar usuário
                Notification.objects.create(
                    user=user,
                    message=f"❌ Falha ao enviar ordem FIX: {symbol}",
                    notification_type=Notification.NotificationType.ERROR
                )
                
                return None
        
        except Exception as e:
            # Exceção durante envio
            logger.error(
                f"[FIX_ENGINE] ❌ Exceção ao enviar ordem FIX: {e}",
                exc_info=True
            )
            
            # Atualizar TradeLog para FAILED
            trade_log.status = TradeLog.TradeStatus.FAILED
            trade_log.comment = f"Exceção ao enviar ordem FIX: {str(e)}"
            trade_log.save()
            
            # Notificar usuário
            Notification.objects.create(
                user=user,
                message=f"❌ Erro ao enviar ordem FIX: {symbol} ({str(e)})",
                notification_type=Notification.NotificationType.ERROR
            )
            
            return None
    
    except Exception as e:
        # Exceção crítica em qualquer parte do processo
        logger.critical(
            f"[FIX_ENGINE] 🔥 EXCEÇÃO CRÍTICA para {account.account_login}: {e}",
            exc_info=True
        )
        
        # Criar TradeLog de EXCEÇÃO
        TradeLog.objects.create(
            instance=instance,
            user=user,
            trading_account=account,
            status=TradeLog.TradeStatus.EXCEPTION,
            request_data=signal_details,
            comment=f"Exceção crítica FIX: {traceback.format_exc()}",
            symbol=symbol
        )
        
        # Notificar usuário
        Notification.objects.create(
            user=user,
            message=f"🔥 Erro crítico no robô {instance.strategy.name} (FIX)",
            notification_type=Notification.NotificationType.ERROR
        )
        
        return None


def execute_trade_from_signal(instance: ActiveRobotInstance, signal_details: dict):
    """
    Função Mestra de Execução V16.0 - Com suporte a MT5 e FIX Protocol.
    
    NOVIDADE:
    Agora detecta automaticamente qual protocolo usar baseado na 
    configuração da conta (TradingAccount.trading_protocol).
    
    Fluxos suportados:
    - MT5: Síncrono (resposta imediata, TradeLog criado com status final)
    - FIX: Assíncrono (TradeLog PENDING, atualizado pelo ExecutionReportHandler)
    """
    # =========================================================================
    # ROTEAMENTO POR PROTOCOLO (NOVO)
    # =========================================================================
    
    # Obtém a conta de trading associada à instância do robô
    account = instance.trading_account
    # Detecta qual protocolo está configurado para esta conta
    protocol = account.trading_protocol

    # =========================================================================
    # DECISÃO: Qual função chamar?
    # =========================================================================
    
    if protocol == 'FIX':
        # ✅ Usar FIX Protocol (cTrader, brokers profissionais)
        logger.info(
            f"[TRADE_ROUTER] → Roteando para _execute_via_fix() "
            f"(Assíncrono)"
        )
        return _execute_via_fix(instance, signal_details)
    elif protocol == 'MT5':
        # ✅ Usar MetaTrader 5 (maioria dos brokers retail)
        logger.info(
            f"[TRADE_ROUTER] → Roteando para _execute_via_mt5() "
            f"(Síncrono)"
        )
        return _execute_via_mt5(instance, signal_details)
    else:
        # ❌ Protocolo desconhecido (não deveria acontecer devido às choices)
        logger.error(
            f"[TRADE_ROUTER] ❌ Protocolo desconhecido: '{protocol}' "
            f"para conta {account.account_login}"
        )
        
        # Criar log de erro
        TradeLog.objects.create(
            instance=instance,
            user=instance.user,
            trading_account=account,
            status=TradeLog.TradeStatus.EXCEPTION,
            request_data=signal_details,
            comment=f"Protocolo de trading inválido: {protocol}",
            symbol=signal_details.get('symbol', 'UNKNOWN')
        )
        
        # Notificar usuário
        Notification.objects.create(
            user=instance.user,
            message=f"Erro: Protocolo '{protocol}' não suportado",
            notification_type=Notification.NotificationType.ERROR
        )
        
        return None



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