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
import contextlib

import magic
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.functions import Now
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from .exceptions import MimeMismatch
from .enums import FileStatus, TokenAccess, PostProcessingType, PostProcessingStatus


class UploadManager(models.Manager):
    def from_token(self, token):
        queryset = self.filter(
            tokens__token=token,
            tokens__expires_at__gt=Now(),
        ).exclude(
            status=FileStatus.DELETED.name
        ).select_related('modified_upload')
        return queryset.first()


class OsisDocumentFileExtensionValidator(FileExtensionValidator):
    def __call__(self, value):
        self.allowed_extensions = getattr(settings, 'OSIS_DOCUMENT_ALLOWED_EXTENSIONS', [])
        super().__call__(value)


@deconstructible
class OsisDocumentMimeMatchValidator:
    ext_cnt_mapping = {
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'txt': 'text/plain',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'odt': 'application/vnd.oasis.opendocument.text',
        'pdf': 'application/pdf',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }

    def __call__(self, data):
        if getattr(settings, 'ENABLE_MIMETYPE_VALIDATION', False):
            extension = Path(data.name).suffix[1:].lower()
            content_type = magic.from_buffer(data.read(1024), mime=True)
            if content_type != self.ext_cnt_mapping[extension]:
                raise MimeMismatch


class Upload(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        primary_key=True,
        default=uuid.uuid4,
    )
    file = models.FileField(
        verbose_name=_("File"),
        max_length=255,
        validators=[OsisDocumentFileExtensionValidator()],
    )
    uploaded_at = models.DateTimeField(
        verbose_name=_("Uploaded at"),
        auto_now_add=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("Modified at"),
        auto_now=True,
    )
    expires_at = models.DateField(
        verbose_name=_("Expires at"),
        null=True,
        blank=True
    )
    mimetype = models.CharField(
        verbose_name=_("MIME Type"),
        max_length=255,
    )
    size = models.IntegerField(
        verbose_name=_("Size (in bytes)"),
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=255,
        choices=FileStatus.choices(),
        default=FileStatus.REQUESTED.name,
    )
    metadata = models.JSONField(
        verbose_name=_("Metadata"),
        default=dict,
    )

    objects = UploadManager()

    class Meta:
        verbose_name = _("Upload")

    def __str__(self):
        return "Upload '{}'".format(self.file.name)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        assert self.metadata.get('hash')
        super().save(force_insert, force_update, using, update_fields)

    def get_file(self, modified=False):
        if modified:
            with contextlib.suppress(Upload.modified_upload.RelatedObjectDoesNotExist):
                return self.modified_upload.file
        return self.file

    def get_hash(self, modified=False):
        if modified:
            with contextlib.suppress(Upload.modified_upload.RelatedObjectDoesNotExist):
                self.modified_upload
                return self.metadata.get('modified_hash')
        return self.metadata.get('hash')


class ModifiedUpload(models.Model):
    """
    A modified version of an upload (with annotation, rotation, ...).
    """

    upload = models.OneToOneField(
        Upload,
        verbose_name=_("Upload"),
        related_name='modified_upload',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("Modified at"),
        auto_now=True,
    )
    file = models.FileField(
        verbose_name=_("File"),
        max_length=255,
    )
    size = models.IntegerField(
        verbose_name=_("Size (in bytes)"),
    )


def default_expiration_time():
    from django.utils.timezone import now

    max_age = getattr(settings, 'OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15)
    return now() + timedelta(seconds=max_age)


class TokenManager(models.Manager):
    def writing_not_expired(self):
        return self.filter(
            access=TokenAccess.WRITE.name,
            expires_at__gt=Now(),
        ).exclude(
            upload__status=FileStatus.DELETED.name,
        )


class Token(models.Model):
    token = models.CharField(
        max_length=1024,
        verbose_name=_("Token"),
    )
    upload = models.ForeignKey(
        to='osis_document.Upload',
        verbose_name=_("Upload"),
        on_delete=models.CASCADE,
        related_name='tokens',
    )
    for_modified_upload = models.BooleanField(
        verbose_name=_("For modified upload"),
        default=False,
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires at"),
        default=default_expiration_time,
    )
    access = models.CharField(
        verbose_name=_("Access type"),
        max_length=255,
        choices=TokenAccess.choices(),
        default=TokenAccess.WRITE.name,
    )

    objects = TokenManager()

    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['token', 'expires_at'])
        ]

    def __str__(self):
        return self.token

    def __repr__(self):
        return '{self.access} token for {self.upload}'.format(self=self)


class PostProcessing(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        primary_key=True,
        default=uuid.uuid4,
    )
    input_files = models.ManyToManyField(
        to='osis_document.Upload',
        verbose_name=_("Input"),
        related_name='post_processing_input_files'
    )
    output_files = models.ManyToManyField(
        to='osis_document.Upload',
        verbose_name=_("Output"),
        related_name='post_processing_output_files',
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
    )
    type = models.CharField(
        max_length=255,
        choices=PostProcessingType.choices(),
        blank=False)


class PostProcessAsync(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        primary_key=True,
        default=uuid.uuid4,
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=255,
        choices=PostProcessingStatus.choices(),
        default=PostProcessingStatus.PENDING.name,
    )
    data = models.JSONField(
        verbose_name=_("Data Post Processing"),
        default=dict,
        blank=False,
        encoder=DjangoJSONEncoder
    )
    results = models.JSONField(
        verbose_name=_("Result Post Processing"),
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder
    )
