from __future__ import annotations

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.tests.factories import create_user


class PasswordResetEmailDomainTests(TestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_DOMAIN="example.com",
        SITE_PROTOCOL="https",
    )
    def test_password_reset_email_uses_site_domain_and_protocol(self):
        user = create_user(username="reset1", password="12345678", email="reset1@example.com")

        resp = self.client.post(reverse("password_reset"), data={"email": "reset1@example.com"})
        # PasswordResetView redireciona para done
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body

        # link deve conter https e domínio example.com
        self.assertIn("https://example.com", body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_DOMAIN="myhost.local:8000",
        SITE_PROTOCOL="http",
    )
    def test_password_reset_email_http_when_protocol_http(self):
        user = create_user(username="reset2", password="12345678", email="reset2@example.com")

        resp = self.client.post(reverse("password_reset"), data={"email": "reset2@example.com"})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("http://myhost.local:8000", body)