import logging
import magic
import os
import pypdf
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import F, Case, When, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from calls.models import *

from pathlib import Path

from titulus_ws.models import TitulusConfiguration

from weasyprint import HTML

from . decorators import *
from . forms import *
from . models import *
from . settings import *
from . titulus import application_protocol
from . utils import generate_application_merged_docs


logger = logging.getLogger('__name__')


@login_required
def applications(request):
    template = 'applications.html'
    applications = Application.objects.filter(user=request.user)
    return render(request, template, {'applications': applications})


@login_required
@application_check
def application(request, application_pk, template='application.html', application=None):
    tot_credits = application.get_credits_status()

    free_credits_rules = CallFreeCreditsRule.objects.filter(
        call=application.call,
        is_active=True
    )

    insertions_required = ApplicationInsertionRequired.objects.filter(
        application=application
    ).count()

    insertions_free = ApplicationInsertionFree.objects.filter(
        application=application
    ).count()

    # ~ template = 'application.html'

    form = PaymentForm(instance=application)

    old_payment_receipt = application.payment_receipt

    if request.method == 'POST':

        form = PaymentForm(
            instance=application,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            application = form.save(commit=False)
            application.modified_by = request.user
            application.save()

            if old_payment_receipt and old_payment_receipt != application.payment_receipt:
                old_payment_receipt.delete(save=False)

            messages.add_message(
                request,
                messages.SUCCESS,
                _('Receipt uploaded successfully')
            )

            # messaggio di successo
            return redirect(
                'applications:application',
                application_pk=application.pk
            )
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form'))
            )

    return render(
        request,
        template,
        {
            'application': application,
            'form': form,
            'free_credits_rules': free_credits_rules,
            'insertions_required': insertions_required,
            'insertions_free': insertions_free,
            'tot_credits': tot_credits or 0
        }
    )


@login_required
def application_new(request, call_pk):
    call = get_object_or_404(Call, pk=call_pk)

    # check bando attivo
    if not call.is_in_progress():
        messages.add_message(
            request,
            messages.ERROR,
            _('Unable to participate in the selected call')
        )
        return redirect('calls:calls')

    # domanda già presente per questo bando
    application = Application.objects.filter(
        user=request.user,
        call=call
    ).only('pk').first()

    if application:
        messages.add_message(
            request,
            messages.WARNING,
            _("There is already an application against you for this call")
        )
        return redirect('applications:application', application_pk=application.pk)

    requirements = CallRequirement.objects.filter(
        call=call,
        is_active=True
    )

    form = ApplicationForm(requirements=call.get_requirements())
    template = 'application_new.html'

    if request.method == 'POST':

        form = ApplicationForm(
            requirements=call.get_requirements(),
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.call = call
            application.created_by = request.user
            application.modified_by = request.user
            application.save()

            # messaggio di successo
            return redirect(
                'applications:application',
                application_pk=application.pk
            )
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form'))
            )

    return render(
        request,
        template,
        {
            'call': call,
            'form': form,
            'requirements': requirements
        }
    )


@login_required
@application_check
@application_editable
def application_edit(request, application_pk, application=None):
    form = ApplicationForm(instance=application)
    template = 'application_edit.html'

    old_home_exams_certification = application.home_exams_certification
    old_home_teaching_plan = application.home_teaching_plan
    old_home_votes_conversion = application.home_votes_conversion
    old_home_language_certification = application.home_language_certification
    old_declaration_of_value = application.declaration_of_value

    if request.method == 'POST':

        form = ApplicationForm(
            instance=application,
            data=request.POST,
            files=request.FILES
        )

        if form.is_valid():
            application = form.save(commit=False)
            application.modified_by = request.user
            application.save()

            if old_home_exams_certification and old_home_exams_certification != application.home_exams_certification:
                old_home_exams_certification.delete(save=False)
            if old_home_teaching_plan and old_home_teaching_plan != application.home_teaching_plan:
                old_home_teaching_plan.delete(save=False)
            if old_home_votes_conversion and old_home_votes_conversion != application.home_votes_conversion:
                old_home_votes_conversion.delete(save=False)
            if old_home_language_certification and old_home_language_certification != application.home_language_certification:
                old_home_language_certification.delete(save=False)
            if old_declaration_of_value and old_declaration_of_value != application.declaration_of_value:
                old_declaration_of_value.delete(save=False)

            # messaggio di successo
            messages.add_message(
                request,
                messages.SUCCESS,
                _('Data modified successfully')
            )
            return redirect(
                'applications:application',
                application_pk=application.pk
            )
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form'))
            )

    return render(
        request,
        template,
        {
            'application': application,
            'form': form,
        }
    )


