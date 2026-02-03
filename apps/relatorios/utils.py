from datetime import datetime

def parse_mes_ano(request, default_to_now=True):
    """
    Obtém mês e ano do request.GET (com fallback seguro), usado em todos os relatórios.
    """
    now = datetime.now()
    try:
        mes = int(request.GET.get('mes', now.month if default_to_now else 1))
    except (TypeError, ValueError):
        mes = now.month if default_to_now else 1
    try:
        ano = int(request.GET.get('ano', now.year if default_to_now else 2024))
    except (TypeError, ValueError):
        ano = now.year if default_to_now else 2024
    return mes, ano

def csv_header_romaneio(writer):
    writer.writerow([
        "Data", "Cliente", "Espécie", "Comp", "Rôdo", "Desconto", "Total (em M³)", "Observação"
    ])

def soma_total_m3(itens):
    """
    Soma o campo quantidade_m3 de uma queryset ou lista de itens.
    """
    return sum(float(getattr(item, "quantidade_m3", 0)) for item in itens)