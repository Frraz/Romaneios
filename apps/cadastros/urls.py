from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/novo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/excluir/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    
    # Tipos de Madeira
    path('madeiras/', views.TipoMadeiraListView.as_view(), name='tipo_madeira_list'),
    path('madeiras/novo/', views.TipoMadeiraCreateView.as_view(), name='tipo_madeira_create'),
    path('madeiras/<int:pk>/editar/', views.TipoMadeiraUpdateView.as_view(), name='tipo_madeira_update'),
    
    # Motoristas
    path('motoristas/', views.MotoristaListView.as_view(), name='motorista_list'),
    path('motoristas/novo/', views.MotoristaCreateView.as_view(), name='motorista_create'),
    path('motoristas/<int:pk>/editar/', views.MotoristaUpdateView.as_view(), name='motorista_update'),
]