@login_required
@require_POST
@application_check
@application_editable
def application_submit(request, application_pk, application=None):
    if application.get_credits_status() < application.call.credits_threshold:
        messages.add_message(
            request,
            messages.DANGER,
            '{} <b>({})</b>'.format(
                _('You have not yet reached the minimum number of required credits by the call'),
                application.call.credits_threshold
            )
        )
    elif application.call.payment_required and not application.payment_receipt:
        messages.add_message(
            request,
            messages.DANGER,
            _('It is necessary to upload the payment receipt to submit the application')
        )
    else:
        application.submission_date = timezone.localtime()
        application.save(
            update_fields=['submission_date']
        )

        # log
        logger.info(
            "[{}] utente {} ha inviato la domanda di partecipazione a {}".format(
                timezone.localtime(),
                request.user,
                application.call
            )
        )
        # end log

        messages.add_message(request, messages.SUCCESS, _('Application successfully submitted'))

        call_name = application.call.title_it if request.LANGUAGE_CODE == 'it' else application.call.title_en
        email_body=EMAIL_BODY.format(
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            call=call_name
        )
        result = send_mail(
            subject=_("Enrollment in years after the first"),
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        if application.call.protocol_required:
            try:
                generate_application_merged_docs(application)
                protocol_global_configuration = TitulusConfiguration.objects.filter(is_active=True).first()
                protocol_call_configuration = CallTitulusConfiguration.objects.filter(
                    call=application.call,
                    is_active=True
                ).first()
                protocol_response = application_protocol(
                    application=application,
                    user=request.user,
                    subject=application.call.title_it,
                    global_configuration=protocol_global_configuration,
                    call_configuration=protocol_call_configuration,
                    test=False,
                )

                protocol_number = protocol_response["numero"]

                # set protocol data in application
                application.protocol_number = protocol_number
                application.protocol_date = timezone.localtime()
                application.save(
                    update_fields=[
                        "protocol_number",
                        "protocol_date"
                    ]
                )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Request successfully registered: n. <b>{}/{}</b>").format(
                        protocol_number,
                        timezone.localtime().year
                    ),
                )

                if protocol_response.get("message"):
                    messages.add_message(
                        request, messages.INFO, protocol_response["message"]
                    )
            # if protocol fails
            # raise Exception and do some operations
            except Exception as e:
                # log protocol fails
                logger.error(
                    "[{}] utente {} protocollo domanda {} fallito: {}".format(
                        timezone.localtime(),
                        request.user,
                        application,
                        e
                    )
                )

                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Protocol error: {}").format(e),
                )

                messages.add_message(
                    request,
                    messages.INFO,
                    _(
                        "Your request was created anyway, even though registration failed. Registration will be performed automatically in the next few hours."
                    ),
                )

        # LOG
    return redirect(
        'applications:application',
        application_pk=application_pk
    )


@login_required
@require_POST
@application_check
@application_editable
def application_delete(request, application_pk, application=None):
    folder_path = f'{settings.MEDIA_ROOT}/allegati/bando-{application.call.pk}/domanda-{application.pk}'
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

    # log
    logger.info(
        "[{}] utente {} ha eliminato la domanda di partecipazione a {}".format(
            timezone.localtime(),
            request.user,
            application.call
        )
    )
    # end log

    application.delete()

    messages.add_message(request, messages.SUCCESS, _('Application successfully deleted'))
    return redirect('applications:applications')


@login_required
@application_check
def application_required_list(request, application_pk, application=None):
    insertions = application.applicationinsertionrequired_set.all()

    codes_to_exclude = CallExcludedActivity.objects.filter(
        call=application.call,
        is_active=True
    ).values_list('code', flat=True)

    codes_list = insertions.values_list('target_teaching_id', flat=True)

    declared_credits = {}
    for insertion in insertions:
        if not declared_credits.get(insertion.target_teaching_id):
            declared_credits[insertion.target_teaching_id] = [
                insertion.source_teaching_credits,
                insertion.source_teaching_credits >= insertion.target_teaching_credits
            ]
        else:
            tot = declared_credits[insertion.target_teaching_id][0] + insertion.source_teaching_credits
            declared_credits[insertion.target_teaching_id] = [
                tot,
                tot >= insertion.target_teaching_credits
            ]

    tot_credits = application.get_credits_status()

    template = 'application_required_list.html'
    return render(
        request,
        template,
        {
            'codes_to_exclude': codes_to_exclude,
            'declared_credits': declared_credits,
            'insertions': codes_list,
            'application': application,
            'tot_credits': tot_credits or 0
        }
    )


