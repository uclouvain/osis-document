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
from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ModelSerializer


class OsisDocumentConfig(AppConfig):
    name = 'osis_document'
    verbose_name = _("Documents")

    def ready(self):
        from osis_document.contrib import FileField, FileFieldSerializer

        settings.OSIS_DOCUMENT_TOKEN_MAX_AGE = getattr(settings, 'OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15)
        settings.OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE = getattr(settings, 'OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE', 60 * 15)

        # Add FileFieldSerializer the default_serializer_mapping
        ModelSerializer.serializer_field_mapping[FileField] = FileFieldSerializer
