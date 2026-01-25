from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
#from django.views.generic import TemplateView


# 1. Rotas Principais (Admin e API)
# O Django verificará estas primeiro. Se a URL coincidir, ele para aqui.
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Todas as rotas do backend (Trading Platform) ficam sob /api/
    path('api/', include('trading_platform.urls')),
]

# 2. Configuração de Arquivos Estáticos e Mídia (Apenas DEBUG)
# IMPORTANTE: Isso DEVE vir antes da rota catch-all do React.
# Se não fizermos isso, o Django tentará servir imagens como se fossem páginas HTML.
# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

