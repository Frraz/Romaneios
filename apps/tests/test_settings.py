from __future__ import annotations

from django.conf import settings
from django.test import SimpleTestCase


class SettingsSmokeTests(SimpleTestCase):
    def test_secret_key_is_set(self):
        self.assertTrue(getattr(settings, "SECRET_KEY", None))

    def test_installed_apps_contains_project_apps(self):
        installed = set(settings.INSTALLED_APPS)
        for app in (
            "apps.cadastros",
            "apps.romaneio",
            "apps.financeiro",
            "apps.relatorios",
            "apps.core",
        ):
            self.assertIn(app, installed)

    def test_login_urls_are_expected(self):
        self.assertEqual(settings.LOGIN_URL, "/accounts/login/")
        self.assertEqual(settings.LOGIN_REDIRECT_URL, "/")
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, "/accounts/login/")

    def test_database_engine_is_configured(self):
        default = settings.DATABASES["default"]
        self.assertIn("ENGINE", default)
        self.assertTrue(default["ENGINE"])