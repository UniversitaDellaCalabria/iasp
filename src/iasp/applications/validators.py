import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from generics.settings import MAX_UPLOAD_SIZE, PDF_FILETYPE


def validate_attachment_extension(f):
    allowed_extensions = PDF_FILETYPE
    if hasattr(f.file, "content_type"):
        content_type = f.file.content_type
        if not content_type.lower() in allowed_extensions:
            raise ValidationError(
                _("Invalid file extension: {}. Enter only {}").format(
                    content_type,
                    allowed_extensions,
                )
            )


def validate_file_size(f):
    if f.size > int(MAX_UPLOAD_SIZE):
        raise ValidationError(
            _("Excessive file size: {} bytes. Max {} bytes").format(
                f.size,
                MAX_UPLOAD_SIZE,
            )
        )
