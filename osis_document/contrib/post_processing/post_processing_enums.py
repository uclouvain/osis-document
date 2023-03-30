from enum import Enum

from django.utils.translation import gettext_lazy as _


class PostProcessingEnums(Enum):
    MERGE = _('Merge')
    CONVERT_IMAGE_TO_PDF = _('Convert image to pdf')
    CONVERT_TEXT_DOCUMENT_TO_PDF = _('Convert text document to pdf')
