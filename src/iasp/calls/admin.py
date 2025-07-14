from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from . models import *


class CallExcludedActivityModelForm(forms.ModelForm):
    class Meta:
        model = CallExcludedActivity
        exclude = ('created_by','created','modified_by','modified')


class CallExcludedActivityInline(admin.TabularInline):
    model = CallExcludedActivity
    form = CallExcludedActivityModelForm
    extra = 0


class CallRequirementModelForm(forms.ModelForm):
    class Meta:
        model = CallRequirement
        exclude = ('created_by','created','modified_by','modified')


class CallRequirementInline(admin.StackedInline):
    model = CallRequirement
    form = CallRequirementModelForm
    extra = 0


class CallFreeCreditsRuleModelForm(forms.ModelForm):
    class Meta:
        model = CallFreeCreditsRule
        exclude = ('created_by','created','modified_by','modified')


class CallFreeCreditsRuleInline(admin.TabularInline):
    model = CallFreeCreditsRule
    form = CallFreeCreditsRuleModelForm
    extra = 0


class CallTitulusConfigurationModelForm(forms.ModelForm):
    class Meta:
        model = CallTitulusConfiguration
        exclude = ('created_by','created','modified_by','modified')


class CallTitulusConfigurationInline(admin.StackedInline):
    model = CallTitulusConfiguration
    form = CallTitulusConfigurationModelForm
    extra = 0


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = (
        'title_it',
        'course_cod',
        'course_cohort',
        'course_year',
        'ordering',
        'is_active',
    )
    list_editable = ('is_active', 'ordering')
    readonly_fields = (
        'course_json_it',
        'course_json_en',
        'course_studyplan_json_it_trunked',
        'course_studyplan_json_en_trunked',
    )
    exclude = ('course_studyplans_json_it', 'course_studyplans_json_en')
    inlines = [
        CallExcludedActivityInline,
        CallRequirementInline,
        CallFreeCreditsRuleInline,
        CallTitulusConfigurationInline,
    ]

    def course_studyplan_json_it_trunked(self, obj):
        text = str(obj.course_studyplans_json_it) or ""
        if len(text) > 1000:
            return f'{text[:1000]}.....'
        return text
    course_studyplan_json_it_trunked.short_description = _("Course studyplan (IT) trunked")

    def course_studyplan_json_en_trunked(self, obj):
        text = str(obj.course_studyplans_json_en) or ""
        if len(text) > 1000:
            return f'{text[:1000]}.....'
        return text
    course_studyplan_json_en_trunked.short_description = _("Course studyplan (EN) trunked")
