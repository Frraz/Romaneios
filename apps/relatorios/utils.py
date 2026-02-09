from __future__ import annotations

from dataclasses import dataclass
import re
from django.utils import timezone


@dataclass(frozen=True)
class PeriodoFiltro:
    mes: int
    ano: int
    cliente_id: str | None = None


def parse_mes_ano(request, default_to_now: bool = True) -> tuple[int, int]:
    """
    Obtém mês e ano do request.GET com fallback seguro.
    Usa timezone.localdate() (padrão recomendado no Django).
    """
    now = timezone.localdate()
    default_mes = now.month if default_to_now else 1
    default_ano = now.year if default_to_now else now.year

    try:
        mes = int(request.GET.get("mes", default_mes))
    except (TypeError, ValueError):
        mes = default_mes

    try:
        ano = int(request.GET.get("ano", default_ano))
    except (TypeError, ValueError):
        ano = default_ano

    # clamp simples
    if mes < 1 or mes > 12:
        mes = default_mes
    if ano < 1900 or ano > 2500:
        ano = default_ano

    return mes, ano


def get_periodo_filtro(request) -> PeriodoFiltro:
    """Retorna um objeto com mes/ano/cliente_id (cliente é opcional)."""
    mes, ano = parse_mes_ano(request, default_to_now=True)
    cliente_id = request.GET.get("cliente") or None
    return PeriodoFiltro(mes=mes, ano=ano, cliente_id=cliente_id)


def apply_mes_ano_filter(qs, date_field: str, mes: int, ano: int):
    """
    Aplica filtro month/year para um campo de data.
    Ex: apply_mes_ano_filter(Romaneio.objects.all(), "data_romaneio", mes, ano)
    """
    return qs.filter(**{f"{date_field}__month": mes, f"{date_field}__year": ano})


def csv_header_romaneios_por_item(writer, delimiter: str = ";"):
    """
    Header CSV para export de ROMANEIOS POR ITEM (alinhado com sua view atual).
    """
    writer.writerow([
        "Modalidade",
        "Tipo Romaneio",
        "Nº Romaneio",
        "Data",
        "Cliente",
        "Motorista",
        "Espécie",
        "Qtd Item (m³)",
        "Valor Unit. (R$/m³)",
        "Total Item (R$)",
    ])


def soma_total_m3_itens(itens) -> float:
    """Soma quantidade_m3_total (por item)."""
    return sum(float(getattr(item, "quantidade_m3_total", 0) or 0) for item in itens)


def soma_total_valor_itens(itens) -> float:
    """Soma valor_total (por item)."""
    return sum(float(getattr(item, "valor_total", 0) or 0) for item in itens)


def safe_filename(value: str, default: str = "arquivo") -> str:
    """Gera nome seguro para download (sem caracteres estranhos)."""
    value = (value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value or default