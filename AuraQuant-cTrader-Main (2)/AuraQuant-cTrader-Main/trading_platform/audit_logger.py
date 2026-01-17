
import logging
from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
import json

logger = logging.getLogger('audit')

class AuditLog(models.Model):
    """Modelo para logs de auditoria"""
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('READ', 'Leitura'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ERROR', 'Erro'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)  # Nome do modelo/recurso
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource', 'timestamp']),
        ]

def audit_log(user, action, resource, resource_id=None, details=None, request=None):
    """
    Função helper para criar logs de auditoria
    """
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        AuditLog.objects.create(
            user=user,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        
        logger.info(f"Audit: {user.username if user else 'Anonymous'} {action} {resource} {resource_id or ''}")
        
    except Exception as e:
        logger.error(f"Erro ao criar log de auditoria: {e}")

def get_client_ip(request):
    """Extrai o IP real do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
