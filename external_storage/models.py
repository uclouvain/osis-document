# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _


def default_expiration_time():
    from django.utils.timezone import now

    max_age = getattr(settings, 'OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15)
    return now() + timedelta(seconds=max_age)



class Token(models.Model):
    class ExternalStorageName(models.TextChoices):
        EPC = 'EPC', 'EPC'

    token = models.CharField(
        primary_key=True,
        default=uuid.uuid4,
        max_length=1024,
        verbose_name=_("Token"),
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires at"),
        default=default_expiration_time,
    )
    external_storage_name = models.CharField(
        verbose_name=_("External storage name"),
        choices=ExternalStorageName.choices,
    )
    metadata = models.JSONField(
        verbose_name=_("Metadata"),
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        indexes = [
            models.Index(fields=['token', 'external_storage_name']),
            models.Index(fields=['expires_at', 'external_storage_name'])
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(expires_at__gt=models.F('created_at')), name='valid_expiry'),
        ]

    def __str__(self):
        return self.token
