import os

from kombu import Queue
from pathlib import Path
from decouple import config, Csv
from cryptography.fernet import Fernet



# =============================================================================
#           1. CONFIGURAÇÕES BASE E DE SEGURANÇA
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Decouple lê as variáveis do arquivo .env na raiz do projeto
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)



# Lógica de Criptografia Centralizada e "Fail-Fast"
# Não use default para chaves de criptografia, pois podem ser descriptografadas por qualquer um!
#E em produção todos os dados sensíveis estão comprometidos
ENCRYPTION_KEY = config('ENCRYPTION_KEY')  # ← SEM default!

try:
    if len(ENCRYPTION_KEY) != 44:  # Chave Fernet base64 tem 44 caracteres
        raise ValueError("ENCRYPTION_KEY deve ter 44 caracteres (base64 de 32 bytes)")
    FERNET = Fernet(ENCRYPTION_KEY.encode())
except Exception as e:
    print(f"ERRO CRÍTICO ao inicializar a criptografia: {e}")
    raise e
# =============================================================================
#           2. CONFIGURAÇÕES DA APLICAÇÃO
# =============================================================================
MAGIC_NUMBER_BASE = config('MAGIC_NUMBER_BASE', default=202500, cast=int)
TRADE_HISTORY_LIMIT = config('TRADE_HISTORY_LIMIT', default=100, cast=int)
SIGNAL_LOCK_TIMEOUT = config('SIGNAL_LOCK_TIMEOUT', default=60, cast=int) # Timeout em segundos

# =============================================================================
#           3. APLICAÇÕES INSTALADAS
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Permite que o runserver sirva estáticos via WhiteNoise
    'django.contrib.staticfiles',
    'rest_framework', 'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'trading_platform.apps.TradingPlatformConfig',
]

# =============================================================================
#           4. MIDDLEWARE
# =============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =============================================================================
#           5. URLs, WSGI, TEMPLATES
# =============================================================================
ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [os.path.join(BASE_DIR, 'frontend_dist')],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',],},},]

# =============================================================================
#           6. BANCO DE DADOS E CACHE
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'birdstone',
        'TIMEOUT': 300,  # 5 minutos
    }
}

# =============================================================================
#           7. ARQUIVOS ESTÁTICOS E DE MÍDIA
# =============================================================================
STATIC_URL = '/static/' # <-- [CORREÇÃO] Variável que estava faltando.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'frontend_dist')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
#           8. CONFIGURAÇÕES DE REDE E SEGURANÇA
# =============================================================================
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8080",  # <--- ADICIONAR
        "http://127.0.0.1:8080"   # <--- ADICIONAR
    ]
else:
    # Em produção, seja explícito
    
    # [CORREÇÃO] Define explicitamente as origens confiáveis
    TRUSTED_DOMAIN = "https://plataformabeta.birdstone.com.br"
    CORS_ALLOWED_ORIGINS = [TRUSTED_DOMAIN]
    CSRF_TRUSTED_ORIGINS = [TRUSTED_DOMAIN]
    
    # Configurações para confiar nos cabeçalhos do proxy Caddy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication','rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle','rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': config('THROTTLE_RATE_ANON', default='100/hour'), 'user': config('THROTTLE_RATE_USER', default='1000/hour')}
}

# =============================================================================
#           9. CONFIGURAÇÃO CELERY
# =============================================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Broker e Backend
CELERY_BROKER_URL = config('REDIS_URL')
CELERY_RESULT_BACKEND = config('REDIS_URL')

# Serialização
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Timezone
CELERY_TIMEZONE = config('TIME_ZONE', default='America/Sao_Paulo')
TIME_ZONE = CELERY_TIMEZONE

# Beat Scheduler (Tarefas Agendadas)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Filas Personalizadas
CELERY_TASK_QUEUES = [
    Queue('realtime_trading', routing_key='trading.#'),
    Queue('backtesting_heavy', routing_key='backtest.#'),
]

# Roteamento de Tasks
CELERY_TASK_ROUTES = {
    'trading_platform.tasks.monitor_robot_instance_task': {'queue': 'realtime_trading'},
    'trading_platform.tasks.process_single_instance': {'queue': 'realtime_trading'},
    'trading_platform.tasks.send_test_order_task': {'queue': 'realtime_trading'},
    'trading_platform.tasks.close_positions_task': {'queue': 'realtime_trading'},
    'trading_platform.tasks.run_validation_task': {'queue': 'backtesting_heavy'},
}

# Performance e Segurança
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # Evita que uma task trave eternamente. -> 30 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Reinicia worker após 1000 tasks
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # configurações importantes para trading: Em trading, você quer processar uma ordem por vez, não pegar 4 ordens de uma vez (pode causar problemas de timing).

# Retry
CELERY_TASK_ACKS_LATE = True  # Confirma task só depois de completar: Se o worker morrer no meio, a task volta pra fila.
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Re-executa se worker morrer

# Logs
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'

# =============================================================================
#           10. EMAIL (PARA RESET DE SENHA)
# =============================================================================
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default=None)
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default=None)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default=None)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Birdstone <nao-responda@birdstone.com.br>')

# =============================================================================
#           11. LOGGING E OUTROS
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_trading': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'trading.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'trading_platform': {
            'handlers': ['console', 'file_trading'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
#           12. CHANNELS (WEBSOCKETS)
#  configura Django Channels para WebSockets em tempo real.
# =============================================================================

ASGI_APPLICATION = 'core.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config('REDIS_URL')],
        },
    },
}


# =============================================================================
#           13. HEADERS DE SEGURANÇA
# =============================================================================

if not DEBUG:
    # Força HTTPS
    SECURE_SSL_REDIRECT = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Previne clickjacking
    X_FRAME_OPTIONS = 'DENY'
    
    # Previne MIME sniffing
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # XSS Protection
    SECURE_BROWSER_XSS_FILTER = True


# =============================================================================
#           14. CONFIGURAÇÕES FIX PROTOCOL (cTrader)
# =============================================================================

# Endpoint TRADE (para enviar ordens)
FIX_TRADE_HOST = os.getenv('FIX_TRADE_HOST', 'h51.p.ctrader.com')
FIX_TRADE_PORT = int(os.getenv('FIX_TRADE_PORT', '5201'))

# Endpoint QUOTE (para receber cotações)
FIX_QUOTE_HOST = os.getenv('FIX_QUOTE_HOST', 'h51.p.ctrader.com')
FIX_QUOTE_PORT = int(os.getenv('FIX_QUOTE_PORT', '5211'))

# Target IDs (padrão cTrader)
FIX_TARGET_ID = os.getenv('FIX_TARGET_ID', 'CSERVER')
FIX_QUOTE_TARGET_ID = os.getenv('FIX_QUOTE_TARGET_ID', 'QUOTE')

# Versão do protocolo FIX
FIX_VERSION = os.getenv('FIX_VERSION', 'FIX.4.4')

# Timeout de conexão (segundos)
FIX_CONNECTION_TIMEOUT = int(os.getenv('FIX_CONNECTION_TIMEOUT', '30'))

# Heartbeat interval (segundos)
FIX_HEARTBEAT_INTERVAL = int(os.getenv('FIX_HEARTBEAT_INTERVAL', '30'))