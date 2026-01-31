from django import forms
from .models import Cliente, TipoMadeira, Motorista
from decimal import Decimal

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf_cnpj', 'telefone', 'endereco', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do cliente'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome


class TipoMadeiraForm(forms.ModelForm):
    class Meta:
        model = TipoMadeira
        fields = ['nome', 'preco_normal', 'preco_com_frete', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CASCA SECA, ANGICO, MIXTA'
            }),
            'preco_normal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '460.00',
                'step': '0.01'
            }),
            'preco_com_frete': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '330.00',
                'step': '0.01'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome

    def clean(self):
        cleaned_data = super().clean()
        preco_normal = cleaned_data.get('preco_normal')
        preco_com_frete = cleaned_data.get('preco_com_frete')

        if preco_normal and preco_com_frete:
            if preco_com_frete >= preco_normal:
                raise forms.ValidationError(
                    "O preço COM FRETE deve ser menor que o preço NORMAL."
                )
        return cleaned_data


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = ['nome', 'cpf', 'telefone', 'placa_veiculo', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do motorista'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'placa_veiculo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ABC-1234'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome

    # (Se quiser validar CPF ou placa futuramente, adicione os métodos aqui!)