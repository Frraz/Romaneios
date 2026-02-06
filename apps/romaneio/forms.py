from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.cadastros.models import Cliente, Motorista, TipoMadeira
from .models import ItemRomaneio, Romaneio, UnidadeRomaneio


# ================= ROMANEIO =================
class RomaneioForm(forms.ModelForm):
    """
    Form principal do Romaneio.
    - Filtra Cliente/Motorista apenas ativos
    - Widget HTML5 para data (YYYY-MM-DD)
    """

    class Meta:
        model = Romaneio
        fields = [
            "numero_romaneio",
            "data_romaneio",
            "cliente",
            "motorista",
            "tipo_romaneio",
            "modalidade",
        ]
        widgets = {
            "numero_romaneio": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 11613"}),
            "data_romaneio": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),
            "cliente": forms.Select(attrs={"class": "form-control select2"}),
            "motorista": forms.Select(attrs={"class": "form-control select2"}),
            "tipo_romaneio": forms.Select(attrs={"class": "form-control"}),
            "modalidade": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].queryset = Cliente.objects.filter(ativo=True).order_by("nome")
        self.fields["motorista"].queryset = Motorista.objects.filter(ativo=True).order_by("nome")

        if self.instance and self.instance.pk and self.instance.data_romaneio:
            self.fields["data_romaneio"].initial = self.instance.data_romaneio.strftime("%Y-%m-%d")


