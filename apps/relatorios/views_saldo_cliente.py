from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import ListView

from apps.cadastros.models import Cliente

from .utils import safe_filename

TIPOS_SALDO = ["todos", "negativos", "positivos", "zerados"]

TIPO_SALDO_LABELS = {
    "todos": "Todos",
    "negativos": "Negativos (Devendo)",
    "positivos": "Positivos (Crédito)",
    "zerados": "Zerados",
}


def _clientes_filtrados(request) -> tuple[list[Cliente], str, str]:
    """
    Lista de clientes filtrada por tipo_saldo/q, ordenada do mais devedor
    para o mais positivo. Reutilizada pela view HTML e pelos exports.

    O saldo é calculado UMA vez por cliente e cacheado em c.saldo_calc
    (o template já prefere saldo_calc quando presente).
    """
    tipo_saldo = (request.GET.get("tipo_saldo") or "todos").strip().lower()
    if tipo_saldo not in TIPOS_SALDO:
        tipo_saldo = "todos"
    q = (request.GET.get("q") or "").strip().lower()

    clientes = list(Cliente.objects.all())
    for c in clientes:
        c.saldo_calc = c.saldo_atual

    # ===== busca (q) =====
    if q:
        def match(c: Cliente) -> bool:
            nome = (getattr(c, "nome", "") or "").lower()
            telefone = (getattr(c, "telefone", "") or "").lower()
            cpf_cnpj = (getattr(c, "cpf_cnpj", "") or "").lower()
            return (q in nome) or (q in telefone) or (q in cpf_cnpj)

        clientes = [c for c in clientes if match(c)]

    # ===== filtro por tipo de saldo =====
    if tipo_saldo == "negativos":
        clientes = [c for c in clientes if c.saldo_calc < 0]
    elif tipo_saldo == "positivos":
        clientes = [c for c in clientes if c.saldo_calc > 0]
    elif tipo_saldo == "zerados":
        clientes = [c for c in clientes if c.saldo_calc == 0]

    # ===== ordenação padrão =====
    # do mais negativo para o mais positivo; em empate, por nome
    clientes.sort(key=lambda c: (c.saldo_calc, (getattr(c, "nome", "") or "").lower()))

    return clientes, tipo_saldo, q


def _resumo_saldos(clientes: list[Cliente]) -> dict:
    """Totais do relatório: a receber (|Σ| negativos) e créditos (Σ positivos)."""
    total_receber = sum((-c.saldo_calc for c in clientes if c.saldo_calc < 0), Decimal("0.00"))
    total_creditos = sum((c.saldo_calc for c in clientes if c.saldo_calc > 0), Decimal("0.00"))
    return {
        "qtd_clientes": len(clientes),
        "total_receber": total_receber,
        "total_creditos": total_creditos,
    }


class RelatorioSaldoClientesView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "relatorios/saldo_clientes.html"
    context_object_name = "clientes"
    paginate_by = 100  # opcional: evita página gigante se tiver muitos clientes

    def get_queryset(self):
        clientes, tipo_saldo, q = _clientes_filtrados(self.request)
        self._tipo_saldo = tipo_saldo
        self._q = q
        return clientes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos_saldo"] = TIPOS_SALDO
        context["tipo_saldo"] = getattr(self, "_tipo_saldo", "todos")
        context["q"] = getattr(self, "_q", "")
        return context


