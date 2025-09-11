from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from applications.models import ApplicationInsertionFree, ApplicationInsertionRequired

from calls.models import Call

from generics.models import *


class CallCommission(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    call = models.OneToOneField(
        Call,
        on_delete=models.CASCADE,
        related_name="commission"
    )
    name = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    show_results = models.BooleanField(default=False)

    def is_in_progress(self):
        return self.is_active and self.start<=timezone.localtime() and self.end>timezone.localtime()

    def get_members(self, is_active=True):
        members = CallCommissionMember.objects.filter(commission=self)
        if is_active:
            return members.filter(is_active=True)
        return members


class CallCommissionMember(ActivableModel, CreatedModifiedBy, TimeStampedModel):
    commission = models.ForeignKey(CallCommission, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    role = models.CharField(max_length=255, default='', blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['commission', 'user'],
                name='unique_call_commission_component'
            )
        ]


class ApplicationInsertionRequiredCommissionReview(CreatedModifiedBy, TimeStampedModel):
    insertion = models.OneToOneField(
        ApplicationInsertionRequired,
        on_delete=models.PROTECT,
        related_name="review"
    )
    changed_credits = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    notes = models.TextField()


class ApplicationInsertionFreeCommissionReview(CreatedModifiedBy, TimeStampedModel):
    insertion = models.OneToOneField(
        ApplicationInsertionFree,
        on_delete=models.PROTECT,
        related_name="review"
    )
    changed_credits = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0)]
    )
    notes = models.TextField()
