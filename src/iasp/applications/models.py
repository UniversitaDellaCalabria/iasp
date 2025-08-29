import os
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Case, When, Sum
from django.db.models.fields.files import FileField

from calls.models import Call, CallFreeCreditsRule
from generics.models import *

from . settings import COUNTRIES
from . validators import *


# ~ CommissionLogModel = apps.get_model('management', 'ApplicationInsertionCommissionReviewLogUser')


def _attachment_path_required(instance, filename):
    # file will be uploaded to MEDIA_ROOT
    return "allegati/bando-{0}/domanda-{1}/obbligatori/{2}-anno/{3}".format(
        instance.application.call.id,
        instance.application.user.taxpayer_id,
        instance.target_teaching_year,
        filename
    )


def _attachment_path_free(instance, filename):
    # file will be uploaded to MEDIA_ROOT
    return "allegati/bando-{0}/domanda-{1}/scelta/{2}-anno/{3}".format(
        instance.application.call.id,
        instance.application.user.taxpayer_id,
        instance.free_credits.course_year,
        filename
    )


def _attachment_path_application(instance, filename):
    # file will be uploaded to MEDIA_ROOT
    return "allegati/bando-{0}/domanda-{1}/{2}".format(
        instance.call.id,
        instance.user.taxpayer_id,
        filename
    )


class Application(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    call = models.ForeignKey(Call, on_delete=models.PROTECT)
    user_country = models.CharField(
        max_length=2,
        choices=COUNTRIES,
        default="IT"
    )
    home_university = models.CharField(max_length=255)
    home_country = models.CharField(
        max_length=2,
        choices=COUNTRIES,
        default="IT"
    )
    home_city = models.CharField(max_length=255)
    home_course = models.CharField(max_length=255)
    home_exams_certification = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255
    )
    home_teaching_plan = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255
    )
    home_votes_conversion = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255,
        blank=True,
        null=True
    )
    home_language_certification = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255,
        blank=True,
        null=True
    )
    declaration_of_value = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255,
        blank=True,
        null=True
    )
    payment_receipt = models.FileField(
        upload_to=_attachment_path_application,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255,
        blank=True,
        null=True
    )
    submission_date = models.DateTimeField(blank=True, null=True)
    protocol_number = models.CharField(max_length=255, blank=True, default='')
    protocol_date = models.DateTimeField(blank=True, null=True)
    protocol_taken = models.DateTimeField(blank=True, null=True)

    def get_filefield_attributes(self):
        file_fields = []
        for field in self._meta.get_fields():
            if isinstance(field, FileField):
                file_fields.append(field.name)
        return file_fields

    def is_editable(self):
        return self.call.is_in_progress() and not self.submission_date

    def is_submittabile(self):
        if not self.is_editable():
            return False
        if self.call.payment_required and not self.payment_receipt:
            return False
        return self.get_credits_status() >= self.call.credits_threshold

    def get_credits_status(self, show_commission_review=False):
        # ~ tot_required = 0

        # ~ required_insertions = (
            # ~ ApplicationInsertionRequired.objects
            # ~ .filter(
                # ~ application=self,
                # ~ target_teaching_year__lte=self.call.credits_reference_year
            # ~ )
            # ~ .values('target_teaching_id', 'target_teaching_credits')
            # ~ .annotate(total_source_credits=Sum('source_teaching_credits'))
        # ~ )

        # ~ for req in required_insertions:
            # ~ tot_required += min(req['total_source_credits'], req['target_teaching_credits'])

        # ~ free_insertions = ApplicationInsertionFree.objects.filter(
            # ~ application=self,
            # ~ free_credits__course_year__lte=self.call.credits_reference_year,
            # ~ free_credits__is_active=True
        # ~ ).annotate(
            # ~ min_credits=Case(
                # ~ When(source_teaching_credits__lt=F('free_credits__max_value'), then=F('source_teaching_credits')),
                # ~ default=F('free_credits__max_value')
            # ~ )
        # ~ )

        tot_required = 0
        tot_free = 0

        required_insertions = (
            ApplicationInsertionRequired.objects
            .filter(
                application=self,
                target_teaching_year__lte=self.call.credits_reference_year
            )
        )

        for req in required_insertions:
            tot_required += req.get_credits(show_commission_review)

        free_insertions = ApplicationInsertionFree.objects.filter(
            application=self,
            free_credits__course_year__lte=self.call.credits_reference_year,
            free_credits__is_active=True
        )
        for free in free_insertions:
            tot_free += free.get_credits(show_commission_review)

        return tot_required + tot_free


class ApplicationInsertion(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    source_university = models.CharField(max_length=255)
    source_university_country = models.CharField(
        max_length=2,
        choices=COUNTRIES,
        default="IT"
    )
    source_university_city = models.CharField(max_length=255)
    source_degree_course = models.CharField(max_length=255)
    source_teaching_name = models.CharField(max_length=255)
    source_teaching_cod = models.CharField(max_length=255)
    source_teaching_credits = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    source_teaching_ssd = models.CharField(max_length=10, blank=True, default='')
    source_teaching_attachment = models.FileField(
        upload_to=_attachment_path_required,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ],
        max_length=255
    )
    source_teaching_url = models.URLField(max_length=200, blank=True, default='')
    source_teaching_grade = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')

    class Meta:
        abstract = True

    def get_credits(self, show_commission_reviews=False):
        if show_commission_reviews and hasattr(self, 'review'):
            return self.review.changed_credits
        return self.source_teaching_credits


class ApplicationInsertionRequired(ApplicationInsertion):
    target_teaching_name = models.CharField(max_length=255)
    target_teaching_id = models.IntegerField()
    target_teaching_cod = models.CharField(max_length=255)
    target_teaching_credits = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    target_teaching_ssd = models.CharField(max_length=10)
    target_teaching_year = models.PositiveIntegerField()

    class Meta:
        ordering = ('target_teaching_year', 'target_teaching_cod')

    def get_credits(self, show_commission_reviews=True):
        value = super().get_credits(show_commission_reviews)
        if value > self.target_teaching_credits:
            return self.target_teaching_credits
        return value


class ApplicationInsertionFree(ApplicationInsertion):
    source_teaching_attachment = models.FileField(
        upload_to=_attachment_path_free,
        validators=[
            validate_attachment_extension,
            validate_file_size
        ]
    )
    free_credits = models.ForeignKey(
        CallFreeCreditsRule,
        on_delete=models.PROTECT
    )

    def get_credits(self, show_commission_reviews=True):
        value = super().get_credits(show_commission_reviews)
        if value > self.free_credits.max_value:
            return self.free_credits.max_value
        return value
