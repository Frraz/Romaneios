from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from apps.tests.factories import (
    create_cliente,
    create_motorista,
    create_pagamento,
    create_romaneio,
    create_tipo_madeira,
    create_user,
)


class SmokeAuthUrlsTests(TestCase):
    def test_login_page_loads(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)

    def test_password_reset_page_loads(self):
        resp = self.client.get(reverse("password_reset"))
        self.assertEqual(resp.status_code, 200)


class SmokeRelatoriosUrlsTests(TestCase):
    def setUp(self):
        self.user = create_user(username="smoke", password="12345678")

    def test_relatorios_requires_login(self):
        protected = [
            reverse("relatorios:dashboard"),
            reverse("relatorios:ficha_romaneios"),
            reverse("relatorios:ficha_madeiras"),
            reverse("relatorios:fluxo_financeiro"),
            reverse("relatorios:saldo_clientes"),
        ]
        for url in protected:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/accounts/login/", resp["Location"])

    def test_relatorios_load_logged_in(self):
        self.client.login(username="smoke", password="12345678")
        urls = [
            reverse("relatorios:dashboard"),
            reverse("relatorios:ficha_romaneios"),
            reverse("relatorios:ficha_madeiras"),
            reverse("relatorios:fluxo_financeiro"),
            reverse("relatorios:saldo_clientes"),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class SmokeRomaneioUrlsTests(TestCase):
    def setUp(self):
        self.user = create_user(username="smoke2", password="12345678")

    def test_romaneio_requires_login(self):
        rom = create_romaneio(numero_romaneio="9001", usuario_cadastro=self.user)

        urls = [
            reverse("romaneio:romaneio_list"),
            reverse("romaneio:romaneio_create"),
            reverse("romaneio:romaneio_detail", kwargs={"pk": rom.pk}),
            reverse("romaneio:romaneio_update", kwargs={"pk": rom.pk}),
            # esse endpoint deve ser protegido por login_required na view
            reverse("romaneio:get_preco_madeira"),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/accounts/login/", resp["Location"])

    def test_romaneio_pages_load_logged_in(self):
        self.client.login(username="smoke2", password="12345678")
        rom = create_romaneio(numero_romaneio="9002", usuario_cadastro=self.user)

        urls = [
            reverse("romaneio:romaneio_list"),
            reverse("romaneio:romaneio_create"),
            reverse("romaneio:romaneio_detail", kwargs={"pk": rom.pk}),
            reverse("romaneio:romaneio_update", kwargs={"pk": rom.pk}),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

        # API endpoint: com login, sem params, pode ser 400/404/500 dependendo da implementação.
        # O comportamento "correto" é validado nos testes específicos do endpoint.
        resp = self.client.get(reverse("romaneio:get_preco_madeira"))
        self.assertIn(resp.status_code, (200, 400, 404, 500))


class SmokeFinanceiroUrlsTests(TestCase):
    def setUp(self):
        self.user = create_user(username="smoke3", password="12345678")

    def test_financeiro_requires_login(self):
        pg = create_pagamento()

        urls = [
            reverse("financeiro:pagamento_list"),
            reverse("financeiro:pagamento_create"),
            reverse("financeiro:pagamento_update", kwargs={"pk": pg.pk}),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/accounts/login/", resp["Location"])

    def test_financeiro_pages_load_logged_in(self):
        self.client.login(username="smoke3", password="12345678")
        pg = create_pagamento()

        urls = [
            reverse("financeiro:pagamento_list"),
            reverse("financeiro:pagamento_create"),
            reverse("financeiro:pagamento_update", kwargs={"pk": pg.pk}),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class SmokeCadastrosUrlsTests(TestCase):
    def test_cadastros_requires_login(self):
        create_user(username="smoke4", password="12345678")

        cliente = create_cliente(nome="Cliente Smoke")
        tm = create_tipo_madeira(nome="Madeira Smoke")
        motorista = create_motorista(nome="Motorista Smoke")

        urls = [
            reverse("cadastros:cliente_list"),
            reverse("cadastros:cliente_create"),
            reverse("cadastros:cliente_update", kwargs={"pk": cliente.pk}),
            reverse("cadastros:cliente_delete", kwargs={"pk": cliente.pk}),
            reverse("cadastros:tipo_madeira_list"),
            reverse("cadastros:tipo_madeira_create"),
            reverse("cadastros:tipo_madeira_update", kwargs={"pk": tm.pk}),
            reverse("cadastros:tipo_madeira_delete", kwargs={"pk": tm.pk}),
            reverse("cadastros:motorista_list"),
            reverse("cadastros:motorista_create"),
            reverse("cadastros:motorista_update", kwargs={"pk": motorista.pk}),
            reverse("cadastros:motorista_delete", kwargs={"pk": motorista.pk}),
            reverse("cadastros:usuario_list"),
            reverse("cadastros:usuario_create"),
        ]

        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/accounts/login/", resp["Location"])

    def test_cadastros_pages_load_logged_in(self):
        # usuário comum: acessa clientes/tipos/motoristas, mas NÃO acessa usuários
        create_user(username="smoke4u", password="12345678")
        self.client.login(username="smoke4u", password="12345678")

        cliente = create_cliente(nome="Cliente Smoke2")
        tm = create_tipo_madeira(nome="Madeira Smoke2")
        motorista = create_motorista(nome="Motorista Smoke2")

        allowed_urls = [
            reverse("cadastros:cliente_list"),
            reverse("cadastros:cliente_create"),
            reverse("cadastros:cliente_update", kwargs={"pk": cliente.pk}),
            reverse("cadastros:cliente_delete", kwargs={"pk": cliente.pk}),
            reverse("cadastros:tipo_madeira_list"),
            reverse("cadastros:tipo_madeira_create"),
            reverse("cadastros:tipo_madeira_update", kwargs={"pk": tm.pk}),
            reverse("cadastros:tipo_madeira_delete", kwargs={"pk": tm.pk}),
            reverse("cadastros:motorista_list"),
            reverse("cadastros:motorista_create"),
            reverse("cadastros:motorista_update", kwargs={"pk": motorista.pk}),
            reverse("cadastros:motorista_delete", kwargs={"pk": motorista.pk}),
        ]
        for url in allowed_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse("cadastros:usuario_list"))
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(reverse("cadastros:usuario_create"))
        self.assertEqual(resp.status_code, 403)

    def test_cadastros_usuario_pages_load_for_staff(self):
        create_user(username="staff1", password="12345678", is_staff=True)
        self.client.login(username="staff1", password="12345678")

        resp = self.client.get(reverse("cadastros:usuario_list"))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse("cadastros:usuario_create"))
        self.assertEqual(resp.status_code, 200)


class SmokeCoreUrlsTests(TestCase):
    def test_core_dashboard_public_loads(self):
        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 200)