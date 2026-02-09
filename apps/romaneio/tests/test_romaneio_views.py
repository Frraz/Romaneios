from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.romaneio.forms import ItemRomaneioFormSet
from apps.romaneio.models import Romaneio
from apps.tests.factories import create_cliente, create_tipo_madeira, create_user


class GetPrecoMadeiraEndpointTests(TestCase):
    def setUp(self):
        self.user = create_user(username="user_preco", password="12345678")
        self.client.login(username="user_preco", password="12345678")

    def test_get_preco_madeira_returns_price_normal(self):
        tm = create_tipo_madeira(
            nome="ANGICO PRECO",
            preco_normal=Decimal("10.00"),
            preco_com_frete=Decimal("20.00"),
        )

        url = reverse("romaneio:get_preco_madeira")
        resp = self.client.get(url, {"tipo_madeira_id": tm.id, "tipo_romaneio": "NORMAL"})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["preco"], 10.0)

    def test_get_preco_madeira_returns_price_com_frete(self):
        tm = create_tipo_madeira(
            nome="IPÊ PRECO",
            preco_normal=Decimal("10.00"),
            preco_com_frete=Decimal("99.00"),
        )

        url = reverse("romaneio:get_preco_madeira")
        resp = self.client.get(url, {"tipo_madeira_id": tm.id, "tipo_romaneio": "COM_FRETE"})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["preco"], 99.0)

    def test_get_preco_madeira_404_when_not_found(self):
        url = reverse("romaneio:get_preco_madeira")
        resp = self.client.get(url, {"tipo_madeira_id": 999999, "tipo_romaneio": "NORMAL"})
        self.assertEqual(resp.status_code, 404)

        data = resp.json()
        self.assertEqual(data["success"], False)
        self.assertIn("Tipo de madeira não encontrado", data["error"])


