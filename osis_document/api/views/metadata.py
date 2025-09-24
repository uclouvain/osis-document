# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import hashlib

from django.db.models.functions import Now
from drf_spectacular.openapi import AutoSchema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.exceptions import FileReferenceNotFound, HashMismatch
from osis_document.api import serializers
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import DocumentError, FileStatus
from osis_document.models import Token, Upload
from osis_document.utils import get_upload_metadata


class MetadataSchema(AutoSchema):  # pragma: no cover
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
        token = self.kwargs['token']
        upload = Upload.objects.from_token(token)
        if not upload:
            raise FileReferenceNotFound()

        if not self._is_valid_checksum(upload):
            raise HashMismatch()

        metadata = self._build_metadata_response(upload, token)
        return Response(metadata)

    def _is_valid_checksum(self, upload):
        with upload.file.open() as file:
            file_hash = hashlib.sha256(file.read()).hexdigest()
        return upload.get_hash() == file_hash

    def _build_metadata_response(self, upload, token):
        return get_upload_metadata(token, upload, upload.file.name)


class MetadataSampleFileView(MetadataView):
    def _is_valid_checksum(self, upload):
        if self.__is_file_exist_on_disk(upload):
            return super()._is_valid_checksum(upload)
        return True

    def _build_metadata_response(self, upload, token):
        if self.__is_file_exist_on_disk(upload):
            return super()._build_metadata_response(upload, token)

        from osis_document.utils import get_sample_file_resolver
        file_path = get_sample_file_resolver(upload.mimetype)
        filename = file_path.split('/')[-1]
        return get_upload_metadata(token, upload, filename)

    def __is_file_exist_on_disk(self, upload) -> bool:
        file_field = upload.get_file()
        return file_field.storage.exists(file_field.name)


class MetadataListSchema(AutoSchema):  # pragma: no cover
    def get_operation_id(self):
        return 'getSeveralMetadata'

    def get_request_body(self, path, method):
        self.request_media_types = self.map_parsers(path, method)
        return {
            'content': {
                ct: {
                    'schema': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'description': 'The file token',
                        },
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
                    'schema': {
                        'type': 'object',
                        'additionalProperties': {
                            'oneOf': [
                                {'$ref': '#/components/schemas/Metadata'},
                                {'$ref': '#/components/schemas/ErrorWithStatus'},
                            ],
                        },
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
        ).exclude(
            upload__status=FileStatus.DELETED.name
        ).select_related('upload')

        for token in tokens:
            metadata[token.token] = self._build_metadata_response(token)
        return Response(metadata)

    def _build_metadata_response(self, token):
        return get_upload_metadata(
            token=token.token,
            upload=token.upload,
            filename=token.upload.file.name,
        )

class MetadataSampleFileListView(MetadataListView):
    def _build_metadata_response(self, token):
        if self.__is_file_exist_on_disk(token):
            return super()._build_metadata_response(token)

        from osis_document.utils import get_sample_file_resolver
        file_path = get_sample_file_resolver(token.upload.mimetype)
        filename = file_path.split('/')[-1]
        return get_upload_metadata(
            token=token.token,
            upload=token.upload,
            filename=filename,
        )

    def __is_file_exist_on_disk(self, upload) -> bool:
        file_field = upload.get_file()
        return file_field.storage.exists(file_field.name)


class ChangeMetadataSchema(AutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.ChangeMetadataSerializer, serializers.MetadataSerializer),
    }

    def get_operation_id(self):
        return 'changeMetadata'

    def get_request_body(self, path, method):
        self.request_media_types = self.map_parsers(path, method)
        return {
            'content': {
                ct: {
                    'schema': {
                        'type': 'object',
                        'additionalProperties': True,
                    },
                }
                for ct in self.request_media_types
            }
        }

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
    # List of the metadata fields that cannot be updated through this view
    READ_ONLY_METADATA_FIELDS = [
        'hash',
    ]

    def post(self, *args, **kwargs):
        token = get_object_or_404(
            Token.objects.writing_not_expired(),
            token=self.kwargs['token'],
        )

        if any(read_only_field in self.request.data for read_only_field in self.READ_ONLY_METADATA_FIELDS):
            raise PermissionDenied

        upload = token.upload
        upload.metadata.update(self.request.data)
        upload.save()

        metadata = self._build_metadata_response(upload, token)
        return Response(metadata, status=status.HTTP_200_OK)

    def _build_metadata_response(self, upload, token):
        return get_upload_metadata(
            token=token.token,
            upload=upload,
            filename=upload.file.name,
        )


class ChangeMetadataSampleFileListView(ChangeMetadataView):
    def _build_metadata_response(self, upload, token):
        if self.__is_file_exist_on_disk(token):
            return super()._build_metadata_response(upload, token)

        from osis_document.utils import get_sample_file_resolver
        file_path = get_sample_file_resolver(token.upload.mimetype)
        filename = file_path.split('/')[-1]
        return get_upload_metadata(
            token=token.token,
            upload=upload,
            filename=filename,
        )

    def __is_file_exist_on_disk(self, upload) -> bool:
        file_field = upload.get_file()
        return file_field.storage.exists(file_field.name)
