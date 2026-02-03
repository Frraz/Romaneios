from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from apps.cadastros.models import Cliente, TipoMadeira, Motorista

# ===================== ROMANEIO SIMPLES =====================
class Romaneio(models.Model):
    """
    Romaneio de venda de madeira (Simples).
    """
    TIPO_ROMANEIO_CHOICES = [
        ('NORMAL', 'Normal'),
        ('COM_FRETE', 'Com Frete'),
    ]
    numero_romaneio = models.CharField(max_length=20, unique=True, db_index=True)
    data_romaneio = models.DateField(db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='romaneios')
    tipo_romaneio = models.CharField(max_length=15, choices=TIPO_ROMANEIO_CHOICES, default='NORMAL')
    motorista = models.ForeignKey(Motorista, on_delete=models.SET_NULL, null=True, blank=True, related_name='romaneios')
    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='romaneios_cadastrados'
    )
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    m3_total = models.DecimalField(max_digits=10, decimal_places=3, default=0, editable=False)

    class Meta:
        ordering = ['-data_romaneio', '-numero_romaneio']
        verbose_name = "Romaneio"
        verbose_name_plural = "Romaneios"

    def __str__(self):
        return f"Romaneio {self.numero_romaneio} - {self.cliente.nome if self.cliente else 'Sem cliente'} - {self.data_romaneio:%d/%m/%Y}"

    def atualizar_totais(self):
        totais = self.itens.aggregate(
            total_valor=models.Sum('valor_total'),
            total_m3=models.Sum('quantidade_m3')
        )
        self.valor_total = totais['total_valor'] or Decimal('0.00')
        self.m3_total = totais['total_m3'] or Decimal('0.000')
        super().save(update_fields=['valor_total', 'm3_total'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Não recalcula ao criar, pois ainda não tem itens (senão loop infinito).
        # Cálculo acontece ao salvar Itens.

class ItemRomaneio(models.Model):
    """
    Item individual do Romaneio Simples.
    """
    romaneio = models.ForeignKey(Romaneio, on_delete=models.CASCADE, related_name='itens')
    tipo_madeira = models.ForeignKey(TipoMadeira, on_delete=models.PROTECT, related_name='itens_romaneio')
    quantidade_m3 = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        ordering = ['romaneio', 'tipo_madeira']
        verbose_name = "Item do Romaneio"
        verbose_name_plural = "Itens do Romaneio"

    def __str__(self):
        return f"{self.tipo_madeira.nome if self.tipo_madeira else ''} - {self.quantidade_m3:.3f} m³"

    def save(self, *args, **kwargs):
        # Garante que valor_unitario está correto pelo tipo de madeira se não informado.
        if not self.valor_unitario and hasattr(self.tipo_madeira, 'get_preco') and self.romaneio:
            self.valor_unitario = self.tipo_madeira.get_preco(self.romaneio.tipo_romaneio)
        # Cálculo seguro e arredondamento.
        self.valor_total = (self.quantidade_m3 * self.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
        # Atualiza totais do pai.
        if self.romaneio_id:
            self.romaneio.atualizar_totais()

    def delete(self, *args, **kwargs):
        romaneio = self.romaneio
        super().delete(*args, **kwargs)
        if romaneio:
            romaneio.atualizar_totais()

# ===================== ROMANEIO DETALHADO =====================
class RomaneioDetalhado(models.Model):
    """
    Romaneio detalhado de madeira, com desconto e campos auxiliares.
    """
    TIPO_ROMANEIO_CHOICES = [
        ('NORMAL', 'Normal'),
        ('COM_FRETE', 'Com Frete'),
    ]
    numero_romaneio = models.CharField(max_length=20, unique=True, db_index=True)
    data_romaneio = models.DateField(db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='romaneios_detalhados')
    tipo_romaneio = models.CharField(max_length=15, choices=TIPO_ROMANEIO_CHOICES, default='NORMAL')
    motorista = models.ForeignKey(Motorista, on_delete=models.SET_NULL, null=True, blank=True, related_name='romaneios_detalhados')
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentual de desconto (0 ~ 100)")
    m3_total = models.DecimalField(max_digits=10, decimal_places=3, default=0, editable=False)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    valor_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=0, editable=False)
    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='romaneios_detalhados_cadastrados'
    )
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_romaneio', '-numero_romaneio']
        verbose_name = "Romaneio Detalhado"
        verbose_name_plural = "Romaneios Detalhados"

    def __str__(self):
        tipo = dict(self.TIPO_ROMANEIO_CHOICES).get(self.tipo_romaneio, self.tipo_romaneio)
        return f"Romaneio Det. {self.numero_romaneio} [{tipo}] - {self.cliente.nome if self.cliente else ''} - {self.data_romaneio:%d/%m/%Y}"

    def atualizar_totais(self):
        totais = self.itens.aggregate(
            total_valor=models.Sum('valor_total'),
            total_m3=models.Sum('quantidade_m3')
        )
        bruto = totais['total_valor'] or Decimal('0.00')
        self.valor_bruto = bruto
        desconto = self.desconto or Decimal('0')
        self.valor_total = (bruto * (Decimal('1.0') - (desconto / Decimal('100.0')))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.m3_total = totais['total_m3'] or Decimal('0.000')
        super().save(update_fields=['valor_bruto', 'valor_total', 'm3_total'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Não recalcula ao criar: o cascade ItensRomaneioDetalhado fará.

class ItemRomaneioDetalhado(models.Model):
    """
    Item individual do Romaneio Detalhado.
    """
    romaneio = models.ForeignKey(RomaneioDetalhado, on_delete=models.CASCADE, related_name='itens')
    tipo_madeira = models.ForeignKey(TipoMadeira, on_delete=models.PROTECT, related_name='itens_romaneio_detalhado')
    comprimento = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Comprimento")
    rodo = models.CharField(max_length=20, blank=True)
    quantidade_m3 = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        ordering = ['romaneio', 'tipo_madeira']
        verbose_name = "Item do Romaneio Detalhado"
        verbose_name_plural = "Itens do Romaneio Detalhado"

    def __str__(self):
        return f"{self.tipo_madeira.nome if self.tipo_madeira else ''} | {self.comprimento} m | Rôdo: {self.rodo or '-'} | m³: {self.quantidade_m3:.3f}"

    def save(self, *args, **kwargs):
        # Cálculo sempre seguro:
        self.valor_total = (self.quantidade_m3 * self.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
        if self.romaneio_id:
            self.romaneio.atualizar_totais()

    def delete(self, *args, **kwargs):
        romaneio = self.romaneio
        super().delete(*args, **kwargs)
        if romaneio:
            romaneio.atualizar_totais()