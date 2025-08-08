from django.conf import settings


APPLICATIONS_PAGINATION = getattr(settings, 'APPLICATIONS_PAGINATION', 50)
VIEW_APPLICATIONS_OFFICE = getattr(settings, 'VIEW_APPLICATIONS_OFFICE', 'view')
