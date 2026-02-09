from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tests.factories import create_cliente, create_pagamento, create_user


class PagamentoListViewTests(TestCase):
    def setUp(self):
        self.user = create_user(username="fin1", password="12345678")
        self.client.login(username="fin1", password="12345678")

    def test_list_view_defaults_to_current_month_year(self):
        # cria pagamento no mês atual e outro em mês diferente
        c = create_cliente(nome="Cliente Pag")
        today = timezone.localdate()

        create_pagamento(cliente=c, data_pagamento=today, valor=Decimal("10.00"))

        other_date = today.replace(day=1)
        if other_date.month == 1:
            other_date = other_date.replace(year=other_date.year - 1, month=12)
        else:
            other_date = other_date.replace(month=other_date.month - 1)

        create_pagamento(cliente=c, data_pagamento=other_date, valor=Decimal("99.00"))

        resp = self.client.get(reverse("financeiro:pagamento_list"))
        self.assertEqual(resp.status_code, 200)

        pagamentos = resp.context["pagamentos"]
        self.assertTrue(all(p.data_pagamento.month == today.month and p.data_pagamento.year == today.year for p in pagamentos))

    def test_list_view_filters_by_cliente(self):
        c1 = create_cliente(nome="C1")
        c2 = create_cliente(nome="C2")
        today = timezone.localdate()

        create_pagamento(cliente=c1, data_pagamento=today, valor=Decimal("10.00"))
        create_pagamento(cliente=c2, data_pagamento=today, valor=Decimal("20.00"))

        resp = self.client.get(reverse("financeiro:pagamento_list"), {"mes": today.month, "ano": today.year, "cliente": c1.id})
        self.assertEqual(resp.status_code, 200)

        pagamentos = list(resp.context["pagamentos"])
        self.assertEqual(len(pagamentos), 1)
        self.assertEqual(pagamentos[0].cliente_id, c1.id)

    def test_list_view_total_periodo(self):
        c = create_cliente(nome="CT")
        today = timezone.localdate()

        create_pagamento(cliente=c, data_pagamento=today, valor=Decimal("10.00"))
        create_pagamento(cliente=c, data_pagamento=today, valor=Decimal("20.00"))

        resp = self.client.get(reverse("financeiro:pagamento_list"), {"mes": today.month, "ano": today.year})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["total_periodo"], Decimal("30.00"))


class PagamentoCreateViewTests(TestCase):
    def setUp(self):
        self.user = create_user(username="fin2", password="12345678")
        self.client.login(username="fin2", password="12345678")

    def test_create_pagamento_sets_usuario_cadastro(self):
        c = create_cliente(nome="Cliente Create")
        today = timezone.localdate()

        resp = self.client.post(
            reverse("financeiro:pagamento_create"),
            data={
                "data_pagamento": today.isoformat(),
                "cliente": c.id,
                "valor": "12.34",
                "tipo_pagamento": "PIX",
                "descricao": "Teste",
            },
        )
        # CreateView retorna redirect
        self.assertEqual(resp.status_code, 302)

        from apps.financeiro.models import Pagamento
        pg = Pagamento.objects.get(cliente=c, valor=Decimal("12.34"))
        self.assertEqual(pg.usuario_cadastro_id, self.user.id)