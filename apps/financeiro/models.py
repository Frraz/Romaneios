from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from apps.cadastros.models import Cliente

class Pagamento(models.Model):
    """
    Pagamento/adiantamento realizado pelo cliente para abatimento do saldo.
    Saldo do cliente é sempre dinâmico, nunca persistido.
    """
    TIPO_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('TRANSFERENCIA', 'Transferência'),
        ('CHEQUE', 'Cheque'),
        ('DEPOSITO', 'Depósito'),
        ('OUTROS', 'Outros'),
    ]

    data_pagamento = models.DateField(db_index=True, verbose_name="Data do Pagamento")
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT,
        related_name='pagamentos',
        verbose_name="Cliente"
    )
    valor = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valor"
    )
    tipo_pagamento = models.CharField(
        max_length=20,
        choices=TIPO_PAGAMENTO_CHOICES,
        default='DINHEIRO',
        verbose_name="Tipo de Pagamento"
    )
    descricao = models.TextField(
        blank=True, null=True,
        help_text="Ex: PIX C/C TROPICAL AGRO, PAGAMENTO EM ESPÉCIE",
        verbose_name="Descrição"
    )

    usuario_cadastro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pagamentos_cadastrados',
        verbose_name="Usuário do Cadastro"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data do Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        ordering = ['-data_pagamento', '-id']
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        indexes = [
            models.Index(fields=['data_pagamento', 'cliente']),
        ]

    def __str__(self):
        return f"{self.cliente.nome} - R$ {self.valor:.2f} ({self.tipo_pagamento}) em {self.data_pagamento:%d/%m/%Y}"

    def clean(self):
        if self.valor <= 0:
            raise ValidationError('O valor do pagamento deve ser positivo.')
        # Corrigido: comparar data do pagamento com a data de hoje
        if self.data_pagamento > timezone.now().date():
            raise ValidationError('A data do pagamento não pode ser no futuro.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)