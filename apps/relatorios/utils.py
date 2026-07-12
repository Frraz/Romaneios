from __future__ import annotations

import datetime
import re

from django.utils import timezone


def parse_mes_ano(request, *, allow_todos: bool = True) -> tuple[int | None, int | None]:
    """
    Lê mes/ano do request.GET com a convenção compartilhada pelos relatórios:

      - parâmetro ausente (primeira visita)  → mês/ano atual
      - parâmetro == "" ("Todos")            → None (sem restrição), se allow_todos
      - inválido ou fora de faixa            → mês/ano atual

    Retorna (mes, ano), cada um int ou None.
    """
    hoje = timezone.localdate()

    def _parse(raw: str | None, default: int, minimo: int, maximo: int) -> int | None:
        if raw is None:
            return default
        if raw == "":
            return None if allow_todos else default
        try:
            valor = int(raw)
        except (TypeError, ValueError):
            return default
        if valor < minimo or valor > maximo:
            return default
        return valor

    mes = _parse(request.GET.get("mes"), hoje.month, 1, 12)
    ano = _parse(request.GET.get("ano"), hoje.year, 1900, 2500)
    return mes, ano


def apply_periodo(qs, date_field: str, mes: int | None, ano: int | None):
    """
    Aplica filtro de período a um queryset. None significa "Todos" (sem restrição).
    Ex.: apply_periodo(Romaneio.objects.all(), "data_romaneio", mes, ano)
    """
    if mes:
        qs = qs.filter(**{f"{date_field}__month": mes})
    if ano:
        qs = qs.filter(**{f"{date_field}__year": ano})
    return qs


def inicio_periodo(mes: int | None, ano: int | None) -> datetime.date | None:
    """
    Data de início do período filtrado, para cálculo de saldo anterior.

    Sem ano definido não há período contíguo (ex.: "mês 07 de todos os anos"),
    então não existe um "antes" bem definido → retorna None.
    """
    if ano is None:
        return None
    return datetime.date(ano, mes or 1, 1)


def periodo_label(mes: int | None, ano: int | None) -> str:
    """Rótulo humano do período para títulos de tela/PDF/Excel."""
    if mes and ano:
        return f"{mes:02d}/{ano}"
    if mes:
        return f"Mês {mes:02d} / Todos os anos"
    if ano:
        return f"Todos os meses / {ano}"
    return "Todos os períodos"


def periodo_slug(mes: int | None, ano: int | None) -> str:
    """Versão segura do período para nomes de arquivo/abas."""
    if mes and ano:
        return f"{mes:02d}_{ano}"
    if mes:
        return f"mes{mes:02d}"
    if ano:
        return f"ano{ano}"
    return "todos"


def get_cliente_id(request) -> str:
    """
    Lê o filtro de cliente aceitando tanto "cliente_id" (fluxo financeiro)
    quanto "cliente" (fichas), para links/bookmarks antigos continuarem válidos.
    """
    return (request.GET.get("cliente_id") or request.GET.get("cliente") or "").strip()


def safe_filename(value: str, default: str = "arquivo") -> str:
    """Gera nome seguro para download (sem caracteres estranhos)."""
    value = (value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value or default
