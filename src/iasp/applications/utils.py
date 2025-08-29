import logging
import os
import pypdf
import shutil

from django.conf import settings
from django.contrib.staticfiles import finders
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse

from calls.models import CallExcludedActivity, CallFreeCreditsRule

from management.models import *
from management.settings import VIEW_APPLICATIONS_OFFICE

from organizational_area.models import OrganizationalStructureOfficeEmployee

from pathlib import Path

from weasyprint import CSS, HTML

from . forms import InsertionFreeForm, InsertionRequiredForm
from . models import ApplicationInsertionFree, ApplicationInsertionRequired
from . settings import (
    PDF_TEMP_FOLDER_PATH,
    PDF_TEMP_FOLDER_ATTACHMENTS_PATH,
    PDF_TO_MERGE_TEMP_FOLDER_PATH
)


logger = logging.getLogger(__name__)


def generate_application_pdf(application):
    template = get_template('print/application.html')
    context = {
        'application': application,
    }
    html = template.render(context)

    application_folder_path = os.path.join(
        settings.MEDIA_ROOT,
        f'{PDF_TEMP_FOLDER_PATH}/{application.pk}'
    )
    if os.path.isdir(application_folder_path):
        shutil.rmtree(application_folder_path)

    os.makedirs(application_folder_path, exist_ok=True)
    file_path = os.path.join(application_folder_path, 'domanda.pdf')

    css_italia_path = finders.find('css/bootstrap-italia.min.css')  # percorso reale sul disco
    css_italia = CSS(filename=css_italia_path)
    # ~ css_unical_path = finders.find('css/unical-style.css')  # percorso reale sul disco
    # ~ css_unical = CSS(filename=css_unical_path)
    HTML(string=html).write_pdf(file_path, stylesheets=[css_italia]) #, css_unical])


def get_application_attachments(application):
    attachments = application.get_filefield_attributes()
    for attachment in attachments:
        attachment_file = getattr(application, attachment)
        if not attachment_file: continue

        folder_path = os.path.join(
            settings.MEDIA_ROOT,
            f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TEMP_FOLDER_ATTACHMENTS_PATH}'
        )
        os.makedirs(folder_path, exist_ok=True)

        attachment_source = getattr(application, attachment).path
        attachment_destination = os.path.join(
            folder_path,
            f'{attachment}.pdf'
        )
        shutil.copyfile(attachment_source, attachment_destination)


def generate_required_insertion_pdf(application):
    css_italia_path = finders.find('css/bootstrap-italia.min.css')  # percorso reale sul disco
    css_italia = CSS(filename=css_italia_path)

    for insertion in application.applicationinsertionrequired_set.all():
        target_teaching = application.call.get_teaching_data(
            insertion.target_teaching_id
        )
        form = InsertionRequiredForm(
            target_teaching=target_teaching,
            instance=insertion,
            application=application
        )

        template = get_template('print/application_required_form.html')
        context = {
            'application': application,
            'form': form,
            'target_teaching': target_teaching
        }
        html = template.render(context)

        folder_path = os.path.join(
            settings.MEDIA_ROOT,
            f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TO_MERGE_TEMP_FOLDER_PATH}'
        )
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f'required-{insertion.pk:03d}-a.pdf')

        HTML(string=html).write_pdf(file_path, stylesheets=[css_italia])

        attachment_source = insertion.source_teaching_attachment.path
        attachment_destination = os.path.join(
            folder_path,
            f'required-{insertion.pk:03d}-file.pdf'
        )
        shutil.copyfile(attachment_source, attachment_destination)


def generate_free_insertion_pdf(application):
    css_italia_path = finders.find('css/bootstrap-italia.min.css')  # percorso reale sul disco
    css_italia = CSS(filename=css_italia_path)

    for insertion in application.applicationinsertionfree_set.all():
        form = InsertionFreeForm(
            instance=insertion,
            application=application,
            free_credits_rule=insertion.free_credits
        )
        template = get_template('print/application_free_form.html')
        context = {
            'free_credits_rule': insertion.free_credits,
            'application': application,
            'form': form
        }
        html = template.render(context)

        folder_path = os.path.join(
            settings.MEDIA_ROOT,
            f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TO_MERGE_TEMP_FOLDER_PATH}'
        )
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f'zfree-{insertion.pk:03d}-a.pdf')

        HTML(string=html).write_pdf(file_path, stylesheets=[css_italia])

        attachment_source = insertion.source_teaching_attachment.path
        attachment_destination = os.path.join(
            folder_path,
            f'zfree-{insertion.pk:03d}-file.pdf'
        )
        shutil.copyfile(attachment_source, attachment_destination)


