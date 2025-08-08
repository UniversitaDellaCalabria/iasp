from django.contrib import admin

from . models import *


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'call',
        'submission_date',
        'protocol_number',
        'protocol_date',
    )

    def get_readonly_fields(self, request, obj=None):
        # ~ return [field.name for field in self.model._meta.fields]
        return []