@login_required
@application_check
@activity_check
def application_required(request, application_pk, teaching_id, application=None, target_teaching={}):
    insertions = ApplicationInsertionRequired.objects.filter(
        application=application,
        target_teaching_id=teaching_id
    )

    template = 'application_required.html'
    return render(
        request,
        template,
        {
            'insertions': insertions,
            'application': application,
            'target_teaching': target_teaching
        }
    )


@login_required
@application_check
@application_editable
@activity_check
def application_required_new(request, application_pk, teaching_id, application=None, target_teaching={}):
    form = InsertionRequiredForm(
        target_teaching=target_teaching,
        application=application
    )
    template = 'application_required_form.html'

    if request.method == 'POST':
        form = InsertionRequiredForm(
            data=request.POST,
            files=request.FILES,
            target_teaching=target_teaching,
            application=application
        )
        if form.is_valid():
            insertion = form.save(commit=False)
            insertion.target_teaching_name = target_teaching['name']
            insertion.target_teaching_id = target_teaching['id']
            insertion.target_teaching_cod = target_teaching['cod']
            insertion.target_teaching_credits = target_teaching['credits']
            insertion.target_teaching_ssd = target_teaching['ssd']
            insertion.target_teaching_year = target_teaching['year']
            insertion.modified_by = request.user
            insertion.created_by = request.user
            insertion.application = application

            insertion.save()

            application.modified_by = request.user
            application.save(update_fields=['modified', 'modified_by'])

            # messaggio di successo
            return redirect('applications:application_required_list', application_pk=application_pk)
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form')))

    return render(
        request,
        template,
        {
            'application': application,
            'form': form,
            'target_teaching': target_teaching
        }
    )


@login_required
@application_check
@activity_check
def application_required_edit(request, application_pk, teaching_id, insertion_pk, application=None, target_teaching={}):
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
    template = 'application_required_form.html'

    old_attachment = insertion.source_teaching_attachment

    if request.method == 'POST':
        if not application.is_editable():
            messages.add_message(
                request,
                messages.ERROR,
                _('Unable to edit application')
            )
            return redirect('applications:application', application_pk=application_pk)

        form = InsertionRequiredForm(
            instance=insertion,
            data=request.POST,
            files=request.FILES,
            target_teaching=target_teaching,
            application=application
        )
        if form.is_valid():
            insertion = form.save(commit=False)
            insertion.modified_by = request.user
            insertion.save()

            if old_attachment and old_attachment != insertion.source_teaching_attachment:
                old_attachment.delete(save=False)

            application.modified_by = request.user
            application.save(update_fields=['modified', 'modified_by'])

            messages.add_message(
                request,
                messages.SUCCESS,
                _('Change successful')
            )

            # messaggio di successo
            return redirect(
                'applications:application_required',
                application_pk=application_pk,
                teaching_id=target_teaching['id'],
            )
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form')))

    return render(
        request,
        template,
        {
            'application': application,
            'form': form,
            'target_teaching': target_teaching
        }
    )


@login_required
@require_POST
@application_check
@application_editable
def application_required_delete(request, application_pk, insertion_pk, application=None):
    insertion = get_object_or_404(
        ApplicationInsertionRequired,
        application=application,
        pk=insertion_pk
    )

    teaching_id = insertion.target_teaching_id

    try:
        insertion.source_teaching_attachment.delete(save=False)
    except:
        pass

    insertion.delete()

    application.modified_by = request.user
    application.save(update_fields=['modified', 'modified_by'])

    return redirect(
        'applications:application_required',
        application_pk=application_pk,
        teaching_id=teaching_id
        )


@login_required
@application_check
def application_free(request, application_pk, year, application=None):
    free_credits_rule = get_object_or_404(
        CallFreeCreditsRule,
        is_active=True,
        call=application.call,
        course_year=year
    )
    insertions = ApplicationInsertionFree.objects.filter(
        application=application,
        free_credits=free_credits_rule
    )
    tot_credits = application.get_credits_status()
    template = 'application_free.html'
    return render(
        request,
        template,
        {
            'insertions': insertions,
            'free_credits_rule': free_credits_rule,
            'application': application,
            'tot_credits': tot_credits or 0
        }
    )


