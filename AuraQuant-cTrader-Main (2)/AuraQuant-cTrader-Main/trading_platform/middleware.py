
import logging
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
import time

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Middleware de segurança para APIs"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar rate limiting por IP
        if not self._check_rate_limit(request):
            return JsonResponse(
                {"error": "Taxa de requisições excedida. Tente novamente em alguns minutos."}, 
                status=429
            )
        
        # Log de tentativas suspeitas
        self._log_suspicious_activity(request)
        
        response = self.get_response(request)
        
        # Adicionar headers de segurança
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response

    def _check_rate_limit(self, request):
        """Verifica rate limiting por IP"""
        if request.path.startswith('/admin/'):
            return True
            
        client_ip = self._get_client_ip(request)
        cache_key = f"rate_limit_{client_ip}"
        
        current_requests = cache.get(cache_key, 0)
        if current_requests >= getattr(settings, 'API_RATE_LIMIT_PER_MINUTE', 100):
            return False
        
        cache.set(cache_key, current_requests + 1, 60)  # 1 minuto
        return True
    
    def _log_suspicious_activity(self, request):
        """Log atividades suspeitas"""
        suspicious_patterns = [
            'admin', 'wp-admin', '.php', 'shell', 'cmd', 'eval', 'exec'
        ]
        
        path = request.path.lower()
        if any(pattern in path for pattern in suspicious_patterns):
            logger.warning(f"Tentativa suspeita de acesso: {self._get_client_ip(request)} -> {request.path}")
    
    def _get_client_ip(self, request):
        """Obter IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
