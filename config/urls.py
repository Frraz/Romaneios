from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Login, logout, password reset, etc.
    
    # Rotas principais do sistema
    path('', include('apps.relatorios.urls')),      # Dashboard e relatórios
    path('cadastros/', include('apps.cadastros.urls')),
    path('romaneio/', include('apps.romaneio.urls')),
    path('financeiro/', include('apps.financeiro.urls')),
    path('core/', include('apps.core.urls')),       # Só mantenha se usar esse app
    # path('api/', include('apps.api.urls')),       # Exemplo para API futura
]

# Servir arquivos estáticos e de mídia no desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)