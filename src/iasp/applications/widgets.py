from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from . models import Application


class CustomFileWidget(forms.ClearableFileInput):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        # Render del campo input normale
        input_html = super().render(name, None, attrs, renderer)

        output = ''
        if self.instance:
            if isinstance(self.instance, Application):

                if name == 'home_exams_certification': subpath = 'exams_certificate'
                if name == 'home_teaching_plan': subpath = 'teaching_plan'
                if name == 'home_votes_conversion': subpath = 'votes_conversion'
                if name == 'home_language_certification': subpath = 'language_certification'
                if name == 'declaration_of_value': subpath = 'declaration_of_value'
                if name == 'payment_receipt': subpath = 'payment_receipt'

                application_pk = self.instance.pk if isinstance(self.instance, Application) else self.instance.application.pk
                url = reverse(
                    f'applications:download_{subpath}',
                    kwargs={
                        'application_pk': application_pk,
                    }
                )
            else:
                application_pk = self.instance.application.pk
                url = reverse(
                    'applications:download_insertion_attachment',
                    kwargs={
                        'application_pk': application_pk,
                        'insertion_pk': self.instance.pk
                    }
                )

            if value and getattr(value, 'name', None):
                text = _("View currently loaded file")
                output += f'<a href="{url}" target="_blank">{text}</a><br>'

            output += input_html
            return mark_safe(output)

        return input_html

    def format_value(self, value):
        # Disattiva completamente il valore iniziale per evitare testo automatico
        return ''
