import logging
import magic

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from io import BytesIO

from pathlib import Path

from titulus_ws import settings as titulus_settings

from . settings import (
    PDF_TEMP_FOLDER_PATH,
    PDF_TEMP_FOLDER_ATTACHMENTS_PATH,
    PDF_TO_MERGE_TEMP_FOLDER_PATH
)


logger = logging.getLogger(__name__)


def application_protocol(
    application,
    user,
    subject,
    global_configuration=None,
    call_configuration=None,
    test=False,
):

    # protocol class and settings from settings file
    prot_class = __import__(
        titulus_settings.PROTOCOL_CLASS,
        globals(), locals(), ["*"]
    )
    prot_utils = __import__(
        titulus_settings.PROTOCOL_UTILS,
        globals(), locals(), ["*"]
    )

    valid_conf = global_configuration and call_configuration

    # fix zeep key words issue
    subject = subject.upper()

    # attachments
    attachments_folder_path  = os.path.join(
        settings.MEDIA_ROOT,
        f'{PDF_TEMP_FOLDER_PATH}/{application.pk}/{PDF_TEMP_FOLDER_ATTACHMENTS_PATH}'
    )
    attachments = sorted(Path(attachments_folder_path).glob('*.pdf'))

    # Check only if protocol system works
    # if test and not configuration:
    if test:
        prot_url = titulus_settings.PROTOCOL_TEST_URL
        prot_login = titulus_settings.PROTOCOL_TEST_LOGIN
        prot_passw = titulus_settings.PROTOCOL_TEST_PASSW
        prot_aoo = titulus_settings.PROTOCOL_TEST_AOO
        prot_agd = titulus_settings.PROTOCOL_TEST_AGD
        prot_uo = titulus_settings.PROTOCOL_TEST_UO
        prot_uo_rpa = titulus_settings.PROTOCOL_TEST_UO_RPA
        prot_uo_rpa_username = ""
        prot_uo_rpa_matricola = ""
        prot_send_email = titulus_settings.PROTOCOL_SEND_MAIL_DEBUG
        prot_email = titulus_settings.PROTOCOL_EMAIL_DEFAULT
        prot_titolario = titulus_settings.PROTOCOL_TEST_TITOLARIO
        prot_fascicolo_num = titulus_settings.PROTOCOL_TEST_FASCICOLO
        prot_fascicolo_anno = titulus_settings.PROTOCOL_TEST_FASCICOLO_ANNO
        prot_template = titulus_settings.PROTOCOL_XML
    # for production
    elif not test and valid_conf:
        prot_url = titulus_settings.PROTOCOL_URL
        prot_login = global_configuration.username
        prot_passw = global_configuration.password
        prot_aoo = global_configuration.aoo
        prot_agd = global_configuration.agd
        prot_uo = call_configuration.uo
        prot_uo_rpa = call_configuration.uo_rpa
        prot_uo_rpa_username = call_configuration.uo_rpa_username
        prot_uo_rpa_matricola = call_configuration.uo_rpa_matricola
        prot_send_email = call_configuration.send_email
        prot_email = call_configuration.email or titulus_settings.PROTOCOL_EMAIL_DEFAULT
        prot_titolario = call_configuration.cod_titolario
        prot_fascicolo_num = call_configuration.fascicolo_numero
        prot_fascicolo_anno = call_configuration.fascicolo_anno
        prot_template = titulus_settings.PROTOCOL_XML
    # for production a custom configuration is necessary
    elif not test and not valid_conf:
        raise Exception(_("Missing XML configuration for production"))

    protocol_data = prot_utils.protocol_entrata_dict(
        oggetto=subject,
        autore="iscrizioneannisuccessivi.unical.it",
        aoo=prot_aoo,
        agd=prot_agd,
        destinatario=prot_uo_rpa,
        destinatario_username=prot_uo_rpa_username,
        destinatario_code=prot_uo_rpa_matricola,
        send_email=prot_send_email,
        uo_nome=dict(titulus_settings.UO_DICT)[prot_uo],
        uo=prot_uo,
        email_ufficio=prot_template,
        nome_mittente=user.first_name,
        cognome_mittente=user.last_name,
        cod_fis_mittente=user.taxpayer_id,
        cod_mittente=user.taxpayer_id,
        email_mittente=user.email,
        titolario="",
        cod_titolario=prot_titolario,
        num_allegati=len(attachments),
        fascicolo_num=prot_fascicolo_num,
        fascicolo_anno=prot_fascicolo_anno,
    )

    wsclient = prot_class.Protocollo(
        wsdl_url=prot_url,
        username=prot_login,
        password=prot_passw,
        template_xml_flusso=prot_template,
        **protocol_data,
    )

    logger.info(f"Protocollazione richiesta {subject}")

    # principal file
    principal_file_path = os.path.join(
        settings.MEDIA_ROOT,
        f'{PDF_TEMP_FOLDER_PATH}/{application.pk}',
        'domanda.pdf'
    )
    principal_file = open(principal_file_path, "rb")
    principal_file_response = HttpResponse(
        principal_file.read(),
        content_type=content_type
    )
    principal_file_name = principal_file.name.split('/')[-1]
    principal_file_response["Content-Disposition"] = "inline; filename=" + principal_file_name
    principal_file.close()
    principal_file_bytes = BytesIO()
    principal_file_bytes.write(principal_file_response.content)
    principal_file_bytes.seek(0)

    wsclient.aggiungi_docPrinc(
        fopen=principal_file_bytes,
        nome_doc=principal_file_name,
        tipo_doc=principal_file_name
    )
    # end principal file

    # attachments
    for attachment in attachments:
        mime = magic.Magic(mime=True)
        content_type = mime.from_file(attachment)
        f = open(attachment, "rb")
        attachment_response = HttpResponse(
            f.read(),
            content_type=content_type
        )
        attachment_name = f.name.split('/')[-1]
        attachment_response["Content-Disposition"] = "inline; filename=" + attachment_name
        f.close()
        attachment_bytes = BytesIO()
        attachment_bytes.write(attachment_response.content)
        attachment_bytes.seek(0)
        wsclient.aggiungi_allegato(
            nome=attachment_name,
            descrizione=subject,
            fopen=attachment_bytes,
            test=test
        )
    # end attachments

    wsclient.protocolla(test=test)
    assert wsclient.numero

    response = {"numero": wsclient.numero}

    if titulus_settings.FASCICOLAZIONE_SEPARATA and prot_fascicolo_num:
        try:
            fascicolo_physdoc = ""
            fascicolo_nrecord = ""
            fascicolo_numero = prot_fascicolo_num
            doc_physdoc = ""
            doc_nrecord = ""
            doc_num_prot = wsclient.numero
            doc_minuta = "no"  # si/no

            fasc = open(titulus_settings.FASCICOLO_PATH, "r").read()
            fasc = fasc.format(
                fascicolo_physdoc=fascicolo_physdoc,
                fascicolo_nrecord=fascicolo_nrecord,
                fascicolo_numero=fascicolo_numero,
                doc_physdoc=doc_physdoc,
                doc_nrecord=doc_nrecord,
                doc_num_prot=doc_num_prot,
                doc_minuta=doc_minuta,
            )
            wsclient.fascicolaDocumento(fasc)
            msg = "Collation completed: {} in {}".format(
                fascicolo_numero,
                wsclient.numero
            )

        except Exception as e:
            msg = "Collation failed: {} in {}".format(
                fascicolo_numero,
                wsclient.numero,
                e
            )
        response["message"] = msg
        logger.info(msg)

    # raise exception if wsclient hasn't a protocol number
    return response
