from django.urls import path
from . import views

app_name = 'romaneio'

urlpatterns = [
    # Romaneio Simples
    path('', views.RomaneioListView.as_view(), name='romaneio_list'),
    path('novo/', views.RomaneioCreateView.as_view(), name='romaneio_create'),
    path('<int:pk>/', views.RomaneioDetailView.as_view(), name='romaneio_detail'),
    path('<int:pk>/editar/', views.RomaneioUpdateView.as_view(), name='romaneio_update'),

    # Romaneio Detalhado
    path('detalhados/', views.RomaneioDetalhadoListView.as_view(), name='romaneio_detalhado_list'),
    path('detalhados/novo/', views.RomaneioDetalhadoCreateView.as_view(), name='romaneio_detalhado_create'),
    path('detalhados/<int:pk>/', views.RomaneioDetalhadoDetailView.as_view(), name='romaneio_detalhado_detail'),
    path('detalhados/<int:pk>/editar/', views.RomaneioDetalhadoUpdateView.as_view(), name='romaneio_detalhado_update'),

    # API utilitária
    path('api/preco-madeira/', views.get_preco_madeira, name='get_preco_madeira'),
]