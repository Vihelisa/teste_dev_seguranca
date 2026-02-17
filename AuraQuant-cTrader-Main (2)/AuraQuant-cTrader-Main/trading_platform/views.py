import logging
from django.conf import settings
import traceback
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time

from django.contrib.auth.models import User
from django.db import transaction
from django.core.cache import cache
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import api_view, permission_classes, action, throttle_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from celery.result import AsyncResult
from django.core.mail import send_mail

from .models import Strategy, TradingAccount, ActiveRobotInstance, TradeLog, UserProfile, Notification, PortfolioAnalysis
from .serializers import (
    UserProfileSerializer, NotificationSerializer, StrategySerializer,
    ActiveRobotInstanceSerializer, TradingAccountSerializer, TradeLogSerializer,
    PortfolioAnalysisSerializer
)
from .tasks import run_validation_task, send_test_order_task, close_positions_task, generate_portfolio_analysis_task
from .utils.mt5_connector import mt5_connection

logger = logging.getLogger(__name__)

# =============================================================================
#           THROTTLE CLASSES CUSTOMIZADAS
# =============================================================================

class LoginRateThrottle(AnonRateThrottle):
    """Throttle específico para login — 5 tentativas por minuto."""
    scope = 'login'

class PasswordResetRateThrottle(AnonRateThrottle):
    """Throttle específico para reset de senha — 3 tentativas por minuto."""
    scope = 'password_reset'

