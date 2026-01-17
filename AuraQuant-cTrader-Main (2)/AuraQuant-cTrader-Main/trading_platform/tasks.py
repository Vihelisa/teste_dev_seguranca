# trading_platform/tasks.py (VERSÃO V1.0 GOLD - COM GUARDIÃO ATIVO)
import logging
import json
import traceback
import os
import time
import datetime as dt
import uuid
import openai
import joblib

import pandas as pd
import numpy as np
from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.core.cache import cache

# Importação dos modelos (incluindo Notification para o Guardião)
from trading_platform.models import Strategy, ActiveRobotInstance, TradeLog, TradingAccount, Notification
from trading_platform.quant_engine import backtester
from trading_platform.utils.ctrader_fix_connector import FIXConnector
from trading_platform.quant_engine.decision_engine import analyze_and_get_signal

logger = logging.getLogger(__name__)

# =============================================================================
#           SERIALIZADOR JSON
# =============================================================================
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (dt.datetime, pd.Timestamp)): return obj.isoformat()
        if pd.isna(obj): return None
        if isinstance(obj, BaseException): return str(obj)
        try: return super(NpEncoder, self).default(obj)
        except TypeError: return str(obj)

# =============================================================================
#           TAREFA DE VALIDAÇÃO (BACKTESTING)
# =============================================================================
@shared_task(name='trading_platform.tasks.run_validation_task', bind=True, queue='backtesting_heavy')
def run_validation_task(self, strategy_id):
    logger.info(f"CELERY WORKER (Backtest): Iniciando validação para Strategy ID: {strategy_id}")
    try:
        strategy = Strategy.objects.get(id=strategy_id)

        # Busca credenciais de DADOS (MT5) no .env/settings
        mt5_login = getattr(settings, 'MT5_DATA_LOGIN', None)
        mt5_password = getattr(settings, 'MT5_DATA_PASSWORD', None)
        mt5_server = getattr(settings, 'MT5_DATA_SERVER', None)

        # Fallback graceful se não configurado (usa conexão padrão/manual se disponível)
        if not all([mt5_login, mt5_password, mt5_server]):
             logger.warning("Credenciais MT5_DATA_* não configuradas no .env. Tentando conexão padrão do terminal.")
        else:
             logger.info(f"Usando a conta MT5 {mt5_login} dos settings como fonte de dados.")

        final_results = backtester.run_strategy_backtest(
            strategy_name=strategy.strategy_file,
            strategy_id=strategy.id,
            assets=[asset.strip() for asset in strategy.assets.split(',')],
            params=strategy.portfolio_composition,
            capital_inicial=float(strategy.suggested_capital),
            dias=strategy.backtest_period_days
        )
        with transaction.atomic():
            strategy_to_update = Strategy.objects.select_for_update().get(id=strategy_id)
            strategy_to_update.celery_task_id = None
            strategy_to_update.backtest_results = json.loads(json.dumps(final_results, cls=NpEncoder))
            strategy_to_update.is_public = True
            strategy_to_update.save()

        logger.info(f"CELERY WORKER (Backtest): VALIDAÇÃO PARA '{strategy.name}' CONCLUÍDA.")
        return f"Sucesso: {strategy.name}"

    except Exception as e:
        logger.critical(f"!!!!!! ERRO CRÍTICO NA VALIDAÇÃO (ID: {strategy_id}) !!!!!!\n{traceback.format_exc()}")
        try:
            strategy_to_fail = Strategy.objects.get(id=strategy_id)
            strategy_to_fail.backtest_results = {"status": "FAILED", "error_message": str(e)}
            strategy_to_fail.celery_task_id = None
            strategy_to_fail.save()
        except Strategy.DoesNotExist:
            logger.error(f"Não foi possível salvar o estado de falha, pois a Strategy ID {strategy_id} não foi encontrada.")
        raise e

