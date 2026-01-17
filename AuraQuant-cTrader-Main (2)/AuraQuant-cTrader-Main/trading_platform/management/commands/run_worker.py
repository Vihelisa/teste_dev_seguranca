# C:\birdstone\trading_platform\management\commands\run_worker.py
import time
import logging
import traceback
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import close_old_connections
# Importamos os modelos e o nosso conector MT5 seguro
from trading_platform.models import ActiveRobotInstance, TradingAccount
# from trading_platform.utils.mt5_connector import mt5_connection # Comentado pois não pode ser instalado em ambiente Linux

# Configura o logger para este comando específico
logger = logging.getLogger('django.command.run_worker')

# =============================================================================
#           MAPEAMENTO DE LÓGICA DE TRADING
# =============================================================================
# No futuro, esta seção será substituída pela lógica dinâmica do `quant_engine`
# mas por enquanto, serve como um exemplo claro.

def logic_example_price_action(mt5_conn, lot_size, symbol="EURUSD"):
    """Lógica de exemplo para Price Action."""
    logger.info(f"[LOGIC_PA] Executando para {symbol} com lote {lot_size}.")
    # ... (seu código de análise e mt5.order_send() aqui) ...
    pass

def logic_example_moving_average(mt5_conn, lot_size, symbol="GBPUSD"):
    """Lógica de exemplo para Cruzamento de Médias."""
    logger.info(f"[LOGIC_MA] Executando para {symbol} com lote {lot_size}.")
    # ... (seu código de análise e mt5.order_send() aqui) ...
    pass

# O ROBOT_LOGIC_MAP associa o `strategy_file` do modelo `Strategy` à função de lógica.
ROBOT_LOGIC_MAP = {
    "price_action_example": logic_example_price_action,
    "moving_average_example": logic_example_moving_average,
}

# =============================================================================
#           O WORKER (COMANDO DE GERENCIAMENTO)
# =============================================================================
class Command(BaseCommand):
    help = 'Inicia o worker de produção que executa os robôs de trade ativos.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- [WORKER] Iniciando Worker de Robôs de Produção ---'))

        while True:
            try:
                # 1. BUSCA AS INSTÂNCIAS ATIVAS
                # `select_related` otimiza a busca, fazendo um JOIN no banco de dados e
                # evitando múltiplas queries dentro do loop.
                active_instances = ActiveRobotInstance.objects.filter(is_active=True).select_related('user', 'strategy', 'trading_account')
                
                if active_instances.exists():
                    self.stdout.write(f"[{datetime.now()}] Encontradas {active_instances.count()} instâncias ativas para processar.")
                    
                    # 2. ITERA SOBRE CADA INSTÂNCIA
                    for instance in active_instances:
                        log_prefix = f"  - [Instância #{instance.id} | Usuário: {instance.user.username}]"
                        try:
                            # 3. CONEXÃO SEGURA COM O MT5
                            # Usamos nosso `mt5_connection` para garantir que a conexão
                            # seja sempre aberta e fechada corretamente.
                            # with mt5_connection(instance.trading_account) as mt5_conn:
                            #     if not mt5_conn:
                            #         self.stderr.write(self.style.ERROR(f"{log_prefix} ERRO: Falha ao conectar na conta MT5 {instance.trading_account.account_login}."))
                            #         continue # Pula para a próxima instância

                            #     self.stdout.write(f"{log_prefix} Processando '{instance.strategy.name}'...")
                                
                            #     # 4. DESPACHO DA LÓGICA CORRETA
                            #     logic_function = ROBOT_LOGIC_MAP.get(instance.strategy.strategy_file)
                                
                            #     if logic_function:
                            #         # Executa a lógica de trading
                            #         logic_function(mt5_conn, instance.lot_size)
                            #     else:
                            #         self.stderr.write(self.style.WARNING(f"{log_prefix} AVISO: Nenhuma lógica encontrada para '{instance.strategy.strategy_file}'"))
                        
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"{log_prefix} ERRO INESPERADO: {e}\n{traceback.format_exc()}"))
                else:
                    self.stdout.write(f"[{datetime.now()}] Nenhuma instância ativa encontrada.")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"ERRO CRÍTICO no loop principal do worker: {e}\n{traceback.format_exc()}"))

            finally:
                # 5. GERENCIAMENTO DE CONEXÃO COM O BANCO
                # Em loops de longa duração, é crucial fechar conexões antigas
                # com o banco de dados para evitar "connection timeout".
                close_old_connections()

            # 6. O CICLO DE ESPERA
            self.stdout.write("--- Ciclo concluído. Aguardando 60 segundos... ---\n")
            time.sleep(60)