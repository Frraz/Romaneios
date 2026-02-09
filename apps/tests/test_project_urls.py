from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from apps.tests.factories import create_user


class ProjectUrlsSmokeTests(TestCase):
    def test_home_redirects_to_login_when_anonymous(self):
        # home = relatorios:dashboard (LoginRequiredMixin)
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_home_loads_when_logged_in(self):
        create_user(username="home1", password="12345678")
        self.client.login(username="home1", password="12345678")

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_admin_login_page_exists(self):
        resp = self.client.get("/admin/login/")
        self.assertIn(resp.status_code, (200, 302))

    def test_core_dashboard_currently_public(self):
        resp = self.client.get(reverse("core:dashboard"))
        self.assertEqual(resp.status_code, 200)