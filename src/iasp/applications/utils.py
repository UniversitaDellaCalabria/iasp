import logging
import os
import pypdf
import shutil

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.urls import reverse

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

        attachments_path = os.path.join(
            settings.MEDIA_ROOT,
            f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TEMP_FOLDER_ATTACHMENTS_PATH}'
        )
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
