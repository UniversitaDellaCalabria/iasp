from django.conf import settings


STORAGE_API_CDS = getattr(settings, 'STORAGE_API_CDS', 'https://storage.portale.unical.it/api/ricerca/cds/')

# OLD UGOV BASED
# STORAGE_API_CDS_STUDYPLANS = getattr(settings, 'STORAGE_API_CDS_STUDYPLANS', 'https://storage.portale.unical.it/api/ricerca/cds-websites-studyplans/')

# NEW GDA BASED
STORAGE_API_CDS_STUDYPLANS = getattr(settings, 'STORAGE_API_CDS_STUDYPLANS', 'https://storage.portale.unical.it/api/ricerca/studyplans/')
