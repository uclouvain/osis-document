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
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from osis_document.api import serializers
from osis_document.api.permissions import APIKeyPermission
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus, DocumentError
from osis_document.exceptions import FileInfectedException
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


class GetTokenView(CorsAllowOriginMixin, generics.CreateAPIView):
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
        if upload.status == FileStatus.INFECTED.name:
            raise FileInfectedException
        request.data['upload_id'] = upload.pk
        request.data['access'] = self.token_access
        return super().create(request, *args, **kwargs)


class GetTokenListSchema(AutoSchema):  # pragma: no cover
    def get_operation_id(self, path, method):
        return 'getReadTokenList'

    def get_request_body(self, path, method):
        self.request_media_types = self.map_parsers(path, method)
        return {
            'content': {
                ct: {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'uuid',
                        'description': 'The uuid of the persisted file upload',
                    },
                }
                for ct in self.request_media_types
            }
        }

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['201'] = {
            'description': 'The tokens of several uploads',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'type': 'string',
                    },
                    'additionalProperties': {
                        'oneOf': [
                            {'$ref': '#/components/schemas/Token'},
                            {'$ref': '#/components/schemas/ErrorWithStatus'},
                        ],
                    },
                },
            },
        }
        return responses

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class GetTokenListView(GetTokenView):
    """Get tokens for several uploads"""

    schema = GetTokenListSchema()

    def create(self, request, *args, **kwargs):
        results = {
            upload: {'error': DocumentError.get_dict_error(DocumentError.UPLOAD_NOT_FOUND.name)}
            for upload in request.data
        }

        uploads = self.get_queryset().filter(uuid__in=request.data)
        data = []

        for upload in uploads:
            if upload.status == FileStatus.INFECTED.name:
                results[str(upload.pk)] = {'error': DocumentError.get_dict_error(DocumentError.INFECTED.name)}
            else:
                data.append({'upload_id': upload.pk, 'access': self.token_access})

        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        for token in serializer.data:
            results[token['upload_id']] = token

        return Response(
            data=results,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )
