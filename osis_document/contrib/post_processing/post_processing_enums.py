from enum import Enum

from django.utils.translation import gettext_lazy as _


class PostProcessingEnums(Enum):
    MERGE_PDF = _('Merge PDF')
    CONVERT_TO_PDF = _('Convert file to pdf')
