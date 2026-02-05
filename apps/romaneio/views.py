from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.cadastros.models import Cliente, TipoMadeira

from .forms import RomaneioForm, ItemRomaneioFormSet
from .models import Romaneio


def get_mes_ano(request):
    now = datetime.now()
    try:
        mes = int(request.GET.get("mes", now.month))
    except Exception:
        mes = now.month
    try:
        ano = int(request.GET.get("ano", now.year))
    except Exception:
        ano = now.year
    return mes, ano


# ======= ROMANEIO (ÚNICO: SIMPLES + DETALHADO) =======
class RomaneioListView(LoginRequiredMixin, ListView):
    model = Romaneio
    template_name = "romaneio/romaneio_list.html"
    context_object_name = "romaneios"
    paginate_by = 20

    def get_queryset(self):
        qs = self.model.objects.select_related("cliente", "motorista")

        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")
        cliente_id = self.request.GET.get("cliente")
        numero = self.request.GET.get("numero")
        modalidade = self.request.GET.get("modalidade")  # opcional

        if mes and ano:
            qs = qs.filter(data_romaneio__month=int(mes), data_romaneio__year=int(ano))
        else:
            now = datetime.now()
            qs = qs.filter(data_romaneio__month=now.month, data_romaneio__year=now.year)

        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if numero:
            qs = qs.filter(numero_romaneio__icontains=numero)
        if modalidade:
            qs = qs.filter(modalidade=modalidade)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["clientes"] = Cliente.objects.filter(ativo=True).order_by("nome")

        qs = self.object_list
        totais = qs.aggregate(total_m3=Sum("m3_total"), total_valor=Sum("valor_total"))
        context["total_m3_periodo"] = totais["total_m3"] or 0
        context["total_valor_periodo"] = totais["total_valor"] or 0

        context["anos"] = sorted(set(q.data_romaneio.year for q in Romaneio.objects.all()))
        context["meses"] = range(1, 13)
        if not context["anos"]:
            context["anos"] = [datetime.now().year]

        context["modalidades"] = Romaneio.MODALIDADE_CHOICES  # para filtro opcional no template
        return context


class RomaneioCreateView(LoginRequiredMixin, CreateView):
    model = Romaneio
    form_class = RomaneioForm
    template_name = "romaneio/romaneio_form.html"
    success_url = reverse_lazy("romaneio:romaneio_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = ItemRomaneioFormSet(self.request.POST)
        else:
            context["formset"] = ItemRomaneioFormSet()

        tipos_madeira = TipoMadeira.objects.filter(ativo=True)
        context["tipos_madeira_json"] = {
            str(tm.id): {
                "normal": float(tm.preco_normal or 0),
                "com_frete": float(tm.preco_com_frete or 0),
            }
            for tm in tipos_madeira
        }
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Controla validação do form + formset de forma consistente.
        """
        self.object = None
        form = self.get_form()
        context = self.get_context_data(form=form)
        formset = context["formset"]

        if form.is_valid() and formset.is_valid():
            return self.forms_valid(form, formset)

        return self.render_to_response(context)

    def forms_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.usuario_cadastro = self.request.user
        self.object.save()

        formset.instance = self.object
        formset.save()

        messages.success(
            self.request,
            f"Romaneio {self.object.numero_romaneio} cadastrado com sucesso! Total: R$ {self.object.valor_total:.2f}",
        )
        return redirect(self.get_success_url())


class RomaneioUpdateView(LoginRequiredMixin, UpdateView):
    model = Romaneio
    form_class = RomaneioForm
    template_name = "romaneio/romaneio_form.html"
    success_url = reverse_lazy("romaneio:romaneio_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = ItemRomaneioFormSet(self.request.POST, instance=self.object)
        else:
            context["formset"] = ItemRomaneioFormSet(instance=self.object)

        tipos_madeira = TipoMadeira.objects.filter(ativo=True)
        context["tipos_madeira_json"] = {
            str(tm.id): {
                "normal": float(tm.preco_normal or 0),
                "com_frete": float(tm.preco_com_frete or 0),
            }
            for tm in tipos_madeira
        }
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Controla validação do form + formset de forma consistente.
        """
        self.object = self.get_object()
        form = self.get_form()
        context = self.get_context_data(form=form)
        formset = context["formset"]

        if form.is_valid() and formset.is_valid():
            return self.forms_valid(form, formset)

        return self.render_to_response(context)

    def forms_valid(self, form, formset):
        self.object = form.save()
        formset.instance = self.object
        formset.save()

        messages.success(self.request, f"Romaneio {self.object.numero_romaneio} atualizado com sucesso!")
        return redirect(self.get_success_url())


class RomaneioDetailView(LoginRequiredMixin, DetailView):
    model = Romaneio
    template_name = "romaneio/romaneio_detail.html"
    context_object_name = "romaneio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["itens"] = self.object.itens.select_related("tipo_madeira")
        return context


# ======= API AUXILIAR =======
def get_preco_madeira(request):
    tipo_madeira_id = request.GET.get("tipo_madeira_id")
    tipo_romaneio = request.GET.get("tipo_romaneio")
    try:
        tipo_madeira = TipoMadeira.objects.get(id=tipo_madeira_id)
        preco = tipo_madeira.get_preco(tipo_romaneio)
        return JsonResponse({"success": True, "preco": float(preco)})
    except TipoMadeira.DoesNotExist:
        return JsonResponse({"success": False, "error": "Tipo de madeira não encontrado"}, status=404)