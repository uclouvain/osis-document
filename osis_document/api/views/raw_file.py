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
import hashlib
from datetime import datetime

from django.conf import settings
from django.http import FileResponse
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus
from osis_document.exceptions import FileInfectedException, TokenNotFound, TokenExpired, FileReferenceNotFound, \
    HashMismatch
from osis_document.models import Upload, Token


class RawFileSchema(AutoSchema):  # pragma: no cover
    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = {
            "description": "The raw binary file",
            "content": {"*/*": {"schema": {"type": "string", "format": "binary"}}},
        }
        return responses


class RawFileView(CorsAllowOriginMixin, APIView):
    """Get raw file from a token"""
    name = 'raw-file'
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    authentication_classes = []
    permission_classes = []
    schema = RawFileSchema()

    def get(self, request, *args, **kwargs):
        token = self._get_token(kwargs.get("token"))
        if not token:
            raise TokenNotFound()

        if self._is_expired(token):
            raise TokenExpired()

        upload = Upload.objects.from_token(token.token)
        if not upload:
            raise FileReferenceNotFound()

        if upload.status == FileStatus.INFECTED.name:
            raise FileInfectedException()

        if not self._is_valid_checksum(upload, token):
            raise HashMismatch()

        return self._serve_file(request, upload, token)

    def _get_token(self, token_str):
        return Token.objects.filter(token=token_str).first()

    def _is_expired(self, token):
        return token.expires_at < datetime.now()

    def _is_valid_checksum(self, upload, token):
        with upload.get_file(modified=token.for_modified_upload).open() as file:
            file_hash = hashlib.sha256(file.read()).hexdigest()
        return upload.get_hash(modified=token.for_modified_upload) == file_hash

    def _serve_file(self, request, upload, token):
        kwargs = {}
        if request.GET.get("dl"):
            kwargs = dict(as_attachment=True, filename=upload.metadata.get("name"))

        response = self._build_file_response(upload, token, **kwargs)
        domain_list = getattr(settings, "OSIS_DOCUMENT_DOMAIN_LIST", [])
        if domain_list:
            response["Content-Security-Policy"] = "frame-ancestors {};".format(" ".join(domain_list))
            response["X-Frame-Options"] = ";"
        return response

    def _build_file_response(self, upload, token, **kwargs):
        return FileResponse(
            upload.get_file(modified=token.for_modified_upload).open("rb"),
            **kwargs,
        )


class RawSampleFileView(RawFileView):
    def _is_valid_checksum(self, upload, token):
        if self.__is_file_exist_on_disk(upload, token):
            return super()._is_valid_checksum(upload, token)
        return True

    def _build_file_response(self, upload, token, **kwargs):
        if self.__is_file_exist_on_disk(upload, token):
            return super()._build_file_response(upload, token, **kwargs)

        from utils import get_sample_file_resolver
        file_path = get_sample_file_resolver(upload.mimetype)
        file_obj = open(file_path, 'rb')
        return FileResponse(
            file_obj,
            **kwargs
        )

    def __is_file_exist_on_disk(self, upload, token) -> bool:
        file_field = upload.get_file(modified=token.for_modified_upload)
        return file_field.storage.exists(file_field.name)
