from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from datetime import datetime
from apps.romaneio.models import Romaneio, ItemRomaneio
from apps.financeiro.models import Pagamento
from apps.cadastros.models import Cliente

def get_mes_ano(request):
    now = datetime.now()
    try:
        mes = int(request.GET.get('mes', now.month))
    except (TypeError, ValueError):
        mes = now.month
    try:
        ano = int(request.GET.get('ano', now.year))
    except (TypeError, ValueError):
        ano = now.year
    return mes, ano

class RelatorioRomaneiosView(ListView):
    model = Romaneio
    template_name = 'relatorios/ficha_romaneios.html'
    context_object_name = 'romaneios'

    def get_queryset(self):
        queryset = super().get_queryset()
        mes, ano = get_mes_ano(self.request)
        cliente_id = self.request.GET.get('cliente')
        queryset = queryset.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano
        )
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.select_related('cliente', 'motorista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)
        context['mes'] = mes
        context['ano'] = ano
        context['clientes'] = Cliente.objects.all()
        return context

class RelatorioMadeirasView(TemplateView):
    template_name = 'relatorios/ficha_madeiras.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)
        relatorio = ItemRomaneio.objects.filter(
            romaneio__data_romaneio__month=mes,
            romaneio__data_romaneio__year=ano,
        ).values('tipo_madeira__nome'
        ).annotate(
            total_m3=Sum('quantidade_m3'),
            total_valor=Sum('valor_total')
        ).order_by('-total_m3')
        context['relatorio'] = relatorio
        context['mes'] = mes
        context['ano'] = ano
        return context

class RelatorioFluxoView(TemplateView):
    template_name = 'relatorios/fluxo_financeiro.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)
        vendas = Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        pagamentos = Pagamento.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).aggregate(total=Sum('valor'))['total'] or 0

        # --- CORREÇÃO CRUCIAL: variável para sinal de saldo ---
        saldo_mes = pagamentos - vendas
        # define classe para saldo positivo/negativo/zero
        if saldo_mes > 0:
            saldo_mes_classe = 'text-success'
        elif saldo_mes < 0:
            saldo_mes_classe = 'text-danger'
        else:
            saldo_mes_classe = 'text-secondary'
        context['saldo_mes_classe'] = saldo_mes_classe

        context['mes'] = mes
        context['ano'] = ano
        context['vendas'] = vendas
        context['pagamentos'] = pagamentos
        context['saldo_mes'] = saldo_mes

        # EXTRAS: vendas e pagamentos detalhados do mês
        context['vendas_detalhadas'] = Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano
        )

        context['pagamentos_detalhados'] = Pagamento.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).select_related('cliente')

        return context

class RelatorioSaldoClientesView(ListView):
    model = Cliente
    template_name = 'relatorios/saldo_clientes.html'
    context_object_name = 'clientes'

    def get_queryset(self):
        tipo_saldo = self.request.GET.get('tipo_saldo', 'todos')
        queryset = Cliente.objects.all()
        clientes = list(queryset)
        if tipo_saldo == 'negativos':
            clientes = [c for c in clientes if c.saldo_atual < 0]
        elif tipo_saldo == 'positivos':
            clientes = [c for c in clientes if c.saldo_atual > 0]
        elif tipo_saldo == 'zerados':
            clientes = [c for c in clientes if c.saldo_atual == 0]
        clientes = sorted(clientes, key=lambda c: c.saldo_atual)
        return clientes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_saldo'] = ['todos', 'negativos', 'positivos', 'zerados']
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'relatorios/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        romaneios_mes = Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano
        )
        totais_mes = romaneios_mes.aggregate(
            total_m3=Sum('m3_total'),
            total_valor=Sum('valor_total'),
            qtd_romaneios=Count('id')
        )
        context['mes'] = mes
        context['ano'] = ano
        context['total_m3_mes'] = totais_mes['total_m3'] or 0
        context['total_faturado_mes'] = totais_mes['total_valor'] or 0
        context['qtd_romaneios_mes'] = totais_mes['qtd_romaneios'] or 0

        # Saldo total a receber = soma dos débitos (clientes negativos)
        todos_clientes = Cliente.objects.all()
        saldos_negativos = [c.saldo_atual for c in todos_clientes if c.saldo_atual < 0]
        context['saldo_total_receber'] = abs(sum(saldos_negativos)) if saldos_negativos else 0

        # Top 5 maiores devedores
        devedores = sorted(
            [c for c in todos_clientes if c.saldo_atual < 0],
            key=lambda c: c.saldo_atual
        )[:5]
        context['maiores_devedores'] = devedores

        # Top 5 clientes que mais compraram no mês
        top_clientes = romaneios_mes.values('cliente__nome').annotate(
            total_comprado=Sum('valor_total')
        ).order_by('-total_comprado')[:5]
        context['top_clientes_mes'] = top_clientes

        # Vendas por tipo de madeira no mês
        vendas_por_madeira = ItemRomaneio.objects.filter(
            romaneio__data_romaneio__month=mes,
            romaneio__data_romaneio__year=ano
        ).values('tipo_madeira__nome').annotate(
            total_m3=Sum('quantidade_m3'),
            total_valor=Sum('valor_total')
        ).order_by('-total_m3')[:10]
        context['vendas_por_madeira'] = vendas_por_madeira

        return context