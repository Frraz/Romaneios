from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.cadastros.models import Cliente, Motorista, TipoMadeira
from apps.financeiro.models import Pagamento
from apps.romaneio.models import ItemRomaneio, Romaneio, UnidadeRomaneio


def create_user(**kwargs):
    User = get_user_model()
    username = kwargs.pop("username", "testuser")
    password = kwargs.pop("password", "123456")
    user = User.objects.create_user(username=username, password=password, **kwargs)
    return user


def create_cliente(**kwargs) -> Cliente:
    defaults = {
        "nome": "Cliente Teste",
        "cpf_cnpj": None,
        "telefone": None,
        "endereco": None,
        "ativo": True,
    }
    defaults.update(kwargs)
    return Cliente.objects.create(**defaults)


def create_tipo_madeira(**kwargs) -> TipoMadeira:
    defaults = {
        "nome": "ANGICO",
        "preco_normal": Decimal("100.00"),
        "preco_com_frete": Decimal("120.00"),
        "ativo": True,
    }
    defaults.update(kwargs)
    return TipoMadeira.objects.create(**defaults)


def create_motorista(**kwargs) -> Motorista:
    defaults = {
        "nome": "Motorista Teste",
        "cpf": None,
        "telefone": None,
        "placa_veiculo": None,
        "ativo": True,
    }
    defaults.update(kwargs)
    return Motorista.objects.create(**defaults)


def create_romaneio(**kwargs) -> Romaneio:
    cliente = kwargs.pop("cliente", None) or create_cliente(nome="Cliente Romaneio")
    defaults = {
        "numero_romaneio": "1001",
        "data_romaneio": timezone.localdate(),
        "cliente": cliente,
        "motorista": None,
        "tipo_romaneio": "NORMAL",
        "modalidade": "SIMPLES",
        "usuario_cadastro": None,
    }
    defaults.update(kwargs)
    return Romaneio.objects.create(**defaults)


def create_item_romaneio(**kwargs) -> ItemRomaneio:
    romaneio = kwargs.pop("romaneio", None) or create_romaneio(numero_romaneio="1002")
    tipo_madeira = kwargs.pop("tipo_madeira", None) or create_tipo_madeira(nome="ANGICO ITEM")
    defaults = {
        "romaneio": romaneio,
        "tipo_madeira": tipo_madeira,
        "valor_unitario": tipo_madeira.get_preco(romaneio.tipo_romaneio),
        "quantidade_m3_total": Decimal("1.000"),
    }
    defaults.update(kwargs)
    item = ItemRomaneio.objects.create(**defaults)
    return item


def create_unidade_romaneio(**kwargs) -> UnidadeRomaneio:
    item = kwargs.pop("item", None) or create_item_romaneio()
    defaults = {
        "item": item,
        "comprimento": Decimal("4.00"),
        "rodo": Decimal("30.00"),
        "desconto_1": Decimal("0.00"),
        "desconto_2": Decimal("0.00"),
        "quantidade_m3": Decimal("0.500"),
    }
    defaults.update(kwargs)
    unidade = UnidadeRomaneio.objects.create(**defaults)
    return unidade


def create_pagamento(**kwargs) -> Pagamento:
    cliente = kwargs.pop("cliente", None) or create_cliente(nome="Cliente Pagamento")
    defaults = {
        "data_pagamento": timezone.localdate(),
        "cliente": cliente,
        "valor": Decimal("100.00"),
        "tipo_pagamento": "DINHEIRO",
        "descricao": None,
        "usuario_cadastro": None,
    }
    defaults.update(kwargs)
    return Pagamento.objects.create(**defaults)