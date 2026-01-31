from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal

from apps.cadastros.models import Cliente, TipoMadeira, Motorista

class Romaneio(models.Model):
    """
    Romaneio de venda de madeira.
    """
    TIPO_ROMANEIO_CHOICES = [
        ('NORMAL', 'Normal'),
        ('COM_FRETE', 'Com Frete'),
    ]

    numero_romaneio = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Ex: 11613, 11627"
    )
    data_romaneio = models.DateField(db_index=True, verbose_name="Data do Romaneio")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='romaneios',
        verbose_name="Cliente"
    )
    tipo_romaneio = models.CharField(
        max_length=15,
        choices=TIPO_ROMANEIO_CHOICES,
        default='NORMAL',
        verbose_name="Tipo do Romaneio"
    )
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='romaneios',
        verbose_name="Motorista"
    )

    # Auditoria
    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='romaneios_cadastrados',
        verbose_name="Usuário do Cadastro"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    # Totais (sincronizados pelos itens)
    valor_total = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=0, editable=False,
        verbose_name="Valor Total"
    )
    m3_total = models.DecimalField(
        max_digits=10, decimal_places=3,
        default=0, editable=False,
        verbose_name="Volume Total (m³)"
    )

    class Meta:
        ordering = ['-data_romaneio', '-numero_romaneio']
        verbose_name = "Romaneio"
        verbose_name_plural = "Romaneios"
        indexes = [
            models.Index(fields=['data_romaneio', 'cliente']),
            models.Index(fields=['numero_romaneio']),
        ]

    def __str__(self):
        nome_cliente = self.cliente.nome if self.cliente else "Sem cliente"
        return f"Romaneio {self.numero_romaneio} - {nome_cliente} - {self.data_romaneio:%d/%m/%Y}"

    def atualizar_totais(self):
        """
        Recalcula os totais (valor e volume) baseado nos itens vinculados.
        """
        totais = self.itens.aggregate(
            total_valor=models.Sum('valor_total'),
            total_m3=models.Sum('quantidade_m3')
        )
        novo_valor_total = totais['total_valor'] or Decimal('0.00')
        novo_m3_total = totais['total_m3'] or Decimal('0.000')
        # Atualiza apenas se mudou, evita loops de save/signals
        if self.valor_total != novo_valor_total or self.m3_total != novo_m3_total:
            Romaneio.objects.filter(pk=self.pk).update(
                valor_total=novo_valor_total,
                m3_total=novo_m3_total
            )
            self.valor_total = novo_valor_total
            self.m3_total = novo_m3_total

    def save(self, *args, **kwargs):
        """
        Ao salvar, atualiza totais se não for a criação inicial.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if not is_new:
            self.atualizar_totais()


class ItemRomaneio(models.Model):
    """
    Item individual de um romaneio - registra tipo de madeira, quantidade e valores.
    """
    romaneio = models.ForeignKey(
        Romaneio,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Romaneio"
    )
    tipo_madeira = models.ForeignKey(
        TipoMadeira,
        on_delete=models.PROTECT,
        related_name='itens_romaneio',
        verbose_name="Tipo de Madeira"
    )
    quantidade_m3 = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade (m³)",
        help_text="Quantidade em metros cúbicos"
    )
    valor_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valor Unitário (R$/m³)",
        help_text="Valor por m³"
    )
    valor_total = models.DecimalField(
        max_digits=15, decimal_places=2,
        editable=False,
        verbose_name="Valor Total"
    )

    class Meta:
        ordering = ['romaneio', 'tipo_madeira']
        verbose_name = "Item do Romaneio"
        verbose_name_plural = "Itens do Romaneio"

    def __str__(self):
        tipo = self.tipo_madeira.nome if self.tipo_madeira else "Item sem madeira"
        return f"{tipo} - {self.quantidade_m3:.3f} m³"

    def save(self, *args, **kwargs):
        """
        Calcula valor_total sempre antes de salvar.
        Se não há valor_unitario, busca preço no TipoMadeira.
        """
        if not self.valor_unitario:
            # Garante que TipoMadeira tem método get_preco
            if hasattr(self.tipo_madeira, 'get_preco'):
                self.valor_unitario = self.tipo_madeira.get_preco(self.romaneio.tipo_romaneio)
            else:
                raise ValueError("TipoMadeira precisa do método get_preco(tipo_romaneio).")
        self.valor_total = self.quantidade_m3 * self.valor_unitario
        super().save(*args, **kwargs)

        # Atualiza totais do romaneio pai
        if self.romaneio_id:
            self.romaneio.atualizar_totais()

    def delete(self, *args, **kwargs):
        """
        Após deletar o item, atualiza totais do romaneio pai.
        """
        romaneio = self.romaneio
        super().delete(*args, **kwargs)
        if romaneio:
            romaneio.atualizar_totais()