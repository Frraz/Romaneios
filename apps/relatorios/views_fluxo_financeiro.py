from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import TemplateView

from apps.cadastros.models import TipoMadeira
from apps.financeiro.models import Pagamento
from apps.romaneio.models import Romaneio

from .views_ficha_romaneio import get_mes_ano, _safe_filename


def _fluxo_querysets(request):
    """
    Retorna (vendas_qs, pagamentos_qs) aplicando filtros e ordenação do Fluxo Financeiro.

    Filtros (GET):
      - mes, ano
      - numero_romaneio (opcional) -> filtra vendas; e filtra pagamentos por cliente dos romaneios encontrados
      - tipo_madeira_id (opcional) -> filtra vendas por itens; e filtra pagamentos por cliente dos romaneios encontrados

    Ordenação (GET):
      - vendas: sort_v=data|cliente|valor  dir_v=asc|desc
      - pagamentos: sort_p=data|cliente|tipo|valor  dir_p=asc|desc
    """
    mes, ano = get_mes_ano(request)

    numero_romaneio = (request.GET.get("numero_romaneio") or "").strip()
    tipo_madeira_id = (request.GET.get("tipo_madeira_id") or "").strip()

    sort_v = (request.GET.get("sort_v") or "data").strip().lower()
    dir_v = (request.GET.get("dir_v") or "asc").strip().lower()
    sort_p = (request.GET.get("sort_p") or "data").strip().lower()
    dir_p = (request.GET.get("dir_p") or "asc").strip().lower()

    vendas_qs = (
        Romaneio.objects.filter(
            data_romaneio__month=mes,
            data_romaneio__year=ano,
        )
        .select_related("cliente", "motorista")
    )

    if numero_romaneio:
        vendas_qs = vendas_qs.filter(numero_romaneio=numero_romaneio)

    if tipo_madeira_id:
        # Romaneios do mês que possuem ao menos 1 item da madeira selecionada
        vendas_qs = vendas_qs.filter(itens__tipo_madeira_id=tipo_madeira_id).distinct()

    # Pagamentos do mês
    pagamentos_qs = (
        Pagamento.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano,
        )
        .select_related("cliente")
    )

    # Se filtrou por número do romaneio e/ou tipo de madeira, faz sentido limitar pagamentos ao(s) cliente(s)
    # presentes nas vendas filtradas (senão o saldo fica incoerente).
    if numero_romaneio or tipo_madeira_id:
        cliente_ids = list(vendas_qs.values_list("cliente_id", flat=True).distinct())
        pagamentos_qs = pagamentos_qs.filter(cliente_id__in=cliente_ids)

    # ===== ordenação vendas =====
    sort_map_v = {
        "data": "data_romaneio",
        "cliente": "cliente__nome",
        "valor": "valor_total",
    }
    field_v = sort_map_v.get(sort_v, "data_romaneio")
    if dir_v == "desc":
        field_v = f"-{field_v}"
    vendas_qs = vendas_qs.order_by(field_v, "id")

    # ===== ordenação pagamentos =====
    sort_map_p = {
        "data": "data_pagamento",
        "cliente": "cliente__nome",
        "tipo": "tipo_pagamento",
        "valor": "valor",
    }
    field_p = sort_map_p.get(sort_p, "data_pagamento")
    if dir_p == "desc":
        field_p = f"-{field_p}"
    pagamentos_qs = pagamentos_qs.order_by(field_p, "id")

    return vendas_qs, pagamentos_qs


