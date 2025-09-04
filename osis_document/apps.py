# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import os
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class OsisDocumentConfig(AppConfig):
    name = 'osis_document'
    verbose_name = _("Documents")

    def ready(self):
        settings.OSIS_DOCUMENT_API_SHARED_SECRET = os.environ.get('OSIS_DOCUMENT_API_SHARED_SECRET')
        if settings.OSIS_DOCUMENT_API_SHARED_SECRET is None:
            raise ImproperlyConfigured("You sould set OSIS_DOCUMENT_API_SHARED_SECRET")

        settings.OSIS_DOCUMENT_BASE_URL = os.environ.get('OSIS_DOCUMENT_BASE_URL')
        if settings.OSIS_DOCUMENT_BASE_URL is None:
            raise ImproperlyConfigured("You sould set OSIS_DOCUMENT_BASE_URL")

        settings.OSIS_DOCUMENT_DOMAIN_LIST = os.environ.get('OSIS_DOCUMENT_DOMAIN_LIST', '').split()
        settings.OSIS_DOCUMENT_ALLOWED_EXTENSIONS = os.environ.get(
            'OSIS_DOCUMENT_ALLOWED_EXTENSIONS',
            'pdf txt docx doc odt png jpg',
        ).split()
        settings.OSIS_DOCUMENT_UPLOAD_LIMIT = os.environ.get('OSIS_DOCUMENT_UPLOAD_LIMIT', '10/minute')
        settings.OSIS_DOCUMENT_TOKEN_MAX_AGE = os.environ.get('OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15)
        settings.OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE = os.environ.get('OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE', 60 * 15)
        settings.OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE = os.environ.get(
            'OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE',
            60 * 60 * 24 * 15,
        )
        settings.OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE = os.environ.get(
            'OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE',
            60 * 60 * 24 * 15,
        )
        settings.ENABLE_MIMETYPE_VALIDATION = os.environ.get('ENABLE_MIMETYPE_VALIDATION', False)
