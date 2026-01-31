from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('ficha-romaneios/', views.RelatorioRomaneiosView.as_view(), name='ficha_romaneios'),
    path('ficha-madeiras/', views.RelatorioMadeirasView.as_view(), name='ficha_madeiras'),
    path('fluxo-financeiro/', views.RelatorioFluxoView.as_view(), name='fluxo_financeiro'),
    path('saldo-clientes/', views.RelatorioSaldoClientesView.as_view(), name='saldo_clientes'),
]