# =============================================================================
# Exports
# =============================================================================
@login_required
def saldo_clientes_export_excel(request):
    """Exporta o Saldo de Clientes (lista filtrada inteira) em Excel."""
    from io import BytesIO

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    clientes, tipo_saldo, q = _clientes_filtrados(request)
    resumo = _resumo_saldos(clientes)

    brand_fill = PatternFill("solid", fgColor="246B29")
    head_fill  = PatternFill("solid", fgColor="EEF3EF")
    zebra_fill = PatternFill("solid", fgColor="F7F7F7")

    title_font = Font(bold=True, size=16, color="FFFFFF")
    bold   = Font(bold=True)
    thin   = Side(style="thin", color="D0D7DE")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    wb = Workbook()
    ws = wb.active
    ws.title = "Saldo de Clientes"

    ws.merge_cells("A1:E1")
    ws["A1"] = "SALDO DE CLIENTES"
    ws["A1"].font  = title_font
    ws["A1"].fill  = brand_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:E2")
    ws["A2"] = f"Tipo: {TIPO_SALDO_LABELS.get(tipo_saldo, tipo_saldo)}  |  Busca: {q or '—'}"
    ws["A2"].font      = Font(color="FFFFFF", bold=True, size=11)
    ws["A2"].fill      = brand_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # Resumo
    resumo_rows = [
        ("Clientes exibidos",       resumo["qtd_clientes"], None),
        ("Total a receber (R$)",    float(resumo["total_receber"]), '"R$" #,##0.00'),
        ("Total de créditos (R$)",  float(resumo["total_creditos"]), '"R$" #,##0.00'),
    ]
    start = 4
    for i, (k, v, fmt) in enumerate(resumo_rows):
        r = start + i
        ws.cell(row=r, column=1, value=k).font = bold
        cell = ws.cell(row=r, column=2, value=v)
        if fmt:
            cell.number_format = fmt
        ws.cell(row=r, column=1).border = border
        ws.cell(row=r, column=2).border = border

    header_row = start + len(resumo_rows) + 1
    headers = ["Cliente", "Telefone", "CPF/CNPJ", "Saldo (R$)", "Situação"]
    for col_idx, text in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=text)
        cell.font      = Font(bold=True, color="1F2937")
        cell.fill      = head_fill
        cell.border    = border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    row = header_row + 1
    for idx, c in enumerate(clientes, start=1):
        saldo = c.saldo_calc
        if saldo < 0:
            situacao = "Devendo"
        elif saldo > 0:
            situacao = "Crédito"
        else:
            situacao = "Zerado"

        ws.cell(row=row, column=1, value=c.nome)
        ws.cell(row=row, column=2, value=c.telefone or "")
        ws.cell(row=row, column=3, value=c.cpf_cnpj or "")
        ws.cell(row=row, column=4, value=float(saldo)).number_format = '"R$" #,##0.00'
        ws.cell(row=row, column=5, value=situacao)

        for cidx in range(1, 6):
            cell = ws.cell(row=row, column=cidx)
            cell.border    = border
            cell.alignment = Alignment(horizontal="right" if cidx == 4 else "left", vertical="center")
            if idx % 2 == 0:
                cell.fill = zebra_fill

        row += 1

    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    ws.auto_filter.ref = f"A{header_row}:E{max(header_row, row - 1)}"

    widths = {1: 38, 2: 18, 3: 20, 4: 16, 5: 12}
    for col_idx, width in widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = safe_filename(f"saldo_clientes_{tipo_saldo}.xlsx")
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def saldo_clientes_export_pdf(request):
    """Exporta o Saldo de Clientes (lista filtrada inteira) para PDF via WeasyPrint."""
    clientes, tipo_saldo, q = _clientes_filtrados(request)
    resumo = _resumo_saldos(clientes)

    context = {
        "clientes": clientes,
        "tipo_saldo": tipo_saldo,
        "tipo_saldo_label": TIPO_SALDO_LABELS.get(tipo_saldo, tipo_saldo),
        "q": q,
        "now": timezone.localtime(),
        **resumo,
    }

    html_string = render_to_string("relatorios/saldo_clientes_pdf.html", context)
    base_url    = request.build_absolute_uri("/")

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
    except Exception as exc:
        return HttpResponse(
            f"Falha ao gerar PDF. Erro: {exc}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )

    filename = safe_filename(f"saldo_clientes_{tipo_saldo}.pdf")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
