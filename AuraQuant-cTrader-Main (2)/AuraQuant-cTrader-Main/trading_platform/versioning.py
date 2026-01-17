
from rest_framework.versioning import URLPathVersioning
from rest_framework.response import Response
from rest_framework import status

class CustomAPIVersioning(URLPathVersioning):
    """Versionamento customizado da API"""
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'

    def determine_version(self, request, *args, **kwargs):
        version = super().determine_version(request, *args, **kwargs)
        
        # Log da versão utilizada
        if hasattr(request, 'user') and request.user.is_authenticated:
            from .audit_logger import audit_log
            audit_log(
                user=request.user,
                action='READ',
                resource='API_VERSION',
                details={'version': version, 'endpoint': request.path},
                request=request
            )
        
        return version

def deprecated_endpoint(version='v2'):
    """Decorator para marcar endpoints como deprecated"""
    def decorator(view_func):
        def wrapper(*args, **kwargs):
            response = view_func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['Warning'] = f'299 - "This endpoint is deprecated. Please use {version}"'
                response.headers['Sunset'] = 'Tue, 31 Dec 2024 23:59:59 GMT'
            return response
        return wrapper
    return decorator
