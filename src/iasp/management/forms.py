from django import forms
from django.utils.translation import gettext_lazy as _

from . models import *


class ApplicationInsertionRequiredCommissionReviewForm(forms.ModelForm):
    class Meta:
        model = ApplicationInsertionRequiredCommissionReview
        fields = [
            'changed_credits',
            'notes',
        ]
        labels = {
            'changed_credits': _("Credits"),
            'notes': _("Notes"),
        }


class ApplicationInsertionFreeCommissionReviewForm(forms.ModelForm):
    class Meta:
        model = ApplicationInsertionFreeCommissionReview
        fields = [
            'changed_credits',
            'notes',
        ]
        labels = {
            'changed_credits': _("Credits"),
            'notes': _("Notes"),
        }
