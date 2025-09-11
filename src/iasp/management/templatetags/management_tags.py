from django import template

from .. models import *


register = template.Library()


@register.simple_tag
def is_commission_member(user):
    return CallCommissionMember.objects.filter(
        user=user,
        is_active=True,
        commission__is_active=True
    ).exists()
