from datetime import datetime

from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from .models import Romaneio, ItemRomaneio
from .forms import RomaneioForm, ItemRomaneioFormSet
from apps.cadastros.models import TipoMadeira, Cliente

class RomaneioListView(LoginRequiredMixin, ListView):
    model = Romaneio
    template_name = 'romaneio/romaneio_list.html'
    context_object_name = 'romaneios'
    paginate_by = 20

    def get_queryset(self):
        queryset = (super().get_queryset()
            .select_related('cliente', 'motorista'))

        # Filtros
        mes = self.request.GET.get('mes')
        ano = self.request.GET.get('ano')
        cliente_id = self.request.GET.get('cliente')
        numero = self.request.GET.get('numero')

        if mes and ano:
            try:
                mes = int(mes)
                ano = int(ano)
                queryset = queryset.filter(
                    data_romaneio__month=mes,
                    data_romaneio__year=ano
                )
            except ValueError:
                pass
        elif not mes and not ano:
            now = datetime.now()
            queryset = queryset.filter(
                data_romaneio__month=now.month,
                data_romaneio__year=now.year
            )

        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        if numero:
            queryset = queryset.filter(numero_romaneio__icontains=numero)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Para dropdowns/filtros
        context['clientes'] = Cliente.objects.filter(ativo=True).order_by('nome')

        # Totais do período filtrado
        queryset = self.get_queryset()
        from django.db.models import Sum
        totais = queryset.aggregate(
            total_m3=Sum('m3_total'),
            total_valor=Sum('valor_total')
        )
        context['total_m3_periodo'] = totais['total_m3'] or 0
        context['total_valor_periodo'] = totais['total_valor'] or 0

        return context


class RomaneioCreateView(LoginRequiredMixin, CreateView):
    model = Romaneio
    form_class = RomaneioForm
    template_name = 'romaneio/romaneio_form.html'
    success_url = reverse_lazy('romaneio:romaneio_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Garante inicialização correta do formset mesmo quando criando
        if self.request.POST:
            context['formset'] = ItemRomaneioFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ItemRomaneioFormSet(instance=self.object)

        tipos_madeira = TipoMadeira.objects.filter(ativo=True)
        context['tipos_madeira_json'] = {
            str(tm.id): {
                'normal': float(tm.preco_normal),
                'com_frete': float(tm.preco_com_frete)
            }
            for tm in tipos_madeira
        }

        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.usuario_cadastro = self.request.user
            self.object.save()
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                f'Romaneio {self.object.numero_romaneio} cadastrado com sucesso! Total: R$ {self.object.valor_total:.2f}'
            )
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RomaneioUpdateView(LoginRequiredMixin, UpdateView):
    model = Romaneio
    form_class = RomaneioForm
    template_name = 'romaneio/romaneio_form.html'
    success_url = reverse_lazy('romaneio:romaneio_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ItemRomaneioFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ItemRomaneioFormSet(instance=self.object)

        tipos_madeira = TipoMadeira.objects.filter(ativo=True)
        context['tipos_madeira_json'] = {
            str(tm.id): {
                'normal': float(tm.preco_normal),
                'com_frete': float(tm.preco_com_frete)
            }
            for tm in tipos_madeira
        }
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                f'Romaneio {self.object.numero_romaneio} atualizado com sucesso!'
            )
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RomaneioDetailView(LoginRequiredMixin, DetailView):
    model = Romaneio
    template_name = 'romaneio/romaneio_detail.html'
    context_object_name = 'romaneio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['itens'] = self.object.itens.select_related('tipo_madeira')
        return context

# API para buscar preço da madeira (AJAX)
def get_preco_madeira(request):
    """Retorna o preço da madeira baseado no tipo de romaneio"""
    tipo_madeira_id = request.GET.get('tipo_madeira_id')
    tipo_romaneio = request.GET.get('tipo_romaneio')

    try:
        tipo_madeira = TipoMadeira.objects.get(id=tipo_madeira_id)
        preco = tipo_madeira.get_preco(tipo_romaneio)
        return JsonResponse({
            'success': True,
            'preco': float(preco)
        })
    except TipoMadeira.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tipo de madeira não encontrado'
        }, status=404)