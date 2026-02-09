from __future__ import annotations

from django.test import TestCase

from apps.core.models import ConfiguracaoGeral


class ConfiguracaoGeralModelTests(TestCase):
    def test_str(self):
        cfg = ConfiguracaoGeral.objects.create(nome="empresa_nome", valor="Madeireira JD")
        self.assertEqual(str(cfg), "empresa_nome: Madeireira JD")