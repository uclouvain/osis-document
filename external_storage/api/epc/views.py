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
from typing import Dict, List

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.response import Response
from rest_framework.views import APIView

from external_storage.api.epc.serializers import StudentFilesSerializer
from external_storage.constants import EPC_EXTERNAL_STORAGE_NAME
from external_storage.exceptions import ExternalStorageAPICallTimeout, ExternalStorageAPICallException
from external_storage.models import Token


class EPCStudentFilesMixin:
    @staticmethod
    def _call_student_files_api(noma: str) -> Dict:
        if settings.STUDENT_FILES_API_URL is None:
            raise ImproperlyConfigured("You should set STUDENT_FILES_API_URL")

        url = settings.STUDENT_FILES_API_URL.format(noma=noma)
        try:
            response = requests.get(
                url,
                headers={'Authorization': settings.STUDENT_FILES_API_AUTHORIZATION_HEADER},
                timeout=settings.STUDENT_FILES_API_CALL_TIMEOUT
            )
            response.raise_for_status()
            return response.json() or {}  # EPC API return null when no documents
        except requests.exceptions.Timeout:
            raise ExternalStorageAPICallTimeout()
        except requests.exceptions.RequestException:
            raise ExternalStorageAPICallException()


class GetStudentFilesCount(EPCStudentFilesMixin, APIView):
    def get(self, request, noma: str):
        response_data = self._call_student_files_api(noma)
        count = len(response_data.get('fichierDocumentDescription', []))
        return Response({'count': count})


class GetStudentFiles(EPCStudentFilesMixin, APIView):
    def get(self, request, noma: str):
        response_data = self._call_student_files_api(noma)
        files_list = self._process_external_storage_response(response_data)
        serializer = StudentFilesSerializer(data=files_list, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def _process_external_storage_response(self, response_data: Dict) -> List[Dict]:
        files_list = []
        for file in response_data.get('fichierDocumentDescription') or []:
            token = Token.objects.create(
                external_storage_name=EPC_EXTERNAL_STORAGE_NAME,
                metadata={
                    'path': f"{file['cheminAbsolu']}{file['nomFichier']}",
                    'name': file.get('nom', 'Unknown'),
                    'external_storage_id': file['id'],
                }
            )
            validated_data = {
                'token': token.token,
                'nom': file['nom'],
                'description': file.get('description', ''),
                'description_detaillee': file.get('descriptionDetaillee', ''),
                'type_contenu': file.get('typeContenu', ''),
            }
            if file.get('anac'):
                validated_data['annee'] = file['anac']
            files_list.append(validated_data)
        return files_list
