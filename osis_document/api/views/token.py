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
from rest_framework import generics
from rest_framework.schemas.openapi import AutoSchema

from osis_document.api import serializers
from osis_document.api.permissions import APIKeyPermission
from osis_document.models import Upload


class GetTokenSchema(AutoSchema):  # pragma: no cover
    def get_operation_id(self, path, method):
        if 'write' in path:
            return 'getWriteToken'
        return 'getReadToken'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class GetTokenView(generics.CreateAPIView):
    """Get a token for an upload"""
    name = 'get-token'
    serializer_class = serializers.TokenSerializer
    queryset = Upload.objects.all()
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    token_access = None
    schema = GetTokenSchema()

    def create(self, request, *args, **kwargs):
        upload = self.get_object()
        request.data['upload_id'] = upload.pk
        request.data['access'] = self.token_access
        return super().create(request, *args, **kwargs)
