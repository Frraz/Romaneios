from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.tests.factories import create_cliente
from apps.financeiro.models import Pagamento


class PagamentoModelTests(TestCase):
    def test_pagamento_valor_deve_ser_positivo(self):
        cliente = create_cliente(nome="Cliente X")

        with self.assertRaises(ValidationError):
            Pagamento.objects.create(
                data_pagamento=timezone.localdate(),
                cliente=cliente,
                valor=Decimal("0.00"),
                tipo_pagamento="DINHEIRO",
            )

    def test_pagamento_data_nao_pode_ser_futura(self):
        cliente = create_cliente(nome="Cliente Y")
        amanha = timezone.localdate() + timezone.timedelta(days=1)

        with self.assertRaises(ValidationError):
            Pagamento.objects.create(
                data_pagamento=amanha,
                cliente=cliente,
                valor=Decimal("10.00"),
                tipo_pagamento="PIX",
            )

    def test_str_pagamento(self):
        cliente = create_cliente(nome="Cliente Z")
        pg = Pagamento.objects.create(
            data_pagamento=timezone.localdate(),
            cliente=cliente,
            valor=Decimal("12.34"),
            tipo_pagamento="PIX",
        )
        s = str(pg)
        self.assertIn("Cliente Z", s)
        self.assertIn("12.34", s)
        self.assertIn("PIX", s)