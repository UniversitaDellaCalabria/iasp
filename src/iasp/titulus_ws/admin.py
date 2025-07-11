from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from . models import *


@admin.register(TitulusConfiguration)
class TitulusConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'aoo',
        'is_active',
    )
    list_editable = ('is_active',)