# ================= ITEM ROMANEIO =================
class ItemRomaneioForm(forms.ModelForm):
    """
    Item do Romaneio:
    - Tipo de madeira
    - Quantidade total (m³)
      * SIMPLES: usuário informa
      * DETALHADO: calculado pelas unidades (campo pode vir preenchido pelo JS)
    - Valor unitário (m³)
    """

    class Meta:
        model = ItemRomaneio
        fields = [
            "tipo_madeira",
            "quantidade_m3_total",
            "valor_unitario",
        ]
        widgets = {
            "tipo_madeira": forms.Select(
                attrs={
                    "class": "form-control select2 tipo-madeira-select",
                    "onchange": "atualizarPrecoItem(this)",
                }
            ),
            "quantidade_m3_total": forms.NumberInput(
                attrs={
                    "class": "form-control quantidade-m3-total",
                    "step": "0.001",
                    "min": "0.001",
                    "placeholder": "0.000",
                    "inputmode": "decimal",
                }
            ),
            "valor_unitario": forms.NumberInput(
                attrs={
                    "class": "form-control valor-unitario",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                    "readonly": "readonly",
                    "inputmode": "decimal",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_madeira"].queryset = TipoMadeira.objects.filter(ativo=True).order_by("nome")

        # A validação de "se é obrigatório" fica no clean (depende da modalidade)
        # mas aqui já dá para ajudar quando estamos editando um item existente.
        romaneio = getattr(self.instance, "romaneio", None)
        if romaneio and romaneio.modalidade == "DETALHADO":
            self.fields["quantidade_m3_total"].required = False

    def clean_valor_unitario(self):
        valor = self.cleaned_data.get("valor_unitario")
        if valor is None or valor <= Decimal("0.00"):
            raise ValidationError("O valor unitário deve ser maior que zero!")
        return valor

    def clean_quantidade_m3_total(self):
        """
        SIMPLES: obrigatório > 0.
        DETALHADO: pode ser 0/blank durante a digitação, mas no submit deve estar coerente.
        Como no DETALHADO as unidades são salvas e os models recalculam, aceitamos 0 aqui,
        mas a view/model vão recalcular após salvar unidades.
        """
        qtd = self.cleaned_data.get("quantidade_m3_total")
        qtd = qtd if qtd is not None else Decimal("0.000")

        romaneio = getattr(self.instance, "romaneio", None)
        modalidade = romaneio.modalidade if romaneio else None

        if modalidade == "SIMPLES" or modalidade is None:
            if qtd <= Decimal("0.000"):
                raise ValidationError("Informe a quantidade (m³) do item.")
        return qtd


class BaseItemRomaneioFormSet(BaseInlineFormSet):
    """
    - exige pelo menos 1 item não deletado
    - NÃO bloqueia DETALHADO (agora as unidades já são implementadas)
    """

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        valid_forms = [
            f for f in self.forms
            if getattr(f, "cleaned_data", None) and not f.cleaned_data.get("DELETE")
        ]
        if len(valid_forms) < 1:
            raise ValidationError("O romaneio precisa ter pelo menos um item.")

        # Opcional: você pode validar duplicidade de tipo_madeira por romaneio
        tipos = []
        for f in valid_forms:
            tm = f.cleaned_data.get("tipo_madeira")
            if tm:
                tipos.append(tm.pk)
        if len(tipos) != len(set(tipos)):
            raise ValidationError("Não é permitido repetir o mesmo Tipo de Madeira no mesmo romaneio.")


ItemRomaneioFormSet = inlineformset_factory(
    parent_model=Romaneio,
    model=ItemRomaneio,
    form=ItemRomaneioForm,
    formset=BaseItemRomaneioFormSet,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# ================= UNIDADE ROMANEIO =================
class UnidadeRomaneioForm(forms.ModelForm):
    """
    Unidade (tora) do item.
    """

    class Meta:
        model = UnidadeRomaneio
        fields = [
            "comprimento",
            "rodo",
            "desconto_1",
            "desconto_2",
            "quantidade_m3",
        ]
        widgets = {
            "comprimento": forms.NumberInput(
                attrs={
                    "class": "form-control campo-detalhado campo-unidade",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Ex: 3.00",
                    "inputmode": "decimal",
                }
            ),
            "rodo": forms.NumberInput(
                attrs={
                    "class": "form-control campo-detalhado campo-unidade",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Ex: 40.00",
                    "inputmode": "decimal",
                }
            ),
            "desconto_1": forms.NumberInput(
                attrs={
                    "class": "form-control campo-detalhado campo-unidade",
                    "step": "0.01",
                    "min": "0.00",
                    "placeholder": "0.00",
                    "inputmode": "decimal",
                }
            ),
            "desconto_2": forms.NumberInput(
                attrs={
                    "class": "form-control campo-detalhado campo-unidade",
                    "step": "0.01",
                    "min": "0.00",
                    "placeholder": "0.00",
                    "inputmode": "decimal",
                }
            ),
            "quantidade_m3": forms.NumberInput(
                attrs={
                    "class": "form-control campo-unidade quantidade-m3",
                    "step": "0.001",
                    "min": "0.001",
                    "placeholder": "0.000",
                    "inputmode": "decimal",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not (self.instance and self.instance.pk):
            self.fields["desconto_1"].initial = Decimal("0.00")
            self.fields["desconto_2"].initial = Decimal("0.00")

    def clean(self):
        super().clean()

        # Normaliza descontos vazios para 0.00
        for field in ("desconto_1", "desconto_2"):
            if self.cleaned_data.get(field) is None:
                self.cleaned_data[field] = Decimal("0.00")

        return self.cleaned_data

    def clean_quantidade_m3(self):
        qtd = self.cleaned_data.get("quantidade_m3")
        if qtd is None or qtd <= Decimal("0.000"):
            raise ValidationError("A quantidade deve ser maior que zero!")
        return qtd


class BaseUnidadeRomaneioFormSet(BaseInlineFormSet):
    """
    - exige pelo menos 1 unidade não deletada
    - se DETALHADO: comprimento e rodo obrigatórios
    """

    def _get_modalidade(self):
        # Quando existe instance, é o mais confiável
        if self.instance and getattr(self.instance, "romaneio", None):
            return self.instance.romaneio.modalidade

        # Fallback: tenta buscar no POST (nem sempre existe, mas ajuda)
        if self.data:
            return self.data.get("modalidade")

        return None

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        valid_forms = [
            f for f in self.forms
            if getattr(f, "cleaned_data", None) and not f.cleaned_data.get("DELETE")
        ]
        if len(valid_forms) < 1:
            raise ValidationError("O item precisa ter pelo menos uma unidade.")

        modalidade = self._get_modalidade()
        if modalidade != "DETALHADO":
            return

        for form in valid_forms:
            comprimento = form.cleaned_data.get("comprimento")
            rodo = form.cleaned_data.get("rodo")

            if comprimento is None or comprimento <= Decimal("0.00"):
                form.add_error("comprimento", "Comprimento é obrigatório na modalidade Detalhado.")
            if rodo is None or rodo <= Decimal("0.00"):
                form.add_error("rodo", "Rôdo é obrigatório na modalidade Detalhado.")


UnidadeRomaneioFormSet = inlineformset_factory(
    parent_model=ItemRomaneio,
    model=UnidadeRomaneio,
    form=UnidadeRomaneioForm,
    formset=BaseUnidadeRomaneioFormSet,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)