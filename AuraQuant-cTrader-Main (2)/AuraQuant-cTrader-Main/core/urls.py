from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

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
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 3. Rota Catch-All para o Frontend (React/SPA)
# Esta rota usa uma expressão regular que diz "pegue qualquer coisa que sobrou".
# Como ela é a ÚLTIMA da lista, ela só será acionada se a URL não for /admin/,
# não for /api/ e não for um arquivo de mídia/estático.
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]
