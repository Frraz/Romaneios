from django.conf import settings
from django.contrib.auth.views import PasswordResetView


class CustomPasswordResetView(PasswordResetView):
    """
    Força domínio e protocolo (http/https) do link enviado no e-mail, usando SITE_DOMAIN e SITE_PROTOCOL.
    """

    def form_valid(self, form):
        opts = {
            "use_https": getattr(settings, "SITE_PROTOCOL", "http") == "https",
            "request": self.request,
            "subject_template_name": self.subject_template_name,
            "email_template_name": self.email_template_name,
            "from_email": self.from_email,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
        }

        site_domain = getattr(settings, "SITE_DOMAIN", None)
        if site_domain:
            opts["domain_override"] = site_domain

        form.save(**opts)
        return super().form_valid(form)