# -*- coding: utf-8 -*-
"""
Módulo: execution_report_handler.py
Descrição: Processa mensagens ExecutionReport (Tag 35=8) do protocolo FIX
           e atualiza o banco de dados com confirmações/rejeições de ordens.
"""

import logging
from decimal import Decimal
from django.utils import timezone
from trading_platform.models import TradeLog, Notification

logger = logging.getLogger(__name__)

class ExecutionReportHandler:
    """
    Classe responsável por processar ExecutionReports do FIX Protocol
    e atualizar o banco de dados de acordo com o status da ordem.
    """
    
    def __init__(self):
        """Inicializa o handler."""
        self.logger = logger
    
    # =========================================================================
    # MÉTODO PRINCIPAL: Processar ExecutionReport
    # =========================================================================
    
    def process_execution_report(self, fix_message):
        """
        Processa uma mensagem ExecutionReport (Tag 35=8) recebida do broker.
        
        Args:
            fix_message (simplefix.FixMessage): Mensagem FIX recebida
            
        Returns:
            dict: Dicionário com dados extraídos do ExecutionReport
        """
        try:
            # -----------------------------------------------------------------
            # PASSO 1: Extrair campos principais do ExecutionReport
            # -----------------------------------------------------------------
            
            # ClOrdID (Tag 11): ID da ordem enviada pelo cliente
            # Este é o identificador único que usamos para rastrear a ordem
            clord_id = self._get_field_value(fix_message, 11, 'ClOrdID')
            
            # OrderID (Tag 37): ID da ordem atribuído pelo broker
            # Este é o número de ticket que o broker usa
            order_id = self._get_field_value(fix_message, 37, 'OrderID')
            
            # ExecType (Tag 150): Tipo de execução
            # 0 = New (nova ordem aceita)
            # 1 = Partial Fill (preenchimento parcial)
            # 2 = Fill (ordem totalmente preenchida) ← ESTE É O IMPORTANTE!
            # 4 = Cancelled (cancelada)
            # 8 = Rejected (rejeitada) ← ESTE TAMBÉM É IMPORTANTE!
            exec_type = self._get_field_value(fix_message, 150, 'ExecType')
            
            # OrdStatus (Tag 39): Status atual da ordem
            # 0 = New
            # 1 = Partially Filled
            # 2 = Filled ← CONFIRMAÇÃO DE SUCESSO!
            # 4 = Cancelled
            # 8 = Rejected ← ORDEM REJEITADA!
            ord_status = self._get_field_value(fix_message, 39, 'OrdStatus')
            
            # Symbol (Tag 55): Símbolo do ativo
            symbol = self._get_field_value(fix_message, 55, 'Symbol')
            
            # Side (Tag 54): Lado da ordem (1=Buy, 2=Sell)
            side = self._get_field_value(fix_message, 54, 'Side')
            
            # OrderQty (Tag 38): Quantidade da ordem
            order_qty = self._get_field_value(fix_message, 38, 'OrderQty')
            
            # LastPx (Tag 31): Preço da última execução (preço real de entrada)
            last_px = self._get_field_value(fix_message, 31, 'LastPx')
            
            # CumQty (Tag 14): Quantidade total executada até agora
            cum_qty = self._get_field_value(fix_message, 14, 'CumQty')
            
            # Text (Tag 58): Mensagem de texto (usado para erros)
            text_msg = self._get_field_value(fix_message, 58, 'Text', required=False)
            
            # -----------------------------------------------------------------
            # PASSO 2: Criar dicionário com dados estruturados
            # -----------------------------------------------------------------
            
            report_data = {
                'clord_id': clord_id.decode() if isinstance(clord_id, bytes) else clord_id,
                'order_id': order_id.decode() if isinstance(order_id, bytes) else order_id,
                'exec_type': exec_type.decode() if isinstance(exec_type, bytes) else exec_type,
                'ord_status': ord_status.decode() if isinstance(ord_status, bytes) else ord_status,
                'symbol': symbol.decode() if isinstance(symbol, bytes) else symbol,
                'side': side.decode() if isinstance(side, bytes) else side,
                'order_qty': float(order_qty) if order_qty else 0.0,
                'last_px': float(last_px) if last_px else 0.0,
                'cum_qty': float(cum_qty) if cum_qty else 0.0,
                'text': text_msg.decode() if isinstance(text_msg, bytes) and text_msg else '',
                'timestamp': timezone.now()
            }
            
            self.logger.info(
                f"ExecutionReport recebido: "
                f"ClOrdID={report_data['clord_id']}, "
                f"OrderID={report_data['order_id']}, "
                f"OrdStatus={report_data['ord_status']}, "
                f"ExecType={report_data['exec_type']}"
            )
            
            # -----------------------------------------------------------------
            # PASSO 3: Processar de acordo com o status
            # -----------------------------------------------------------------
            
            # OrdStatus='2' ou ExecType='2' = FILLED (Ordem preenchida!)
            if report_data['ord_status'] == '2' or report_data['exec_type'] == '2':
                self._handle_order_filled(report_data)
            
            # OrdStatus='8' ou ExecType='8' = REJECTED (Ordem rejeitada!)
            elif report_data['ord_status'] == '8' or report_data['exec_type'] == '8':
                self._handle_order_rejected(report_data)
            
            # OrdStatus='4' ou ExecType='4' = CANCELLED (Ordem cancelada)
            elif report_data['ord_status'] == '4' or report_data['exec_type'] == '4':
                self._handle_order_cancelled(report_data)
            
            # OrdStatus='0' = NEW (Ordem aceita pelo broker, aguardando execução)
            elif report_data['ord_status'] == '0':
                self._handle_order_new(report_data)
            
            # OrdStatus='1' = PARTIALLY FILLED (Preenchimento parcial)
            elif report_data['ord_status'] == '1':
                self._handle_order_partial_fill(report_data)
            
            else:
                self.logger.warning(
                    f"OrdStatus desconhecido: {report_data['ord_status']} "
                    f"para ordem {report_data['clord_id']}"
                )
            
            return report_data
            
        except Exception as e:
            self.logger.error(
                f"Erro ao processar ExecutionReport: {e}",
                exc_info=True
            )
            return None
    
    # =========================================================================
    # HANDLERS PARA CADA TIPO DE STATUS
    # =========================================================================
    
    def _handle_order_filled(self, report_data):
        """
        Processa ordem que foi TOTALMENTE PREENCHIDA (OrdStatus=2).
        ESTE É O CASO DE SUCESSO!
        
        Args:
            report_data (dict): Dados extraídos do ExecutionReport
        """
        self.logger.info(
            f"✅ ORDEM PREENCHIDA: ClOrdID={report_data['clord_id']}, "
            f"OrderID={report_data['order_id']}, "
            f"Symbol={report_data['symbol']}, "
            f"Qty={report_data['cum_qty']}, "
            f"Price={report_data['last_px']}"
        )
        
        try:
            # Busca o TradeLog correspondente pelo ClOrdID
            # O ClOrdID foi gerado em build_and_send_new_order_single()
            # e deveria ter sido salvo no TradeLog com status='PENDING'
            trade_log = TradeLog.objects.filter(
                broker_order_id=report_data['clord_id']
            ).first()
                        
            if not trade_log:
                self.logger.error(
                    f"TradeLog não encontrado para ClOrdID={report_data['clord_id']}. "
                    f"A ordem pode ter sido enviada fora do sistema."
                )
                return
            
            # Atualiza o TradeLog com os dados da confirmação
            trade_log.status = TradeLog.TradeStatus.SUCCESS
            trade_log.order_ticket = report_data['order_id']  # Ticket do broker
            trade_log.price_entry = Decimal(str(report_data['last_px']))  # Preço real de entrada
            trade_log.volume = Decimal(str(report_data['cum_qty']))  # Quantidade executada
            
            # Adiciona dados do ExecutionReport ao response_data
            if not trade_log.response_data:
                trade_log.response_data = {}
            
            trade_log.response_data['execution_report'] = {
                'order_id': report_data['order_id'],
                'exec_type': report_data['exec_type'],
                'ord_status': report_data['ord_status'],
                'last_px': report_data['last_px'],
                'cum_qty': report_data['cum_qty'],
                'timestamp': report_data['timestamp'].isoformat()
            }
            
            trade_log.comment = f"Ordem executada com sucesso. Ticket: {report_data['order_id']}"
            trade_log.save()
            
            # Criar notificação para o usuário
            Notification.objects.create(
                user=trade_log.user,
                message=f"Ordem executada: {report_data['symbol']} "
                        f"({report_data['cum_qty']} lotes a {report_data['last_px']})",
                notification_type=Notification.NotificationType.SUCCESS
            )
            
            self.logger.info(f"TradeLog ID={trade_log.id} atualizado com sucesso (FILLED)")
            
        except Exception as e:
            self.logger.error(
                f"Erro ao atualizar TradeLog para ordem preenchida: {e}",
                exc_info=True
            )
    
    def _handle_order_rejected(self, report_data):
        """
        Processa ordem que foi REJEITADA pelo broker (OrdStatus=8).
        ESTE É UM ERRO CRÍTICO!
        
        Motivos comuns:
        - Margem insuficiente
        - Mercado fechado
        - Símbolo inválido
        - Quantidade inválida
        
        Args:
            report_data (dict): Dados extraídos do ExecutionReport
        """
        self.logger.error(
            f"❌ ORDEM REJEITADA: ClOrdID={report_data['clord_id']}, "
            f"Symbol={report_data['symbol']}, "
            f"Motivo: {report_data['text']}"
        )
        
        try:
            # Busca o TradeLog correspondente
            trade_log = TradeLog.objects.filter(
                broker_order_id=report_data['clord_id']
            ).first()
            
            if not trade_log:
                self.logger.error(
                    f"TradeLog não encontrado para ordem rejeitada "
                    f"ClOrdID={report_data['clord_id']}"
                )
                return
            
            # Atualiza o TradeLog com status de falha
            trade_log.status = TradeLog.TradeStatus.FAILED
            trade_log.comment = f"Ordem rejeitada pelo broker. Motivo: {report_data['text']}"
            
            # Adiciona dados do ExecutionReport
            if not trade_log.response_data:
                trade_log.response_data = {}
            
            trade_log.response_data['execution_report'] = {
                'exec_type': report_data['exec_type'],
                'ord_status': report_data['ord_status'],
                'reject_reason': report_data['text'],
                'timestamp': report_data['timestamp'].isoformat()
            }
            
            trade_log.save()
            
            # Criar notificação de ERRO para o usuário
            Notification.objects.create(
                user=trade_log.user,
                message=f"❌ Ordem rejeitada: {report_data['symbol']}. "
                        f"Motivo: {report_data['text']}",
                notification_type=Notification.NotificationType.ERROR
            )
            
            self.logger.info(f"TradeLog ID={trade_log.id} atualizado (REJECTED)")
            
        except Exception as e:
            self.logger.error(
                f"Erro ao processar ordem rejeitada: {e}",
                exc_info=True
            )
    
    def _handle_order_cancelled(self, report_data):
        """
        Processa ordem que foi CANCELADA (OrdStatus=4).
        
        Args:
            report_data (dict): Dados extraídos do ExecutionReport
        """
        self.logger.warning(
            f"⚠️ ORDEM CANCELADA: ClOrdID={report_data['clord_id']}, "
            f"Symbol={report_data['symbol']}"
        )
        
        try:
            trade_log = TradeLog.objects.filter(
                broker_order_id=report_data['clord_id']
            ).first()
            
            if trade_log:
                trade_log.status = TradeLog.TradeStatus.FAILED
                trade_log.comment = f"Ordem cancelada. {report_data['text']}"
                trade_log.save()
                
                Notification.objects.create(
                    user=trade_log.user,
                    message=f"Ordem cancelada: {report_data['symbol']}",
                    notification_type=Notification.NotificationType.WARNING
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao processar ordem cancelada: {e}")
    
    def _handle_order_new(self, report_data):
        """
        Processa ordem que foi ACEITA pelo broker (OrdStatus=0).
        A ordem foi aceita mas ainda não foi executada.
        
        Args:
            report_data (dict): Dados extraídos do ExecutionReport
        """
        self.logger.info(
            f"🔄 ORDEM ACEITA (aguardando execução): "
            f"ClOrdID={report_data['clord_id']}, "
            f"OrderID={report_data['order_id']}"
        )
        
        try:
            trade_log = TradeLog.objects.filter(
                broker_order_id=report_data['clord_id']
            ).first()
            
            if trade_log:
                # Atualiza com o OrderID do broker
                trade_log.order_ticket = report_data['order_id']
                trade_log.comment = f"Ordem aceita pelo broker. Ticket: {report_data['order_id']}"
                trade_log.save()
                
        except Exception as e:
            self.logger.error(f"Erro ao processar ordem aceita: {e}")
    
    def _handle_order_partial_fill(self, report_data):
        """
        Processa ordem que foi PARCIALMENTE PREENCHIDA (OrdStatus=1).
        
        Args:
            report_data (dict): Dados extraídos do ExecutionReport
        """
        self.logger.info(
            f"🔸 PREENCHIMENTO PARCIAL: "
            f"ClOrdID={report_data['clord_id']}, "
            f"Executado={report_data['cum_qty']}/{report_data['order_qty']}"
        )
        
        try:
            trade_log = TradeLog.objects.filter(
                broker_order_id=report_data['clord_id']
            ).first()
            
            if trade_log:
                trade_log.comment = (
                    f"Preenchimento parcial: "
                    f"{report_data['cum_qty']}/{report_data['order_qty']} lotes"
                )
                trade_log.save()
                
        except Exception as e:
            self.logger.error(f"Erro ao processar preenchimento parcial: {e}")
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _get_field_value(self, fix_message, tag, field_name, required=True):
        """
        Extrai o valor de um campo (tag) da mensagem FIX.
        
        Args:
            fix_message: Mensagem FIX
            tag (int): Número da tag FIX
            field_name (str): Nome do campo (para logs)
            required (bool): Se o campo é obrigatório
            
        Returns:
            bytes ou None: Valor do campo
        """
        value = fix_message.get_value(tag)
        
        if required and not value:
            raise ValueError(f"Campo obrigatório {field_name} (Tag {tag}) não encontrado")
        
        return value