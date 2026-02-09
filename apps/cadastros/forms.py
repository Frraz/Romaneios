from django import forms
from .models import Cliente, TipoMadeira, Motorista
from decimal import Decimal
import re

def is_valid_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d1 = (sum1 * 10 % 11) % 10
    d2 = (sum2 * 10 % 11) % 10
    return d1 == int(cpf[-2]) and d2 == int(cpf[-1])

def is_valid_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc(digits, multipliers):
        s = sum(int(d) * m for d, m in zip(digits, multipliers))
        r = s % 11
        return '0' if r < 2 else str(11 - r)

    m1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    m2 = [6] + m1
    digits = cnpj[:12]
    d1 = calc(digits, m1)
    d2 = calc(digits + d1, m2)
    return cnpj[-2:] == d1 + d2

class ClienteForm(forms.ModelForm):
    TIPO_PESSOA_CHOICES = (
        ("F", "Pessoa Física (CPF)"),
        ("J", "Pessoa Jurídica (CNPJ)"),
    )

    tipo_pessoa = forms.ChoiceField(
        choices=TIPO_PESSOA_CHOICES,
        widget=forms.RadioSelect,
        initial="F",
        label="Tipo de pessoa",
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'tipo_pessoa', 'cpf_cnpj', 'telefone', 'endereco', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do cliente'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control input-cpf-cnpj',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CPF/CNPJ é opcional pelo model, mas garanta no form também:
        self.fields['cpf_cnpj'].required = False

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome

    def clean_cpf_cnpj(self):
        valor = (self.cleaned_data.get('cpf_cnpj') or '').strip()
        tipo = self.cleaned_data.get('tipo_pessoa')
        sem_mascara = re.sub(r'\D', '', valor)

        # Correção: só valida se foi preenchido!
        if not sem_mascara:
            return None  # ou "", mas None evita problema no banco

        if tipo == "F":
            # CPF: 11 dígitos
            if len(sem_mascara) != 11 or not is_valid_cpf(sem_mascara):
                raise forms.ValidationError("CPF inválido.")
        else:
            # CNPJ: 14 dígitos
            if len(sem_mascara) != 14 or not is_valid_cnpj(sem_mascara):
                raise forms.ValidationError("CNPJ inválido.")

        return valor

class TipoMadeiraForm(forms.ModelForm):
    class Meta:
        model = TipoMadeira
        fields = ['nome', 'preco_normal', 'preco_com_frete', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CASCA SECA, ANGICO, MIXTA',
            }),
            'preco_normal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '460.00',
                'step': '0.01',
            }),
            'preco_com_frete': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '330.00',
                'step': '0.01',
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome

class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = ['nome', 'cpf', 'telefone', 'placa_veiculo', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do motorista',
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000',
            }),
            'placa_veiculo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ABC-1234',
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        return nome.upper().strip() if nome else nome