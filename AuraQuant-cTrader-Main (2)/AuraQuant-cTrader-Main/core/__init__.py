try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery não está disponível, continuar sem ele
    pass

__all__ = ('celery_app',)