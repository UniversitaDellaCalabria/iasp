import logging
import magic
import os
import pypdf
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from applications.decorators import activity_check
from applications.forms import InsertionRequiredForm
from applications.models import *
from applications.utils import *

from calls.models import *

from django_tables2 import RequestConfig

from organizational_area.decorators import *

from pathlib import Path

from . decorators import *
from . filters import ApplicationFilter
from . settings import *
from . tables import ApplicationTable


logger = logging.getLogger(__name__)


@login_required
@is_structure_operator
def calls(request, structure_code, structure=None):
    template = 'management/calls.html'
    calls = Call.objects.filter(
        is_active=True,
        course_json_it__isnull=False
    )
    structure_calls = []
    for call in calls:
        if call.course_json_it.get('DepartmentCod', '') == structure_code:
            structure_calls.append(call)

    return render(
        request,
        template,
        {
            'structure': structure,
            'structure_calls': structure_calls
        }
    )


@login_required
@is_structure_operator
@can_manage_call
def call(request, structure_code, call_pk, structure=None, call=None):
    template = 'management/call.html'
    return render(
        request,
        template,
        {
            'structure': structure,
            'call': call
        }
    )


@login_required
@is_structure_operator
@can_manage_call
def applications(request, structure_code, call_pk, structure=None, call=None):
    template = 'management/applications.html'
    applications = Application.objects.filter(
        call=call,
        submission_date__isnull=False
    )
    f = ApplicationFilter(request.GET, queryset=applications)
    table = ApplicationTable(f.qs)
    RequestConfig(request, paginate={"per_page": APPLICATIONS_PAGINATION}).configure(table)

    return render(
        request,
        template,
        {
            'call': call,
            'filter': f,
            'structure': structure,
            'table': table
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
def application(request, structure_code, call_pk, application_pk, structure=None, call=None, application=None):
    template = 'management/application.html'
    insertions_required = ApplicationInsertionRequired.objects.filter(
        application=application
    ).count()

    free_credits_rules = CallFreeCreditsRule.objects.filter(
        call=call,
        is_active=True
    )
    insertions_free = ApplicationInsertionFree.objects.filter(
        application=application
    ).count()

    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'free_credits_rules': free_credits_rules,
            'insertions_required': insertions_required,
            'insertions_free': insertions_free,
            'structure': structure,
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
def application_required_list(request, structure_code, call_pk, application_pk, structure=None, call=None, application=None):
    template = 'management/application_required_list.html'
    application_data = get_application_required_insertions_data(application)
    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'structure': structure,
            **application_data
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
@activity_check
def application_required(request, structure_code, call_pk, application_pk, teaching_id, structure=None, call=None, application=None, target_teaching={}):
    insertions = ApplicationInsertionRequired.objects.filter(
        application=application,
        target_teaching_id=teaching_id
    )
    template = 'management/application_required.html'
    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'insertions': insertions,
            'structure': structure,
            'target_teaching': target_teaching
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
@activity_check
def application_required_detail(request, structure_code, call_pk, application_pk, teaching_id, insertion_pk, structure=None, call=None, application=None, target_teaching={}):
    template = 'management/application_required_detail.html'
    insertion = get_object_or_404(
        ApplicationInsertionRequired,
        application=application,
        pk=insertion_pk
    )

    form = InsertionRequiredForm(
        target_teaching=target_teaching,
        instance=insertion,
        application=application
    )
    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'form': form,
            'structure': structure,
            'target_teaching': target_teaching
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
def application_free(request, structure_code, call_pk, application_pk, year, structure=None, call=None, application=None):
    data = get_application_free_insertions_data(application, year)
    template = 'management/application_free.html'
    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'structure': structure,
            **data
        }
    )


@login_required
@is_structure_operator
@can_manage_call
@application_check
def application_free_detail(request, structure_code, call_pk, application_pk, year, insertion_pk, structure=None, call=None, application=None):
    free_credits_rule = get_object_or_404(
        CallFreeCreditsRule,
        is_active=True,
        call=application.call,
        course_year=year
    )

    insertion = get_object_or_404(
        ApplicationInsertionFree,
        application=application,
        pk=insertion_pk
    )

    form = InsertionFreeForm(
        instance=insertion,
        application=application,
        free_credits_rule=free_credits_rule
    )
    template = 'management/application_free_detail.html'

    return render(
        request,
        template,
        {
            'application': application,
            'call': call,
            'free_credits_rule': free_credits_rule,
            'form': form,
            'structure': structure,
        }
    )
