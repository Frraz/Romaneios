from django.views.generic import TemplateView
from django.db.models import Sum
from datetime import datetime
from apps.romaneio.models import Romaneio
from apps.cadastros.models import Cliente

def get_mes_ano(request):
    """Obtém mês/ano via GET, padrão é atual."""
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

class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Permite ajustar mes/ano via URL ?mes=5&ano=2024
        mes, ano = get_mes_ano(self.request)

        # Romaneios do mês
        romaneios_mes = Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano
        )

        # Total vendido em m³
        context['total_m3_mes'] = romaneios_mes.aggregate(
            total_m3=Sum('m3_total')
        )['total_m3'] or 0

        # Total faturado
        context['total_faturado_mes'] = romaneios_mes.aggregate(
            total_valor=Sum('valor_total')
        )['total_valor'] or 0

        # Quantidade de romaneios
        context['qtd_romaneios_mes'] = romaneios_mes.count()

        # Clientes e saldo
        todos_clientes = Cliente.objects.all()
        saldos_negativos = [c.saldo_atual for c in todos_clientes if c.saldo_atual < 0]

        # Saldo total a receber = soma dos saldos negativos absolutos
        context['saldo_total_receber'] = abs(sum(saldos_negativos)) if saldos_negativos else 0

        # Top 5 maiores devedores
        devedores = sorted(
            [c for c in todos_clientes if c.saldo_atual < 0],
            key=lambda c: c.saldo_atual
        )[:5]
        context['maiores_devedores'] = devedores

        # Informações de período para o template
        context['mes'] = mes
        context['ano'] = ano

        # Futuras métricas: vendas por madeira, top clientes, gráficos
        # context['vendas_por_madeira'] = ...
        # context['top_clientes_mes'] = ...

        return context