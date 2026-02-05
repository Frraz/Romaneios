from datetime import datetime
import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView

from apps.romaneio.models import Romaneio, ItemRomaneio
from apps.financeiro.models import Pagamento
from apps.cadastros.models import Cliente


def get_mes_ano(request):
    now = datetime.now()
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

    def get_queryset(self):
        qs = super().get_queryset().select_related("cliente", "motorista")
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

        # Faixa de anos disponíveis p/ select (melhor pegar do Romaneio)
        context["anos"] = sorted(set(q.data_romaneio.year for q in Romaneio.objects.all()))
        context["meses"] = range(1, 13)
        if not context["anos"]:
            context["anos"] = [datetime.now().year]

        # Totais do período: melhor somar no próprio Romaneio
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
    """Exporta relatório de romaneios por item em CSV."""
    mes, ano = get_mes_ano(request)
    cliente_id = request.GET.get("cliente")

    qs = Romaneio.objects.filter(data_romaneio__month=mes, data_romaneio__year=ano)
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    qs = qs.select_related("cliente", "motorista")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="relatorio_romaneios_{mes}_{ano}.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "Modalidade",
        "Nº Romaneio",
        "Data",
        "Cliente",
        "Espécie",
        "Comp",
        "Rôdo",
        "Desconto (%)",
        "Qtd Item (m³)",
        "Valor Unit.",
        "Total Item",
    ])

    total_m3_geral = 0.0
    total_valor_itens = 0.0

    for romaneio in qs:
        itens = romaneio.itens.select_related("tipo_madeira").all()
        for item in itens:
            writer.writerow([
                getattr(romaneio, "modalidade", ""),
                romaneio.numero_romaneio,
                romaneio.data_romaneio.strftime("%d/%m/%Y"),
                romaneio.cliente.nome if romaneio.cliente else "",
                item.tipo_madeira.nome if item.tipo_madeira else "",
                item.comprimento if item.comprimento is not None else "",
                item.rodo or "",
                float(romaneio.desconto or 0),
                float(item.quantidade_m3),
                float(item.valor_unitario),
                float(item.valor_total),
            ])
            total_m3_geral += float(item.quantidade_m3)
            total_valor_itens += float(item.valor_total)

    writer.writerow([])
    writer.writerow(["", "", "", "", "", "", "", "TOTAL", total_m3_geral, "", total_valor_itens])
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
            .annotate(total_m3=Sum("quantidade_m3"), total_valor=Sum("valor_total"))
            .order_by("-total_m3")
        )

        context["relatorio"] = relatorio
        context["mes"] = mes
        context["ano"] = ano
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
        if saldo_mes > 0:
            saldo_mes_classe = "text-success"
        elif saldo_mes < 0:
            saldo_mes_classe = "text-danger"
        else:
            saldo_mes_classe = "text-secondary"

        context["saldo_mes_classe"] = saldo_mes_classe
        context["mes"] = mes
        context["ano"] = ano
        context["vendas"] = vendas
        context["pagamentos"] = pagamentos
        context["saldo_mes"] = saldo_mes

        context["vendas_detalhadas"] = Romaneio.objects.filter(
            data_romaneio__month=mes, data_romaneio__year=ano
        ).select_related("cliente", "motorista")

        context["pagamentos_detalhados"] = Pagamento.objects.filter(
            data_pagamento__month=mes, data_pagamento__year=ano
        ).select_related("cliente")

        return context


class RelatorioSaldoClientesView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "relatorios/saldo_clientes.html"
    context_object_name = "clientes"

    def get_queryset(self):
        tipo_saldo = self.request.GET.get("tipo_saldo", "todos")
        clientes = list(Cliente.objects.all())

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

        top_clientes = romaneios_mes.values("cliente__nome").annotate(
            total_comprado=Sum("valor_total")
        ).order_by("-total_comprado")[:5]
        context["top_clientes_mes"] = top_clientes

        vendas_por_madeira = (
            ItemRomaneio.objects.filter(
                romaneio__data_romaneio__month=mes,
                romaneio__data_romaneio__year=ano,
            )
            .values("tipo_madeira__nome")
            .annotate(total_m3=Sum("quantidade_m3"), total_valor=Sum("valor_total"))
            .order_by("-total_m3")[:10]
        )
        context["vendas_por_madeira"] = vendas_por_madeira

        return context