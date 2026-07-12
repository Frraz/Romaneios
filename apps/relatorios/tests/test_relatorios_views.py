from __future__ import annotations

import datetime
from decimal import Decimal
from io import BytesIO

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.relatorios.utils import inicio_periodo, parse_mes_ano, periodo_label, periodo_slug
from apps.relatorios.views_fluxo_financeiro import _fluxo_querysets
from apps.tests.factories import (
    create_cliente,
    create_item_romaneio,
    create_pagamento,
    create_romaneiador,
    create_romaneio,
    create_tipo_madeira,
    create_user,
)


def _mes_anterior(dia: datetime.date) -> datetime.date:
    """Retorna o dia 1 do mês anterior ao informado."""
    primeiro = dia.replace(day=1)
    if primeiro.month == 1:
        return primeiro.replace(year=primeiro.year - 1, month=12)
    return primeiro.replace(month=primeiro.month - 1)


class FluxoClienteParamToleranceTests(TestCase):
    """O fluxo financeiro deve filtrar por cliente tanto com `cliente_id` quanto com `cliente`."""

    def setUp(self):
        self.factory = RequestFactory()
        today = timezone.localdate()
        self.c1 = create_cliente(nome="Fluxo C1")
        self.c2 = create_cliente(nome="Fluxo C2")
        create_romaneio(numero_romaneio="fx-1", cliente=self.c1, data_romaneio=today)
        create_romaneio(numero_romaneio="fx-2", cliente=self.c2, data_romaneio=today)

    def _vendas_nums(self, **params):
        request = self.factory.get("/relatorios/fluxo-financeiro/", params)
        vendas_qs, _ = _fluxo_querysets(request)
        return {r.numero_romaneio for r in vendas_qs}

    def test_filtra_com_cliente_id(self):
        self.assertEqual(self._vendas_nums(cliente_id=str(self.c1.id)), {"fx-1"})

    def test_filtra_com_cliente(self):
        self.assertEqual(self._vendas_nums(cliente=str(self.c1.id)), {"fx-1"})


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

    def test_ficha_romaneios_filter_by_romaneiador(self):
        rom_x = create_romaneiador(nome="ROMANEIADOR X")
        rom_y = create_romaneiador(nome="ROMANEIADOR Y")

        self.r2.romaneiador = rom_x
        self.r2.save(update_fields=["romaneiador"])
        self.r10.romaneiador = rom_y
        self.r10.save(update_fields=["romaneiador"])
        # r3 fica sem romaneiador

        resp = self.client.get(
            reverse("relatorios:ficha_romaneios"),
            {"mes": self.mes, "ano": self.ano, "romaneiador": rom_x.id},
        )
        self.assertEqual(resp.status_code, 200)
        numeros = [r.numero_romaneio for r in resp.context["romaneios"]]
        self.assertEqual(numeros, ["2"])

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

        movimentacoes = list(resp.context["movimentacoes"])
        self.assertTrue(movimentacoes)
        # vendas e pagamentos: só cliente 1 (madeira A)
        self.assertTrue(all(m.cliente_id == self.c1.id for m in movimentacoes))

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


