from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal
from .models import (
    Romaneio, ItemRomaneio,
    RomaneioDetalhado, ItemRomaneioDetalhado
)
from apps.cadastros.models import Cliente, TipoMadeira, Motorista

# ===== ROMANEIO SIMPLES =====
class RomaneioForm(forms.ModelForm):
    class Meta:
        model = Romaneio
        fields = ['numero_romaneio', 'data_romaneio', 'cliente', 'tipo_romaneio', 'motorista']
        widgets = {
            'numero_romaneio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 11613'}),
            'data_romaneio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo_romaneio': forms.Select(attrs={'class': 'form-control'}),
            'motorista': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        self.fields['motorista'].queryset = Motorista.objects.filter(ativo=True)

class ItemRomaneioForm(forms.ModelForm):
    class Meta:
        model = ItemRomaneio
        fields = ['tipo_madeira', 'quantidade_m3', 'valor_unitario']
        widgets = {
            'tipo_madeira': forms.Select(attrs={
                'class': 'form-control select2 tipo-madeira-select',
                'onchange': 'atualizarPreco(this)'
            }),
            'quantidade_m3': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.001',
                'min': '0.001', 'placeholder': '0.000',
                'onchange': 'calcularTotal(this)'
            }),
            'valor_unitario': forms.NumberInput(attrs={
                'class': 'form-control valor-unitario',
                'step': '0.01', 'min': '0.01',
                'placeholder': '0.00', 'readonly': 'readonly'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_madeira'].queryset = TipoMadeira.objects.filter(ativo=True)

    def clean_quantidade_m3(self):
        qtd = self.cleaned_data.get('quantidade_m3')
        if qtd is None or qtd <= Decimal('0.000'):
            raise forms.ValidationError('A quantidade deve ser maior que zero!')
        return qtd

    def clean_valor_unitario(self):
        valor = self.cleaned_data.get('valor_unitario')
        if valor is None or valor <= Decimal('0.00'):
            raise forms.ValidationError('O valor unitário deve ser maior que zero!')
        return valor

ItemRomaneioFormSet = inlineformset_factory(
    Romaneio,
    ItemRomaneio,
    form=ItemRomaneioForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True
)

# ===== ROMANEIO DETALHADO =====
class RomaneioDetalhadoForm(forms.ModelForm):
    class Meta:
        model = RomaneioDetalhado
        # Inclua 'tipo_romaneio' SE existir no seu modelo detalhado:
        fields = [
            'numero_romaneio',
            'data_romaneio',
            'cliente',
            'motorista',
            'tipo_romaneio',  # Só se existir!
            'desconto',
        ]
        widgets = {
            'numero_romaneio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: D11613'}),
            'data_romaneio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'motorista': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo_romaneio': forms.Select(attrs={'class': 'form-control'}),  # Só se existir!
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        self.fields['motorista'].queryset = Motorista.objects.filter(ativo=True)
        # Se 'tipo_romaneio' não existe, remova dos fields/widgets acima!

class ItemRomaneioDetalhadoForm(forms.ModelForm):
    class Meta:
        model = ItemRomaneioDetalhado
        fields = [
            'tipo_madeira', 'comprimento', 'rodo',
            'quantidade_m3', 'valor_unitario'
        ]
        widgets = {
            'tipo_madeira': forms.Select(attrs={
                'class': 'form-control select2 tipo-madeira-select', 'onchange': 'atualizarPreco(this)'
            }),
            'comprimento': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01',
                'min': '0.01', 'placeholder': 'Ex: 3.00'
            }),
            'rodo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rôdo'}),
            'quantidade_m3': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.001',
                'min': '0.001', 'placeholder': '0.000', 'onchange': 'calcularTotal(this)'
            }),
            'valor_unitario': forms.NumberInput(attrs={
                'class': 'form-control valor-unitario', 'step': '0.01',
                'min': '0.01', 'placeholder': '0.00', 'readonly': 'readonly'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_madeira'].queryset = TipoMadeira.objects.filter(ativo=True)

    def clean_quantidade_m3(self):
        qtd = self.cleaned_data.get('quantidade_m3')
        if qtd is None or qtd <= Decimal('0.000'):
            raise forms.ValidationError('A quantidade deve ser maior que zero!')
        return qtd

    def clean_valor_unitario(self):
        valor = self.cleaned_data.get('valor_unitario')
        if valor is None or valor <= Decimal('0.00'):
            raise forms.ValidationError('O valor unitário deve ser maior que zero!')
        return valor

ItemRomaneioDetalhadoFormSet = inlineformset_factory(
    RomaneioDetalhado,
    ItemRomaneioDetalhado,
    form=ItemRomaneioDetalhadoForm,
    extra=2,
    can_delete=True,
    min_num=1,
    validate_min=True
)