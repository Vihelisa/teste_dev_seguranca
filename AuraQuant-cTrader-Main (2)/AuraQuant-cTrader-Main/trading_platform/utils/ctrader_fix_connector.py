# -*- coding: utf-8 -*-
"""
Módulo: ctrader_fix_connector.py
Autor: Jules, Engenheiro Quantitativo Sênior
Descrição: Este módulo fornece uma interface robusta e de baixa latência para interagir
com a API FIX da cTrader (ou qualquer servidor FIX padrão). Ele gerencia o ciclo de vida
da conexão, a troca de mensagens de sessão e a execução de ordens de trading.
Protocolo: PHOENIX ASCENSION
"""

import simplefix
import socket
import ssl
import threading
import time
import logging
from datetime import datetime, timezone
from queue import Queue, Empty

# ============================================================================
# IMPORT DO HANDLER DE EXECUTION REPORT (NOVO)
# ============================================================================
try:
    from .execution_report_handler import ExecutionReportHandler
except ImportError:
    # Se falhar (ex: em ambiente de testes), define como None
    ExecutionReportHandler = None
    logging.warning("ExecutionReportHandler não pôde ser importado")

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

class FIXConnector:
    """
    Uma classe para gerenciar uma sessão de trading FIX completa, incluindo
    conexões separadas para cotações (QUOTE) and ordens (TRADE).
    """
    def __init__(self, trade_config, quote_config, fix_version="FIX.4.4"):
        """
        Inicializa o conector com as configurações para os endpoints de TRADE e QUOTE.

        Args:
            trade_config (dict): Dicionário com as credenciais para o endpoint de ordens.
                                 Ex: {'host': ..., 'port': ..., 'sender_id': ..., 'target_id': ..., 'password': ...}
            quote_config (dict): Dicionário com as credenciais para o endpoint de cotações.
            fix_version (str): A versão do protocolo FIX a ser usada (BeginString).
        """
        self.trade_config = trade_config
        self.quote_config = quote_config
        self.fix_version = fix_version

        # Sockets e contextos SSL
        self.trade_socket = None
        self.quote_socket = None
        self.ssl_context = ssl.create_default_context()

        # Estado da sessão
        self.is_connected_trade = False
        self.is_connected_quote = False
        self.trade_seq_num = 1
        self.quote_seq_num = 1

        # Threads para operações em background
        self.trade_listener_thread = None
        self.quote_listener_thread = None
        self.trade_heartbeat_thread = None
        self.quote_heartbeat_thread = None

        # Filas para comunicação entre threads
        self.trade_message_queue = Queue()
        self.quote_message_queue = Queue()

        # Controle de encerramento
        self._stop_event = threading.Event()

        # =========================================================================
        # ADICIONAR: Instância do ExecutionReportHandler (NOVO)
        # =========================================================================
        # Cria uma instância do handler para processar ExecutionReports
        # Este handler será chamado automaticamente quando recebermos
        # uma mensagem de confirmação do broker
        # CORRETO:
        if ExecutionReportHandler:
            self.execution_handler = ExecutionReportHandler()
            logger.info("ExecutionReportHandler inicializado")
        else:
            self.execution_handler = None
            logger.warning("ExecutionReportHandler não disponível")  # ← só no else
        # Callback opcional para processar mensagens customizadas
        # Isso permite que código externo registre funções que serão
        # chamadas quando mensagens específicas chegarem
        self.message_callbacks = {}
        # =========================================================================
        # PREÇOS EM TEMPO REAL (FEED QUOTE)
        # =========================================================================
        # Armazena o último preço recebido por símbolo via feed QUOTE
        # Formato: { 'EURUSD': Decimal('1.08523'), 'USDJPY': Decimal('155.342') }
        # Atualizado automaticamente pelo _handle_received_message ao receber
        # mensagens W (MarketDataSnapshot) e X (MarketDataIncrementalRefresh)
        self.last_prices = {}


    def _create_fix_client(self):
        """Cria uma instância do cliente simplefix."""
        return simplefix.FixClient()

    def connect(self):
        """
        Estabelece as conexões SSL para os endpoints de TRADE e QUOTE e inicia o processo de logon.
        """
        logger.info("Iniciando conexão FIX...")
        try:
            # Conexão TRADE
            logger.info(f"Conectando ao endpoint TRADE em {self.trade_config['host']}:{self.trade_config['port']}...")
            sock_trade = socket.create_connection((self.trade_config['host'], self.trade_config['port']))
            self.trade_socket = self.ssl_context.wrap_socket(sock_trade, server_hostname=self.trade_config['host'])
            logger.info("Socket TRADE conectado e envolto em SSL.")

            # Conexão QUOTE
            logger.info(f"Conectando ao endpoint QUOTE em {self.quote_config['host']}:{self.quote_config['port']}...")
            sock_quote = socket.create_connection((self.quote_config['host'], self.quote_config['port']))
            self.quote_socket = self.ssl_context.wrap_socket(sock_quote, server_hostname=self.quote_config['host'])
            logger.info("Socket QUOTE conectado e envolto em SSL.")

            # Iniciar listeners antes do logon para capturar a resposta
            self._start_listener_thread('trade')
            self._start_listener_thread('quote')

            # Processo de Logon
            self._send_logon('trade')
            self._send_logon('quote')

            # Aguardar confirmação de logon (simplificado, uma implementação real teria um timeout e verificação de estado)
            time.sleep(5) # Dando tempo para as respostas de logon chegarem

            # Iniciar threads de heartbeat após logon bem-sucedido
            self._start_heartbeat_thread('trade')
            self._start_heartbeat_thread('quote')

            self.is_connected_trade = True
            self.is_connected_quote = True
            logger.info("Conexão FIX estabelecida e threads de background iniciadas.")

        except Exception as e:
            logger.critical(f"Falha crítica durante a conexão FIX: {e}", exc_info=True)
            self.disconnect()
            raise

    def disconnect(self):
        """
        Envia mensagens de Logoff e fecha as conexões de forma graciosa.
        """
        logger.info("Iniciando desconexão FIX...")
        self._stop_event.set() # Sinaliza para todas as threads terminarem

        # Envia mensagem de Logoff para as sessões ativas
        if self.is_connected_trade:
            self._send_logout('trade')
        if self.is_connected_quote:
            self._send_logout('quote')

        time.sleep(2) # Espera para garantir que as mensagens foram enviadas

        # Fecha os sockets
        if self.trade_socket:
            self.trade_socket.close()
            self.is_connected_trade = False
            logger.info("Socket TRADE fechado.")
        if self.quote_socket:
            self.quote_socket.close()
            self.is_connected_quote = False
            logger.info("Socket QUOTE fechado.")

        logger.info("Desconexão FIX concluída.")

    def _get_session_details(self, session_type):
        """Retorna os detalhes corretos da sessão (config, socket, seq_num, etc.)."""
        if session_type == 'trade':
            return self.trade_config, self.trade_socket, self.trade_seq_num, self.trade_message_queue
        elif session_type == 'quote':
            return self.quote_config, self.quote_socket, self.quote_seq_num, self.quote_message_queue
        else:
            raise ValueError("Tipo de sessão inválido. Use 'trade' ou 'quote'.")

    def _update_seq_num(self, session_type, new_seq_num):
        """Atualiza o número de sequência para a sessão especificada."""
        if session_type == 'trade':
            self.trade_seq_num = new_seq_num
        elif session_type == 'quote':
            self.quote_seq_num = new_seq_num

    def _send_message(self, message, session_type):
        """Codifica e envia uma mensagem FIX, incrementando o número de sequência."""
        config, sock, seq_num, _ = self._get_session_details(session_type)

        # Preenche os cabeçalhos padrão
        message.append_pair(8, self.fix_version)
        message.append_pair(35, message.get_value(35))
        message.append_pair(49, config['sender_id'])
        message.append_pair(56, config['target_id'])
        if 'sender_sub_id' in config:
             message.append_pair(50, config['sender_sub_id'])
        message.append_pair(34, seq_num)
        message.append_pair(52, datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3])

        # Codifica a mensagem
        encoded_message = message.encode()
        logger.debug(f"Enviando [{session_type.upper()}] ->: {encoded_message.replace(b'\\x01', b'|')}")

        # Envia pelo socket
        sock.sendall(encoded_message)

        # Incrementa o número de sequência
        self._update_seq_num(session_type, seq_num + 1)

    def _send_logon(self, session_type):
        """Constrói e envia uma mensagem de Logon (A)."""
        config, _, _, _ = self._get_session_details(session_type)
        logon_msg = simplefix.FixMessage()
        logon_msg.append_pair(35, "A")
        logon_msg.append_pair(98, 0)  # EncryptMethod: None
        logon_msg.append_pair(108, 30) # HeartBtInt: 30 segundos
        logon_msg.append_pair(554, config['password']) # Password

        logger.info(f"Enviando mensagem de Logon para a sessão {session_type.upper()}.")
        self._send_message(logon_msg, session_type)

    def _send_logout(self, session_type):
        """Constrói e envia uma mensagem de Logoff (5)."""
        logout_msg = simplefix.FixMessage()
        logout_msg.append_pair(35, "5")
        logger.info(f"Enviando mensagem de Logoff para a sessão {session_type.upper()}.")
        try:
            self._send_message(logout_msg, session_type)
        except Exception as e:
            logger.error(f"Erro ao enviar logoff para {session_type}: {e}")

    def _send_heartbeat(self, session_type):
        """Constrói e envia uma mensagem de Heartbeat (0)."""
        heartbeat_msg = simplefix.FixMessage()
        heartbeat_msg.append_pair(35, "0")
        self._send_message(heartbeat_msg, session_type)

    def _handle_received_message(self, message, session_type):
        """
        Processa uma mensagem FIX recebida.
        Agora com suporte a ExecutionReport!
        """
        # Extrai o tipo de mensagem (Tag 35)
        msg_type = message.get_value(35)

        # =========================================================================
        # CASE 1: Test Request (Tag 35=1)
        # =========================================================================
        # O broker está testando se estamos vivos
        # Precisamos responder com um Heartbeat
        if msg_type == b'1':
            logger.info(f"[{session_type.upper()}] Test Request recebido. Respondendo com Heartbeat.")
            
            # Obtém o ID do Test Request (se houver)
            test_req_id = message.get_value(112)
            
            # Cria mensagem de Heartbeat como resposta
            hb_msg = simplefix.FixMessage()
            hb_msg.append_pair(35, "0")  # Tag 35=0 → Heartbeat
            if test_req_id:
                hb_msg.append_pair(112, test_req_id)  # Inclui mesmo ID
            
            # Envia o Heartbeat de volta
            self._send_message(hb_msg, session_type)

        # =========================================================================
        # CASE 2: Heartbeat (Tag 35=0)
        # =========================================================================
        # Mensagem de "estou vivo" do broker
        # Apenas registramos no log, não precisa fazer nada
        elif msg_type == b'0':
            logger.debug(f"[{session_type.upper()}] Heartbeat do servidor recebido.")

        # =========================================================================
        # CASE 3: MarketDataSnapshot (Tag 35=W)
        # =========================================================================
        # Mensagem completa de snapshot de preço para um símbolo
        # Recebida após enviar um MarketDataRequest ao broker
        # Contém: Bid (Tag 270 com Tag 269=0) e Ask (Tag 270 com Tag 269=1)
        elif msg_type == b'W':
            self._parse_and_store_price(message, 'W')

        # =========================================================================
        # CASE 4: MarketDataIncrementalRefresh (Tag 35=X)
        # =========================================================================
        # Atualização incremental de preço (apenas o que mudou)
        # Chega continuamente durante a sessão QUOTE ativa
        elif msg_type == b'X':
            self._parse_and_store_price(message, 'X')

        # =========================================================================
        # CASE 5: ExecutionReport (Tag 35=8) ← NOVO!
        # =========================================================================
        # Esta é a mensagem mais importante!
        # Confirma se a ordem foi executada, rejeitada, etc.
        elif msg_type == b'8':
            logger.info(f"[{session_type.upper()}] ExecutionReport recebido!")
            
            # =====================================================================
            # PROCESSAR COM O HANDLER
            # =====================================================================
            # Verifica se o handler está disponível
            if self.execution_handler:
                try:
                    # Chama o método principal do handler
                    # Este método vai:
                    # 1. Extrair dados da mensagem
                    # 2. Identificar o tipo de status
                    # 3. Atualizar o banco de dados
                    report_data = self.execution_handler.process_execution_report(message)
                    
                    # Log de sucesso
                    if report_data:
                        logger.info(
                            f"ExecutionReport processado: "
                            f"ClOrdID={report_data['clord_id']}, "
                            f"Status={report_data['ord_status']}"
                        )
                    
                except Exception as e:
                    # Se der erro, registra mas não quebra o sistema
                    logger.error(
                        f"Erro ao processar ExecutionReport: {e}",
                        exc_info=True  # Inclui stack trace completo
                    )
            else:
                # Handler não está disponível
                # Apenas coloca na fila para processamento manual
                logger.warning("ExecutionReportHandler não disponível. Mensagem colocada na fila.")
                _, _, _, queue = self._get_session_details(session_type)
                queue.put(message)
            
            # =====================================================================
            # CHAMAR CALLBACKS CUSTOMIZADOS (se registrados)
            # =====================================================================
            # Permite que código externo também processe a mensagem
            if '8' in self.message_callbacks:
                try:
                    self.message_callbacks['8'](message)
                except Exception as e:
                    logger.error(f"Erro no callback customizado para ExecutionReport: {e}")

        # =========================================================================
        # CASE 4: Outras mensagens
        # =========================================================================
        # Qualquer outro tipo de mensagem vai para a fila
        # Pode ser processado externamente se necessário
        else:
            _, _, _, queue = self._get_session_details(session_type)
            queue.put(message)
            
            # Se houver callback registrado para este tipo, chama
            msg_type_str = msg_type.decode() if isinstance(msg_type, bytes) else msg_type
            if msg_type_str in self.message_callbacks:
                try:
                    self.message_callbacks[msg_type_str](message)
                except Exception as e:
                    logger.error(f"Erro no callback para tipo {msg_type_str}: {e}")

    def _listener_loop(self, session_type):
        """Loop que escuta por mensagens no socket e as processa."""
        config, sock, _, _ = self._get_session_details(session_type)
        client = self._create_fix_client()

        while not self._stop_event.is_set():
            try:
                # Leitura não bloqueante para permitir verificação do _stop_event
                sock.settimeout(1.0)
                data = sock.recv(4096)
                if not data:
                    logger.warning(f"[{session_type.upper()}] Conexão fechada pelo servidor.")
                    break

                client.append_buffer(data)

                while True:
                    try:
                        message = client.get_message()
                        if message is None:
                            break
                        logger.debug(f"Recebido [{session_type.upper()}] <-: {message.encode().replace(b'\\x01', b'|')}")
                        self._handle_received_message(message, session_type)
                    except simplefix.FixParserError as e:
                        logger.error(f"[{session_type.upper()}] Erro de parsing FIX: {e}")
                        break # Sai do loop interno para obter mais dados

            except socket.timeout:
                continue # Volta ao início do loop while para checar o stop_event
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"[{session_type.upper()}] Erro no listener: {e}", exc_info=True)
                break
        logger.info(f"Thread listener para {session_type.upper()} terminando.")

    def _heartbeat_loop(self, session_type):
        """Loop que envia heartbeats em intervalos regulares."""
        while not self._stop_event.wait(30): # Espera por 30 segundos ou até o evento ser setado
            try:
                self._send_heartbeat(session_type)
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"[{session_type.upper()}] Erro ao enviar heartbeat: {e}", exc_info=True)
                break
        logger.info(f"Thread de heartbeat para {session_type.upper()} terminando.")

    def _start_listener_thread(self, session_type):
        """Inicia a thread de escuta de mensagens para uma sessão."""
        thread = threading.Thread(target=self._listener_loop, args=(session_type,), daemon=True)
        thread.start()
        if session_type == 'trade':
            self.trade_listener_thread = thread
        else:
            self.quote_listener_thread = thread
        logger.info(f"Thread listener para {session_type.upper()} iniciada.")

    def _start_heartbeat_thread(self, session_type):
        """Inicia a thread de envio de heartbeats para uma sessão."""
        thread = threading.Thread(target=self._heartbeat_loop, args=(session_type,), daemon=True)
        thread.start()
        if session_type == 'trade':
            self.trade_heartbeat_thread = thread
        else:
            self.quote_heartbeat_thread = thread
        logger.info(f"Thread de heartbeat para {session_type.upper()} iniciada.")

    def get_message(self, session_type, block=True, timeout=None):
        """
        Obtém a próxima mensagem da fila da sessão especificada.

        Args:
            session_type (str): 'trade' ou 'quote'.
            block (bool): Se a chamada deve bloquear até um item estar disponível.
            timeout (float): Tempo máximo em segundos para esperar.

        Returns:
            simplefix.FixMessage ou None se a fila estiver vazia e block for False.
        """
        _, _, _, queue = self._get_session_details(session_type)
        try:
            return queue.get(block=block, timeout=timeout)
        except Empty:
            return None

    def build_and_send_new_order_single(self, clordid, symbol, side, quantity, order_type='1', sl_price=None, tp_price=None):
        """
        Constrói e envia uma mensagem NewOrderSingle (D).

        Args:
            clordid (str): ID único da ordem do cliente.
            symbol (str): O ativo a ser negociado.
            side (int): 1 para Compra (Buy), 2 para Venda (Sell).
            quantity (float): A quantidade a ser negociada.
            order_type (str): '1' para Ordem a Mercado (Market).
            sl_price (float, optional): Preço de Stop Loss.
            tp_price (float, optional): Preço de Take Profit.

        Returns:
            bool: True se a mensagem foi enviada, False caso contrário.
        """
        if not self.is_connected_trade:
            logger.error("Não é possível enviar ordem: sessão TRADE não está conectada.")
            return False

        order_msg = simplefix.FixMessage()
        order_msg.append_pair(35, "D")  # NewOrderSingle
        order_msg.append_pair(11, clordid)
        order_msg.append_pair(55, symbol)
        order_msg.append_pair(54, side)
        order_msg.append_pair(38, int(quantity)) # OrderQty, geralmente como inteiro
        order_msg.append_pair(40, order_type) # OrdType
        order_msg.append_pair(59, "0") # TimeInForce: 0 = Day

        # Adiciona SL e TP se fornecidos
        # A implementação exata (tags) pode variar entre corretoras
        if sl_price:
             order_msg.append_pair(99, sl_price) # Tag 99 é comumente usada para StopPx
        # TP pode não ter uma tag padrão universalmente aceita em NewOrderSingle
        # e pode precisar ser enviado como uma ordem separada ou via outras tags.
        # Esta implementação é um exemplo e deve ser validada com a corretora.

        logger.info(f"Enviando NewOrderSingle: ClOrdID={clordid}, Symbol={symbol}, Side={side}, Qty={quantity}")
        self._send_message(order_msg, 'trade')
        return True

    def close_all_market_orders(self, positions):
        """
        Fecha uma lista de posições abertas enviando ordens opostas a mercado.

        Args:
            positions (list): Lista de dicionários {'symbol': str, 'side': int, 'volume': float}.
                              Side deve ser o lado da posição ABERTA (1=Buy, 2=Sell).
                              A função enviará uma ordem com o lado OPOSTO.
        """
        if not self.is_connected_trade:
            logger.error("Não é possível fechar ordens: sessão TRADE não está conectada.")
            return

        for pos in positions:
            try:
                symbol = pos['symbol']
                open_side = pos['side'] # 1 (Buy) ou 2 (Sell)
                volume = pos['volume']

                # Lado oposto para fechar: Se Buy(1) -> Sell(2). Se Sell(2) -> Buy(1).
                close_side = 2 if open_side == 1 else 1

                clordid = f"close_{symbol}_{int(time.time() * 1000)}"
                logger.warning(f"KILL SWITCH: Fechando posição {symbol} (Side: {open_side}) com ordem oposta (Side: {close_side}).")

                self.build_and_send_new_order_single(
                    clordid=clordid,
                    symbol=symbol,
                    side=close_side,
                    quantity=volume
                )
                time.sleep(0.2) # Breve pausa para não inundar o servidor
            except Exception as e:
                logger.error(f"Erro ao tentar fechar posição {pos}: {e}")

    
    # ... métodos existentes acima ...
    
    def register_message_callback(self, msg_type, callback_function):
        """
        Registra uma função callback para ser chamada quando
        uma mensagem de determinado tipo for recebida.
        
        Args:
            msg_type (str): Tipo da mensagem FIX (ex: '8' para ExecutionReport)
            callback_function (callable): Função a ser chamada quando mensagem chegar
            
        Exemplo de uso:
            def meu_processador(message):
                print(f"Recebi mensagem: {message}")
            
            connector.register_message_callback('8', meu_processador)
        """
        self.message_callbacks[msg_type] = callback_function
        logger.info(f"Callback registrado para tipo de mensagem: {msg_type}")
    
    def unregister_message_callback(self, msg_type):
        """
        Remove um callback previamente registrado.
        
        Args:
            msg_type (str): Tipo da mensagem FIX
        """
        if msg_type in self.message_callbacks:
            del self.message_callbacks[msg_type]
            logger.info(f"Callback removido para tipo de mensagem: {msg_type}")

    def _parse_and_store_price(self, message, msg_type_label):
        """
        Extrai o preço Bid/Ask de uma mensagem de MarketData (W ou X)
        e armazena em self.last_prices para consulta posterior.

        Protocolo FIX — tags relevantes:
        Tag 55  = Symbol (ex: b'EURUSD')
        Tag 269 = MDEntryType: b'0'=Bid, b'1'=Ask
        Tag 270 = MDEntryPx (o preço em si)

        Usamos o MID PRICE (média de Bid e Ask) como referência,
        pois é o mais neutro para cálculo de risco e validação de sinal.
        """
        from decimal import Decimal, InvalidOperation

        try:
            # Extrai símbolo
            symbol_raw = message.get_value(55)
            if not symbol_raw:
                return
            symbol = symbol_raw.decode() if isinstance(symbol_raw, bytes) else symbol_raw

            # Extrai tipo de entrada e preço
            # Nota: simplefix retorna o último valor das tags repetidas.
            # Para uma implementação completa com MDEntryType correto,
            # seria necessário iterar sobre os grupos repetidos.
            # Para V1.0, usamos Tag 270 diretamente como referência de preço.
            price_raw = message.get_value(270)
            if not price_raw:
                return

            price_str = price_raw.decode() if isinstance(price_raw, bytes) else price_raw
            price = Decimal(price_str)

            # Armazena o preço
            self.last_prices[symbol] = price

            logger.debug(
                f"[QUOTE FEED] {msg_type_label} → {symbol} = {price}"
            )

        except (InvalidOperation, AttributeError, Exception) as e:
            logger.warning(f"[QUOTE FEED] Falha ao parsear preço ({msg_type_label}): {e}")

    def get_last_price(self, symbol):
        """
        Retorna o último preço recebido via feed QUOTE para um símbolo.

        Args:
            symbol (str): Nome do símbolo (ex: 'EURUSD', 'USDJPY')

        Returns:
            Decimal: Último preço conhecido, ou None se ainda não recebido.

        Uso no tasks.py:
            fix_price = fix_connector.get_last_price('EURUSD')
            if fix_price:
                # usa preço real do FIX
            else:
                # usa preço do sinal (fallback)
        """
        return self.last_prices.get(symbol, None)
