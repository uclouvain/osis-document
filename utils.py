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
import hashlib
import sys

from django.conf import settings
from django.core import signing
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from osis_document.enums import FileStatus
from osis_document.exceptions import Md5Mismatch
from osis_document.models import Upload, Token


def confirm_upload(token):
    # Verify token existence and expiration
    token = Token.objects.writing_not_expired().filter(
        token=token,
    ).select_related('upload').first()
    if not token:
        raise FieldError(_("Token non-existent or expired"))

    # Delete token
    upload = token.upload
    token.delete()

    # Set upload as persisted and return its uuid
    if upload.status != FileStatus.UPLOADED.name:
        upload.status = FileStatus.UPLOADED.name
        upload.save()
    return upload.uuid


def get_file_url(token: str):
    # We can not use reverse because the potential prefix would be present twice
    return '{base_url}file/{token}'.format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        token=token,
    )


def get_metadata(token: str):
    upload = Upload.objects.from_token(token)
    if not upload:
        return None
    with upload.file.open() as file:
        md5 = hashlib.md5(file.read()).hexdigest()
    if upload.metadata.get('md5') != md5:
        raise Md5Mismatch()
    return {
        'size': upload.size,
        'mimetype': upload.mimetype,
        'name': upload.file.name,
        'url': get_file_url(token),
        **upload.metadata,
    }


def get_token(uuid, **kwargs):
    return Token.objects.create(
        upload_id=uuid,
        token=signing.dumps(str(uuid)),
        **kwargs
    ).token


def calculate_md5(file):
    hash_md5 = hashlib.md5()
    if isinstance(file, bytes):
        hash_md5.update(file)
    else:
        for chunk in file.chunks():
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_raw_upload(file, name, mimetype, **metadata):
    """Save a file into an Upload object with given parameters."""

    md5 = calculate_md5(file)
    upload = Upload.objects.create(
        mimetype=mimetype,
        size=sys.getsizeof(file),
        metadata={"md5": md5, **metadata},
    )
    upload.file.save(
        content=ContentFile(file),
        name=name,
        save=True,
    )
    # create a related token
    token = Token.objects.create(
        upload_id=upload.uuid,
        token=signing.dumps(str(upload.uuid)),
    )
    return token
