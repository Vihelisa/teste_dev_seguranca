import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings # Importa as configurações centrais do Django
from django.core.validators import MinValueValidator # Para garantir valores positivos

# =============================================================================
#                        MODELOS DO BANCO DE DADOS
# =============================================================================

class UserProfile(models.Model):
    """ Estende o modelo User padrão com configurações e preferências da plataforma. """
    # Relação um-para-um com o User. Se o User for deletado, o Perfil também é.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Número de telefone do usuário.")
    # Campo JSON para armazenar uma lista de strings (símbolos favoritos).
    favorite_tickers = models.JSONField(default=list, blank=True, help_text="Lista de símbolos favoritos do usuário.")
    
    # Campo para a feature "Guardião Birdstone".
    global_drawdown_limit = models.DecimalField(
        max_digits=10, decimal_places=2, default=20.0, # Padrão de 20%
        validators=[MinValueValidator(0.0)], # Garante que o valor nunca seja negativo.
        help_text="Limite de Drawdown Diário Global (%). Se atingido, todos os robôs são pausados."
    )
    max_open_positions = models.IntegerField(default=5, help_text="Número máximo de posições abertas simultaneamente em todas as contas.")
    max_risk_per_trade = models.DecimalField(
        max_digits=5,           # Permite até 999.99
        decimal_places=2,       # Duas casas decimais
        default=Decimal('1.00'),
        help_text="Risco máximo por trade, como uma porcentagem do saldo da conta (ex: 1.00 para 1%)."
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"

class TradingAccount(models.Model):
    """ Armazena as credenciais criptografadas das contas de trading (MT5/cTrader/FIX) dos usuários. """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trading_accounts')
    nickname = models.CharField(max_length=50, blank=True, null=True, help_text="Apelido para a conta")
    account_login = models.CharField(max_length=100, unique=True, help_text="O número de login da conta, deve ser único.")
    server = models.CharField(max_length=100)
    encrypted_password = models.CharField(max_length=255)

    # [PHOENIX COMPLIANCE] - Monitoramento de Saldo
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, help_text="Saldo atual da conta (atualizado periodicamente).")

    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        """ Criptografa a senha usando a instância FERNET centralizada do settings. """
        if settings.FERNET:
            self.encrypted_password = settings.FERNET.encrypt(raw_password.encode()).decode()
        else:
            raise ValueError("A chave de criptografia (FERNET) não está configurada.")
    
    def get_password(self):
        """ Descriptografa a senha para uso em conexões. """
        if settings.FERNET:
            return settings.FERNET.decrypt(self.encrypted_password.encode()).decode()
        else:
            raise ValueError("A chave de criptografia (FERNET) não está configurada.")
    
    def __str__(self):
        return f'Conta {self.account_login} ({self.nickname or "Sem Apelido"}) de {self.user.username}'

class Strategy(models.Model):
    """ Armazena o catálogo de estratégias de trading que a plataforma oferece. """
    name = models.CharField(max_length=100, unique=True, help_text="Nome público da estratégia.")
    description = models.TextField(blank=True, help_text="Descrição de marketing e técnica.")
    assets = models.CharField(max_length=255, default='', help_text="Ativos que a estratégia opera (ex: EURUSD,XAUUSD).")
    TIMEFRAME_CHOICES = [
        ('M1', '1 Minuto'), ('M5', '5 Minutos'), ('M15', '15 Minutos'),
        ('M30', '30 Minutos'), ('H1', '1 Hora'), ('H4', '4 Horas'),
        ('D1', 'Diário'),
    ]
    timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES, default='M15', help_text="Timeframe principal da execução.")
    portfolio_composition = models.JSONField(default=dict, blank=True, help_text="JSON com os parâmetros da estratégia.")
    suggested_capital = models.DecimalField(max_digits=10, decimal_places=2, default=500.0, validators=[MinValueValidator(0.0)])
    backtest_period_days = models.IntegerField(default=730, validators=[MinValueValidator(1)])
    
    STRATEGY_TYPES = [('SINGLE_PORTFOLIO', 'Ativo Único / Portfólio'), ('PAIRS', 'Pairs Trading')]
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPES, default='SINGLE_PORTFOLIO')
    
    strategy_file = models.CharField(max_length=100, help_text="Nome do arquivo Python da estratégia (sem .py).")
    ml_model_path = models.FileField(upload_to='ml_models/', blank=True, null=True, help_text="Caminho para o modelo de IA treinado.")
    ml_threshold = models.FloatField(default=0.55, help_text="Limiar de probabilidade (0-1) para a IA aprovar um trade.")
    
    backtest_results = models.JSONField(default=dict, blank=True, help_text="Resultados numéricos do último backtest.")
    aura_analysis = models.TextField(blank=True, help_text="Análise qualitativa da IA (LLM).")
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID da última tarefa Celery associada.")
    
    is_public = models.BooleanField(default=False, db_index=True, help_text="Controla a visibilidade no marketplace.")
    magic_number = models.IntegerField(unique=True, null=True, blank=True, help_text="Número mágico para identificar as ordens no MT5.")

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = "Estratégia"; verbose_name_plural = "Estratégias"

