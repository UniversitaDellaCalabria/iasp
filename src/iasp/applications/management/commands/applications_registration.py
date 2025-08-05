import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from calls.models import CallTitulusConfiguration

from titulus_ws.models import TitulusConfiguration

from ... models import Application
from ... settings import REGISTRATION_JOB_SLEEP_TIME
from ... titulus import application_protocol
from ... utils import generate_application_merged_docs



logger = logging.getLogger(__name__)



def confirm():
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["Y", "N"]:
        answer = input("OK to push to continue [Y/N]? ").lower()
    return answer == "y"


class Command(BaseCommand):
    help = 'IASP - register all submitted applications'

    def add_arguments(self, parser):
        parser.epilog = 'Example: ./manage.py applications_registration'
        parser.add_argument('-y', required=False, action="store_true",
                            help="send all ready messages")

    def handle(self, *args, **options):
        if options['y'] or confirm():
            now = timezone.localtime()
            applications = Application.objects.filter(
                call__protocol_required=True,
                submission_date__isnull=False,
                protocol_date__isnull=True,
                protocol_taken__isnull=True
            )
            for index, application in enumerate(applications):

                if index: time.sleep(REGISTRATION_JOB_SLEEP_TIME)

                application.refresh_from_db()
                if application.protocol_taken: continue

                print(f'[{application}] - Registering application {application.pk} - {application.call.title_it}')

                application.protocol_taken = timezone.localtime()
                application.save(update_fields=['protocol_taken'])

                try:
                    generated_documents = generate_application_merged_docs(application)
                    if not generated_documents: continue

                    protocol_call_configuration = CallTitulusConfiguration.objects.filter(
                        call=application.call,
                        is_active=True
                    ).select_related('configuration').first()

                    protocol_response = application_protocol(
                        application=application,
                        user=application.user,
                        subject=application.call.title_it,
                        global_configuration=protocol_call_configuration.configuration,
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

                    logger.info(
                        "[{}] utente {} richiesta {} protocollata con successo: n. <b>{}/{}</b>".format(
                            timezone.localtime(),
                            application.user,
                            application.pk,
                            protocol_number,
                            timezone.localtime().year
                        )
                    )

                    print(f'[{application}] - Registered application {application.pk} - {application.call.title_it} COMPLETED')

                # if protocol fails
                # raise Exception and do some operations
                except Exception as e:
                    # log protocol fails
                    logger.exception(
                        "[{}] utente {} protocollo domanda {} fallito: {}".format(
                            timezone.localtime(),
                            application.user,
                            application,
                            e
                        )
                    )

                    application.protocol_taken = None
                    application.save(update_fields=['protocol_taken'])

                    print(f'[{application}] - Registered application {application.pk} - {application.call.title_it} FAILED')

                    continue

