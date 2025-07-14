import requests
import sys

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from generics.models import *

from titulus_ws import settings as titulus_settings
from titulus_ws.models import TitulusConfiguration

from . settings import STORAGE_API_CDS, STORAGE_API_CDS_STUDYPLANS


_protocol_titolario_list = titulus_settings.TITOLARIO_DICT
_protocol_uo_list = titulus_settings.UO_DICT
if 'makemigrations' in sys.argv or 'migrate' in sys.argv: # pragma: no cover
    _protocol_titolario_list = [('', '-')]
    _protocol_uo_list = [('', '-')]



class Call(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    title_it = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)
    course_cod = models.CharField(max_length=10)
    course_cohort = models.IntegerField(
        validators=[
            MinValueValidator(2015),
            MaxValueValidator(2200)
        ]
    )
    course_year = models.PositiveIntegerField(default=1)
    places_available = models.PositiveIntegerField(default=1)
    credits_threshold = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    credits_reference_year = models.PositiveIntegerField()
    study_plan_cod = models.CharField(max_length=10)
    payment_required = models.BooleanField(default=False)
    payment_url = models.URLField(max_length=200, blank=True, default='')
    protocol_required = models.BooleanField(default=False)
    start = models.DateTimeField()
    end = models.DateTimeField()
    notes_it = models.TextField(blank=True, default='')
    notes_en = models.TextField(blank=True, default='')
    course_json_it = models.JSONField(blank=True, null=True)
    course_json_en = models.JSONField(blank=True, null=True)
    course_studyplans_json_it = models.JSONField(blank=True, null=True)
    course_studyplans_json_en = models.JSONField(blank=True, null=True)
    ordering = models.IntegerField(default=10)

    class Meta:
        ordering = ('ordering',)

    def __str__(self):
        return f'{self.title_it}'

    def save(self, *args, **kwargs):
        if self.payment_required and not self.payment_url:
            raise ValidationError(_("If payment is required you must specify a URL pointing to this"))

        old = None
        if self.pk:
            old = Call.objects.get(pk=self.pk)

        critical_data_changed = not old or (old.course_cod != self.course_cod or old.course_cohort != self.course_cohort)

        if not self.course_json_it or critical_data_changed:
            try:
                data_it = requests.get(f"{STORAGE_API_CDS}?lang=it&cdscod={self.course_cod}&academicyear={self.course_cohort}&format=json", timeout=10000).json()['results'][0]
                data_en = requests.get(f"{STORAGE_API_CDS}?lang=en&cdscod={self.course_cod}&academicyear={self.course_cohort}&format=json", timeout=10000).json()['results'][0]
            except:
                data_it = {}
                data_en = {}
            self.course_json_it = data_it
            self.course_json_en = data_en

        if not self.course_studyplans_json_it or critical_data_changed:
            try:
                plans_it = requests.get(f"{STORAGE_API_CDS_STUDYPLANS}?lang=it&cds_cod={self.course_cod}&year={self.course_cohort}&format=json", timeout=10000).json()['results']
                plans_en = requests.get(f"{STORAGE_API_CDS_STUDYPLANS}?lang=en&cds_cod={self.course_cod}&year={self.course_cohort}&format=json", timeout=10000).json()['results']
            except:
                plans_it = {}
                plans_en = {}
            self.course_studyplans_json_it = plans_it
            self.course_studyplans_json_en = plans_en
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(
            is_active=True,
            start__lte=timezone.localtime(),
            end__gt=timezone.localtime()
        )

    def is_in_progress(self):
        return self.is_active and self.start<=timezone.localtime() and self.end>timezone.localtime()

    def get_requirements(self):
        return CallRequirement.objects.filter(call=self, is_active=True)

    def get_teaching_data(self, teaching_id, lang="it"):
        data = self.course_studyplans_json_en if lang == "en" else self.course_studyplans_json_it
        if not data: return {}
        result = {}
        for plan in data[0]['PlanTabs']:
            if plan['PlanTabCod'].upper() == self.study_plan_cod.upper():
                for group in plan['AfRequired']:
                    for teaching in group['Required']:
                        if teaching['AfId'] == teaching_id:
                            result['name'] = teaching['AfDescription']
                            result['id'] = teaching['AfId']
                            result['cod'] = teaching['AfCod']
                            result['credits'] = teaching['CreditValue']
                            result['ssd'] = teaching['SettCod']
                            result['year'] = group['Year']
                            result['modules'] = True if teaching['AfSubModules'] else False
                            return result
                        for module in teaching['AfSubModules']:
                            if module['StudyActivityID'] == teaching_id:
                                result['name'] = module['StudyActivityName']
                                result['id'] = module['StudyActivityID']
                                result['cod'] = module['StudyActivityCod']
                                result['credits'] = module['StudyActivityCreditValue']
                                result['ssd'] = module['StudyActivitySettCod']
                                result['year'] = group['Year']
                                result['modules'] = False
                                return result
        return {}


class CallExcludedActivity(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    call = models.ForeignKey(Call, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['call', 'code'],
                name='unique_call_excluded_activity_code'
            )
        ]


class CallRequirement(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    call = models.ForeignKey(Call, on_delete=models.CASCADE)
    title_it = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)
    content_it = models.TextField()
    content_en = models.TextField()


class CallFreeCreditsRule(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    call = models.ForeignKey(Call, on_delete=models.CASCADE)
    course_year = models.PositiveIntegerField(default=1)
    min_value = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    max_value = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['call', 'course_year'],
                name='unique_call_free_credits_rule'
            )
        ]


class CallTitulusConfiguration(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    call = models.ForeignKey(Call, on_delete=models.CASCADE)
    configuration = models.ForeignKey(TitulusConfiguration, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    uo = models.CharField("UO", max_length=12, choices=_protocol_uo_list)
    uo_rpa = models.CharField(
        "RPA", max_length=255, default="", blank=True, help_text=_("Nominativo RPA")
    )
    uo_rpa_username = models.CharField(
        "RPA username",
        max_length=255,
        default="",
        blank=True,
        help_text=_("Username RPA sul sistema di protocollo"),
    )
    uo_rpa_matricola = models.CharField(
        "RPA matricola",
        max_length=255,
        default="",
        blank=True,
        help_text=_("Matricola RPA sul sistema di protocollo"),
    )
    send_email = models.BooleanField(
        _("Invia e-mail a RPA"), default=True)
    email = models.EmailField(
        "E-mail",
        max_length=255,
        blank=True,
        null=True,
        help_text=f"default: {titulus_settings.PROTOCOL_EMAIL_DEFAULT}",
    )
    cod_titolario = models.CharField(
        _("Codice titolario"), max_length=12, choices=_protocol_titolario_list
    )
    fascicolo_numero = models.CharField(
        _("Fascicolo numero"), max_length=255, default="", blank=True
    )
    fascicolo_anno = models.IntegerField(
        _("Fascicolo anno"), null=True, blank=True
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Configurazione WS Protocollo Categoria")
        verbose_name_plural = _("Configurazioni WS Protocollo Categorie")

    def disable_other_configurations(self):
        others = CallTitulusConfiguration.objects.filter(
            call=self.call
        ).exclude(pk=self.pk)
        for other in others:
            other.is_active = False
            other.save(update_fields=["is_active", "modified"])

    def __str__(self):
        return "{} - {}".format(self.name, self.call)
