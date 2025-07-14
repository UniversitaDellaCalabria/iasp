from django.conf import settings


ADMIN_PATH = getattr(settings, 'ADMIN_PATH', 'admin')

PDF_FILETYPE = getattr(
    settings,
    "PDF_FILETYPE",
    ['application/pdf']
)

# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = getattr(settings, "MAX_UPLOAD_SIZE", 10485760)
