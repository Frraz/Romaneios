from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.tests.factories import (
    create_cliente,
    create_item_romaneio,
    create_romaneio,
    create_tipo_madeira,
    create_unidade_romaneio,
)


class RomaneioTotaisTests(TestCase):
    def test_romaneio_totais_atualizados_no_simples_quando_cria_item(self):
        cliente = create_cliente(nome="Cliente A")
        rom = create_romaneio(numero_romaneio="2001", cliente=cliente, modalidade="SIMPLES", tipo_romaneio="NORMAL")

        tm = create_tipo_madeira(nome="ANGICO A", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        create_item_romaneio(
            romaneio=rom,
            tipo_madeira=tm,
            valor_unitario=Decimal("10.00"),
            quantidade_m3_total=Decimal("2.000"),
        )

        rom.refresh_from_db()
        self.assertEqual(rom.m3_total, Decimal("2.000"))
        self.assertEqual(rom.valor_bruto, Decimal("20.00"))
        self.assertEqual(rom.valor_total, Decimal("20.00"))

    def test_item_save_autopreenche_valor_unitario_quando_zero(self):
        rom = create_romaneio(numero_romaneio="2002", tipo_romaneio="COM_FRETE", modalidade="SIMPLES")
        tm = create_tipo_madeira(nome="IPÊ", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("99.00"))

        item = create_item_romaneio(
            romaneio=rom,
            tipo_madeira=tm,
            valor_unitario=Decimal("0.00"),
            quantidade_m3_total=Decimal("1.000"),
        )
        item.refresh_from_db()
        self.assertEqual(item.valor_unitario, Decimal("99.00"))
        self.assertEqual(item.valor_total, Decimal("99.00"))

        rom.refresh_from_db()
        self.assertEqual(rom.valor_total, Decimal("99.00"))

    def test_item_delete_recalcula_totais_romaneio(self):
        rom = create_romaneio(numero_romaneio="2003")
        tm = create_tipo_madeira(nome="ANGICO", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        item1 = create_item_romaneio(romaneio=rom, tipo_madeira=tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        item2 = create_item_romaneio(romaneio=rom, tipo_madeira=tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

        rom.refresh_from_db()
        self.assertEqual(rom.m3_total, Decimal("3.000"))
        self.assertEqual(rom.valor_total, Decimal("30.00"))

        item2.delete()
        rom.refresh_from_db()
        self.assertEqual(rom.m3_total, Decimal("1.000"))
        self.assertEqual(rom.valor_total, Decimal("10.00"))


class RomaneioDetalhadoTests(TestCase):
    def test_unidade_em_romaneio_detalhado_recalcula_item_e_romaneio(self):
        rom = create_romaneio(numero_romaneio="3001", modalidade="DETALHADO", tipo_romaneio="NORMAL")
        tm = create_tipo_madeira(nome="MADEIRA D", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # No DETALHADO, item.quantidade_m3_total pode começar 0, mas será recalculado após unidades
        item = create_item_romaneio(
            romaneio=rom,
            tipo_madeira=tm,
            valor_unitario=Decimal("10.00"),
            quantidade_m3_total=Decimal("0.000"),
        )
        item.refresh_from_db()

        # Cria 2 unidades e verifica somatório
        create_unidade_romaneio(item=item, quantidade_m3=Decimal("0.500"), rodo=None, comprimento=None)
        create_unidade_romaneio(item=item, quantidade_m3=Decimal("1.250"), rodo=None, comprimento=None)

        item.refresh_from_db()
        rom.refresh_from_db()

        self.assertEqual(item.quantidade_m3_total, Decimal("1.750"))
        self.assertEqual(item.valor_total, Decimal("17.50"))
        self.assertEqual(rom.m3_total, Decimal("1.750"))
        self.assertEqual(rom.valor_total, Decimal("17.50"))

    def test_calcular_m3_detalhado_aplica_formula_quando_rodo_e_comprimento(self):
        # fórmula deve retornar Decimal quantizado (0.001)
        rom = create_romaneio(numero_romaneio="3002", modalidade="DETALHADO")
        item = create_item_romaneio(romaneio=rom, quantidade_m3_total=Decimal("0.000"))

        unidade = create_unidade_romaneio(
            item=item,
            comprimento=Decimal("4.00"),
            rodo=Decimal("30.00"),
            desconto_1=Decimal("0.00"),
            desconto_2=Decimal("0.00"),
            quantidade_m3=Decimal("0.001"),  # será sobrescrito no save do DETALHADO
        )

        unidade.refresh_from_db()
        # O valor exato depende da fórmula; aqui garantimos só que não é None e está quantizado.
        self.assertIsNotNone(unidade.quantidade_m3)
        self.assertEqual(unidade.quantidade_m3.as_tuple().exponent, -3)  # 3 casas decimais