class ParseMesAnoTests(TestCase):
    """Parser canônico de mes/ano compartilhado pelos relatórios."""

    def setUp(self):
        self.factory = RequestFactory()
        self.hoje = timezone.localdate()

    def _parse(self, params, **kwargs):
        request = self.factory.get("/relatorios/", params)
        return parse_mes_ano(request, **kwargs)

    def test_sem_parametros_usa_mes_ano_atual(self):
        self.assertEqual(self._parse({}), (self.hoje.month, self.hoje.year))

    def test_vazio_significa_todos(self):
        self.assertEqual(self._parse({"mes": "", "ano": ""}), (None, None))

    def test_vazio_com_allow_todos_false_usa_atual(self):
        self.assertEqual(
            self._parse({"mes": "", "ano": ""}, allow_todos=False),
            (self.hoje.month, self.hoje.year),
        )

    def test_invalido_usa_atual(self):
        # "None" literal era o que o link quebrado antigo enviava
        for invalido in ("abc", "None"):
            self.assertEqual(
                self._parse({"mes": invalido, "ano": invalido}),
                (self.hoje.month, self.hoje.year),
            )

    def test_fora_de_faixa_usa_atual(self):
        self.assertEqual(self._parse({"mes": "13", "ano": "1800"}), (self.hoje.month, self.hoje.year))

    def test_inicio_periodo(self):
        self.assertEqual(inicio_periodo(7, 2026), datetime.date(2026, 7, 1))
        self.assertEqual(inicio_periodo(None, 2026), datetime.date(2026, 1, 1))
        self.assertIsNone(inicio_periodo(7, None))
        self.assertIsNone(inicio_periodo(None, None))

    def test_labels_e_slugs(self):
        self.assertEqual(periodo_label(7, 2026), "07/2026")
        self.assertEqual(periodo_label(None, None), "Todos os períodos")
        self.assertEqual(periodo_slug(7, 2026), "07_2026")
        self.assertEqual(periodo_slug(None, 2026), "ano2026")
        self.assertEqual(periodo_slug(None, None), "todos")


