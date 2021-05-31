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
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import FieldError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from osis_document.enums import FileStatus, TokenAccess
from osis_document.models import Upload, Token


def is_uuid(value):
    if not isinstance(value, (str, uuid.UUID)):
        return False
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def confirm_upload(token):
    # Verify token existence and expiration
    token = Token.objects.filter(
        token=token,
        access=TokenAccess.WRITE.name,
    ).select_related('upload').first()
    if not token:
        raise FieldError(_("Token non-existent or expired"))
    if now() > token.expires_at:
        raise FieldError(_("Token non-existent or expired"))

    # Delete token
    upload = token.upload
    token.delete()

    # Set upload as persisted and return its uuid
    upload.status = FileStatus.UPLOADED.name
    upload.save()
    return upload.uuid


def get_metadata(token_or_uuid: str):
    if is_uuid(token_or_uuid):
        upload = Upload.objects.filter(uuid=token_or_uuid).first()
    else:
        upload = Upload.objects.filter(tokens__token=token_or_uuid).first()
    if not upload:
        return None
    return {
        'size': upload.size,
        'mimetype': upload.mimetype,
        **upload.metadata,
    }
