# trading_platform/admin.py
from django.contrib import admin
from django.utils.html import format_html # Para renderizar HTML seguro no admin
from .models import Strategy, TradingAccount, ActiveRobotInstance, UserProfile, Notification, TradeLog
import logging
from .tasks import run_validation_task, send_test_order_task

logger = logging.getLogger(__name__)

# =============================================================================
#           AÇÕES CUSTOMIZADAS DO ADMIN
# =============================================================================

@admin.action(description='Agendar Validação Completa (via Celery)')
def schedule_full_validation(modeladmin, request, queryset):
    """Enfileira a tarefa de validação para as estratégias selecionadas."""
    count = 0
    for strategy in queryset:    
        run_validation_task.delay(strategy.id)
        count += 1
    modeladmin.message_user(request, f"{count} validações foram agendadas com sucesso na fila de backtest.")

@admin.action(description='(TESTE) Enviar Ordem de Compra Manual')
def send_manual_test_order(modeladmin, request, queryset):
    """Dispara uma tarefa de teste de ordem para as instâncias selecionadas."""
    count = 0
    for instance in queryset:
        if instance.is_active:
            logger.info(f"[DJANGO_ADMIN] Tentando enfileirar 'send_test_order_task' para a instância ID: {instance.id}.")
            try:
                task_result = send_test_order_task.delay(instance.id)
                logger.info(f"[DJANGO_ADMIN] Tarefa enfileirada com sucesso! ID da Tarefa: {task_result.id}")
                count += 1
            except Exception as e:
                logger.error(f"[DJANGO_ADMIN] Falha ao enfileirar tarefa para instância {instance.id}: {e}", exc_info=True)
                modeladmin.message_user(request, f"Falha ao agendar tarefa para a instância {instance.id}: {e}", level='error')
        else:
            modeladmin.message_user(request, f"Instância {instance.id} está inativa e não pode receber ordens.", level='warning')
    
    if count > 0:
        modeladmin.message_user(request, f"{count} ordens de teste foram agendadas com sucesso na fila de trading.")

# =============================================================================
#           CONFIGURAÇÕES DO PAINEL DE ADMIN POR MODELO
# =============================================================================

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    """Interface de admin para o nosso catálogo de produtos (estratégias)."""
    list_display = ('id', 'name', 'strategy_type', 'assets', 'timeframe', 'is_public', 'get_task_status')
    list_filter = ('is_public', 'strategy_type')
    search_fields = ('name', 'assets')
    actions = [schedule_full_validation]
    
    fieldsets = (
        ('Informações Principais', {'fields': ('name', 'description', 'is_public')}),
        ('Configuração Técnica', {'fields': ('strategy_type', 'strategy_file', 'assets', 'timeframe', 'portfolio_composition')}),
        ('Parâmetros de Backtest', {'fields': ('suggested_capital', 'backtest_period_days')}),
        ('Resultados (Automático)', {
            'fields': ('celery_task_id', 'backtest_results', 'ml_model_path', 'aura_analysis'),
            'classes': ('collapse',) # Começa "fechado" para uma interface mais limpa
        }),
    )
    #readonly_fields = ('celery_task_id', 'backtest_results', 'aura_analysis', 'ml_model_path')

    @admin.display(description='Status do Backtest')
    def get_task_status(self, obj):
        """Exibe o início do ID da tarefa Celery para referência."""
        if obj.celery_task_id:
            return f"ID: {obj.celery_task_id[:8]}..."
        return "N/A"

@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    """Interface para as contas MT5 dos usuários."""
    list_display = ('nickname', 'account_login', 'server', 'user')
    search_fields = ('user__username', 'nickname', 'account_login')
    # Impede que senhas criptografadas sejam exibidas ou editadas diretamente
    exclude = ('encrypted_password',) 
    raw_id_fields = ('user',) # Melhora a performance em produção com muitos usuários

@admin.register(ActiveRobotInstance)
class ActiveRobotInstanceAdmin(admin.ModelAdmin):
    """Interface de admin para monitorar e gerenciar os robôs ativos."""
    list_display = ('id', 'strategy', 'user', 'trading_account', 'lot_size', 'is_active', 'started_at')
    list_filter = ('is_active', 'strategy__name', 'user__username')
    search_fields = ('user__username', 'strategy__name', 'trading_account__nickname')
    actions = [send_manual_test_order]
    raw_id_fields = ('user', 'trading_account', 'strategy')
    list_editable = ('is_active', 'lot_size') # [MELHORIA] Permite edições rápidas na lista

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Interface para gerenciar os perfis e configurações dos usuários."""
    list_display = ('user', 'global_drawdown_limit')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    list_editable = ('global_drawdown_limit',) # [MELHORIA] Permite edições rápidas

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Interface para visualizar as notificações enviadas aos usuários."""
    list_display = ('user', 'message', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'message')
    list_per_page = 25 # Paginação para performance
    raw_id_fields = ('user',)

@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    """Interface de auditoria para todos os eventos de trade."""
    list_display = ('timestamp', 'status', 'strategy_name', 'user', 'symbol', 'order_ticket', 'retcode_display')
    list_filter = ('status', 'instance__strategy__name', 'user__username')
    search_fields = ('user__username', 'order_ticket', 'comment')
    # Torna TODOS os campos apenas leitura, garantindo a imutabilidade dos logs
    readonly_fields = [f.name for f in TradeLog._meta.fields] 
    list_per_page = 20
    
    @admin.display(description='Estratégia', ordering='instance__strategy__name')
    def strategy_name(self, obj):
        """Permite ordenar pela coluna de nome da estratégia."""
        if obj.instance and obj.instance.strategy:
            return obj.instance.strategy.name
        return "N/A"
        
    @admin.display(description='RetCode', ordering='retcode')
    def retcode_display(self, obj):
        """Colore o RetCode para fácil identificação de sucesso/falha."""
        if obj.retcode == 10009: # Código MT5 para SUCESSO
            return format_html('<span style="color: green; font-weight: bold;">{} (DONE)</span>', obj.retcode)
        elif obj.status == 'SUCCESS':
             return format_html('<span style="color: blue;">{}</span>', obj.retcode or 'N/A')
        elif obj.retcode is not None:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.retcode)
        return "N/A"

    def has_add_permission(self, request):
        """[MELHORIA] Impede que logs sejam criados manualmente pelo admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """[MELHORIA] Impede que logs sejam editados pelo admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """[MELHORIA] Impede que logs sejam deletados pelo admin (exceto por superusuários)."""
        return request.user.is_superuser