# =============================================================================
#           HEALTHCHECK E VIEWS DE AUTENTICAÇÃO
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny]) # Healthcheck deve ser público
def healthcheck(request):
    return Response({"status": "healthy", "message": "Backend está funcionando"})

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_user(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not all([username, password]):
        return Response({"error": "Usuário e senha são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)
    
    from django.contrib.auth import authenticate
    user = authenticate(username=username, password=password)
    
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        logger.info(f"Usuário '{username}' logado com sucesso.")
        return Response({
            "token": token.key,
            "user": {"id": user.id, "email": user.email}
        })
    else:
        logger.warning(f"Falha na tentativa de login para o usuário '{username}'.")
        return Response({"error": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Retorna dados do usuário atual."""
    return Response({
        "id": request.user.id,
        "email": request.user.email,
        "username": request.user.username
    })

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def register_user(request):
    """Registra um novo usuário na plataforma."""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    # Validações de segurança
    if not all([email, password]):
        return Response({"error": "E-mail e senha são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Formato de e-mail inválido."}, status=status.HTTP_400_BAD_REQUEST)

    # Validação de senha forte
    if len(password) < 8:
        return Response({"error": "Senha deve ter pelo menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

    if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        return Response({"error": "Senha deve conter pelo menos uma letra e um número."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({"error": "Um usuário com este e-mail já existe."}, status=status.HTTP_409_CONFLICT)
    try:
        user = User.objects.create_user(username=email, email=email, password=password)
        token, _ = Token.objects.get_or_create(user=user)
        logger.info(f"Usuário '{email}' registrado com sucesso.")
        return Response({"status": "SUCESSO", "token": token.key})
    except Exception as e:
        logger.error(f"Erro ao registrar usuário '{email}': {e}\n{traceback.format_exc()}")
        return Response({"error": "Erro interno ao criar usuário."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_request(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Do not reveal that the user does not exist for security reasons.
        logger.info(f"Solicitação de redefinição de senha para email inexistente: {email}")
        return Response({'status': 'Se um usuário com este email existir, um link de redefinição foi enviado.'}, status=status.HTTP_200_OK)

    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    # The base URL of your frontend password reset page
    reset_link = f"https://plataformabeta.birdstone.com.br/reset-password?uidb64={uidb64}&token={token}"

    subject = 'Redefinição de Senha - Plataforma Birdstone'
    message = f'Olá {user.username},\n\nClique no link a seguir para redefinir sua senha:\n{reset_link}\n\nSe você não solicitou isso, por favor ignore este email.\n\nAtenciosamente,\nEquipe Birdstone'

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        logger.info(f"Email de redefinição de senha enviado para {user.email}")
    except Exception as e:
        logger.error(f"Falha ao enviar email de redefinição de senha para {user.email}: {e}")
        return Response({'error': 'Não foi possível enviar o email de redefinição.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'status': 'Se um usuário com este email existir, um link de redefinição foi enviado.'}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def password_reset_confirm(request):
    uidb64 = request.data.get('uidb64')
    token = request.data.get('token')
    password = request.data.get('password')

    if not all([uidb64, token, password]):
        return Response({'error': 'Todos os campos (uidb64, token, password) são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if user is not None and token_generator.check_token(user, token):
        # Add password validation logic here if needed
        if len(password) < 8:
             return Response({"error": "Senha deve ter pelo menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save()
        logger.info(f"Senha para o usuário {user.username} foi redefinida com sucesso.")
        return Response({'status': 'Senha redefinida com sucesso.'}, status=status.HTTP_200_OK)
    else:
        logger.warning(f"Tentativa de redefinição de senha falhou com token inválido.")
        return Response({'error': 'Link de redefinição inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Changes the password for the currently authenticated user.
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not all([current_password, new_password]):
        return Response({'error': 'Senha atual e nova senha são obrigatórias.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.check_password(current_password):
        return Response({'error': 'Senha atual incorreta.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 8:
        return Response({"error": "Nova senha deve ter pelo menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    logger.info(f"Usuário {user.username} alterou a senha com sucesso.")
    return Response({'status': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)


# =============================================================================
#           VIEWSETS PRINCIPAIS
# =============================================================================

class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    API para buscar e atualizar o perfil do usuário logado.
    Trata o perfil como um recurso singleton para o usuário autenticado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()

    def get_object(self):
        """
        Sobrescreve o método padrão para sempre retornar o perfil do usuário logado,
        criando um se não existir. Ignora o 'pk' da URL por segurança.
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if created:
            logger.info(f"UserProfile criado sob demanda para '{self.request.user.username}'.")
        return profile

    def list(self, request, *args, **kwargs):
        """
        Permite que `GET /profile/` funcione retornando o perfil do usuário.
        """
        return self.retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        """Loga a atualização do perfil."""
        serializer.save()
        logger.info(f"Perfil de '{self.request.user.username}' atualizado.")

class TradingAccountViewSet(viewsets.ModelViewSet):
    serializer_class = TradingAccountSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return TradingAccount.objects.filter(user=self.request.user).order_by('-created_at')
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    def perform_destroy(self, instance):
        with transaction.atomic():
            ActiveRobotInstance.objects.filter(trading_account=instance, is_active=True).update(is_active=False)
            instance.delete()
        logger.info(f"Conta MT5 '{instance.nickname}' deletada para '{self.request.user.username}'.")

class StrategyViewSet(viewsets.ReadOnlyModelViewSet):
    """API para visualizar estratégias públicas e gerenciar backtests."""
    queryset = Strategy.objects.filter(is_public=True).order_by('id')
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='run-backtest')
    def run_backtest(self, request, pk=None):
        """Enfileira uma tarefa Celery para executar o backtest de uma estratégia."""
        strategy = self.get_object()
        if strategy.celery_task_id:
            task_result = AsyncResult(strategy.celery_task_id)
            if task_result.status in ['PENDING', 'STARTED', 'RETRY']:
                logger.info(f"Backtest já em andamento (status: {task_result.status}) para Estratégia ID {strategy.id}.")
                return Response({'status': 'Um backtest já está em andamento.'}, status=status.HTTP_409_CONFLICT)

        # Enfileira a tarefa no Celery para a fila 'backtesting_heavy'
        task = run_validation_task.delay(strategy_id=strategy.id)

        # Atualiza o modelo da estratégia com o ID da nova tarefa e o status pendente.
        strategy.celery_task_id = task.id
        strategy.backtest_results = {"status": "PENDING", "task_id": str(task.id)} # Converte UUID para string
        strategy.save(update_fields=['celery_task_id', 'backtest_results'])

        logger.info(f"Backtest {task.id} enfileirado para Estratégia ID {strategy.id} (usuário: {request.user.username}).")
        return Response({'status': 'Backtest enfileirado', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='backtest-status')
    def backtest_status(self, request, pk=None):
        """Retorna o status e o resultado de um backtest Celery."""
        strategy = self.get_object()
        if not strategy.celery_task_id:
            return Response({'status': 'Nenhum backtest agendado.'}, status=status.HTTP_404_NOT_FOUND)

        task_result = AsyncResult(str(strategy.celery_task_id))

        # Se a tarefa foi bem-sucedida, o resultado REAL está no backtest_results da estratégia,
        # não no retorno da tarefa Celery (que retorna apenas uma string de sucesso).
        if task_result.status == 'SUCCESS':
            strategy.refresh_from_db() # Garante que estamos lendo os dados mais recentes do DB
            result_data = strategy.backtest_results
        elif task_result.ready(): # Se falhou ou outro estado terminal
            try:
                result_data = task_result.get(timeout=1)
            except Exception as e:
                result_data = {"error": f"Erro ao obter resultado da tarefa: {str(e)}"}
        else: # Se ainda está em andamento
            result_data = None

        response_data = {
            'task_id': str(strategy.celery_task_id), 
            'status': task_result.status, 
            'result': result_data
        }
        return Response(response_data)

@method_decorator(csrf_exempt, name='dispatch')
class ActiveRobotInstanceViewSet(viewsets.ModelViewSet):
    """API para gerenciar as instâncias de robôs ativos do usuário."""
    serializer_class = ActiveRobotInstanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A lógica para buscar apenas instâncias do usuário está correta.
        return ActiveRobotInstance.objects.filter(user=self.request.user).select_related(
            'strategy', 'trading_account'
        ).order_by('-started_at')

    def create(self, request, *args, **kwargs):
        """
        [MELHORIA] Sobrescreve o método create para retornar os dados
        serializados da nova instância, permitindo a atualização otimista do frontend.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Retorna 201 Created com os dados da nova instância.
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        logger.info(f"Instância de robô ativada para '{self.request.user.username}'.")

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescreve a ação DELETE. Em vez de deletar, desativa a instância
        e despacha a tarefa para fechar as posições.
        """
        instance = self.get_object()
        if not instance.is_active:
            return Response({"error": "Esta instância já está parada."}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        
        # ✅ CORREÇÃO: Chamada assíncrona com os argumentos corretos (account_id, strategy_id, user_id)
        close_positions_task.delay(instance.trading_account.id, instance.strategy.id, instance.user.id)
        
        logger.info(f"Robô '{instance.strategy.name}' desativado via DELETE. Tarefa de fechamento enfileirada.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='send-test-order')
    def send_test_order(self, request, pk=None):
        """Dispara uma ordem de teste manual para uma instância ativa via Celery."""
        instance = self.get_object()
        if not instance.is_active:
            return Response({"error": "Instância não está ativa para enviar ordens de teste."}, status=status.HTTP_400_BAD_REQUEST)

        send_test_order_task.delay(instance.id)
        logger.info(f"Ordem de teste para instância {instance.id} enfileirada para '{request.user.username}'.")
        return Response({"status": "SUCESSO", "message": "Ordem de teste agendada."}, status=status.HTTP_200_OK)

# =============================================================================
#           APIS DE DADOS OPERACIONAIS E DE MERCADO
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def account_pulse(request):
    """
    Retorna um pulso completo da conta, incluindo P&L, contagem de robôs e P&L individual.
    """
    user = request.user
    account = TradingAccount.objects.filter(user=user).order_by('-created_at').first()

    if not account:
        return Response({
            "balance": 0, "equity": 0, "pnl": 0,
            "active_robots_count": 0, "total_robots_count": 0,
            "active_robots_pnl": []
        })

    try:
        balance = 0
        equity = 0
        pnl = 0
        robot_pnl_map = {}

        with mt5_connection(account) as mt5_conn:
            if mt5_conn:
                account_info = mt5_conn.account_info()
                if account_info:
                    balance = account_info.balance
                    equity = account_info.equity
                    pnl = account_info.profit

                # Coletar P&L por robô (magic number)
                positions = mt5_conn.positions_get()
                if positions:
                    for pos in positions:
                        if pos.profit != 0:
                            robot_pnl_map[pos.magic] = robot_pnl_map.get(pos.magic, 0.0) + pos.profit

        active_instances = ActiveRobotInstance.objects.filter(
            user=user, is_active=True
        ).select_related('strategy')

        active_robots_pnl = []
        for instance in active_instances:
            strategy_magic_number = instance.strategy.magic_number
            instance_pnl = robot_pnl_map.get(strategy_magic_number, 0.0)
            active_robots_pnl.append({
                "name": instance.strategy.name,
                "pnl": round(instance_pnl, 2)
            })

        total_robots_count = Strategy.objects.filter(is_public=True).count()

        data = {
            "balance": round(balance, 2),
            "equity": round(equity, 2),
            "pnl": round(pnl, 2),
            "active_robots_count": active_instances.count(),
            "total_robots_count": total_robots_count,
            "active_robots_pnl": active_robots_pnl,
        }
        return Response(data)

    except Exception as e:
        logger.error(f"Erro em account_pulse para user {user.id}: {e}\n{traceback.format_exc()}")
        return Response({"error": "Erro interno ao processar pulso da conta."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trade_history(request):
    """Retorna o histórico de operações do nosso TradeLog interno."""
    account_id = request.query_params.get('account_id')
    if not account_id: 
        return Response({"error": "ID da conta é obrigatório na requisição."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if not TradingAccount.objects.filter(id=account_id, user=request.user).exists():
            return Response({"error": "Conta não encontrada ou não pertence a você."}, status=404)

        trade_logs = TradeLog.objects.filter(
            user=request.user,
            instance__trading_account_id=account_id
        ).order_by('-timestamp')[:settings.TRADE_HISTORY_LIMIT]

        serializer = TradeLogSerializer(trade_logs, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Erro ao buscar TradeLog para conta {account_id}: {e}\n{traceback.format_exc()}")
        return Response({"error": "Erro interno ao buscar histórico de trades."}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def get_equity_history(request):
    """
    Calculates and returns the daily equity for the last 7 days for the user's primary account.
    """
    user = request.user
    account = TradingAccount.objects.filter(user=user).order_by('-created_at').first()

    if not account:
        return Response({"error": "Nenhuma conta MT5 encontrada."}, status=status.HTTP_404_NOT_FOUND)

    try:
        # 1. Get current equity
        current_equity = 0
        with mt5_connection(account) as mt5_conn:
            if mt5_conn:
                account_info = mt5_conn.account_info()
                if account_info:
                    current_equity = account_info.equity

        # 2. Get all closed trades in the last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        closed_trades = TradeLog.objects.filter(
            user=user,
            trading_account=account,
            status=TradeLog.TradeStatus.CLOSED,
            timestamp__gte=seven_days_ago
        ).values('timestamp', 'profit_loss')

        if not closed_trades.exists() and current_equity == 0:
            return Response([], status=status.HTTP_200_OK)

        # 3. Process data with pandas
        df = pd.DataFrame(list(closed_trades))
        if not df.empty:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            # Ensure profit_loss is numeric, coercing errors to 0
            df['profit_loss'] = pd.to_numeric(df['profit_loss'], errors='coerce').fillna(0)
            daily_pnl = df.groupby('date')['profit_loss'].sum()
        else:
            daily_pnl = pd.Series(dtype=float)

        # 4. Reconstruct equity curve
        equity_history = []
        today = datetime.now().date()

        for i in range(7): # Iterate for the last 7 days
            date_to_process = today - timedelta(days=i)

            # The equity at the end of `date_to_process` is the current equity minus any profit made since that day.
            pnl_since_date = daily_pnl[daily_pnl.index > date_to_process].sum()
            equity_at_end_of_day = float(current_equity) - float(pnl_since_date)

            equity_history.append({
                "date": date_to_process.strftime('%Y-%m-%d'),
                "equity": round(equity_at_end_of_day, 2)
            })

        # The result is from newest to oldest, so we reverse it
        return Response(equity_history[::-1])

    except Exception as e:
        logger.error(f"Error in get_equity_history for user {user.id}: {e}\n{traceback.format_exc()}")
        return Response({"error": "Erro interno ao processar o histórico de equity."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_market_data(request):
    """Retorna dados de mercado (preços de tick) para símbolos selecionados."""
    symbols = request.data.get('symbols', [])
    account = TradingAccount.objects.filter(user=request.user).first()
    if not account: return Response({"error": "Nenhuma conta MT5 conectada."}, status=status.HTTP_404_NOT_FOUND)

    data = {}
    with mt5_connection(account) as mt5_conn:
        if mt5_conn:
            for symbol in symbols:
                tick = mt5_conn.symbol_info_tick(symbol)
                if tick:
                    # Convert namedtuple to dict for JSON serialization
                    data[symbol] = tick._asdict()
    return Response(data)

# =============================================================================
#           APIS DE NOTIFICAÇÕES E FAVORITOS
# =============================================================================

class FavoriteTickersView(APIView):
    """Gerencia a lista de tickers (símbolos) favoritos do usuário."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(profile.favorite_tickers or [])

    def post(self, request):
        tickers = request.data.get('tickers')
        if not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):
            return Response({"error": "O campo 'tickers' deve ser uma lista de strings."}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.favorite_tickers = tickers
        profile.save(update_fields=['favorite_tickers'])
        logger.info(f"Tickers favoritos de '{request.user.username}' atualizados.")
        return Response({"status": "SUCESSO", "tickers": profile.favorite_tickers})


class NotificationViewSet(viewsets.ViewSet):
    """API para visualizar e gerenciar notificações."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def list(self, request):
        """Retorna as 20 notificações mais recentes e a contagem de não lidas."""
        user = request.user
        notifications_qs = user.notifications.order_by('-created_at')[:20]
        unread_count = user.notifications.filter(is_read=False).count()
        serializer = self.serializer_class(notifications_qs, many=True)
        return Response({"notifications": serializer.data, "unread_count": unread_count})

    @action(detail=False, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request):
        """Marca todas as notificações não lidas como lidas."""
        request.user.notifications.filter(is_read=False).update(is_read=True)
        logger.info(f"Notificações de '{request.user.username}' marcadas como lidas.")
        return Response(status=status.HTTP_204_NO_CONTENT)

# =============================================================================
#           CELERY TASK STATUS AND TRADE LOG APIs
# =============================================================================

class TaskStatusView(APIView):
    """API para verificar o status de tarefas Celery (ex: backtests)."""
    permission_classes = [IsAuthenticated]
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        result_data = None
        if task_result.ready(): # If the task has finished (success or failure)
            try:
                result_data = task_result.get(timeout=1)
            except Exception as e:
                logger.error(f"Error getting Celery task result for {task_id}: {e}\n{traceback.format_exc()}")
                result_data = {"error": f"Error getting result: {str(e)}", "traceback": traceback.format_exc()}

        return Response({
            'task_id': task_id, 
            'status': task_result.status, 
            'result': result_data
        })

class TradeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API para visualizar os logs de trade internos da plataforma."""
    serializer_class = TradeLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna apenas os logs de trade do usuário logado.
        Usa select_related para otimizar a query, evitando o problema N+1
        causado pelo acesso a `user`, `instance.strategy` e `trading_account` no serializer.
        """
        return TradeLog.objects.filter(
            user=self.request.user
        ).select_related(
            'user', 'instance__strategy', 'trading_account'
        ).order_by('-timestamp')

# =============================================================================
#           AURA PORTFOLIO AI VIEWS
# =============================================================================

class StartAnalysisView(APIView):
    """ Inicia uma nova análise de portfólio. """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PortfolioAnalysisSerializer(data=request.data)
        if serializer.is_valid():
            # Salva o registro inicial no banco
            analysis = serializer.save(user=request.user)

            # Dispara a tarefa assíncrona
            task = generate_portfolio_analysis_task.delay(analysis.id)

            logger.info(f"Análise {analysis.id} iniciada para {request.user.username} (Task: {task.id})")

            # Retorna o ID da análise para polling
            return Response({"analysis_id": analysis.id, "status": "PENDING"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnalysisStatusView(APIView):
    """ Verifica o status e retorna o resultado da análise. """
    permission_classes = [IsAuthenticated]

    def get(self, request, analysis_id):
        try:
            analysis = PortfolioAnalysis.objects.get(id=analysis_id, user=request.user)
        except PortfolioAnalysis.DoesNotExist:
            return Response({"error": "Análise não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PortfolioAnalysisSerializer(analysis)
        return Response(serializer.data)

class SafetyStatusView(APIView):
    """
    Retorna o status de segurança do usuário.
    Verifica se há notificações de KILL SWITCH recentes ou se o saldo é crítico.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. Verificar Notificações Críticas nas últimas 24h
        last_24h = datetime.now() - timedelta(hours=24)
        critical_notification = Notification.objects.filter(
            user=user,
            notification_type='ERROR',
            created_at__gte=last_24h,
            message__icontains="Kill Switch"
        ).first()

        # 2. Verificar Saldo Crítico
        critical_balance = False
        account = TradingAccount.objects.filter(user=user).first()
        if account and account.current_balance <= 0:
            critical_balance = True

        if critical_notification:
            return Response({
                "status": "CRITICAL",
                "message": critical_notification.message
            })

        if critical_balance:
            return Response({
                "status": "CRITICAL",
                "message": "Saldo da conta é crítico (Zero ou Negativo). Robôs parados."
            })

        return Response({"status": "SAFE", "message": "Sistemas operando normalmente."})