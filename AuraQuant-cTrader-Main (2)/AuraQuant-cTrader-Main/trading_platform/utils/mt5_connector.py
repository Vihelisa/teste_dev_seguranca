import logging
from contextlib import contextmanager
from ..models import TradingAccount
import time

logger = logging.getLogger(__name__)

# Tenta importar a biblioteca MetaTrader5. Se falhar, define uma flag.
# Isso permite que o resto do Django funcione em ambientes onde a biblioteca não pode ser instalada (ex: Linux).
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    logger.warning("Biblioteca MetaTrader5 não encontrada. Todas as funcionalidades de trading e dados ao vivo serão desativadas.")
    MT5_AVAILABLE = False

# =============================================================================
#           GERENCIADOR DE CONEXÃO MT5 (O CONSULADO DIPLOMÁTICO)
# =============================================================================

@contextmanager
def mt5_connection(account: TradingAccount):
    """
    Gerenciador de contexto V3.2 - Portátil, Resiliente e Seguro.
    Só tenta conectar se a biblioteca MT5 estiver disponível e uma conta for fornecida.
    """
    # Se a biblioteca não estiver disponível, não faz nada e retorna None.
    if not MT5_AVAILABLE:
        yield None
        return

    # Se nenhuma conta for fornecida, não podemos prosseguir.
    if account is None:
        logger.warning("[MT5_CONNECTOR] Nenhuma conta fornecida para a conexão. A operação será pulada.")
        yield None
        return

    mt5_instance = None
    max_retries = 3
    retry_delay_seconds = 2
    account_login_info = "N/A" # Default em caso de erro inicial

    try:
        account_login_info = account.account_login
        login_id = int(account_login_info)
        password = account.get_password()
        server = account.server

        for attempt in range(max_retries):
            if mt5.initialize(login=login_id, password=password, server=server, timeout=10000):
                mt5_instance = mt5
                logger.info(f"[MT5_CONNECTOR] Conexão estabelecida para a conta {login_id} na tentativa {attempt + 1}.")
                break
            else:
                error_code, error_message = mt5.last_error()
                log_message = f"[MT5_CONNECTOR] Falha na inicialização para {login_id}. Tentativa {attempt + 1}/{max_retries}. Erro: ({error_code}) {error_message}"
                
                if error_code == -10003 and attempt < max_retries - 1:
                    logger.warning(log_message)
                    time.sleep(retry_delay_seconds)
                else:
                    logger.error(log_message)
                    break
        
        yield mt5_instance
            
    except Exception as e:
        # A variável account_login_info já foi definida, então é seguro usá-la aqui.
        logger.critical(f"[MT5_CONNECTOR] Exceção na conexão para a conta {account_login_info}: {e}")
        yield None
        
    finally:
        if mt5_instance:
            mt5.shutdown()
            # A variável account_login_info já foi definida, então é seguro usá-la aqui.
            logger.info(f"[MT5_CONNECTOR] Conexão com a conta {account_login_info} encerrada.")