class ActiveRobotInstance(models.Model):
    """ Rastreia qual robô está ativo, em qual conta, e para qual usuário. """
    RISK_MODES = [
        ('FIXED', 'Lote Fixo'),
        ('DYNAMIC', 'Risco Dinâmico (%)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_robot_instances')
    trading_account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, related_name='active_robot_instances')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='active_instances')

    # Configuração de Risco
    risk_mode = models.CharField(max_length=10, choices=RISK_MODES, default='FIXED', help_text="Modo de cálculo do tamanho da posição.")
    lot_size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Lote fixo a ser usado nas operações (se risk_mode for FIXED).", validators=[MinValueValidator(Decimal('0.01'))])
    risk_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Porcentagem do saldo a arriscar por trade (se risk_mode for DYNAMIC). Ex: 1.00 = 1%."
    )
    is_active = models.BooleanField(default=True, db_index=True) # Indexado para buscas rápidas pelo worker
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        return f'Instância {self.strategy.name} ({status}) na conta {self.trading_account.nickname} de {self.user.username}'

    class Meta:
        verbose_name = "Instância de Robô Ativa"
        verbose_name_plural = "Instâncias de Robôs Ativas"
        constraints = [
            models.UniqueConstraint(fields=['user', 'strategy'], condition=models.Q(is_active=True), name='unique_active_strategy_per_user')
        ]

class Notification(models.Model):
    """ Representa uma notificação a ser exibida para um usuário. """
    class NotificationType(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Sucesso'; INFO = 'INFO', 'Informativo'; WARNING = 'WARNING', 'Aviso'; ERROR = 'ERROR', 'Erro'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificação para {self.user.username}: {self.message[:30]}..."

    class Meta:
        ordering = ['-created_at']; verbose_name = "Notificação"

class TradeLog(models.Model):
    """ Registra uma trilha de auditoria completa para cada evento de trade. """
    class TradeStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Sucesso'; FAILED = 'FAILED', 'Falhou'; EXCEPTION = 'EXCEPTION', 'Exceção'; IGNORED = 'IGNORED', 'Ignorado'; CLOSED = 'CLOSED', 'Fechado'
    
    instance = models.ForeignKey(ActiveRobotInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='trade_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_logs')
    trading_account = models.ForeignKey(TradingAccount, on_delete=models.SET_NULL, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=30, choices=TradeStatus.choices)
    
    symbol = models.CharField(max_length=50, blank=True); trade_type = models.CharField(max_length=20, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True); price_entry = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    price_exit = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True); profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sl_price = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True) # [MELHORIA] Adicionado para auditoria completa
    tp_price = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True) # [MELHORIA] Adicionado para auditoria completa
    
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    retcode = models.BigIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    order_ticket = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="ID do ticket usado em sistemas legados ou de backtest (ex: MT5).")
    broker_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text="ID da ordem retornado pela corretora (ex: FIX OrderID).")

    # Campos para features avançadas no histórico
    duration = models.DurationField(null=True, blank=True, help_text="Duração total da operação desde a abertura até o fechamento.")
    ai_probability = models.FloatField(null=True, blank=True, help_text="Probabilidade de sucesso calculada pela IA no momento da abertura.")
    ai_decision_features = models.JSONField(null=True, blank=True, help_text="Features que mais influenciaram a decisão da IA.")

    def __str__(self):
        # A verificação 'self.instance' é mais segura que 'self.instance_id'
        instance_str = f"Instância {self.instance.id}" if self.instance else "Instância N/A"
        return f"Log [{self.status}] para {instance_str} em {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp']; verbose_name = "Log de Trade"

class PortfolioAnalysis(models.Model):
    """ Persiste o histórico de consultas da Aura Portfolio AI. """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        COMPLETED = 'COMPLETED', 'Concluído'
        FAILED = 'FAILED', 'Falhou'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_analyses')

    # Inputs
    assets_interest = models.JSONField(help_text="Lista de ativos de interesse (ex: ['Stocks', 'Crypto']).")
    risk_profile = models.CharField(max_length=50)
    objective = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Status e Resultado
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    result_json = models.JSONField(null=True, blank=True, help_text="Resposta estruturada da IA.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análise {self.id} para {self.user.username} ({self.status})"

# =============================================================================
#                        SINAIS (LÓGICA PÓS-CRIAÇÃO)
# =============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Garante que um UserProfile seja criado automaticamente com cada novo User."""
    if created:
        UserProfile.objects.create(user=instance)
        print(f"UserProfile criado para o novo usuário '{instance.username}' (ID: {instance.id}).")