class RelatorioFluxoView(LoginRequiredMixin, TemplateView):
    template_name = "relatorios/fluxo_financeiro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mes, ano = get_mes_ano(self.request)

        vendas_qs, pagamentos_qs = _fluxo_querysets(self.request)

        vendas = vendas_qs.aggregate(total=Sum("valor_total")).get("total") or 0
        pagamentos = pagamentos_qs.aggregate(total=Sum("valor")).get("total") or 0

        saldo_mes = pagamentos - vendas
        if saldo_mes > 0:
            saldo_mes_classe = "text-success"
        elif saldo_mes < 0:
            saldo_mes_classe = "text-danger"
        else:
            saldo_mes_classe = "text-secondary"

        anos_romaneios = [d.year for d in Romaneio.objects.dates("data_romaneio", "year", order="ASC")]
        anos_pagamentos = [d.year for d in Pagamento.objects.dates("data_pagamento", "year", order="ASC")]
        anos = sorted(set(anos_romaneios + anos_pagamentos)) or [timezone.localdate().year]

        context.update({
            "mes": mes,
            "ano": ano,
            "meses": range(1, 13),
            "anos": anos,

            "tipos_madeira": TipoMadeira.objects.order_by("nome"),

            "vendas": vendas,
            "pagamentos": pagamentos,
            "saldo_mes": saldo_mes,
            "saldo_mes_classe": saldo_mes_classe,

            "vendas_detalhadas": vendas_qs,
            "pagamentos_detalhados": pagamentos_qs,

            # úteis para o template (manter estado / setinhas)
            "numero_romaneio": (self.request.GET.get("numero_romaneio") or "").strip(),
            "tipo_madeira_id": (self.request.GET.get("tipo_madeira_id") or "").strip(),
            "sort_v": (self.request.GET.get("sort_v") or "data"),
            "dir_v": (self.request.GET.get("dir_v") or "asc"),
            "sort_p": (self.request.GET.get("sort_p") or "data"),
            "dir_p": (self.request.GET.get("dir_p") or "asc"),
        })
        return context


