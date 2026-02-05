from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum

from apps.cadastros.models import Cliente, TipoMadeira, Motorista


class Romaneio(models.Model):
    """Romaneio único (Simples/Detalhado)."""

    TIPO_ROMANEIO_CHOICES = [
        ("NORMAL", "Normal"),
        ("COM_FRETE", "Com Frete"),
    ]

    MODALIDADE_CHOICES = [
        ("SIMPLES", "Simples"),
        ("DETALHADO", "Detalhado"),
    ]

    numero_romaneio = models.CharField(max_length=20, unique=True, db_index=True)
    data_romaneio = models.DateField(db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="romaneios")
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="romaneios",
    )

    tipo_romaneio = models.CharField(max_length=15, choices=TIPO_ROMANEIO_CHOICES, default="NORMAL")
    modalidade = models.CharField(max_length=10, choices=MODALIDADE_CHOICES, default="SIMPLES")

    desconto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text="Percentual (0 ~ 100).",
    )

    m3_total = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("0.000"), editable=False)
    valor_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"), editable=False)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"), editable=False)

    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="romaneios_cadastrados",
    )
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_romaneio", "-numero_romaneio"]
        verbose_name = "Romaneio"
        verbose_name_plural = "Romaneios"

    def __str__(self):
        return (
            f"Romaneio {self.numero_romaneio} ({self.get_modalidade_display()})"
            f" - {self.cliente.nome} - {self.data_romaneio:%d/%m/%Y}"
        )

    def atualizar_totais(self):
        """
        Atualiza valor_bruto, valor_total (com desconto) e m3_total com base nos itens.
        """
        totais = self.itens.aggregate(
            total_valor=Sum("valor_total"),
            total_m3=Sum("quantidade_m3"),
        )
        bruto = totais["total_valor"] or Decimal("0.00")
        m3 = totais["total_m3"] or Decimal("0.000")

        desconto = self.desconto or Decimal("0.00")
        fator = Decimal("1") - (desconto / Decimal("100"))
        liquido = (bruto * fator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        self.valor_bruto = bruto
        self.valor_total = liquido
        self.m3_total = m3

        super().save(update_fields=["valor_bruto", "valor_total", "m3_total"])


class ItemRomaneio(models.Model):
    """
    Item único do romaneio.
    Campos detalhados são opcionais no banco e obrigatórios via validação quando modalidade=DETALHADO.
    """

    romaneio = models.ForeignKey(Romaneio, on_delete=models.CASCADE, related_name="itens")
    tipo_madeira = models.ForeignKey(TipoMadeira, on_delete=models.PROTECT, related_name="itens_romaneio")

    comprimento = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Comprimento",
    )
    rodo = models.CharField(max_length=20, blank=True, default="")

    quantidade_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        ordering = ["romaneio", "tipo_madeira", "id"]
        verbose_name = "Item do Romaneio"
        verbose_name_plural = "Itens do Romaneio"

    def __str__(self):
        nome = self.tipo_madeira.nome if self.tipo_madeira else ""
        return f"{nome} - {self.quantidade_m3:.3f} m³"

    def save(self, *args, **kwargs):
        # Preço automático se possível e se valor_unitario estiver vazio/zerado
        if (self.valor_unitario in (None, Decimal("0.00"))) and hasattr(self.tipo_madeira, "get_preco") and self.romaneio_id:
            self.valor_unitario = self.tipo_madeira.get_preco(self.romaneio.tipo_romaneio)

        self.valor_total = (self.quantidade_m3 * self.valor_unitario).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        super().save(*args, **kwargs)

        if self.romaneio_id:
            self.romaneio.atualizar_totais()

    def delete(self, *args, **kwargs):
        rom = self.romaneio
        super().delete(*args, **kwargs)
        if rom:
            rom.atualizar_totais()