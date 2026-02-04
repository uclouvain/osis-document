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
import os

from django.apps import AppConfig
from django.conf import settings


class ExternalStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'external_storage'
    verbose_name = "External storage"

    def ready(self):
       settings.EPC_API_URL = os.environ.get('EPC_API_URL')
       settings.EPC_API_AUTHORIZATION_HEADER = os.environ.get('EPC_API_AUTHORIZATION_HEADER')
       settings.EPC_API_CALL_TIMEOUT = int(os.environ.get('EPC_API_CALL_TIMEOUT', 5))
