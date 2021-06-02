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
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import FileStatus, TokenAccess


class Upload(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        primary_key=True,
        default=uuid.uuid4,
    )
    file = models.FileField(
        verbose_name=_("File"),
    )
    uploaded_at = models.DateTimeField(
        verbose_name=_("Uploaded at"),
        auto_now_add=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("Modified at"),
        auto_now=True,
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
    metadata = JSONField(
        verbose_name=_("Metadata"),
        default=dict,
    )

    class Meta:
        verbose_name = _("Upload")


def default_expiration_time():
    from django.utils.timezone import now
    max_age = getattr(settings, 'OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15)
    return now() + timedelta(seconds=max_age)


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
