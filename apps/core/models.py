from django.db import models
from django.conf import settings

class BaseModel(models.Model):
    """
    Base abstrata para auditoria e timestamp.
    Herde este modelo para adicionar:
    - criado_em: Data/hora de criação
    - atualizado_em: Data/hora de última atualização
    - criado_por / modificado_por: FK para usuário responsável
    """
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_criados",
        on_delete=models.SET_NULL,
        null=True, blank=True, editable=False
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_modificados",
        on_delete=models.SET_NULL,
        null=True, blank=True, editable=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auditoria: popular criado/modificado_por em views/forms pelo request.user
        # Sugestão: Integrar com overrides no ModelForm ou signals, ex: usando threadlocals ou request em middleware.
        super().save(*args, **kwargs)

class ConfiguracaoGeral(models.Model):
    """
    Armazena configurações globais (ex: nome da empresa, contato, mensagem de rodapé etc.)
    Chave/valor flexível para parametrização da aplicação.
    """
    nome = models.CharField("Chave/Nome", max_length=200, unique=True)
    valor = models.CharField("Valor", max_length=500)
    descricao = models.CharField("Descrição", max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = "Configuração Geral"
        verbose_name_plural = "Configurações Gerais"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome}: {self.valor}"