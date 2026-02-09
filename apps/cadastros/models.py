from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

class Cliente(models.Model):
    """
    Representa um comprador de madeira.
    Saldo dinâmico — total de pagamentos menos total de vendas.
    Use Cliente.saldo_atual para garantir consistência.
    """

    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome",
    )
    cpf_cnpj = models.CharField(
        max_length=18,  # CPF: 000.000.000-00 (14) ou CNPJ: 00.000.000/0000-00 (18)
        blank=True,
        null=True,  # AGORA: CPF/CNPJ é totalmente opcional
        verbose_name="CPF/CNPJ",
        help_text="CPF ou CNPJ do cliente (opcional).",
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefone",
    )
    endereco = models.TextField(
        blank=True,
        null=True,
        verbose_name="Endereço",
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do cadastro",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.nome

    @property
    def saldo_atual(self) -> Decimal:
        """
        Saldo = pagamentos - vendas (valor líquido do romaneio, com desconto aplicado).
        Negativo = cliente devendo.
        """
        from apps.romaneio.models import Romaneio
        from apps.financeiro.models import Pagamento

        total_vendas = (
            Romaneio.objects.filter(cliente=self)
            .aggregate(total=models.Sum("valor_total"))
            .get("total")
            or Decimal("0.00")
        )

        total_pagamentos = (
            Pagamento.objects.filter(cliente=self)
            .aggregate(total=models.Sum("valor"))
            .get("total")
            or Decimal("0.00")
        )

        return total_pagamentos - total_vendas

    def atualizar_saldo(self) -> Decimal:
        """Método legado — prefira saldo_atual."""
        return self.saldo_atual

class TipoMadeira(models.Model):
    """Tipo de madeira, com preços para cada modalidade."""

    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome",
    )
    preco_normal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Preço Normal por m³",
        help_text="Preço para romaneio normal.",
    )
    preco_com_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Preço com Frete por m³",
        help_text="Preço para romaneio com frete.",
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do cadastro",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Tipo de Madeira"
        verbose_name_plural = "Tipos de Madeira"

    def __str__(self) -> str:
        return f"{self.nome} - Normal: R$ {self.preco_normal:.2f} | Com Frete: R$ {self.preco_com_frete:.2f}"

    def get_preco(self, tipo_romaneio: str) -> Decimal:
        if tipo_romaneio == "COM_FRETE":
            return self.preco_com_frete
        return self.preco_normal

class Motorista(models.Model):
    """Motorista/freteiro responsável pelo transporte."""

    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome",
    )
    cpf = models.CharField(
        max_length=14,  # 000.000.000-00
        blank=True,
        null=True,
        verbose_name="CPF",
        help_text="CPF do motorista. Validação pode ser feita no forms.",
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefone",
    )
    placa_veiculo = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Placa do veículo",
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do cadastro",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"

    def __str__(self) -> str:
        if self.placa_veiculo:
            return f"{self.nome} ({self.placa_veiculo})"
        return self.nome