def generate_application_docs(application):
    generate_application_pdf(application)
    get_application_attachments(application)
    generate_required_insertion_pdf(application)
    generate_free_insertion_pdf(application)


def generate_application_merged_docs(application):
    attachments_path = os.path.join(
        settings.MEDIA_ROOT,
        f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TEMP_FOLDER_ATTACHMENTS_PATH}'
    )

    if os.path.isdir(attachments_path):
        return True

    try:
        generate_application_docs(application)
        merge_folder = os.path.join(
            settings.MEDIA_ROOT,
            f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TO_MERGE_TEMP_FOLDER_PATH}'
        )
        pdfWriter = pypdf.PdfWriter()
        # Filtra solo i file .pdf nella cartella
        pdf_files = sorted(Path(merge_folder).glob('*.pdf'))
        for pdf_file in pdf_files:
            with open(pdf_file, 'rb') as pdfFileObj:
                pdfReader = pypdf.PdfReader(pdfFileObj)
                for page in pdfReader.pages:
                    pdfWriter.add_page(page)

        os.makedirs(attachments_path, exist_ok=True)

        output_path = os.path.join(
            attachments_path,
            f'inserimenti.pdf'
        )
        with open(output_path, 'wb') as pdfOutput:
            pdfWriter.write(pdfOutput)
        return True
    except Exception as e:
        logger.exception(e)
        return False


def get_application_required_insertions_data(application, show_commission_review=False):
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
                insertion.source_teaching_credits >= insertion.target_teaching_credits,
                insertion.review.changed_credits if hasattr(insertion, 'review') else insertion.source_teaching_credits,
                insertion.review.changed_credits >= insertion.target_teaching_credits if hasattr(insertion, 'review') else insertion.source_teaching_credits >= insertion.target_teaching_credits,
            ]
        else:
            tot = declared_credits[insertion.target_teaching_id][0] + insertion.source_teaching_credits
            tot_review = declared_credits[insertion.target_teaching_id][2] + (insertion.review.changed_credits if hasattr(insertion, 'review') else insertion.source_teaching_credits)
            declared_credits[insertion.target_teaching_id] = [
                tot,
                tot >= insertion.target_teaching_credits,
                tot_review,
                tot_review >= insertion.target_teaching_credits
            ]
    tot_credits = application.get_credits_status(show_commission_review)
    return {
        'codes_to_exclude': codes_to_exclude,
        'declared_credits': declared_credits,
        'insertions': codes_list,
        'tot_credits': tot_credits or 0
    }


def get_application_free_insertions_data(application, year, show_commission_review=False):
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

    tot_credits = application.get_credits_status(show_commission_review)
    return {
        'free_credits_rule': free_credits_rule,
        'insertions': insertions,
        'tot_credits': tot_credits or 0
    }


def has_permission_to_download(user, application):
    if application.user == user:
        return True
    elif user.is_superuser and application.submission_date:
        return True
    elif application.call.course_json_it.get('DepartmentCod', '') and application.submission_date:
        is_employee = OrganizationalStructureOfficeEmployee.objects.filter(
            office__organizational_structure__unique_code=application.call.course_json_it['DepartmentCod'],
            office__organizational_structure__is_active=True,
            office__name=VIEW_APPLICATIONS_OFFICE,
            office__is_active=True,
            employee=user
        ).exists()
        if is_employee:
            return True
    if CallCommission.objects.filter(
        call__pk=application.call_id,
        call__is_active=True,
        is_active=True,
        callcommissionmember__user=user,
        callcommissionmember__is_active=True
    ).exists():
        return True
    return False
