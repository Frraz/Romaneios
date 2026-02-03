from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard resumido (home dos relatórios)
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Relatório de romaneios por período/cliente
    path('ficha-romaneios/', views.RelatorioRomaneiosView.as_view(), name='ficha_romaneios'),
    path('ficha-romaneios/export/', views.ficha_romaneios_export, name='ficha_romaneios_export'),

    # Relatório de madeiras
    path('ficha-madeiras/', views.RelatorioMadeirasView.as_view(), name='ficha_madeiras'),

    # Fluxo financeiro consolidado
    path('fluxo-financeiro/', views.RelatorioFluxoView.as_view(), name='fluxo_financeiro'),

    # Relatório de saldo dos clientes
    path('saldo-clientes/', views.RelatorioSaldoClientesView.as_view(), name='saldo_clientes'),
]