import pypdf

from applications.models import *


def merge_attachments_pdf(application=None):
    if not application: return

    required = ApplicationInsertionRequired.objects.filter(application=application)
    free = ApplicationInsertionFree.objects.filter(application=application)

    pdfFiles = []
    for r in required:
        pdfFiles.append(r.source_teaching_attachment.path)
    for f in free:
        pdfFiles.append(f.source_teaching_attachment.path)

    try:
        pdfWriter = pypdf.PdfWriter()

        for filename in pdfFiles:
            pdfFileObj = open(filename, 'rb')
            pdfReader = pypdf.PdfReader(pdfFileObj)
            for pageNum in range(len(pdfReader.pages)):
                pageObj = pdfReader.pages[pageNum]
                pdfWriter.add_page(pageObj)

        pdfOutput = open(f'{settings.MEDIA_ROOT}/allegati/bando-{application.call.pk}/domanda-{application.pk}/allegati.pdf', 'wb')
        pdfWriter.write(pdfOutput)
        pdfOutput.close()
    except:
        return
