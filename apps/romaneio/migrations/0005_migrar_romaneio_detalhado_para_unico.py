from decimal import Decimal
from django.db import migrations


def forwards(apps, schema_editor):
    Romaneio = apps.get_model("romaneio", "Romaneio")
    ItemRomaneio = apps.get_model("romaneio", "ItemRomaneio")

    RomaneioDetalhado = apps.get_model("romaneio", "RomaneioDetalhado")
    ItemRomaneioDetalhado = apps.get_model("romaneio", "ItemRomaneioDetalhado")

    # Mapeia romaneio_detalhado.id -> romaneio_novo.id
    mapa = {}

    # 1) Migrar cabeçalhos
    for rd in RomaneioDetalhado.objects.all().iterator():
        # Como você garantiu que numero_romaneio é único global, não precisamos prefixar.
        r = Romaneio.objects.create(
            numero_romaneio=rd.numero_romaneio,
            data_romaneio=rd.data_romaneio,
            cliente_id=rd.cliente_id,
            motorista_id=rd.motorista_id,
            tipo_romaneio=rd.tipo_romaneio,
            modalidade="DETALHADO",
            desconto=rd.desconto if rd.desconto is not None else Decimal("0.00"),
            usuario_cadastro_id=rd.usuario_cadastro_id,
            # data_cadastro/data_atualizacao: se quiser preservar exatamente, teria que update depois.
        )

        # tenta preservar timestamps (se o banco permitir update)
        try:
            Romaneio.objects.filter(pk=r.pk).update(
                data_cadastro=rd.data_cadastro,
                data_atualizacao=rd.data_atualizacao,
            )
        except Exception:
            pass

        mapa[rd.id] = r.id

    # 2) Migrar itens
    for itd in ItemRomaneioDetalhado.objects.all().iterator():
        novo_romaneio_id = mapa.get(itd.romaneio_id)
        if not novo_romaneio_id:
            continue

        ItemRomaneio.objects.create(
            romaneio_id=novo_romaneio_id,
            tipo_madeira_id=itd.tipo_madeira_id,
            comprimento=itd.comprimento,
            rodo=itd.rodo or "",
            quantidade_m3=itd.quantidade_m3,
            valor_unitario=itd.valor_unitario,
            # valor_total será calculado no save do model real, mas aqui via migration
            # o modelo histórico pode não chamar o save custom. Então gravamos igual ao antigo:
            valor_total=itd.valor_total,
        )

    # 3) Recalcular totais (m3_total, valor_bruto, valor_total)
    # Evita depender de save custom; calcula no banco com aggregate em loop.
    for rom_id in mapa.values():
        rom = Romaneio.objects.get(pk=rom_id)
        itens = ItemRomaneio.objects.filter(romaneio_id=rom_id)

        bruto = sum((i.valor_total or Decimal("0.00")) for i in itens)
        m3 = sum((i.quantidade_m3 or Decimal("0.000")) for i in itens)

        desconto = rom.desconto or Decimal("0.00")
        fator = Decimal("1.00") - (desconto / Decimal("100.00"))
        liquido = (bruto * fator).quantize(Decimal("0.01"))

        Romaneio.objects.filter(pk=rom_id).update(
            valor_bruto=bruto,
            valor_total=liquido,
            m3_total=m3,
        )


def backwards(apps, schema_editor):
    """
    Reversão: remove romaneios unificados que vieram do detalhado.
    Como não guardamos uma marca de origem, removemos por modalidade=DETALHADO
    (isso presume que você não criou manualmente novos detalhados depois da migração).
    """
    Romaneio = apps.get_model("romaneio", "Romaneio")
    ItemRomaneio = apps.get_model("romaneio", "ItemRomaneio")

    # remove itens e cabeçalhos dos detalhados migrados
    ids = list(Romaneio.objects.filter(modalidade="DETALHADO").values_list("id", flat=True))
    ItemRomaneio.objects.filter(romaneio_id__in=ids).delete()
    Romaneio.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("romaneio", "0004_alter_itemromaneio_options_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]