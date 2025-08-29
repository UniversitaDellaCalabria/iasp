from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from applications.models import Application

from . models import CallCommission


def application_check(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        application = get_object_or_404(
            Application,
            call__pk=original_kwargs['call_pk'],
            pk=original_kwargs['application_pk'],
            submission_date__isnull=False
        )
        original_kwargs['application'] = application
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func


def belongs_to_a_commission(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        commissions = CallCommission.objects.filter(
            is_active=True,
            callcommissionmember__user=request.user,
            callcommissionmember__is_active=True
        )

        if not commissions.exists():
            messages.add_message(
                request,
                messages.ERROR,
                _('Access denied')
            )
            return redirect('generics:home')

        original_kwargs['commissions'] = commissions
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func



def belongs_to_commission(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        call_pk = original_kwargs['call_pk']
        commission = CallCommission.objects.filter(
            call__pk=call_pk,
            call__is_active=True,
            is_active=True,
            callcommissionmember__user=request.user,
            callcommissionmember__is_active=True
        ).select_related('call').first()

        if not commission or not commission.is_in_progress():
            messages.add_message(
                request,
                messages.ERROR,
                _('Access denied')
            )
            return redirect('generics:home')

        original_kwargs['commission'] = commission
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func
