# trading_platform/apps.py
from django.apps import AppConfig

class TradingPlatformConfig(AppConfig):
    """
    Configuração para o aplicativo 'trading_platform' do Django.

    Este arquivo define metadados e configurações para o nosso aplicativo principal,
    que gerencia todos os modelos, views e lógicas relacionadas à plataforma de robôs.
    """
    
    # Define o tipo de campo padrão para chaves primárias automáticas,
    # uma boa prática para compatibilidade com bancos de dados maiores.
    default_auto_field = 'django.db.models.BigAutoField'
    
    # O nome técnico do aplicativo, que deve corresponder ao nome da pasta.
    name = 'trading_platform'
    
    # (MELHORIA) Nome amigável que aparecerá no painel de administração do Django.
    verbose_name = "Plataforma de Trading"
    
    def ready(self):
        import trading_platform.models # Import signals
