from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.tests.factories import (
    create_cliente,
    create_item_romaneio,
    create_pagamento,
    create_romaneio,
    create_tipo_madeira,
)


class ClienteSaldoAtualTests(TestCase):
    def test_saldo_sem_vendas_e_sem_pagamentos_eh_zero(self):
        cliente = create_cliente(nome="Cliente Saldo Zero")
        self.assertEqual(cliente.saldo_atual, Decimal("0.00"))

    def test_saldo_negativo_quando_cliente_deve(self):
        cliente = create_cliente(nome="Cliente Devendo")

        rom = create_romaneio(numero_romaneio="4001", cliente=cliente, modalidade="SIMPLES", tipo_romaneio="NORMAL")
        tm = create_tipo_madeira(nome="ANGICO SALDO", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        create_item_romaneio(
            romaneio=rom,
            tipo_madeira=tm,
            valor_unitario=Decimal("10.00"),
            quantidade_m3_total=Decimal("2.000"),
        )
        rom.refresh_from_db()
        self.assertEqual(rom.valor_total, Decimal("20.00"))

        # pagou só 5
        create_pagamento(cliente=cliente, valor=Decimal("5.00"))

        cliente.refresh_from_db()
        self.assertEqual(cliente.saldo_atual, Decimal("5.00") - Decimal("20.00"))

    def test_saldo_positivo_quando_cliente_tem_credito(self):
        cliente = create_cliente(nome="Cliente Credito")

        rom = create_romaneio(numero_romaneio="4002", cliente=cliente, modalidade="SIMPLES", tipo_romaneio="NORMAL")
        tm = create_tipo_madeira(nome="IPÊ SALDO", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        create_item_romaneio(
            romaneio=rom,
            tipo_madeira=tm,
            valor_unitario=Decimal("10.00"),
            quantidade_m3_total=Decimal("1.000"),
        )
        rom.refresh_from_db()
        self.assertEqual(rom.valor_total, Decimal("10.00"))

        create_pagamento(cliente=cliente, valor=Decimal("50.00"))

        self.assertEqual(cliente.saldo_atual, Decimal("50.00") - Decimal("10.00"))

    def test_saldo_calcula_apenas_movimentos_do_proprio_cliente(self):
        cliente_a = create_cliente(nome="Cliente A")
        cliente_b = create_cliente(nome="Cliente B")

        # venda do cliente A (10)
        rom_a = create_romaneio(numero_romaneio="4003", cliente=cliente_a)
        tm = create_tipo_madeira(nome="MADEIRA MIX", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        create_item_romaneio(romaneio=rom_a, tipo_madeira=tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))

        # pagamento do cliente B (99)
        create_pagamento(cliente=cliente_b, valor=Decimal("99.00"))

        self.assertEqual(cliente_a.saldo_atual, Decimal("0.00") - Decimal("10.00"))
        self.assertEqual(cliente_b.saldo_atual, Decimal("99.00") - Decimal("0.00"))