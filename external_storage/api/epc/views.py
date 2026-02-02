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
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests
from django.conf import settings
from django.http import FileResponse
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from backoffice.settings.rest_framework.utils import CorsAllowOriginMixin
from external_storage.api.epc.serializers import StudentFilesSerializer
from external_storage.constants import EPC_EXTERNAL_STORAGE_NAME
from external_storage.exceptions import ExternalStorageAPICallTimeout, ExternalStorageAPICallException, TokenNotFound, \
    TokenExpired, FileReferenceNotFound
from external_storage.models import Token


class GetStudentFiles(APIView):
    def get(self, request, noma):
        url = f"{settings.EPC_API_BASE_URL}/students/{noma}/files"

        try:
            response = requests.get(
                url,
                headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()
            files_list = self._process_external_storage_response(response_data)
            serializer = StudentFilesSerializer(data=files_list, many=True)
            return Response(serializer.data)
        except requests.exceptions.Timeout:
            raise ExternalStorageAPICallTimeout()
        except requests.exceptions.RequestException:
            raise ExternalStorageAPICallException()

    def _process_external_storage_response(self, response_data: Dict) -> List[Dict]:
        files_list = []
        for file in response_data['files']:
            token = Token.objects.create(
                external_storage_name=EPC_EXTERNAL_STORAGE_NAME,
                metadata={
                    'path': file['path'],
                    'name': file.get('name', 'Unknown'),
                }
            )
            files_list.append({
                'token': token.token,
                'type': file['type'],
                'description': file['description'],
                'annee': file['annee'],
            })
        return files_list


class RawFileView(CorsAllowOriginMixin, APIView):
    """Get raw file from a token"""
    name = 'raw-file'
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        token = self._get_token(kwargs.get("token"))
        if not token:
            raise TokenNotFound()

        if self._is_expired(token):
            raise TokenExpired()

        return self._serve_file(request, token)

    def _get_token(self, token_str):
        return Token.objects.filter(token=token_str).first()

    def _is_expired(self, token: Token):
        return token.expires_at < datetime.now()

    def _serve_file(self, request, token: Token):
        kwargs = {}
        if request.GET.get("dl"):
            kwargs = dict(
                as_attachment=True,
                filename=token.metadata.get("name")
            )

        response = self._build_file_response(token, **kwargs)
        domain_list = getattr(settings, "OSIS_DOCUMENT_DOMAIN_LIST", [])
        if domain_list:
            response["Content-Security-Policy"] = "frame-ancestors {};".format(" ".join(domain_list))
            response["X-Frame-Options"] = ";"
        return response

    def _build_file_response(self, token: Token, **kwargs):
        file_path_str = token.metadata.get("path")
        if not file_path_str:
            raise FileReferenceNotFound()

        file_path = Path(file_path_str).resolve()
        if not file_path.is_file():
            raise FileReferenceNotFound()

        return FileResponse(
            file_path.open('rb'),
            **kwargs,
        )