# =============================================================================
#           MOTOR DE EXECUÇÃO EM TEMPO REAL (GUARDIÃO ATIVO)
# =============================================================================
@shared_task(name='trading_platform.tasks.master_monitor_supervisor', bind=True, queue='realtime_trading')
def master_monitor_supervisor(self):
    logger.info("[SUPERVISOR] Iniciando verificação de monitores de conta...")
    active_account_ids = ActiveRobotInstance.objects.filter(is_active=True).values_list('trading_account_id', flat=True).distinct()

    if not active_account_ids.exists():
        logger.info("[SUPERVISOR] Nenhuma conta com robôs ativos encontrada.")
        return

    for account_id in active_account_ids:
        lock_key = f"account_monitor_lock_{account_id}"
        # Se o lock não existe, significa que o monitor caiu ou nunca iniciou
        if cache.get(lock_key) is None:
            logger.warning(f"[SUPERVISOR] Monitor para conta {account_id} inativo. Iniciando...")
            run_account_monitor_task.delay(account_id)
        else:
            logger.info(f"[SUPERVISOR] Monitor para conta {account_id} operante.")

    logger.info("[SUPERVISOR] Verificação concluída.")


@shared_task(name='trading_platform.tasks.run_account_monitor_task', bind=True, queue='realtime_trading')
def run_account_monitor_task(self, account_id):
    """
    [MOTOR DE EXECUÇÃO V1.0]
    - Gerencia conexão FIX persistente.
    - Carrega IA em memória.
    - Executa trades via Decision Engine.
    - IMPLEMENTA O GUARDIÃO (KILL SWITCH) de Risco Global.
    """
    log_prefix = f"[ACC_WORKER #{account_id}]"
    lock_key = f"account_monitor_lock_{account_id}"
    lock_timeout = 60 * 5 # 5 minutos
    if not cache.add(lock_key, "running", timeout=lock_timeout): return

    logger.info(f"{log_prefix} Lock adquirido. Iniciando monitoramento.")
    fix_connector = None

    try:
        account = TradingAccount.objects.get(id=account_id)
        # Busca o perfil para saber o limite de drawdown do Guardião
        user_profile = account.user.profile
        global_dd_limit = float(user_profile.global_drawdown_limit)

        active_instances = list(ActiveRobotInstance.objects.filter(trading_account=account, is_active=True).select_related('strategy'))
        if not active_instances:
            logger.info(f"{log_prefix} Nenhuma instância ativa. Encerrando."); cache.delete(lock_key); return

        # 1. Carregar Modelos de IA (Em Memória)
        saved_ia_map = {}
        for instance in active_instances:
            model_rel_path = instance.strategy.ml_model_path.name if instance.strategy.ml_model_path else None
            if model_rel_path and instance.strategy.strategy_file not in saved_ia_map:
                try:
                    model_full_path = os.path.join(settings.MEDIA_ROOT, model_rel_path)
                    saved_ia_map[instance.strategy.strategy_file] = joblib.load(model_full_path)
                    logger.info(f"{log_prefix} Modelo de IA para '{instance.strategy.strategy_file}' carregado.")
                except Exception as e: logger.error(f"{log_prefix} Falha ao carregar modelo '{model_rel_path}': {e}")

        if not saved_ia_map:
            logger.warning(f"{log_prefix} Nenhum modelo de IA carregado. Robôs podem não operar corretamente.")

        # 2. Conectar ao Broker (FIX)
        password = account.get_password()
        sender_id = f"demo.fpmarkets.{account.account_login}"
        trade_config = { 'host': account.server, 'port': 5212, 'sender_id': sender_id, 'target_id': 'cServer', 'sender_sub_id': 'TRADE', 'password': password }
        quote_config = {**trade_config, 'port': 5211, 'sender_sub_id': 'QUOTE'}

        fix_connector = FIXConnector(trade_config, quote_config)
        fix_connector.connect()

        # Aguardar logon
        start_time = time.time()
        while not (fix_connector.is_connected_trade):
            if time.time() - start_time > 20: raise ConnectionError("Timeout no logon FIX do monitor.")
            time.sleep(1)

        # Inicialização do Estado Financeiro (Guardião)
        # Nota: Em V1.0, assumimos um saldo inicial base para o cálculo de DD da sessão.
        # Em produção real, deveríamos fazer um 'RequestForPositions' via FIX para obter o saldo exato.
        # Usamos o saldo do banco como referência inicial.
        saldo_inicial_sessao = float(account.current_balance) if account.current_balance else 10000.0
        logger.info(f"{log_prefix} Guardião Ativo. Limite de Drawdown: {global_dd_limit}% (Saldo Ref: {saldo_inicial_sessao})")

        # Rastreador de posições abertas nesta sessão: { 'clordid': {'symbol':..., 'volume':..., 'side':...} }
        # [PHOENIX COMPLIANCE] State Persistence using Cache (Redis)
        # Initialize from cache if available (worker restart recovery)
        cache_key_pos = f"birdstone:positions:{account.id}"
        open_positions_tracker = cache.get(cache_key_pos) or {}

        # --- 3. Loop Principal ---
        while True:
            cache.touch(lock_key, lock_timeout) # Heartbeat para o Supervisor

            # A. [GUARDIÃO] Cálculo de Risco e Kill Switch
            # -----------------------------------------------------------
            # Simulação de Shadow Accounting (P&L Flutuante)
            # (Necessário pois FIX não faz streaming de Equity)
            floating_pnl = 0.0
            # TODO: Implementar fix_connector.get_last_price(symbol) para precisão real.
            # Por enquanto, assumimos P&L zero se não tivermos update de preço, para não crashar.

            current_equity = saldo_inicial_sessao + floating_pnl
            current_drawdown_pct = 0.0
            if saldo_inicial_sessao > 0:
                current_drawdown_pct = ((saldo_inicial_sessao - current_equity) / saldo_inicial_sessao) * 100

            if current_drawdown_pct >= global_dd_limit:
                logger.critical(f"{log_prefix} 🚨 KILL SWITCH ACIONADO! DD Atual ({current_drawdown_pct:.2f}%) > Limite ({global_dd_limit}%). FECHANDO TUDO.")

                # 1. Protocolo de Emergência: Fechar posições rastreadas
                positions_to_close = list(open_positions_tracker.values())
                if positions_to_close:
                    fix_connector.close_all_market_orders(positions_to_close)
                    open_positions_tracker = {} # Limpa lista
                    cache.set(cache_key_pos, open_positions_tracker, timeout=None) # Update Redis

                # 2. Desativar Robôs no Banco de Dados
                for inst in active_instances:
                    inst.is_active = False
                    inst.save()

                # 3. Notificar Usuário
                Notification.objects.create(
                    user=account.user,
                    message=f"URGENTE: O Guardião parou seus robôs! Limite de perda global ({global_dd_limit}%) foi atingido.",
                    notification_type='ERROR'
                )
                break # Encerra o loop imediatamente

            # B. Lógica de Trading (O Cérebro)
            # -----------------------------------------------------------
            for instance in active_instances:
                if instance.strategy.strategy_file in saved_ia_map:
                    # Passa o mapa de IA para o decision_engine
                    trade_request = analyze_and_get_signal(instance, instance.strategy.strategy_file, saved_ia_map.get(instance.strategy.strategy_file), log_prefix)

                    if trade_request:
                        logger.info(f"{log_prefix} ✅ CÉREBRO GEROU ORDEM: {trade_request}")
                        clordid = str(uuid.uuid4())

                        # Mapeamento de side string para int FIX
                        side_int = 1 if trade_request['side'] == 'Buy' else 2

                        success = fix_connector.build_and_send_new_order_single(
                            clordid=clordid,
                            symbol=trade_request['symbol_id'],
                            side=side_int,
                            quantity=trade_request['quantity_in_lots']
                        )

                        if success:
                            logger.info(f"{log_prefix} 🚀 ORDEM ENVIADA VIA FIX. ClOrdID: {clordid}")
                            # Adiciona ao rastreador do Guardião
                            open_positions_tracker[clordid] = {
                                'symbol': trade_request['symbol_id'],
                                'volume': trade_request['quantity_in_lots'],
                                'side': side_int
                            }
                            cache.set(cache_key_pos, open_positions_tracker, timeout=None) # Persist to Redis

                            # Registro de Auditoria
                            TradeLog.objects.create(
                                instance=instance, user=instance.user, trading_account=account,
                                status='SUCCESS',
                                symbol=trade_request['symbol_id'], trade_type=trade_request['side'],
                                volume=trade_request['quantity_in_lots'], broker_order_id=clordid,
                                comment="Ordem enviada pelo Motor de Execução."
                            )

            time.sleep(getattr(settings, 'TRADING_CYCLE_INTERVAL_SECONDS', 5))

            # Verifica se o usuário desativou manualmente os robôs pelo painel
            if not ActiveRobotInstance.objects.filter(id__in=[i.id for i in active_instances], is_active=True).exists():
                logger.info(f"{log_prefix} Todas as instâncias foram desativadas manualmente. Encerrando.")
                break

    except Exception as e:
        logger.critical(f"{log_prefix} Erro fatal no monitor: {e}", exc_info=True)
    finally:
        if fix_connector: fix_connector.disconnect()
        cache.delete(lock_key)
        logger.info(f"{log_prefix} Monitoramento finalizado.")

