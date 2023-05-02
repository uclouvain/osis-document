# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.db.models.functions import Now
from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import DocumentError
from osis_document.models import Token
from osis_document.utils import get_metadata, get_upload_metadata


class MetadataSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'GET': serializers.MetadataSerializer,
    }

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['409'] = {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error",
                    }
                }
            },
        }
        return responses


class MetadataView(CorsAllowOriginMixin, APIView):
    """Get metadata for an upload given a token"""

    name = 'get-metadata'
    authentication_classes = []
    permission_classes = []
    schema = MetadataSchema()

    def get(self, *args, **kwargs):
        metadata = get_metadata(self.kwargs['token'])
        if not metadata:
            raise Http404
        return Response(metadata)


class MetadataListSchema(AutoSchema):  # pragma: no cover
    def get_operation_id(self, path, method):
        return 'getSeveralMetadata'

    def get_request_body(self, path, method):
        self.request_media_types = self.map_parsers(path, method)
        return {
            'content': {
                ct: {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'description': 'The file token',
                    },
                }
                for ct in self.request_media_types
            }
        }

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = {
            'description': 'The metadata of several uploads',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'type': 'string',
                    },
                    'additionalProperties': {
                        'oneOf': [
                            {'$ref': '#/components/schemas/Metadata'},
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


class MetadataListView(CorsAllowOriginMixin, APIView):
    """Get metadata of uploads whose tokens are specified"""

    name = 'get-several-metadata'
    authentication_classes = []
    permission_classes = []
    schema = MetadataListSchema()

    def post(self, *args, **kwargs):
        metadata = {
            token: {'error': DocumentError.get_dict_error(DocumentError.TOKEN_NOT_FOUND.name)}
            for token in self.request.data
        }

        tokens = Token.objects.filter(
            token__in=self.request.data,
            expires_at__gt=Now(),
        ).select_related('upload')

        for token in tokens:
            metadata[token.token] = get_upload_metadata(token=token.token, upload=token.upload)

        return Response(metadata)


class ChangeMetadataSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.ChangeMetadataSerializer, serializers.MetadataSerializer),
    }

    def get_operation_id(self, path, method):
        return 'changeMetadata'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = responses.pop('201')
        return responses


class ChangeMetadataView(CorsAllowOriginMixin, APIView):
    """Change metadata from a writing token"""

    name = 'change-metadata'
    authentication_classes = []
    permission_classes = []
    schema = ChangeMetadataSchema()

    def post(self, *args, **kwargs):
        token = get_object_or_404(
            Token.objects.writing_not_expired(),
            token=self.kwargs['token'],
        )
        upload = token.upload
        upload.metadata['name'] = self.request.data.get('name', '')
        upload.save()
        return Response(upload.metadata, status=status.HTTP_200_OK)
