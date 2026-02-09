from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tests.factories import (
    create_cliente,
    create_item_romaneio,
    create_pagamento,
    create_romaneio,
    create_tipo_madeira,
    create_user,
)


class ClienteListViewSaldoTests(TestCase):
    def setUp(self):
        self.user = create_user(username="cad_user", password="12345678")
        self.client.login(username="cad_user", password="12345678")

        self.tm = create_tipo_madeira(nome="Madeira Teste", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # Cliente negativo: vendeu 20, pagou 5 => -15
        self.c_neg = create_cliente(nome="Cliente Neg")
        rom = create_romaneio(numero_romaneio="cneg-1", cliente=self.c_neg)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))
        create_pagamento(cliente=self.c_neg, valor=Decimal("5.00"))

        # Cliente positivo: vendeu 10, pagou 30 => +20
        self.c_pos = create_cliente(nome="Cliente Pos")
        rom = create_romaneio(numero_romaneio="cpos-1", cliente=self.c_pos)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        create_pagamento(cliente=self.c_pos, valor=Decimal("30.00"))

        # Cliente zerado
        self.c_zero = create_cliente(nome="Cliente Zero")

    def _get_clientes_context(self, **params):
        url = reverse("cadastros:cliente_list")
        resp = self.client.get(url, params)
        self.assertEqual(resp.status_code, 200)
        return resp.context["clientes"]

    def test_cliente_list_inclui_saldo_calc_annotation(self):
        clientes = self._get_clientes_context()
        # garante que os objetos carregados têm o atributo anotado
        any_cliente = clientes[0]
        self.assertTrue(hasattr(any_cliente, "saldo_calc"))

    def test_filtro_saldo_negativos(self):
        clientes = self._get_clientes_context(saldo="negativos")
        nomes = {c.nome for c in clientes}
        self.assertIn(self.c_neg.nome, nomes)
        self.assertNotIn(self.c_pos.nome, nomes)
        self.assertNotIn(self.c_zero.nome, nomes)

    def test_filtro_saldo_positivos(self):
        clientes = self._get_clientes_context(saldo="positivos")
        nomes = {c.nome for c in clientes}
        self.assertIn(self.c_pos.nome, nomes)
        self.assertNotIn(self.c_neg.nome, nomes)
        self.assertNotIn(self.c_zero.nome, nomes)

    def test_filtro_saldo_zerados(self):
        clientes = self._get_clientes_context(saldo="zerados")
        nomes = {c.nome for c in clientes}
        self.assertIn(self.c_zero.nome, nomes)
        self.assertNotIn(self.c_neg.nome, nomes)
        self.assertNotIn(self.c_pos.nome, nomes)


class UsuarioViewsPermissionTests(TestCase):
    def test_usuario_list_requires_staff(self):
        u = create_user(username="notstaff", password="12345678", is_staff=False)
        self.client.login(username="notstaff", password="12345678")
        resp = self.client.get(reverse("cadastros:usuario_list"))
        self.assertEqual(resp.status_code, 403)

    def test_usuario_list_allows_staff(self):
        u = create_user(username="staffok", password="12345678", is_staff=True)
        self.client.login(username="staffok", password="12345678")
        resp = self.client.get(reverse("cadastros:usuario_list"))
        self.assertEqual(resp.status_code, 200)