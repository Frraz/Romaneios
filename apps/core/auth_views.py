from django.conf import settings
from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponseRedirect


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        protocol = getattr(settings, "SITE_PROTOCOL", "http")
        domain = getattr(settings, "SITE_DOMAIN", None)

        opts = {
            "use_https": protocol == "https",
            "request": self.request,
            "subject_template_name": self.subject_template_name,
            "email_template_name": self.email_template_name,
            "from_email": self.from_email,
            "html_email_template_name": self.html_email_template_name,
            # garante que o template tenha protocol/domain corretos, independente do request
            "extra_email_context": {
                **(self.extra_email_context or {}),
                "protocol": protocol,
                "domain": domain,
            },
        }

        if domain:
            opts["domain_override"] = domain

        form.save(**opts)
        return HttpResponseRedirect(self.get_success_url())