from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Cliente, TipoMadeira, Motorista
from .forms import ClienteForm, TipoMadeiraForm, MotoristaForm

# ========== CLIENTES ==========

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'cadastros/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20

    def get_queryset(self):
        queryset = list(super().get_queryset())

        # Busca por nome
        busca = self.request.GET.get('q')
        if busca:
            queryset = [c for c in queryset if busca.lower() in c.nome.lower()]

        # Filtro de saldo (property)
        filtro_saldo = self.request.GET.get('saldo')
        if filtro_saldo == 'negativos':
            queryset = [c for c in queryset if c.saldo_atual < 0]
        elif filtro_saldo == 'positivos':
            queryset = [c for c in queryset if c.saldo_atual > 0]
        elif filtro_saldo == 'zerados':
            queryset = [c for c in queryset if c.saldo_atual == 0]

        # Ordenação
        ordenar = self.request.GET.get('ordenar', 'nome')
        if ordenar == 'saldo':
            queryset = sorted(queryset, key=lambda c: c.saldo_atual)
        elif ordenar == 'saldo_desc':
            queryset = sorted(queryset, key=lambda c: c.saldo_atual, reverse=True)
        else:
            queryset = sorted(queryset, key=lambda c: c.nome.lower())

        return queryset

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cadastros/cliente_form.html'
    success_url = reverse_lazy('cadastros:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cadastros/cliente_form.html'
    success_url = reverse_lazy('cadastros:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'cadastros/cliente_confirm_delete.html'
    success_url = reverse_lazy('cadastros:cliente_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Cliente excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

# ========== TIPOS DE MADEIRA ==========

class TipoMadeiraListView(LoginRequiredMixin, ListView):
    model = TipoMadeira
    template_name = 'cadastros/tipo_madeira_list.html'
    context_object_name = 'tipos_madeira'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('q')
        if busca:
            queryset = queryset.filter(nome__icontains=busca)
        return queryset

class TipoMadeiraCreateView(LoginRequiredMixin, CreateView):
    model = TipoMadeira
    form_class = TipoMadeiraForm
    template_name = 'cadastros/tipo_madeira_form.html'
    success_url = reverse_lazy('cadastros:tipo_madeira_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de madeira cadastrado com sucesso!')
        return super().form_valid(form)

class TipoMadeiraUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoMadeira
    form_class = TipoMadeiraForm
    template_name = 'cadastros/tipo_madeira_form.html'
    success_url = reverse_lazy('cadastros:tipo_madeira_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de madeira atualizado com sucesso!')
        return super().form_valid(form)

# ========== MOTORISTAS ==========

class MotoristaListView(LoginRequiredMixin, ListView):
    model = Motorista
    template_name = 'cadastros/motorista_list.html'
    context_object_name = 'motoristas'
    paginate_by = 20

class MotoristaCreateView(LoginRequiredMixin, CreateView):
    model = Motorista
    form_class = MotoristaForm
    template_name = 'cadastros/motorista_form.html'
    success_url = reverse_lazy('cadastros:motorista_list')

    def form_valid(self, form):
        messages.success(self.request, 'Motorista cadastrado com sucesso!')
        return super().form_valid(form)

class MotoristaUpdateView(LoginRequiredMixin, UpdateView):
    model = Motorista
    form_class = MotoristaForm
    template_name = 'cadastros/motorista_form.html'
    success_url = reverse_lazy('cadastros:motorista_list')

    def form_valid(self, form):
        messages.success(self.request, 'Motorista atualizado com sucesso!')
        return super().form_valid(form)