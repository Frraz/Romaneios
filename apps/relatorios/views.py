from __future__ import annotations

import csv
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from apps.cadastros.models import Cliente
from apps.financeiro.models import Pagamento
from apps.romaneio.models import ItemRomaneio, Romaneio


def get_mes_ano(request):
    """
    Lê mes/ano da querystring e retorna defaults coerentes.
    """
    now = timezone.localdate()
    try:
        mes = int(request.GET.get("mes", now.month))
    except (TypeError, ValueError):
        mes = now.month
    try:
        ano = int(request.GET.get("ano", now.year))
    except (TypeError, ValueError):
        ano = now.year
    return mes, ano


class RelatorioRomaneiosView(LoginRequiredMixin, ListView):
    model = Romaneio
    template_name = "relatorios/ficha_romaneios.html"
    context_object_name = "romaneios"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("cliente", "motorista")
        )
        mes, ano = get_mes_ano(self.request)
        cliente_id = self.request.GET.get("cliente")

        qs = qs.filter(data_romaneio__month=mes, data_romaneio__year=ano)
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)
        cliente_id = self.request.GET.get("cliente")

        context["mes"] = mes
        context["ano"] = ano
        context["clientes"] = Cliente.objects.filter(ativo=True).order_by("nome")

        # Anos disponíveis sem varrer tudo em Python
        anos = [d.year for d in Romaneio.objects.dates("data_romaneio", "year", order="ASC")]
        context["anos"] = anos or [timezone.localdate().year]
        context["meses"] = range(1, 13)

        # Totais do período (usando o mesmo filtro do queryset)
        rom_qs = Romaneio.objects.filter(data_romaneio__month=mes, data_romaneio__year=ano)
        if cliente_id:
            rom_qs = rom_qs.filter(cliente_id=cliente_id)

        totais = rom_qs.aggregate(
            total_m3=Sum("m3_total"),
            total_valor_liquido=Sum("valor_total"),
            total_valor_bruto=Sum("valor_bruto"),
        )
        context["total_m3_periodo"] = totais["total_m3"] or 0
        context["total_valor_periodo"] = totais["total_valor_liquido"] or 0
        context["total_valor_bruto_periodo"] = totais["total_valor_bruto"] or 0

        return context


def ficha_romaneios_export(request):
    """
    Exporta relatório de romaneios POR ITEM em CSV.

    Corrigido para refletir o seu model atual:
    - ItemRomaneio não tem comprimento/rodo diretamente (isso fica em UnidadeRomaneio).
    - A quantidade do item é `quantidade_m3_total`.
    """
    mes, ano = get_mes_ano(request)
    cliente_id = request.GET.get("cliente")

    qs = Romaneio.objects.filter(data_romaneio__month=mes, data_romaneio__year=ano)
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    qs = qs.select_related("cliente", "motorista").prefetch_related("itens__tipo_madeira")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="relatorio_romaneios_{mes:02d}_{ano}.csv"'

    # BOM: Excel pt-BR costuma gostar de ; como delimiter. Se quiser manter vírgula, troque.
    writer = csv.writer(response, delimiter=";")

    writer.writerow([
        "Modalidade",
        "Tipo Romaneio",
        "Nº Romaneio",
        "Data",
        "Cliente",
        "Motorista",
        "Espécie",
        "Qtd Item (m³)",
        "Valor Unit. (R$/m³)",
        "Total Item (R$)",
    ])

    total_m3_geral = 0.0
    total_valor_itens = 0.0

    for romaneio in qs:
        itens = romaneio.itens.all()
        for item in itens:
            qtd = float(item.quantidade_m3_total or 0)
            total_item = float(item.valor_total or 0)

            writer.writerow([
                romaneio.get_modalidade_display() if hasattr(romaneio, "get_modalidade_display") else (romaneio.modalidade or ""),
                romaneio.get_tipo_romaneio_display() if hasattr(romaneio, "get_tipo_romaneio_display") else (romaneio.tipo_romaneio or ""),
                romaneio.numero_romaneio,
                romaneio.data_romaneio.strftime("%d/%m/%Y"),
                romaneio.cliente.nome if romaneio.cliente else "",
                romaneio.motorista.nome if romaneio.motorista else "",
                item.tipo_madeira.nome if item.tipo_madeira else "",
                f"{qtd:.3f}",
                f"{float(item.valor_unitario or 0):.2f}",
                f"{total_item:.2f}",
            ])

            total_m3_geral += qtd
            total_valor_itens += total_item

    writer.writerow([])
    writer.writerow(["", "", "", "", "", "", "TOTAL", f"{total_m3_geral:.3f}", "", f"{total_valor_itens:.2f}"])
    return response