@login_required
def fluxo_financeiro_export_excel(request):
    """Exporta o Fluxo Financeiro do período em Excel (Resumo + abas Vendas/Pagamentos), respeitando filtros/ordenação."""
    from io import BytesIO

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    mes, ano = get_mes_ano(request)
    vendas_qs, pagamentos_qs = _fluxo_querysets(request)

    vendas_total = vendas_qs.aggregate(total=Sum("valor_total")).get("total") or 0
    pagamentos_total = pagamentos_qs.aggregate(total=Sum("valor")).get("total") or 0
    saldo = pagamentos_total - vendas_total

    brand_fill = PatternFill("solid", fgColor="246B29")
    head_fill = PatternFill("solid", fgColor="EEF3EF")
    zebra_fill = PatternFill("solid", fgColor="F7F7F7")

    title_font = Font(bold=True, size=16, color="FFFFFF")
    bold = Font(bold=True)
    thin = Side(style="thin", color="D0D7DE")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def set_col_width(ws, widths: dict[int, float]):
        for col_idx, width in widths.items():
            ws.column_dimensions[get_column_letter(col_idx)].width = width

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo"

    ws.merge_cells("A1:D1")
    ws["A1"] = f"FLUXO FINANCEIRO — {mes:02d}/{ano}"
    ws["A1"].font = title_font
    ws["A1"].fill = brand_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    numero_romaneio = (request.GET.get("numero_romaneio") or "").strip()
    tipo_madeira_id = (request.GET.get("tipo_madeira_id") or "").strip()

    madeira_nome = "Todas"
    if tipo_madeira_id:
        tm = TipoMadeira.objects.filter(pk=tipo_madeira_id).first()
        if tm:
            madeira_nome = tm.nome

    ws.merge_cells("A2:D2")
    ws["A2"] = f"Filtro Nº Romaneio: {numero_romaneio if numero_romaneio else '—'}  |  Madeira: {madeira_nome}"
    ws["A2"].font = Font(color="FFFFFF", bold=True, size=11)
    ws["A2"].fill = brand_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    resumo = [
        ("Vendas (R$)", float(vendas_total or 0)),
        ("Pagamentos (R$)", float(pagamentos_total or 0)),
        ("Saldo (R$)", float(saldo or 0)),
    ]
    start = 4
    for i, (k, v) in enumerate(resumo):
        r = start + i
        ws.cell(row=r, column=1, value=k).font = bold
        ws.cell(row=r, column=2, value=v).number_format = '"R$" #,##0.00'
        ws.cell(row=r, column=1).border = border
        ws.cell(row=r, column=2).border = border

    set_col_width(ws, {1: 22, 2: 18, 3: 2, 4: 2})

    # Aba Vendas
    ws_v = wb.create_sheet("Vendas")
    ws_v.append(["Data", "Cliente", "Nº Romaneio", "Valor (R$)"])
    for c in range(1, 5):
        cell = ws_v.cell(row=1, column=c)
        cell.font = Font(bold=True, color="1F2937")
        cell.fill = head_fill
        cell.border = border
        cell.alignment = Alignment(horizontal="center")

    row = 2
    for idx, venda in enumerate(vendas_qs, start=1):
        ws_v.cell(row=row, column=1, value=venda.data_romaneio).number_format = "dd/mm/yyyy"
        ws_v.cell(row=row, column=2, value=venda.cliente.nome if venda.cliente else "")
        ws_v.cell(row=row, column=3, value=venda.numero_romaneio)
        ws_v.cell(row=row, column=4, value=float(venda.valor_total or 0)).number_format = '"R$" #,##0.00'

        for c in range(1, 5):
            cell = ws_v.cell(row=row, column=c)
            cell.border = border
            cell.alignment = Alignment(horizontal="left" if c == 2 else "right", vertical="center")
            if idx % 2 == 0:
                cell.fill = zebra_fill
        row += 1

    ws_v.freeze_panes = "A2"
    ws_v.auto_filter.ref = f"A1:D{max(1, row-1)}"
    set_col_width(ws_v, {1: 12, 2: 38, 3: 14, 4: 16})

    # Aba Pagamentos
    ws_p = wb.create_sheet("Pagamentos")
    ws_p.append(["Data", "Cliente", "Tipo", "Valor (R$)"])
    for c in range(1, 5):
        cell = ws_p.cell(row=1, column=c)
        cell.font = Font(bold=True, color="1F2937")
        cell.fill = head_fill
        cell.border = border
        cell.alignment = Alignment(horizontal="center")

    row = 2
    for idx, pg in enumerate(pagamentos_qs, start=1):
        ws_p.cell(row=row, column=1, value=pg.data_pagamento).number_format = "dd/mm/yyyy"
        ws_p.cell(row=row, column=2, value=pg.cliente.nome if pg.cliente else "")
        ws_p.cell(
            row=row,
            column=3,
            value=str(pg.get_tipo_pagamento_display() if hasattr(pg, "get_tipo_pagamento_display") else getattr(pg, "tipo_pagamento", "")),
        )
        ws_p.cell(row=row, column=4, value=float(pg.valor or 0)).number_format = '"R$" #,##0.00'

        for c in range(1, 5):
            cell = ws_p.cell(row=row, column=c)
            cell.border = border
            cell.alignment = Alignment(horizontal="left" if c in (2, 3) else "right", vertical="center")
            if idx % 2 == 0:
                cell.fill = zebra_fill
        row += 1

    ws_p.freeze_panes = "A2"
    ws_p.auto_filter.ref = f"A1:D{max(1, row-1)}"
    set_col_width(ws_p, {1: 12, 2: 38, 3: 18, 4: 16})

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = _safe_filename(f"fluxo_financeiro_{mes:02d}_{ano}.xlsx")
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def fluxo_financeiro_export_pdf(request):
    """Exporta o Fluxo Financeiro do período para PDF via WeasyPrint, respeitando filtros/ordenação."""
    mes, ano = get_mes_ano(request)
    vendas_qs, pagamentos_qs = _fluxo_querysets(request)

    vendas_total = vendas_qs.aggregate(total=Sum("valor_total")).get("total") or 0
    pagamentos_total = pagamentos_qs.aggregate(total=Sum("valor")).get("total") or 0
    saldo = pagamentos_total - vendas_total

    tipo_madeira_id = (request.GET.get("tipo_madeira_id") or "").strip()
    madeira_nome = ""
    if tipo_madeira_id:
        tm = TipoMadeira.objects.filter(pk=tipo_madeira_id).first()
        if tm:
            madeira_nome = tm.nome

    context = {
        "mes": mes,
        "ano": ano,
        "vendas_total": vendas_total,
        "pagamentos_total": pagamentos_total,
        "saldo": saldo,
        "vendas": list(vendas_qs),
        "pagamentos": list(pagamentos_qs),
        "numero_romaneio": (request.GET.get("numero_romaneio") or "").strip(),
        "madeira_nome": madeira_nome,
        "now": timezone.localtime(),
    }

    html_string = render_to_string("relatorios/fluxo_financeiro_pdf.html", context)
    base_url = request.build_absolute_uri("/")

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
    except Exception as exc:
        return HttpResponse(
            f"Falha ao gerar PDF. Erro: {exc}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )

    filename = _safe_filename(f"fluxo_financeiro_{mes:02d}_{ano}.pdf")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response