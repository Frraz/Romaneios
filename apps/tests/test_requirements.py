from __future__ import annotations

import importlib
import importlib.metadata

from django.test import SimpleTestCase


class RequirementsImportTests(SimpleTestCase):
    def test_can_import_critical_packages(self):
        # Não testa se o SO tem libs (ex Cairo do WeasyPrint), mas pega ausência de pacote python.
        critical = [
            "django",
            "dotenv",  # python-dotenv
            "openpyxl",
            "psycopg2",
        ]
        for mod in critical:
            importlib.import_module(mod)

    def test_can_import_weasyprint(self):
        # Se no seu CI não tiver libs do SO instaladas, esse teste pode falhar.
        # Se isso acontecer, podemos:
        # - marcar como xfail/skip no CI, ou
        # - alterar para não importar weasyprint por padrão.
        importlib.import_module("weasyprint")

    def test_pinned_versions_exist(self):
        # Smoke: garante que conseguimos ler versões instaladas
        pkgs = [
            "Django",
            "openpyxl",
            "weasyprint",
            "psycopg2-binary",
        ]
        for p in pkgs:
            importlib.metadata.version(p)


class RequirementsImportTests(SimpleTestCase):
    def test_weasyprint_package_is_present(self):
        self.assertIsNotNone(importlib.util.find_spec("weasyprint"))