# =============================================================================
#           TAREFAS AUXILIARES
# =============================================================================
@shared_task(name='trading_platform.tasks.close_positions_task', bind=True, queue='realtime_trading')
def close_positions_task(self, account_id, strategy_id, user_id):
    logger.warning("A tarefa 'close_positions_task' é LEGADA e não foi executada.")
    return "Tarefa legada não executada."

@shared_task(name="trading_platform.tasks.simple_ping_task")
def simple_ping_task(message: str):
    result = f"PONG! Mensagem: '{message}' em {dt.datetime.now()}"
    logger.info(f"[PING_TASK] {result}")
    return result

@shared_task(name="trading_platform.tasks.send_test_order_task")
def send_test_order_task(instance_id: int, symbol_id: str = "1", side: str = "Buy"):
    logger.info(f"[TAREFA INICIADA] - send_test_order_task para instância ID: {instance_id}")
    try:
        instance = ActiveRobotInstance.objects.select_related('trading_account', 'user').get(pk=instance_id)
        if not instance.is_active: return f"ERRO: Instância {instance_id} inativa."

        account = instance.trading_account; password = account.get_password()
        sender_id = f"demo.fpmarkets.{account.account_login}"
        trade_config = { 'host': account.server, 'port': 5212, 'sender_id': sender_id, 'target_id': 'cServer', 'sender_sub_id': 'TRADE', 'password': password }
        quote_config = {**trade_config, 'port': 5211, 'sender_sub_id': 'QUOTE'}

        connector = FIXConnector(trade_config, quote_config)
        connector.connect()
        time.sleep(2) # Wait for logon

        clordid = str(uuid.uuid4())
        side_int = 1 if side == 'Buy' else 2
        success = connector.build_and_send_new_order_single(clordid, symbol_id, side_int, float(instance.lot_size))
        connector.disconnect()

        if success:
            TradeLog.objects.create(instance=instance, user=instance.user, trading_account=account, status='SUCCESS',
                                  symbol=symbol_id, trade_type=side, volume=instance.lot_size, broker_order_id=clordid, comment="Teste de Ordem OK.")
            return "SUCESSO: Ordem de teste enviada."
        return "ERRO: Falha no envio."
    except Exception as e:
        logger.error(f"Erro na tarefa de teste: {e}", exc_info=True)
        raise e

