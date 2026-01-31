from datetime import datetime
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum

from .models import Pagamento
from .forms import PagamentoForm
from apps.cadastros.models import Cliente

class PagamentoListView(LoginRequiredMixin, ListView):
    model = Pagamento
    template_name = 'financeiro/pagamento_list.html'
    context_object_name = 'pagamentos'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente')

        # Filtros
        mes = self.request.GET.get('mes')
        ano = self.request.GET.get('ano')
        cliente_id = self.request.GET.get('cliente')

        if mes and ano:
            try:
                mes = int(mes)
                ano = int(ano)
                queryset = queryset.filter(
                    data_pagamento__month=mes,
                    data_pagamento__year=ano
                )
            except ValueError:
                pass
        elif not mes and not ano:
            now = datetime.now()
            queryset = queryset.filter(
                data_pagamento__month=now.month,
                data_pagamento__year=now.year
            )

        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.filter(ativo=True).order_by('nome')
        total = self.get_queryset().aggregate(Sum('valor'))['valor__sum'] or 0
        context['total_periodo'] = total
        return context

class PagamentoCreateView(LoginRequiredMixin, CreateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'financeiro/pagamento_form.html'
    success_url = reverse_lazy('financeiro:pagamento_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.usuario_cadastro = self.request.user
        self.object.save()
        # saldo atualizado do cliente após o pagamento já está correto, pois saldo é property!
        messages.success(
            self.request,
            f'Pagamento de R$ {self.object.valor:.2f} cadastrado com sucesso! '
            f'Saldo atual do cliente: R$ {self.object.cliente.saldo_atual:.2f}'
        )
        return super().form_valid(form)

class PagamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Pagamento
    form_class = PagamentoForm
    template_name = 'financeiro/pagamento_form.html'
    success_url = reverse_lazy('financeiro:pagamento_list')

    def form_valid(self, form):
        messages.success(self.request, 'Pagamento atualizado com sucesso!')
        return super().form_valid(form)