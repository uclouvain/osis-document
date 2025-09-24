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
import datetime

from django.conf import settings
from django.core.exceptions import FieldError

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from osis_document.api import serializers
from backoffice.settings.rest_framework.permissions import APIKeyPermission
from drf_spectacular.openapi import AutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus
from osis_document.models import Upload
from osis_document.utils import calculate_hash, confirm_upload, get_token


class RequestUploadSchema(AutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.RequestUploadSerializer, serializers.RequestUploadResponseSerializer),
    }

    def get_operation_id(self):
        return 'requestUpload'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['429'] = {"description": "Too many requests", "content": {"application/json": {"schema": {}}}}
        return responses

    def get_request_body(self, path, method):
        return {
            "content": {
                "multipart/form-data": {
                    "schema": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}}
                }
            }
        }


class UploadUserThrottle(UserRateThrottle):
    def get_rate(self):
        return settings.OSIS_DOCUMENT_UPLOAD_LIMIT


class RequestUploadView(CorsAllowOriginMixin, APIView):
    """Receive a file (from VueJS) and create a temporary upload object"""

    name = 'request-upload'
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UploadUserThrottle]
    parser_classes = [MultiPartParser]
    schema = RequestUploadSchema()

    def post(self, request, *args, **kwargs):
        serializer = serializers.RequestUploadSerializer(data=request.data)
        if serializer.is_valid():
            # Process file: calculate hash and save it to db
            file = serializer.validated_data['file']
            instance = Upload(
                file=file,
                mimetype=file.content_type,
                size=file.size,
                metadata={'hash': calculate_hash(file), 'name': file.name},
            )
            instance.save()
            # Create a writing token to allow persistance
            return Response({'token': get_token(instance.uuid)}, status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status.HTTP_400_BAD_REQUEST)


class ConfirmUploadSchema(AutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.ConfirmUploadRequestSerializer, serializers.ConfirmUploadResponseSerializer),
    }

    def get_operation_id(self):
        return 'confirmUpload'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class ConfirmUploadView(CorsAllowOriginMixin, APIView):
    """Given a writing token and server-to-server request, persist the matching upload"""

    name = 'confirm-upload'
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    schema = ConfirmUploadSchema()

    def post(self, *args, **kwargs):
        try:
            input_serializer_data = serializers.ConfirmUploadRequestSerializer(
                data={
                    **self.request.data,
                }
            )
            input_serializer_data.is_valid(raise_exception=True)
            validated_data = input_serializer_data.validated_data
            uuid = confirm_upload(
                token=self.kwargs.get('token'),
                upload_to=validated_data.get('upload_to'),
                document_expiration_policy=validated_data.get('document_expiration_policy'),
                metadata=validated_data.get('metadata'),
                model_instance=validated_data.get('related_model', {}).get('instance'),
            )
        except FieldError as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)
        return Response({'uuid': uuid}, status.HTTP_201_CREATED)


class DeclareFilesAsDeletedSchema(AutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': serializers.DeclareFilesAsDeletedSerializer,
    }

    def get_operation_id(self):
        return 'declareFilesAsDeleted'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        del responses['201']
        responses['204'] = {
            'description': 'No content',
        }
        return responses

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class DeclareFilesAsDeletedView(CorsAllowOriginMixin, APIView):
    name = 'declare-files-as-deleted'
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    schema = DeclareFilesAsDeletedSchema()

    def post(self, *args, **kwargs):
        input_serializer_data = serializers.DeclareFilesAsDeletedSerializer(
            data={
                **self.request.data,
            }
        )
        input_serializer_data.is_valid(raise_exception=True)
        validated_data = input_serializer_data.validated_data

        Upload.objects.filter(uuid__in=validated_data['files']).update(
            status=FileStatus.DELETED.name,
            expires_at=datetime.date.today() + datetime.timedelta(
                seconds=settings.OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE
            ),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
