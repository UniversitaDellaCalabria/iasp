from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _


EDITABLE_FIELDS = getattr(settings, 'EDITABLE_FIELDS', ['email', 'phone_number']) #'taxpayer_id'])
REQUIRED_FIELDS = getattr(settings, 'REQUIRED_FIELDS', ['email',])

CHANGE_EMAIL_TOKEN_LIFE = getattr(settings, 'CHANGE_EMAIL_TOKEN_LIFE', 30) # minutes

SAFE_URL_PATHS = getattr(settings, 'SAFE_URL_PATHS', [])
SAFE_URL_APPS = getattr(settings, 'SAFE_URL_APPS', ['admin', 'accounts'])

JWE_RSA_KEY_PATH = getattr(
    settings, "JWE_RSA_KEY_PATH", "certs/private.key"
)
JWE_ALG = getattr(settings, "JWE_ALG", "RSA-OAEP")
JWE_ENC = getattr(settings, "JWE_ENC", "A128CBC-HS256")