@login_required
@application_check
@application_editable
def application_free_new(request, application_pk, year, application=None):
    free_credits_rule = get_object_or_404(
        CallFreeCreditsRule,
        is_active=True,
        call=application.call,
        course_year=year)
    form = InsertionFreeForm(
        application=application,
        free_credits_rule=free_credits_rule
    )
    template = 'application_free_form.html'

    if request.method == 'POST':
        form = InsertionFreeForm(
            data=request.POST,
            files=request.FILES,
            application=application,
            free_credits_rule=free_credits_rule
        )
        if form.is_valid():
            insertion = form.save(commit=False)
            insertion.modified_by = request.user
            insertion.created_by = request.user
            insertion.application = application
            insertion.free_credits = free_credits_rule
            insertion.save()

            application.modified_by = request.user
            application.save(update_fields=['modified', 'modified_by'])

            # messaggio di successo
            return redirect(
                    'applications:application_free',
                    application_pk=application_pk,
                    year=year)
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form')))

    return render(
        request,
        template,
        {
            'free_credits_rule': free_credits_rule,
            'application': application,
            'form': form
        }
    )


@login_required
@application_check
def application_free_edit(request, application_pk, year, insertion_pk, application=None):
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
    template = 'application_free_form.html'

    old_attachment = insertion.source_teaching_attachment

    if request.method == 'POST':

        if not application.is_editable():
            messages.add_message(
                request,
                messages.ERROR,
                _('Unable to edit application')
            )
            return redirect('applications:application', application_pk=application_pk)

        form = InsertionFreeForm(
            instance=insertion,
            data=request.POST,
            files=request.FILES,
            application=application,
            free_credits_rule=free_credits_rule
        )
        if form.is_valid():
            insertion = form.save(commit=False)
            insertion.modified_by = request.user
            insertion.save()

            if old_attachment and old_attachment != insertion.source_teaching_attachment:
                old_attachment.delete(save=False)

            application.modified_by = request.user
            application.save(update_fields=['modified', 'modified_by'])

            # messaggio di successo
            return redirect(
                'applications:application_free',
                application_pk=application.pk,
                year=year
            )
        else:  # pragma: no cover
            messages.add_message(
                request,
                messages.ERROR,
                "<b>{}</b>: {}".format(_('Warning'), _('There are errors in the form')))

    return render(
        request,
        template,
        {
            'free_credits_rule': free_credits_rule,
            'application': application,
            'form': form
        }
    )


@login_required
@require_POST
@application_check
@application_editable
def application_free_delete(request, application_pk, insertion_pk, application=None):
    insertion = get_object_or_404(
        ApplicationInsertionFree,
        application=application,
        pk=insertion_pk
    )

    free_credits = insertion.free_credits

    try:
        insertion.source_teaching_attachment.delete(save=False)
    except:
        pass

    insertion.delete()

    application.modified_by = request.user
    application.save(update_fields=['modified', 'modified_by'])

    return redirect(
        'applications:application_free',
        application_pk=application_pk,
        year=free_credits.course_year
    )


def download_attachment(user, application_pk, field=''):
    application = get_object_or_404(
        Application,
        user=user,
        pk=application_pk
    )

    mime = magic.Magic(mime=True)
    field = getattr(application, field, None)
    if not field:
        return None
    path = field.path
    content_type = mime.from_file(path)

    if os.path.exists(path):
        with open(path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                path
            )
            return response
    return None


@login_required
def download_exams_certificate(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='home_exams_certification'
    )


@login_required
def download_teaching_plan(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='home_teaching_plan'
    )


@login_required
def download_votes_conversion(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='home_votes_conversion'
    )


@login_required
def download_language_certification(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='home_language_certification'
    )


@login_required
def download_payment_receipt(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='payment_receipt'
    )


@login_required
def download_declaration_of_value(request, application_pk):
    return download_attachment(
        user=request.user,
        application_pk=application_pk,
        field='declaration_of_value'
    )


@login_required
def download_insertion_attachment(request, application_pk, insertion_pk):
    insertion = ApplicationInsertionRequired.objects.filter(
        application__user=request.user,
        application__pk=application_pk,
        pk=insertion_pk
    ).first()

    if not insertion:
        insertion = ApplicationInsertionFree.objects.filter(
            application__user=request.user,
            application__pk=application_pk,
            pk=insertion_pk
        ).first()

    if not insertion: raise Http404

    mime = magic.Magic(mime=True)
    path = insertion.source_teaching_attachment.path
    content_type = mime.from_file(path)

    if os.path.exists(path):
        with open(path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                path
            )
            return response
    return None
