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
    list_filter = ('call', )
    search_fields = ('call__title_it', 'user__last_name', 'user__taxpayer_id', 'protocol_number')

    def get_readonly_fields(self, request, obj=None):
        # ~ return [field.name for field in self.model._meta.fields]
        return []
