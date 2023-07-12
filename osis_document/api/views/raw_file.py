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
from datetime import datetime

from django.conf import settings
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus
from osis_document.exceptions import FileInfectedException
from osis_document.models import Upload, Token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView


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
    authentication_classes = []
    permission_classes = []
    schema = RawFileSchema()

    def get(self, *args, **kwargs):
        token = Token.objects.get(token=self.kwargs['token'])
        if token.expires_at < datetime.now():
            return HttpResponseRedirect(reverse('expired_token'))
        upload = Upload.objects.from_token(self.kwargs['token'])
        if not upload:
            return Response({'error': _("Resource not found")}, status.HTTP_404_NOT_FOUND)
        if upload.status == FileStatus.INFECTED.name:
            raise FileInfectedException
        with upload.file.open() as file:
            hash = hashlib.sha256(file.read()).hexdigest()
        if upload.metadata.get('hash') != hash:
            return Response({'error': _("Hash checksum mismatch")}, status.HTTP_409_CONFLICT)
        # TODO handle internal nginx redirect based on a setting
        kwargs = {}
        if self.request.GET.get('dl'):
            kwargs = dict(as_attachment=True, filename=upload.metadata.get('name'))
        response = FileResponse(upload.file.open('rb'), **kwargs)
        domain_list = getattr(settings, 'OSIS_DOCUMENT_DOMAIN_LIST', [])
        if domain_list:
            response['Content-Security-Policy'] = "frame-ancestors {};".format(' '.join(domain_list))
            response['X-Frame-Options'] = ";"
        return response
