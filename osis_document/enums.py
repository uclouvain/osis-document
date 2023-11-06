# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from enum import Enum
from typing import Dict

from django.utils.translation import gettext_lazy as _


class ChoiceEnum(Enum):
    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def choices(cls):
        return tuple((x.name, x.value) for x in cls)

    @classmethod
    def get_value(cls, key):
        return getattr(cls, key, key).value if hasattr(cls, key) else key

    @classmethod
    def get_names(cls):
        return [x.name for x in cls]

    @classmethod
    def get_values(cls):
        return [x.value for x in cls]

    def __deepcopy__(self, memodict: Dict = None) -> 'ChoiceEnum':
        return self


class FileStatus(ChoiceEnum):
    REQUESTED = _('Requested')
    UPLOADED = _('Uploaded')
    INFECTED = _('Infected')


class TokenAccess(ChoiceEnum):
    READ = _('Read')
    WRITE = _('Write')


class DocumentError(ChoiceEnum):
    INFECTED = _('File is flagged as infected')
    HASH_MISMATCH = _('Hash check failed')
    MIME_MISMATCH = _('MIME type mismatch')
    TOKEN_NOT_FOUND = _('Token not found')
    UPLOAD_NOT_FOUND = _('Upload not found')

    @classmethod
    def get_dict_error(cls, key):
        return {
            'code': key,
            'message': cls.get_value(key),
        }


class PostProcessingType(ChoiceEnum):
    MERGE = _('Merge')
    CONVERT = _('Convert')


class PostProcessingWanted(ChoiceEnum):
    MERGE = _('Merge')
    CONVERT = _('Convert')
    ORIGINAL = _('Original')


class PostProcessingStatus(ChoiceEnum):
    PENDING = _('Pending')
    FAILED = _('Failed')
    DONE = _('Done')


class PageFormatEnums(Enum):
    A3 = _('A3')
    A4 = _('A4')
    A5 = _('A5')


class DocumentExpirationPolicy(ChoiceEnum):
    NO_EXPIRATION = None
    EXPORT_EXPIRATION_POLICY = "EXPORT_EXPIRATION_POLICY"

    @classmethod
    def compute_expiration_date(cls, expiration_policy_value: str):
        if expiration_policy_value == cls.NO_EXPIRATION.value:
            return None
        elif expiration_policy_value == cls.EXPORT_EXPIRATION_POLICY.value:
            return datetime.date.today() + datetime.timedelta(
                seconds=settings.OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE
            )
