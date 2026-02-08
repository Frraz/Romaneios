from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard resumido (home dos relatórios)
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Relatório de romaneios por período/cliente
    path('ficha-romaneios/', views.RelatorioRomaneiosView.as_view(), name='ficha_romaneios'),
    path('ficha-romaneios/export/', views.ficha_romaneios_export, name='ficha_romaneios_export'),

    # Export por romaneio
    path('romaneios/<int:romaneio_id>/export/pdf/', views.romaneio_export_pdf, name='romaneio_export_pdf'),
    path('romaneios/<int:romaneio_id>/export/excel/', views.romaneio_export_excel, name='romaneio_export_excel'),

    # Relatório de madeiras (detalhado por item do romaneio)
    path('ficha-madeiras/', views.RelatorioMadeirasView.as_view(), name='ficha_madeiras'),
    path('ficha-madeiras/export/excel/', views.ficha_madeiras_export_excel, name='ficha_madeiras_export_excel'),
    path('ficha-madeiras/export/pdf/', views.ficha_madeiras_export_pdf, name='ficha_madeiras_export_pdf'),

    # Fluxo financeiro consolidado
    path('fluxo-financeiro/', views.RelatorioFluxoView.as_view(), name='fluxo_financeiro'),

    # Relatório de saldo dos clientes
    path('saldo-clientes/', views.RelatorioSaldoClientesView.as_view(), name='saldo_clientes'),
]