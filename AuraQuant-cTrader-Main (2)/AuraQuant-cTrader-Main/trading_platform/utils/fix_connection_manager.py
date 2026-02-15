# -*- coding: utf-8 -*-
"""
Módulo: fix_connection_manager.py
Descrição: Gerencia conexões FIX de forma centralizada, evitando múltiplas
           conexões desnecessárias e fornecendo pool de conectores reutilizáveis.
"""

import logging
import threading
from typing import Dict, Optional
from django.conf import settings

from .ctrader_fix_connector import FIXConnector

logger = logging.getLogger(__name__)


class FIXConnectionManager:
    """
    Singleton que gerencia conexões FIX.
    
    Responsabilidades:
    - Criar e manter pool de conexões FIX
    - Reutilizar conexões existentes
    - Garantir que cada conta tenha apenas uma conexão ativa
    - Limpar conexões inativas
    
    Pattern: Singleton + Factory
    """
    
    # Instância única (Singleton)
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """
        Garante que apenas UMA instância existe (Singleton pattern).
        
        Por que Singleton?
        - Evita múltiplas instâncias competindo por conexões
        - Centraliza o gerenciamento de todas as conexões FIX
        - Economiza recursos (memória, sockets)
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa o gerenciador (chamado apenas uma vez).
        """
        # Previne reinicialização em chamadas subsequentes
        if self._initialized:
            return
        
        # Pool de conexões: {account_login: FIXConnector}
        self.connections: Dict[str, FIXConnector] = {}
        
        # Lock para operações thread-safe
        self.connections_lock = threading.Lock()
        
        # Flag de inicialização
        self._initialized = True
        
        logger.info("FIXConnectionManager inicializado")
    
    # =========================================================================
    # MÉTODO PRINCIPAL: Obter Conector para uma Conta
    # =========================================================================
    
    def get_connector(self, account) -> Optional[FIXConnector]:
        """
        Obtém ou cria um conector FIX para uma conta de trading.
        
        Args:
            account (TradingAccount): Conta de trading
            
        Returns:
            FIXConnector: Conector ativo e pronto para uso (ou None se erro)
        
        Comportamento:
        1. Se já existe conexão para esta conta → Retorna conexão existente
        2. Se não existe → Cria nova conexão, conecta, e retorna
        3. Se conexão existe mas está inativa → Reconecta e retorna
        """
        account_login = account.account_login
        
        with self.connections_lock:
            # -----------------------------------------------------------------
            # CASO 1: Conexão já existe
            # -----------------------------------------------------------------
            if account_login in self.connections:
                connector = self.connections[account_login]
                
                # Verificar se está conectado
                if connector.is_connected_trade and connector.is_connected_quote:
                    logger.info(
                        f"[FIX_MANAGER] Reutilizando conexão existente "
                        f"para {account_login}"
                    )
                    return connector
                
                else:
                    # Conexão existe mas está inativa
                    logger.warning(
                        f"[FIX_MANAGER] Conexão para {account_login} "
                        f"está inativa. Tentando reconectar..."
                    )
                    
                    try:
                        connector.connect()
                        logger.info(
                            f"[FIX_MANAGER] Reconexão bem-sucedida "
                            f"para {account_login}"
                        )
                        return connector
                    
                    except Exception as e:
                        logger.error(
                            f"[FIX_MANAGER] Falha ao reconectar {account_login}: {e}"
                        )
                        # Remove conexão quebrada do pool
                        del self.connections[account_login]
                        return None
            
            # -----------------------------------------------------------------
            # CASO 2: Conexão não existe - Criar nova
            # -----------------------------------------------------------------
            else:
                logger.info(
                    f"[FIX_MANAGER] Criando nova conexão FIX "
                    f"para {account_login}"
                )
                
                try:
                    # Criar configurações
                    trade_config, quote_config = self._build_configs(account)
                    
                    # Criar conector
                    connector = FIXConnector(
                        trade_config=trade_config,
                        quote_config=quote_config,
                        fix_version="FIX.4.4"
                    )
                    
                    # Conectar
                    connector.connect()
                    
                    # Adicionar ao pool
                    self.connections[account_login] = connector
                    
                    logger.info(
                        f"[FIX_MANAGER] ✅ Nova conexão FIX criada e ativa "
                        f"para {account_login}"
                    )
                    
                    return connector
                
                except Exception as e:
                    logger.error(
                        f"[FIX_MANAGER] ❌ Falha ao criar conexão "
                        f"para {account_login}: {e}",
                        exc_info=True
                    )
                    return None
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _build_configs(self, account):
        """
        Constrói as configurações FIX para uma conta.
        
        Args:
            account (TradingAccount): Conta de trading
            
        Returns:
            tuple: (trade_config, quote_config)
        """
        # Obter credenciais
        password = account.get_password()  # Descriptografa senha
        login = account.account_login

        logger.info(
        f"[FIX_MANAGER] Construindo configs FIX para conta {login}"
    )
        # TODO: Estes valores devem vir de settings ou configuração da conta
        # Por enquanto, valores padrão para cTrader

        # =========================================================================
        # CONFIGURAÇÃO DO ENDPOINT TRADE (para enviar ordens)
        # =========================================================================
        
        trade_config = {
            # Host e porta do servidor FIX
            'host': settings.FIX_TRADE_HOST,
            'port': settings.FIX_TRADE_PORT,
            
            # Identificação da sessão
            'sender_id': login,  # Nosso ID = login da conta
            'target_id': settings.FIX_TARGET_ID,  # ID do servidor cTrader
            
            # Credenciais
            'password': password,
            
            # Opcional: Sub-ID (alguns brokers usam)
            # 'sender_sub_id': 'TRADE'
        }

        '''trade_config = {
            'host': getattr(settings, 'FIX_TRADE_HOST', 'h51.p.ctrader.com'),
            'port': getattr(settings, 'FIX_TRADE_PORT', 5201),
            'sender_id': account.account_login,
            'target_id': getattr(settings, 'FIX_TARGET_ID', 'CSERVER'),
            'password': password
        }'''
        
        # =========================================================================
        # CONFIGURAÇÃO DO ENDPOINT QUOTE (para receber cotações)
        # =========================================================================

        quote_config = {
            # Host e porta do servidor FIX de cotações
            'host': settings.FIX_QUOTE_HOST,
            'port': settings.FIX_QUOTE_PORT,
            
            # Identificação da sessão
            'sender_id': login,
            'target_id': settings.FIX_QUOTE_TARGET_ID,
            
            # Credenciais (mesma senha)
            'password': password,
            
            # Opcional: Sub-ID
            # 'sender_sub_id': 'QUOTE'
        }

        '''quote_config = {
            'host': getattr(settings, 'FIX_QUOTE_HOST', 'h51.p.ctrader.com'),
            'port': getattr(settings, 'FIX_QUOTE_PORT', 5211),
            'sender_id': account.account_login,
            'target_id': getattr(settings, 'FIX_QUOTE_TARGET_ID', 'QUOTE'),
            'password': password
        }'''
        
        logger.debug(
            f"[FIX_MANAGER] Configs criadas: "
            f"TRADE={trade_config['host']}:{trade_config['port']}, "
            f"QUOTE={quote_config['host']}:{quote_config['port']}"
        )
        return trade_config, quote_config
    

    def disconnect(self, account_login: str):
        """
        Desconecta e remove um conector do pool.
        
        Args:
            account_login (str): Login da conta
        """
        with self.connections_lock:
            if account_login in self.connections:
                connector = self.connections[account_login]
                
                try:
                    connector.disconnect()
                    logger.info(
                        f"[FIX_MANAGER] Desconectado: {account_login}"
                    )
                except Exception as e:
                    logger.error(
                        f"[FIX_MANAGER] Erro ao desconectar {account_login}: {e}"
                    )
                finally:
                    del self.connections[account_login]
    
    def disconnect_all(self):
        """
        Desconecta todas as conexões (útil para shutdown).
        """
        with self.connections_lock:
            for account_login in list(self.connections.keys()):
                self.disconnect(account_login)
        
        logger.info("[FIX_MANAGER] Todas as conexões FIX foram fechadas")
    
    def get_status(self) -> dict:
        """
        Retorna status de todas as conexões.
        
        Returns:
            dict: {account_login: {'trade': bool, 'quote': bool}}
        """
        status = {}
        
        with self.connections_lock:
            for account_login, connector in self.connections.items():
                status[account_login] = {
                    'trade': connector.is_connected_trade,
                    'quote': connector.is_connected_quote
                }
        
        return status


# =============================================================================
# INSTÂNCIA GLOBAL (Singleton)
# =============================================================================

# Criar instância única
fix_manager = FIXConnectionManager()


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA
# =============================================================================

def get_fix_connector(account):
    """
    Função helper para obter conector FIX.
    
    Args:
        account (TradingAccount): Conta de trading
        
    Returns:
        FIXConnector: Conector pronto para uso
    
    Exemplo de uso:
        connector = get_fix_connector(account)
        if connector:
            connector.build_and_send_new_order_single(...)
    """
    return fix_manager.get_connector(account)