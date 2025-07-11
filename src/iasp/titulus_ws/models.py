from django.db import models
from django.utils.translation import gettext_lazy as _

from generics.models import *


class TitulusConfiguration(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    name = models.CharField(_("Denominazione configurazione"), max_length=255)
    username = models.CharField("Username", max_length=255)
    password = models.CharField("Password", max_length=255)
    aoo = models.CharField("AOO", max_length=12)
    agd = models.CharField(
        "AGD", max_length=12, default="", blank=True
    )

    # protocollo_template = models.TextField('XML template',
    # help_text=_('Template XML che '
    # 'descrive il flusso'))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Configurazione Titulus")
        verbose_name_plural = _("Configurazioni Titulus")

    def __str__(self):
        return self.name