@shared_task(name="trading_platform.tasks.generate_portfolio_analysis_task")
def generate_portfolio_analysis_task(analysis_id):
    """
    Processa a solicitação de análise de portfólio usando OpenAI (GPT-4).
    """
    from .models import PortfolioAnalysis

    logger.info(f"[AURA AI] Iniciando análise {analysis_id}...")
    try:
        analysis = PortfolioAnalysis.objects.get(id=analysis_id)

        # Montagem do Prompt
        prompt_system = """
        Você é Aura, uma analista quantitativa sênior da Birdstone.
        Sua missão é criar um portfólio de investimentos personalizado e profissional.
        Retorne APENAS um JSON válido seguindo estritamente a estrutura solicitada.
        Não inclua markdown ou texto fora do JSON.
        """

        prompt_user = f"""
        Perfil do Investidor:
        - Perfil de Risco: {analysis.risk_profile}
        - Objetivo: {analysis.objective}
        - Capital: R$ {analysis.amount}
        - Ativos de Interesse: {', '.join(analysis.assets_interest)}

        Gere uma análise completa JSON com os campos:
        portfolioTitle, scenarioAnalysis, allocation (lista com assetClass, percentage, justification, examples),
        riskAnalysis, returnProjection (pessimistic, expected, optimistic), nextSteps, disclaimer.
        """

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview", # Ou gpt-3.5-turbo-0125 para economia
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        result_content = response.choices[0].message.content
        result_json = json.loads(result_content)

        # Salva o resultado
        analysis.result_json = result_json
        analysis.status = PortfolioAnalysis.Status.COMPLETED
        analysis.save()

        logger.info(f"[AURA AI] Análise {analysis_id} concluída com sucesso.")
        return "OK"

    except Exception as e:
        logger.error(f"[AURA AI] Erro na análise {analysis_id}: {e}", exc_info=True)
        try:
            analysis = PortfolioAnalysis.objects.get(id=analysis_id)
            analysis.status = PortfolioAnalysis.Status.FAILED
            analysis.save()
        except:
            pass
        return "FAILED"