class FluxoSaldoAnteriorTests(TestCase):
    """O saldo por linha e os KPIs devem considerar o histórico anterior ao período."""

    def setUp(self):
        self.user = create_user(username="rel_saldo_ant", password="12345678")
        self.client.login(username="rel_saldo_ant", password="12345678")

        self.today = timezone.localdate()
        self.mes_passado = _mes_anterior(self.today)

        self.tm = create_tipo_madeira(nome="MADEIRA SA", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        self.c = create_cliente(nome="Cliente Saldo Anterior")
        # Mês passado: venda 100 e pagamento 40 => saldo anterior = -60
        r_old = create_romaneio(numero_romaneio="sa-old", cliente=self.c, data_romaneio=self.mes_passado)
        create_item_romaneio(romaneio=r_old, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("10.000"))
        create_pagamento(cliente=self.c, data_pagamento=self.mes_passado, valor=Decimal("40.00"))

        # Mês atual: venda 10 => saldo final = -70
        r_new = create_romaneio(numero_romaneio="sa-new", cliente=self.c, data_romaneio=self.today)
        create_item_romaneio(romaneio=r_new, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))

    def test_mes_filtrado_com_cliente_mostra_saldo_anterior_e_final(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro"),
            {"mes": self.today.month, "ano": self.today.year, "cliente_id": self.c.id},
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.context["saldo_anterior"], Decimal("-60.00"))
        self.assertEqual(resp.context["saldo_final"], Decimal("-70.00"))

        movs = list(resp.context["movimentacoes"])
        self.assertEqual([m.numero_romaneio for m in movs], ["sa-new"])
        # saldo da linha parte do saldo anterior (-60) e não de zero
        self.assertEqual(movs[-1].saldo_atual, Decimal("-70.00"))

    def test_mes_filtrado_sem_cliente_ainda_seeda_saldo_por_linha(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro"),
            {"mes": self.today.month, "ano": self.today.year},
        )
        self.assertEqual(resp.status_code, 200)

        # KPIs por cliente só aparecem com cliente selecionado
        self.assertIsNone(resp.context["saldo_anterior"])
        self.assertIsNone(resp.context["saldo_final"])

        movs = [m for m in resp.context["movimentacoes"] if m.cliente_id == self.c.id]
        self.assertEqual(movs[-1].saldo_atual, Decimal("-70.00"))

    def test_todos_os_periodos_bate_com_saldo_atual_do_cliente(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro"),
            {"mes": "", "ano": "", "cliente_id": self.c.id},
        )
        self.assertEqual(resp.status_code, 200)

        movs = list(resp.context["movimentacoes"])
        self.assertEqual(len(movs), 3)  # 2 vendas + 1 pagamento
        self.assertEqual(movs[-1].saldo_atual, self.c.saldo_atual)
        self.assertEqual(movs[-1].saldo_atual, Decimal("-70.00"))

    def test_filtro_parcial_nao_seeda_e_marca_saldo_parcial(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro"),
            {
                "mes": self.today.month,
                "ano": self.today.year,
                "cliente_id": self.c.id,
                "numero_romaneio": "sa-new",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["saldo_parcial"])
        self.assertIsNone(resp.context["saldo_anterior"])
        movs = list(resp.context["movimentacoes"])
        # lista parcial: saldo corrido reinicia em zero (comportamento anterior)
        self.assertEqual(movs[-1].saldo_atual, Decimal("-10.00"))


class ExportRespeitaFiltroTodosTests(TestCase):
    """Exportações devem honrar exatamente o filtro da tela, inclusive 'Todos' (mes=""/ano="")."""

    def setUp(self):
        self.user = create_user(username="rel_todos", password="12345678")
        self.client.login(username="rel_todos", password="12345678")

        self.today = timezone.localdate()
        self.ano_passado = self.today.replace(year=self.today.year - 1)

        self.tm = create_tipo_madeira(nome="MADEIRA T", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))
        self.c = create_cliente(nome="Cliente Todos")

        r_old = create_romaneio(numero_romaneio="td-old", cliente=self.c, data_romaneio=self.ano_passado)
        create_item_romaneio(romaneio=r_old, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("1.000"))

        r_new = create_romaneio(numero_romaneio="td-new", cliente=self.c, data_romaneio=self.today)
        create_item_romaneio(romaneio=r_new, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

    def _load_workbook(self, resp):
        from openpyxl import load_workbook
        return load_workbook(BytesIO(resp.content))

    def test_fluxo_export_excel_todos_inclui_todo_o_historico(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro_export_excel"),
            {"mes": "", "ano": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("todos", resp["Content-Disposition"])

        wb = self._load_workbook(resp)
        numeros = {row[1] for row in wb["Movimentações"].iter_rows(min_row=2, values_only=True)}
        self.assertIn("td-old", numeros)
        self.assertIn("td-new", numeros)

    def test_fluxo_export_excel_mes_atual_exclui_historico_antigo(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro_export_excel"),
            {"mes": self.today.month, "ano": self.today.year},
        )
        self.assertEqual(resp.status_code, 200)
        wb = self._load_workbook(resp)
        numeros = {row[1] for row in wb["Movimentações"].iter_rows(min_row=2, values_only=True)}
        self.assertNotIn("td-old", numeros)
        self.assertIn("td-new", numeros)

    def test_fluxo_export_excel_mes_atual_com_cliente_tem_saldo_anterior(self):
        resp = self.client.get(
            reverse("relatorios:fluxo_financeiro_export_excel"),
            {"mes": self.today.month, "ano": self.today.year, "cliente_id": self.c.id},
        )
        self.assertEqual(resp.status_code, 200)
        wb = self._load_workbook(resp)

        rotulos_resumo = {row[0] for row in wb["Resumo"].iter_rows(min_row=4, values_only=True)}
        self.assertIn("Saldo anterior (R$)", rotulos_resumo)
        self.assertIn("Saldo final (R$)", rotulos_resumo)

        primeira_linha = next(wb["Movimentações"].iter_rows(min_row=2, values_only=True))
        self.assertEqual(primeira_linha[2], "SALDO ANTERIOR")
        self.assertEqual(Decimal(str(primeira_linha[6])), Decimal("-10"))  # venda 10 no ano passado

    def test_ficha_romaneios_export_excel_todos(self):
        resp = self.client.get(
            reverse("relatorios:ficha_romaneios_export_excel"),
            {"mes": "", "ano": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("todos", resp["Content-Disposition"])

        wb = self._load_workbook(resp)
        ws = wb.active
        numeros = {row[1] for row in ws.iter_rows(min_row=5, values_only=True)}
        self.assertIn("td-old", numeros)
        self.assertIn("td-new", numeros)

    def test_ficha_romaneios_export_csv_todos(self):
        resp = self.client.get(
            reverse("relatorios:ficha_romaneios_export"),
            {"mes": "", "ano": ""},
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertIn("td-old", content)
        self.assertIn("td-new", content)

    def test_ficha_madeiras_export_excel_todos(self):
        resp = self.client.get(
            reverse("relatorios:ficha_madeiras_export_excel"),
            {"mes": "", "ano": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("todos", resp["Content-Disposition"])

        wb = self._load_workbook(resp)
        ws = wb.active
        numeros = {row[1] for row in ws.iter_rows(min_row=5, values_only=True)}
        self.assertIn("td-old", numeros)
        self.assertIn("td-new", numeros)

    def test_telas_nao_geram_links_com_mes_none(self):
        # Regressão do bug original: link de export renderizava ?mes=None&ano=None
        for url_name in ("fluxo_financeiro", "ficha_romaneios", "ficha_madeiras"):
            resp = self.client.get(reverse(f"relatorios:{url_name}"), {"mes": "", "ano": ""})
            self.assertEqual(resp.status_code, 200, url_name)
            self.assertNotContains(resp, "mes=None", msg_prefix=url_name)
            self.assertNotContains(resp, "ano=None", msg_prefix=url_name)

    def test_telas_com_todos_mostram_todo_o_historico(self):
        resp = self.client.get(reverse("relatorios:ficha_romaneios"), {"mes": "", "ano": ""})
        numeros = {r.numero_romaneio for r in resp.context["romaneios"]}
        self.assertEqual(numeros, {"td-old", "td-new"})

        resp = self.client.get(reverse("relatorios:ficha_madeiras"), {"mes": "", "ano": ""})
        self.assertEqual(len(list(resp.context["rows"])), 2)

    def test_primeira_visita_continua_no_mes_atual(self):
        for url_name in ("fluxo_financeiro", "ficha_romaneios", "ficha_madeiras", "dashboard"):
            resp = self.client.get(reverse(f"relatorios:{url_name}"))
            self.assertEqual(resp.status_code, 200, url_name)
            self.assertEqual(resp.context["mes"], self.today.month, url_name)
            self.assertEqual(resp.context["ano"], self.today.year, url_name)


class SaldoClientesExportTests(TestCase):
    def setUp(self):
        self.user = create_user(username="rel_saldo_exp", password="12345678")
        self.client.login(username="rel_saldo_exp", password="12345678")

        self.tm = create_tipo_madeira(nome="MADEIRA SC", preco_normal=Decimal("10.00"), preco_com_frete=Decimal("20.00"))

        # devedor: -20
        self.c_neg = create_cliente(nome="Devedor Export", telefone="911")
        rom = create_romaneio(numero_romaneio="sc-1", cliente=self.c_neg)
        create_item_romaneio(romaneio=rom, tipo_madeira=self.tm, valor_unitario=Decimal("10.00"), quantidade_m3_total=Decimal("2.000"))

        # crédito: +30
        self.c_pos = create_cliente(nome="Credor Export", telefone="922")
        create_pagamento(cliente=self.c_pos, valor=Decimal("30.00"))

    def test_export_excel_respeita_tipo_saldo(self):
        from openpyxl import load_workbook

        resp = self.client.get(
            reverse("relatorios:saldo_clientes_export_excel"),
            {"tipo_saldo": "negativos"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content[:2] == b"PK")
        self.assertIn("negativos", resp["Content-Disposition"])

        ws = load_workbook(BytesIO(resp.content)).active
        conteudo = [v for row in ws.iter_rows(values_only=True) for v in row if v is not None]
        self.assertIn("Devedor Export", conteudo)
        self.assertNotIn("Credor Export", conteudo)

    def test_export_excel_respeita_busca(self):
        from openpyxl import load_workbook

        resp = self.client.get(
            reverse("relatorios:saldo_clientes_export_excel"),
            {"q": "922"},
        )
        self.assertEqual(resp.status_code, 200)
        ws = load_workbook(BytesIO(resp.content)).active
        conteudo = [v for row in ws.iter_rows(values_only=True) for v in row if v is not None]
        self.assertIn("Credor Export", conteudo)
        self.assertNotIn("Devedor Export", conteudo)

    def test_export_pdf_responde(self):
        resp = self.client.get(reverse("relatorios:saldo_clientes_export_pdf"))
        # 200 com WeasyPrint disponível; 500 gracioso sem as libs nativas
        self.assertIn(resp.status_code, (200, 500))
        if resp.status_code == 200:
            self.assertEqual(resp["Content-Type"], "application/pdf")

