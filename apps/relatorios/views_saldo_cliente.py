from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.cadastros.models import Cliente


class RelatorioSaldoClientesView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "relatorios/saldo_clientes.html"
    context_object_name = "clientes"
    paginate_by = 100  # opcional: evita página gigante se tiver muitos clientes

    def get_queryset(self):
        tipo_saldo = (self.request.GET.get("tipo_saldo") or "todos").strip().lower()
        q = (self.request.GET.get("q") or "").strip().lower()

        # Se quiser exibir apenas clientes ativos, troque para:
        # qs = Cliente.objects.filter(ativo=True)
        qs = Cliente.objects.all()

        # Como saldo_atual é property, vamos para Python
        clientes = list(qs)

        # ===== busca (q) =====
        if q:
            def match(c: Cliente) -> bool:
                nome = (getattr(c, "nome", "") or "").lower()
                telefone = (getattr(c, "telefone", "") or "").lower()
                cpf_cnpj = (getattr(c, "cpf_cnpj", "") or "").lower()
                return (q in nome) or (q in telefone) or (q in cpf_cnpj)

            clientes = [c for c in clientes if match(c)]

        # ===== filtro por tipo de saldo =====
        if tipo_saldo == "negativos":
            clientes = [c for c in clientes if c.saldo_atual < 0]
        elif tipo_saldo == "positivos":
            clientes = [c for c in clientes if c.saldo_atual > 0]
        elif tipo_saldo == "zerados":
            clientes = [c for c in clientes if c.saldo_atual == 0]
        else:
            tipo_saldo = "todos"

        # ===== ordenação padrão =====
        # do mais negativo para o mais positivo; em empate, por nome
        clientes.sort(key=lambda c: (c.saldo_atual, (getattr(c, "nome", "") or "").lower()))

        # salva para contexto
        self._tipo_saldo = tipo_saldo
        self._q = q
        return clientes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos_saldo"] = ["todos", "negativos", "positivos", "zerados"]
        context["tipo_saldo"] = getattr(self, "_tipo_saldo", "todos")
        context["q"] = getattr(self, "_q", "")
        return context