class RelatorioMadeirasView(LoginRequiredMixin, TemplateView):
    template_name = "relatorios/ficha_madeiras.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        relatorio = (
            ItemRomaneio.objects.filter(
                romaneio__data_romaneio__month=mes,
                romaneio__data_romaneio__year=ano,
            )
            .values("tipo_madeira__nome")
            .annotate(
                total_m3=Sum("quantidade_m3_total"),
                total_valor=Sum("valor_total"),
            )
            .order_by("-total_m3")
        )

        context["relatorio"] = relatorio
        context["mes"] = mes
        context["ano"] = ano
        context["meses"] = range(1, 13)
        context["anos"] = [d.year for d in Romaneio.objects.dates("data_romaneio", "year", order="ASC")] or [timezone.localdate().year]
        return context


class RelatorioFluxoView(LoginRequiredMixin, TemplateView):
    template_name = "relatorios/fluxo_financeiro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        vendas = (
            Romaneio.objects.filter(data_romaneio__month=mes, data_romaneio__year=ano)
            .aggregate(total=Sum("valor_total"))
            .get("total")
            or 0
        )

        pagamentos = (
            Pagamento.objects.filter(data_pagamento__month=mes, data_pagamento__year=ano)
            .aggregate(total=Sum("valor"))
            .get("total")
            or 0
        )

        saldo_mes = pagamentos - vendas
        saldo_mes_classe = "text-secondary"
        if saldo_mes > 0:
            saldo_mes_classe = "text-success"
        elif saldo_mes < 0:
            saldo_mes_classe = "text-danger"

        context.update({
            "saldo_mes_classe": saldo_mes_classe,
            "mes": mes,
            "ano": ano,
            "vendas": vendas,
            "pagamentos": pagamentos,
            "saldo_mes": saldo_mes,
            "vendas_detalhadas": Romaneio.objects.filter(
                data_romaneio__month=mes, data_romaneio__year=ano
            ).select_related("cliente", "motorista"),
            "pagamentos_detalhados": Pagamento.objects.filter(
                data_pagamento__month=mes, data_pagamento__year=ano
            ).select_related("cliente"),
        })
        return context


class RelatorioSaldoClientesView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "relatorios/saldo_clientes.html"
    context_object_name = "clientes"

    def get_queryset(self):
        tipo_saldo = self.request.GET.get("tipo_saldo", "todos")

        qs = Cliente.objects.all()

        # Se saldo_atual for property calculada em Python, isso não dá para filtrar no banco.
        # Mantive o comportamento original (lista em Python), mas filtrando ativos pode ser útil.
        clientes = list(qs)

        if tipo_saldo == "negativos":
            clientes = [c for c in clientes if c.saldo_atual < 0]
        elif tipo_saldo == "positivos":
            clientes = [c for c in clientes if c.saldo_atual > 0]
        elif tipo_saldo == "zerados":
            clientes = [c for c in clientes if c.saldo_atual == 0]

        return sorted(clientes, key=lambda c: c.saldo_atual)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos_saldo"] = ["todos", "negativos", "positivos", "zerados"]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "relatorios/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        romaneios_mes = Romaneio.objects.filter(data_romaneio__month=mes, data_romaneio__year=ano)
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

        todos_clientes = Cliente.objects.all()
        saldos_negativos = [c.saldo_atual for c in todos_clientes if c.saldo_atual < 0]
        context["saldo_total_receber"] = abs(sum(saldos_negativos)) if saldos_negativos else 0

        devedores = sorted(
            [c for c in todos_clientes if c.saldo_atual < 0],
            key=lambda c: c.saldo_atual,
        )[:5]
        context["maiores_devedores"] = devedores

        top_clientes = (
            romaneios_mes.values("cliente__nome")
            .annotate(total_comprado=Sum("valor_total"))
            .order_by("-total_comprado")[:5]
        )
        context["top_clientes_mes"] = top_clientes

        vendas_por_madeira = (
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
        context["vendas_por_madeira"] = vendas_por_madeira

        return context