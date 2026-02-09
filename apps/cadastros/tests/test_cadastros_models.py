from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.tests.factories import create_motorista, create_tipo_madeira


class TipoMadeiraModelTests(TestCase):
    def test_get_preco_normal(self):
        tm = create_tipo_madeira(preco_normal=Decimal("50.00"), preco_com_frete=Decimal("70.00"))
        self.assertEqual(tm.get_preco("NORMAL"), Decimal("50.00"))

    def test_get_preco_com_frete(self):
        tm = create_tipo_madeira(preco_normal=Decimal("50.00"), preco_com_frete=Decimal("70.00"))
        self.assertEqual(tm.get_preco("COM_FRETE"), Decimal("70.00"))

    def test_str_contains_nome_and_prices(self):
        tm = create_tipo_madeira(nome="IPÊ", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        s = str(tm)
        self.assertIn("IPÊ", s)
        self.assertIn("Normal:", s)
        self.assertIn("Com Frete:", s)


class MotoristaModelTests(TestCase):
    def test_str_without_plate(self):
        m = create_motorista(nome="João")
        self.assertEqual(str(m), "João")

    def test_str_with_plate(self):
        m = create_motorista(nome="João", placa_veiculo="ABC-1234")
        self.assertEqual(str(m), "João (ABC-1234)")