class RomaneioCreateUpdateViewTests(TestCase):
    """
    Nota importante:
    A RomaneioCreateView/RomaneioUpdateView valida um UnidadeRomaneioFormSet por item
    com prefixo estável 'unidades-{index}', mesmo no modo SIMPLES.
    Por isso, os POSTs precisam sempre incluir o ManagementForm de unidades.
    """

    def setUp(self):
        self.user = create_user(username="romv", password="12345678")
        self.client.login(username="romv", password="12345678")

        self.today = timezone.localdate()
        self.cliente = create_cliente(nome="Cliente Views")
        self.tm = create_tipo_madeira(
            nome="MADEIRA VIEWS",
            preco_normal=Decimal("10.00"),
            preco_com_frete=Decimal("20.00"),
        )

    @staticmethod
    def _unidades_mgmt(prefix: str, total_forms: int = 0) -> dict[str, str]:
        """
        Retorna campos ManagementForm para o formset de unidades.
        prefix: ex 'unidades-0'
        """
        return {
            f"{prefix}-TOTAL_FORMS": str(total_forms),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }

    @staticmethod
    def _item_prefix() -> str:
        return ItemRomaneioFormSet().prefix

    def _post_create_simples_payload(self) -> dict[str, str]:
        p = self._item_prefix()

        payload: dict[str, str] = {
            # RomaneioForm
            "numero_romaneio": "8001",
            "data_romaneio": self.today.isoformat(),
            "cliente": str(self.cliente.id),
            "motorista": "",
            "tipo_romaneio": "NORMAL",
            "modalidade": "SIMPLES",
            # ItemRomaneioFormSet (1 form)
            f"{p}-TOTAL_FORMS": "1",
            f"{p}-INITIAL_FORMS": "0",
            f"{p}-MIN_NUM_FORMS": "1",
            f"{p}-MAX_NUM_FORMS": "1000",
            f"{p}-0-tipo_madeira": str(self.tm.id),
            f"{p}-0-quantidade_m3_total": "2.000",
            f"{p}-0-valor_unitario": "10.00",
        }
        payload.update(self._unidades_mgmt("unidades-0", total_forms=0))
        return payload

    def test_create_romaneio_simples_success(self):
        resp = self.client.post(reverse("romaneio:romaneio_create"), data=self._post_create_simples_payload())
        self.assertEqual(resp.status_code, 302)

        rom = Romaneio.objects.get(numero_romaneio="8001")
        self.assertEqual(rom.modalidade, "SIMPLES")
        self.assertEqual(rom.usuario_cadastro_id, self.user.id)

        self.assertEqual(rom.m3_total, Decimal("2.000"))
        self.assertEqual(rom.valor_total, Decimal("20.00"))

    def _post_create_detalhado_payload(self, *, with_units: bool) -> dict[str, str]:
        p = self._item_prefix()

        payload: dict[str, str] = {
            # RomaneioForm
            "numero_romaneio": "8002",
            "data_romaneio": self.today.isoformat(),
            "cliente": str(self.cliente.id),
            "motorista": "",
            "tipo_romaneio": "NORMAL",
            "modalidade": "DETALHADO",
            # Item formset (1 form)
            f"{p}-TOTAL_FORMS": "1",
            f"{p}-INITIAL_FORMS": "0",
            f"{p}-MIN_NUM_FORMS": "1",
            f"{p}-MAX_NUM_FORMS": "1000",
            f"{p}-0-tipo_madeira": str(self.tm.id),
            # no DETALHADO o backend recalcula por unidades, mas usamos um mínimo > 0 para evitar validações/edge cases
            f"{p}-0-quantidade_m3_total": "0.001",
            f"{p}-0-valor_unitario": "10.00",
        }

        u0 = "unidades-0"
        if not with_units:
            payload.update(self._unidades_mgmt(u0, total_forms=0))
            return payload

        payload.update(self._unidades_mgmt(u0, total_forms=1))
        payload.update(
            {
                f"{u0}-0-comprimento": "4.00",
                f"{u0}-0-rodo": "30.00",
                f"{u0}-0-desconto_1": "0.00",
                f"{u0}-0-desconto_2": "0.00",
                f"{u0}-0-quantidade_m3": "0.500",
            }
        )
        return payload

    def test_create_romaneio_detalhado_requires_units_per_item(self):
        resp = self.client.post(
            reverse("romaneio:romaneio_create"),
            data=self._post_create_detalhado_payload(with_units=False),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Romaneio.objects.filter(numero_romaneio="8002").exists())

    def test_create_romaneio_detalhado_success_with_units(self):
        resp = self.client.post(
            reverse("romaneio:romaneio_create"),
            data=self._post_create_detalhado_payload(with_units=True),
        )
        self.assertEqual(resp.status_code, 302)

        rom = Romaneio.objects.get(numero_romaneio="8002")
        rom.refresh_from_db()

        self.assertEqual(rom.m3_total, Decimal("0.500"))
        self.assertEqual(rom.valor_total, Decimal("5.00"))

    def test_update_romaneio_simples_changes_totals(self):
        # cria primeiro
        self.client.post(reverse("romaneio:romaneio_create"), data=self._post_create_simples_payload())
        rom = Romaneio.objects.get(numero_romaneio="8001")
        item = rom.itens.first()
        self.assertIsNotNone(item)

        p = self._item_prefix()
        payload: dict[str, str] = {
            "numero_romaneio": "8001",
            "data_romaneio": self.today.isoformat(),
            "cliente": str(self.cliente.id),
            "motorista": "",
            "tipo_romaneio": "NORMAL",
            "modalidade": "SIMPLES",
            f"{p}-TOTAL_FORMS": "1",
            f"{p}-INITIAL_FORMS": "1",
            f"{p}-MIN_NUM_FORMS": "1",
            f"{p}-MAX_NUM_FORMS": "1000",
            f"{p}-0-id": str(item.id),
            f"{p}-0-tipo_madeira": str(self.tm.id),
            f"{p}-0-quantidade_m3_total": "3.000",
            f"{p}-0-valor_unitario": "10.00",
        }
        payload.update(self._unidades_mgmt("unidades-0", total_forms=0))

        resp = self.client.post(reverse("romaneio:romaneio_update", kwargs={"pk": rom.pk}), data=payload)
        self.assertEqual(resp.status_code, 302)

        rom.refresh_from_db()
        self.assertEqual(rom.m3_total, Decimal("3.000"))
        self.assertEqual(rom.valor_total, Decimal("30.00"))