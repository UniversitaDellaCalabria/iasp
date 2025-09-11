from django import forms
from django.utils.translation import gettext_lazy as _

from . models import *


class ApplicationInsertionRequiredCommissionReviewForm(forms.ModelForm):
    class Meta:
        model = ApplicationInsertionRequiredCommissionReview
        fields = [
            'changed_credits',
            'changed_grade',
            'notes',
        ]
        labels = {
            'changed_credits': _("Credits"),
            'changed_grade': _("Vote/outcome"),
            'notes': _("Notes"),
        }


class ApplicationInsertionFreeCommissionReviewForm(forms.ModelForm):
    class Meta:
        model = ApplicationInsertionFreeCommissionReview
        fields = [
            'changed_credits',
            'changed_grade',
            'notes',
        ]
        labels = {
            'changed_credits': _("Credits"),
            'changed_grade': _("Vote/outcome"),
            'notes': _("Notes"),
        }
