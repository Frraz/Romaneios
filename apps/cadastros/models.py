from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Cliente(models.Model):
    """
    Representa um comprador de madeira.
    O saldo é dinâmico — total de pagamentos menos total de vendas.
    Nunca armazene o saldo! Use Cliente.saldo_atual para garantir consistência.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome"
    )
    cpf_cnpj = models.CharField(
        max_length=18,
        blank=False,
        null=False,
        verbose_name="CPF/CNPJ"
        # O validador/no formato é garantido pelo forms.py!
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefone"
    )
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data do cadastro")

    class Meta:
        ordering = ['nome']
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome

    @property
    def saldo_atual(self) -> Decimal:
        """
        Saldo = pagamentos - vendas.
        Dinâmico, atualizado em tempo real. Negativo = cliente devendo.
        """
        from apps.romaneio.models import ItemRomaneio
        from apps.financeiro.models import Pagamento

        total_vendas = ItemRomaneio.objects.filter(
            romaneio__cliente=self
        ).aggregate(
            total=models.Sum('valor_total')
        )['total'] or Decimal('0.00')

        total_pagamentos = Pagamento.objects.filter(
            cliente=self
        ).aggregate(
            total=models.Sum('valor')
        )['total'] or Decimal('0.00')

        return total_pagamentos - total_vendas

    def atualizar_saldo(self) -> Decimal:
        """Método legado só para compatibilidade. Prefira saldo_atual."""
        return self.saldo_atual


class TipoMadeira(models.Model):
    """
    Tipo/categoria da madeira, com preços para cada modalidade de venda.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome"
    )
    preco_normal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço Normal por m³",
        help_text="Preço para romaneio normal"
    )
    preco_com_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço com Frete por m³",
        help_text="Preço para romaneio com frete"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data do cadastro")

    class Meta:
        ordering = ['nome']
        verbose_name = "Tipo de Madeira"
        verbose_name_plural = "Tipos de Madeira"

    def __str__(self):
        return f"{self.nome} - Normal: R$ {self.preco_normal:.2f} | Com Frete: R$ {self.preco_com_frete:.2f}"

    def get_preco(self, tipo_romaneio: str) -> Decimal:
        """Retorna o preço correto conforme o tipo do romaneio."""
        if tipo_romaneio == 'COM_FRETE':
            return self.preco_com_frete
        return self.preco_normal


class Motorista(models.Model):
    """
    Motorista/freteiro responsável pelo transporte.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nome"
    )
    cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        verbose_name="CPF"
        # Se desejar, adicione validação de CPF no forms.py.
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Telefone"
    )
    placa_veiculo = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Placa do veículo"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data do cadastro")

    class Meta:
        ordering = ['nome']
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"

    def __str__(self):
        return f"{self.nome}" + (f" ({self.placa_veiculo})" if self.placa_veiculo else "")