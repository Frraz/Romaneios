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


class RelatoriosDashboardViewTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_dash", password="12345678")
        self.client.login(username="rel_dash", password="12345678")
        self.tm = create_tipo_madeira(nome="ANGICO DASH", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

    def test_dashboard_aggregates_current_month(self):
        today = timezone.localdate()

        # romaneio no mês atual: 2m3 * 10 = 20
        c = create_cliente(nome="Cliente Dash")
        rom_ok = create_romaneio(numero_romaneio="dash-1", cliente=c, data_romaneio=today)
        create_item_romaneio(romaneio=rom_ok, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

        # romaneio em outro mês: não deve entrar
        other = today.replace(day=1)
        if other.month == 1:
            other = other.replace(year=other.year - 1, month=12)
        else:
            other = other.replace(month=other.month - 1)

        rom_ign = create_romaneio(numero_romaneio="dash-2", cliente=c, data_romaneio=other)
        create_item_romaneio(romaneio=rom_ign, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("9.000"))

        resp = self.client.get(reverse("relatorios:dashboard"), {"mes": today.month, "ano": today.year})
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.context["qtd_romaneios_mes"], 1)
        self.assertEqual(resp.context["total_m3_mes"], Decimal("2.000"))
        self.assertEqual(resp.context["total_faturado_mes"], Decimal("20.00"))

    def test_dashboard_saldo_total_receber_uses_negative_balances(self):
        # Cliente devendo 15 => saldo_atual = -15 (vendeu 20, pagou 5)
        c_neg = create_cliente(nome="Devendo")
        rom = create_romaneio(numero_romaneio="dash-3", cliente=c_neg)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))
        create_pagamento(cliente=c_neg, valor=Decimal("5.00"))

        # Cliente com crédito não entra
        c_pos = create_cliente(nome="Credito")
        create_pagamento(cliente=c_pos, valor=Decimal("10.00"))

        resp = self.client.get(reverse("relatorios:dashboard"))
        self.assertEqual(resp.status_code, 200)

        # saldo_total_receber é abs(soma negativos) => 15
        self.assertEqual(resp.context["saldo_total_receber"], Decimal("15.00"))


class RelatorioSaldoClientesViewTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_saldo", password="12345678")
        self.client.login(username="rel_saldo", password="12345678")

        self.tm = create_tipo_madeira(nome="MADEIRA SALDO", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # negativo: -15
        self.c_neg = create_cliente(nome="Alice", telefone="111", cpf_cnpj="123")
        rom = create_romaneio(numero_romaneio="saldo-1", cliente=self.c_neg)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))
        create_pagamento(cliente=self.c_neg, valor=Decimal("5.00"))

        # positivo: +20
        self.c_pos = create_cliente(nome="Bruno", telefone="222", cpf_cnpj="456")
        rom = create_romaneio(numero_romaneio="saldo-2", cliente=self.c_pos)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        create_pagamento(cliente=self.c_pos, valor=Decimal("30.00"))

        # zerado
        self.c_zero = create_cliente(nome="Carlos", telefone="333", cpf_cnpj="789")

    def test_saldo_clientes_filter_negativos(self):
        resp = self.client.get(reverse("relatorios:saldo_clientes"), {"tipo_saldo": "negativos"})
        self.assertEqual(resp.status_code, 200)
        nomes = {c.nome for c in resp.context["clientes"]}
        self.assertEqual(nomes, {self.c_neg.nome})

    def test_saldo_clientes_filter_positivos(self):
        resp = self.client.get(reverse("relatorios:saldo_clientes"), {"tipo_saldo": "positivos"})
        self.assertEqual(resp.status_code, 200)
        nomes = {c.nome for c in resp.context["clientes"]}
        self.assertEqual(nomes, {self.c_pos.nome})

    def test_saldo_clientes_filter_zerados(self):
        resp = self.client.get(reverse("relatorios:saldo_clientes"), {"tipo_saldo": "zerados"})
        self.assertEqual(resp.status_code, 200)
        nomes = {c.nome for c in resp.context["clientes"]}
        self.assertEqual(nomes, {self.c_zero.nome})

    def test_saldo_clientes_search_by_nome_telefone_cpf(self):
        resp = self.client.get(reverse("relatorios:saldo_clientes"), {"q": "222"})
        self.assertEqual(resp.status_code, 200)
        nomes = [c.nome for c in resp.context["clientes"]]
        self.assertEqual(nomes, [self.c_pos.nome])

    def test_saldo_clientes_sorted_by_most_negative_first(self):
        # já existe um negativo e um positivo e um zero; ordenação deve começar pelo negativo
        resp = self.client.get(reverse("relatorios:saldo_clientes"), {"tipo_saldo": "todos"})
        self.assertEqual(resp.status_code, 200)
        clientes = list(resp.context["clientes"])
        self.assertEqual(clientes[0].nome, self.c_neg.nome)

class RelatorioFichaRomaneiosTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_rom", password="12345678")
        self.client.login(username="rel_rom", password="12345678")

        self.today = timezone.localdate()
        self.mes = self.today.month
        self.ano = self.today.year

        self.c = create_cliente(nome="Cliente Rom")
        self.tm_a = create_tipo_madeira(nome="A", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        self.tm_b = create_tipo_madeira(nome="B", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # Romaneio 2 com madeira A
        self.r2 = create_romaneio(numero_romaneio="2", cliente=self.c, data_romaneio=self.today)
        create_item_romaneio(romaneio=self.r2, tipo_madeira=self.tm_a, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))

        # Romaneio 10 com madeira B
        self.r10 = create_romaneio(numero_romaneio="10", cliente=self.c, data_romaneio=self.today)
        create_item_romaneio(romaneio=self.r10, tipo_madeira=self.tm_b, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))

        # Romaneio com A e B (para garantir distinct)
        self.r3 = create_romaneio(numero_romaneio="3", cliente=self.c, data_romaneio=self.today)
        create_item_romaneio(romaneio=self.r3, tipo_madeira=self.tm_a, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        create_item_romaneio(romaneio=self.r3, tipo_madeira=self.tm_b, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

    def test_ficha_romaneios_filter_by_tipo_madeira(self):
        resp = self.client.get(
            reverse("relatorios:ficha_romaneios"),
            {"mes": self.mes, "ano": self.ano, "tipo_madeira_id": self.tm_a.id},
        )
        self.assertEqual(resp.status_code, 200)
        romaneios = list(resp.context["romaneios"])
        numeros = [r.numero_romaneio for r in romaneios]

        # deve incluir r2 e r3 (tem A), mas não r10
        self.assertIn("2", numeros)
        self.assertIn("3", numeros)
        self.assertNotIn("10", numeros)

        # e sem duplicar r3 apesar de ter 2 itens
        self.assertEqual(len(numeros), len(set(numeros)))

    def test_ficha_romaneios_sort_numero_is_numeric(self):
        resp = self.client.get(
            reverse("relatorios:ficha_romaneios"),
            {"mes": self.mes, "ano": self.ano, "sort": "numero", "dir": "asc"},
        )
        self.assertEqual(resp.status_code, 200)

        romaneios = list(resp.context["romaneios"])
        numeros = [r.numero_romaneio for r in romaneios]
        # ordem numérica esperada: 2, 3, 10
        self.assertEqual(numeros[:3], ["2", "3", "10"])

    def test_export_csv_respects_tipo_madeira_filter(self):
        url = reverse("relatorios:ficha_romaneios_export")
        resp = self.client.get(url, {"mes": self.mes, "ano": self.ano, "tipo_madeira_id": self.tm_a.id})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn("attachment;", resp["Content-Disposition"])

        content = resp.content.decode("utf-8")
        # deve conter espécie A, e NÃO conter espécie B (por filtro)
        self.assertIn(";A;", content)
        self.assertNotIn(";B;", content)

    def test_export_excel_returns_xlsx(self):
        url = reverse("relatorios:ficha_romaneios_export_excel")
        resp = self.client.get(url, {"mes": self.mes, "ano": self.ano})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        # XLSX é um ZIP => começa com PK
        self.assertTrue(resp.content[:2] == b"PK")




class RelatorioFluxoFinanceiroTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_fluxo", password="12345678")
        self.client.login(username="rel_fluxo", password="12345678")

        self.today = timezone.localdate()
        self.mes = self.today.month
        self.ano = self.today.year

        self.tm_a = create_tipo_madeira(nome="MADEIRA A", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        self.tm_b = create_tipo_madeira(nome="MADEIRA B", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # Cliente 1 tem venda com madeira A
        self.c1 = create_cliente(nome="Cliente 1")
        r1 = create_romaneio(numero_romaneio="5001", cliente=self.c1, data_romaneio=self.today)
        create_item_romaneio(romaneio=r1, tipo_madeira=self.tm_a, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        # pagamento c1 no mês
        create_pagamento(cliente=self.c1, data_pagamento=self.today, valor=Decimal("100.00"))

        # Cliente 2 tem venda com madeira B
        self.c2 = create_cliente(nome="Cliente 2")
        r2 = create_romaneio(numero_romaneio="5002", cliente=self.c2, data_romaneio=self.today)
        create_item_romaneio(romaneio=r2, tipo_madeira=self.tm_b, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))
        create_pagamento(cliente=self.c2, data_pagamento=self.today, valor=Decimal("200.00"))

    def test_fluxo_financeiro_filter_by_tipo_madeira_limits_payments_to_clients_in_sales(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro"),
            {"mes": self.mes, "ano": self.ano, "tipo_madeira_id": self.tm_a.id},
        )
        self.assertEqual(resp.status_code, 200)

        vendas = list(resp.context["vendas_detalhadas"])
        pagamentos = list(resp.context["pagamentos_detalhados"])

        # vendas: só cliente 1
        self.assertTrue(all(v.cliente_id == self.c1.id for v in vendas))
        # pagamentos: só cliente 1
        self.assertTrue(all(p.cliente_id == self.c1.id for p in pagamentos))

        # totais coerentes
        self.assertEqual(resp.context["vendas"], Decimal("10.00"))  # 1m3 * 10
        self.assertEqual(resp.context["pagamentos"], Decimal("100.00"))
        self.assertEqual(resp.context["saldo_mes"], Decimal("90.00"))

    def test_fluxo_export_excel_returns_xlsx(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro_export_excel"),
            {"mes": self.mes, "ano": self.ano},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(resp.content[:2] == b"PK")



class RelatorioFichaMadeirasTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_mad", password="12345678")
        self.client.login(username="rel_mad", password="12345678")

        self.today = timezone.localdate()
        self.mes = self.today.month
        self.ano = self.today.year

        self.cliente = create_cliente(nome="Cliente Madeira")
        self.tm_a = create_tipo_madeira(nome="ANGICO", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        self.tm_b = create_tipo_madeira(nome="IPÊ", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        self.rom = create_romaneio(numero_romaneio="7001", cliente=self.cliente, data_romaneio=self.today, tipo_romaneio="NORMAL")

        create_item_romaneio(romaneio=self.rom, tipo_madeira=self.tm_a, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))
        create_item_romaneio(romaneio=self.rom, tipo_madeira=self.tm_b, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

    def test_ficha_madeiras_filter_by_tipo_madeira(self):
        resp = self.client.get(
            reverse("relatorios:ficha_madeiras"),
            {"mes": self.mes, "ano": self.ano, "tipo_madeira_id": self.tm_a.id},
        )
        self.assertEqual(resp.status_code, 200)

        rows = list(resp.context["rows"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].tipo_madeira_id, self.tm_a.id)

        self.assertEqual(resp.context["total_m3"], Decimal("1.000"))
        self.assertEqual(resp.context["total_itens"], Decimal("10.00"))

    def test_export_excel_returns_xlsx(self):
        resp = self.client.get(
            reverse("relatorios:ficha_madeiras_export_excel"),
            {"mes": self.mes, "ano": self.ano},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(resp.content[:2] == b"PK")

