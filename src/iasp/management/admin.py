from django import forms
from django.contrib import admin

from . models import *


class CallCommissionMemberModelForm(forms.ModelForm):
    class Meta:
        model = CallCommissionMember
        exclude = ('created_by','created','modified_by','modified')


class CallCommissionMemberInline(admin.TabularInline):
    model = CallCommissionMember
    form = CallCommissionMemberModelForm
    raw_id_fields = ["user"]
    extra = 0


class CallCommissionModelForm(forms.ModelForm):
    class Meta:
        model = CallCommission
        exclude = ('created_by','created','modified_by','modified')


class CallCommissionInline(admin.TabularInline):
    model = CallCommission
    form = CallCommissionModelForm
    extra = 0


@admin.register(CallCommission)
class CallCommissionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'start',
        'end',
        'is_active',
    )
    list_editable = ('is_active',)
    raw_id_fields = ["call"]
    inlines = [
        CallCommissionMemberInline,
    ]
