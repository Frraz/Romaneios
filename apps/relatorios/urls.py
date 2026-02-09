from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    # Dashboard resumido (home dos relatórios)
    path("", views.DashboardView.as_view(), name="dashboard"),

    # =========================
    # Ficha de Romaneios
    # =========================
    path("ficha-romaneios/", views.RelatorioRomaneiosView.as_view(), name="ficha_romaneios"),

    # Export antigo (CSV por item)
    path("ficha-romaneios/export/", views.ficha_romaneios_export, name="ficha_romaneios_export"),

    # Export novo do período (Excel/PDF) - igual Ficha de Madeiras
    path("ficha-romaneios/export/excel/", views.ficha_romaneios_export_excel, name="ficha_romaneios_export_excel"),
    path("ficha-romaneios/export/pdf/", views.ficha_romaneios_export_pdf, name="ficha_romaneios_export_pdf"),

    # Export por romaneio (individual)
    path("romaneios/<int:romaneio_id>/export/pdf/", views.romaneio_export_pdf, name="romaneio_export_pdf"),
    path("romaneios/<int:romaneio_id>/export/excel/", views.romaneio_export_excel, name="romaneio_export_excel"),

    # =========================
    # Ficha de Madeiras
    # =========================
    path("ficha-madeiras/", views.RelatorioMadeirasView.as_view(), name="ficha_madeiras"),
    path("ficha-madeiras/export/excel/", views.ficha_madeiras_export_excel, name="ficha_madeiras_export_excel"),
    path("ficha-madeiras/export/pdf/", views.ficha_madeiras_export_pdf, name="ficha_madeiras_export_pdf"),

    # =========================
    # Fluxo Financeiro
    # =========================
    path("fluxo-financeiro/", views.RelatorioFluxoView.as_view(), name="fluxo_financeiro"),
    path("fluxo-financeiro/export/excel/", views.fluxo_financeiro_export_excel, name="fluxo_financeiro_export_excel"),
    path("fluxo-financeiro/export/pdf/", views.fluxo_financeiro_export_pdf, name="fluxo_financeiro_export_pdf"),

    # =========================
    # Saldo de Clientes
    # =========================
    path("saldo-clientes/", views.RelatorioSaldoClientesView.as_view(), name="saldo_clientes"),
]