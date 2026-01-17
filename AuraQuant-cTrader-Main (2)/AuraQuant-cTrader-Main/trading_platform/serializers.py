from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Notification, Strategy, TradingAccount, ActiveRobotInstance, TradeLog, PortfolioAnalysis
import logging

# Handle optional MetaTrader5 import for non-Windows environments
try:
    from .utils.mt5_connector import mt5_connection, MT5_AVAILABLE
except (ImportError, ModuleNotFoundError):
    mt5_connection = None
    MT5_AVAILABLE = False
    logging.warning("MT5 connector not found. Account validation will be skipped.")

# =============================================================================
#           1. SERIALIZERS DE SUPORTE (PERFIL E NOTIFICAÇÕES)
# =============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """ Serializer para o perfil do usuário, incluindo campos do modelo User. """
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'favorite_tickers', 'global_drawdown_limit']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()
        return super().update(instance, validated_data)

class NotificationSerializer(serializers.ModelSerializer):
    """ Serializer simples para notificações (apenas leitura). """
    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'is_read', 'created_at']
        read_only_fields = fields

# =============================================================================
#           2. SERIALIZERS PRINCIPAIS (VIEWSETS)
# =============================================================================

class TradingAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'},
        min_length=1 # Permite qualquer senha, a validação é feita pela corretora
    )
    # [CORREÇÃO] account_login deve ser um IntegerField para corresponder ao modelo e à API MT5
    account_login = serializers.IntegerField(
        required=True, 
        validators=[lambda value: value > 0 or serializers.ValidationError("Login da conta deve ser um número positivo.")]
    )

    class Meta:
        model = TradingAccount
        fields = ['id', 'account_login', 'server', 'nickname', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """ Valida as credenciais da conta MT5 na tentativa de conexão. """
        if not MT5_AVAILABLE:
            # If MT5 is not available, we can't validate, so we skip it.
            # The user will be able to create the account, but it won't connect.
            return data

        temp_account = TradingAccount(
            account_login=data['account_login'],
            server=data['server']
        )
        temp_account.set_password(data['password'])
        
        is_connected = False
        with mt5_connection(temp_account) as mt5_conn:
            if mt5_conn:
                is_connected = True
        
        if not is_connected:
            raise serializers.ValidationError(
                "Falha na conexão com o MT5. Verifique se o login, senha e servidor estão corretos e se o terminal está aberto."
            )
        
        return data

    def create(self, validated_data):
        """
        Cria a nova conta, garantindo a criptografia e associação corretas.
        """
        password = validated_data.pop('password')
        
        # The user is passed in from the view and is already in validated_data.
        instance = TradingAccount.objects.create(**validated_data)
        
        # Set the password securely.
        instance.set_password(password)
        instance.save(update_fields=['encrypted_password'])
        
        return instance

class StrategySerializer(serializers.ModelSerializer):
    """ Serializer de apenas leitura para as estratégias do marketplace. """
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'assets', 'timeframe',
            'strategy_type', 'suggested_capital', 'aura_analysis',
            'backtest_results', 'is_public', 'celery_task_id'
        ]
        read_only_fields = fields

class ActiveRobotInstanceSerializer(serializers.ModelSerializer):
    """ Serializer para criar e listar instâncias de robôs ativas. """
    # strategy_name e account_nickname são mantidos para compatibilidade e conveniência
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    account_nickname = serializers.CharField(source='trading_account.nickname', read_only=True)

    class Meta:
        model = ActiveRobotInstance
        fields = [
            'id', 'strategy', 'strategy_name', 'trading_account',
            'account_nickname', 'lot_size', 'is_active', 'started_at'
        ]
        read_only_fields = ['id', 'strategy_name', 'account_nickname', 'is_active', 'started_at']

    def to_representation(self, instance):
        """
        Sobrescreve a representação para aninhar os detalhes da estratégia e da conta
        apenas em operações de leitura (GET), mantendo os campos de escrita baseados em ID.
        """
        representation = super().to_representation(instance)
        # Aninha os dados completos do StrategySerializer
        representation['strategy'] = StrategySerializer(instance.strategy).data
        # Aninha os dados completos do TradingAccountSerializer
        representation['trading_account'] = TradingAccountSerializer(instance.trading_account).data
        return representation

    def validate_trading_account(self, value):
        if 'request' in self.context and self.context['request'].user != value.user:
            raise serializers.ValidationError("Você só pode ativar robôs em suas próprias contas MT5.")
        return value

    def validate_strategy(self, value):
        if not value.is_public:
            raise serializers.ValidationError("Esta estratégia não está disponível publicamente para ativação.")
        return value

    def validate(self, data):
        """
        Verifica se já existe uma instância ativa para esta mesma estratégia e usuário.
        """
        user = self.context['request'].user
        strategy = data.get('strategy')

        if ActiveRobotInstance.objects.filter(user=user, strategy=strategy, is_active=True).exists():
            raise serializers.ValidationError(
                {"error": "Você já possui uma instância ativa desta estratégia. Desative a antiga antes de ativar uma nova."}
            )
        return data

class TradeLogSerializer(serializers.ModelSerializer):
    """ Serializer de apenas leitura para a trilha de auditoria de trades. """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    strategy_name = serializers.CharField(source='instance.strategy.name', read_only=True, default='N/A')
    account_nickname = serializers.CharField(source='trading_account.nickname', read_only=True, default='N/A')

    class Meta:
        model = TradeLog
        fields = [
            'id', 'timestamp', 'status', 'symbol', 'trade_type', 'volume',
            'price_entry', 'price_exit', 'profit_loss', 'order_ticket', 'broker_order_id',
            'comment', 'user_email', 'strategy_name', 'account_nickname'
        ]
        read_only_fields = fields

class PortfolioAnalysisSerializer(serializers.ModelSerializer):
    """ Serializer para a feature Aura Portfolio AI. """
    result_json = serializers.JSONField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = PortfolioAnalysis
        fields = [
            'id', 'assets_interest', 'risk_profile',
            'objective', 'amount', 'status', 'result_json', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'result_json', 'created_at']

    def validate_assets_interest(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("assets_interest deve ser uma lista.")
        return value