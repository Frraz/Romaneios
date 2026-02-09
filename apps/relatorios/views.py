from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.views.generic import TemplateView

from apps.cadastros.models import Cliente
from apps.romaneio.models import ItemRomaneio, Romaneio

from .views_ficha_romaneio import (
    RelatorioRomaneiosView,
    ficha_romaneios_export,
    ficha_romaneios_export_excel,
    ficha_romaneios_export_pdf,
    romaneio_export_excel,
    romaneio_export_pdf,
    get_mes_ano,
)

from .views_ficha_madeira import (
    RelatorioMadeirasView,
    ficha_madeiras_export_excel,
    ficha_madeiras_export_pdf,
)

from .views_fluxo_financeiro import (
    RelatorioFluxoView,
    fluxo_financeiro_export_excel,
    fluxo_financeiro_export_pdf,
)

from .views_saldo_cliente import (
    RelatorioSaldoClientesView,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "relatorios/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        romaneios_mes = Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano,
        )

        totais_mes = romaneios_mes.aggregate(
            total_m3=Sum("m3_total"),
            total_valor=Sum("valor_total"),
            qtd_romaneios=Count("id"),
        )

        context["mes"] = mes
        context["ano"] = ano
        context["total_m3_mes"] = totais_mes["total_m3"] or 0
        context["total_faturado_mes"] = totais_mes["total_valor"] or 0
        context["qtd_romaneios_mes"] = totais_mes["qtd_romaneios"] or 0

        # Saldo total a receber (somatório dos clientes com saldo negativo)
        todos_clientes = Cliente.objects.all()
        saldos_negativos = [c.saldo_atual for c in todos_clientes if c.saldo_atual < 0]
        context["saldo_total_receber"] = abs(sum(saldos_negativos)) if saldos_negativos else 0

        # Top 5 devedores
        context["maiores_devedores"] = sorted(
            (c for c in todos_clientes if c.saldo_atual < 0),
            key=lambda c: c.saldo_atual,
        )[:5]

        # Top 5 clientes do mês por valor comprado
        context["top_clientes_mes"] = (
            romaneios_mes.values("cliente__nome")
            .annotate(total_comprado=Sum("valor_total"))
            .order_by("-total_comprado")[:5]
        )

        # Top 10 tipos de madeira por m³ no mês
        context["vendas_por_madeira"] = (
            ItemRomaneio.objects.filter(
                romaneio__data_romaneio__month=mes,
                romaneio__data_romaneio__year=ano,
            )
            .values("tipo_madeira__nome")
            .annotate(
                total_m3=Sum("quantidade_m3_total"),
                total_valor=Sum("valor_total"),
            )
            .order_by("-total_m3")[:10]
        )

        return context