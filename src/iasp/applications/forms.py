from django import forms
from django.utils.translation import gettext_lazy as _

from . models import *
from . widgets import CustomFileWidget


class ApplicationForm(forms.ModelForm):
    accept_conditions = forms.BooleanField(
        required=True,
        label=_("I agree with what is stated in the call")
    )

    def __init__(self, *args, **kwargs):
        requirements = kwargs.pop('requirements', None)
        super().__init__(*args, **kwargs)

        if not requirements:
            self.fields.pop('accept_conditions')
        else:
            # Sposta il campo all'inizio
            # Ricrea un ordine dei campi a partire da accetta_termini
            new_fields = {'accept_conditions': self.fields['accept_conditions']}
            new_fields.update(self.fields)  # Aggiunge tutti gli altri
            self.fields = new_fields  # Sovrascrive l'ordine

        self.fields['home_exams_certification'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )
        self.fields['home_teaching_plan'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )
        self.fields['home_votes_conversion'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )
        self.fields['home_language_certification'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )
        self.fields['declaration_of_value'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )

    class Meta:
        model = Application
        fields = [
            'user_country',
            'home_university',
            'home_country',
            'home_city',
            'home_course',
            'home_exams_certification',
            'home_teaching_plan',
            'home_votes_conversion',
            'home_language_certification',
            'declaration_of_value',
        ]
        labels = {
            'user_country': _("Nationality"),
            'home_university': _("Home University"),
            'home_country': _("Home University country"),
            'home_city': _("Home University city"),
            'home_course': _("Home University course"),
            'home_exams_certification': _("Signed self-certification of taken exams"),
            'home_teaching_plan': _("Origin course study plan"),
            'home_votes_conversion': _("Official votes conversion table"),
            'home_language_certification': _("Certification of knowledge of Italian language (at least B2)"),
            'declaration_of_value': _("Declaration of value"),
        }

    def clean(self):
        cleaned_data = super().clean()

        user_country = cleaned_data.get('user_country')
        home_country = cleaned_data.get('home_country')
        home_votes_conversion = cleaned_data.get('home_votes_conversionv')
        home_language_certification = cleaned_data.get('home_language_certification')
        declaration_of_value = cleaned_data.get('declaration_of_value')

        if user_country != 'IT':
            if not home_language_certification:
                self.add_error(
                    'home_language_certification',
                     _("Mandatory for non-Italian users"))

        if home_country != 'IT':
            if not home_votes_conversion:
                self.add_error(
                    'home_votes_conversion',
                     _("Mandatory if coming from a non-Italian university"))
            if not declaration_of_value:
                self.add_error(
                    'declaration_of_value',
                     _("Mandatory if coming from a non-Italian university"))

        return cleaned_data


class InsertionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application')
        super().__init__(*args, **kwargs)
        self.fields['source_teaching_attachment'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )
        self.fields['source_university'].initial = f'{self.application.home_university}'
        if self.application.call.insertions_only_from_same_course:
            self.fields['source_university'].disabled = True
        self.fields['source_university_country'].initial = f'{self.application.home_country}'
        if self.application.call.insertions_only_from_same_course:
            self.fields['source_university_country'].disabled = True
        self.fields['source_university_city'].initial = f'{self.application.home_city}'
        if self.application.call.insertions_only_from_same_course:
            self.fields['source_university_city'].disabled = True
        self.fields['source_degree_course'].initial = f'{self.application.home_course}'
        if self.application.call.insertions_only_from_same_course:
            self.fields['source_degree_course'].disabled = True

    class Meta:
        model = ApplicationInsertion
        fields = [
            'source_university',
            'source_university_country',
            'source_university_city',
            'source_degree_course',
            'source_teaching_name',
            'source_teaching_cod',
            'source_teaching_credits',
            'source_teaching_ssd',
            'source_teaching_grade',
            'source_teaching_attachment',
            'source_teaching_url',
            'notes',
        ]
        labels = {
            'source_university': _("University"),
            'source_university_country': _("Country"),
            'source_university_city': _("City"),
            'source_degree_course': _("Degree course"),
            'source_teaching_name': _("Name"),
            'source_teaching_cod': _("Code"),
            'source_teaching_credits': _("Credits"),
            'source_teaching_ssd': _("SSD"),
            'source_teaching_attachment': _("Teaching program"),
            'source_teaching_url': _("Webpage URL"),
            'source_teaching_grade': _("Vote/outcome"),
            'notes': _("Notes"),
        }
        help_texts = {
            'source_university': _("The field is pre-filled with what was entered during the application creation phase but can be modified if the course was taken in another degree course"),
            'source_university_country': _("The field is pre-filled with what was entered during the application creation phase but can be modified if the course was taken in another degree course"),
            'source_university_city': _("The field is pre-filled with what was entered during the application creation phase but can be modified if the course was taken in another degree course"),
            'source_degree_course': _("The field is pre-filled with what was entered during the application creation phase but can be modified if the course was taken in another degree course"),
            'source_teaching_ssd': _("Mandatory if coming from an Italian university"),
        }

    def clean(self):
        cleaned_data = super().clean()
        source_teaching_ssd = cleaned_data.get('source_teaching_ssd')
        if self.application.home_country == 'IT' and not source_teaching_ssd:
            self.add_error(
                'source_teaching_ssd',
                _("Mandatory if coming from an Italian university")
            )

        return cleaned_data


class InsertionRequiredForm(InsertionForm):
    def __init__(self, *args, **kwargs):
        self.target_teaching = kwargs.pop('target_teaching')
        super().__init__(*args, **kwargs)

    class Meta(InsertionForm.Meta):
        model = ApplicationInsertionRequired

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('source_teaching_cod'):
            existent = ApplicationInsertionRequired.objects.filter(
                application=self.application,
                target_teaching_id=self.target_teaching['id'],
                source_teaching_cod=cleaned_data['source_teaching_cod']
            )

            if self.instance.pk:
                existent = existent.exclude(pk=self.instance.pk)

            if existent.exists():
                self.add_error(
                    'source_teaching_cod',
                    _('You have already entered this teaching!')
                )

        return cleaned_data


class InsertionFreeForm(InsertionForm):
    def __init__(self, *args, **kwargs):
        self.free_credits_rule = kwargs.pop('free_credits_rule')
        super().__init__(*args, **kwargs)

    class Meta(InsertionForm.Meta):
        model = ApplicationInsertionFree

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('source_teaching_cod'):
            existent = ApplicationInsertionFree.objects.filter(
                application=self.application,
                free_credits=self.free_credits_rule,
                source_teaching_cod=cleaned_data['source_teaching_cod']
            )

            if self.instance.pk:
                existent = existent.exclude(pk=self.instance.pk)

            if existent.exists():
                self.add_error(
                    'source_teaching_cod',
                    _('You have already entered this teaching!')
                )

        return cleaned_data


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_receipt'].widget = CustomFileWidget(
            instance=kwargs.get('instance', None)
        )

    class Meta:
        model = Application
        fields = [
            'payment_receipt',
        ]
        labels = {
            'payment_receipt': _("Payment receipt"),
        }
