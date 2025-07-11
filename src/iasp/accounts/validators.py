import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_international_phone_number(value):
    try:
        parsed = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(_('Invalid phone number'))
    except phonenumbers.NumberParseException:
        raise ValidationError(_('Invalid or poorly formatted phone number'))
