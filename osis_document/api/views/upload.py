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
from django.conf import settings
from django.core.exceptions import FieldError
from django.forms import modelform_factory
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.api.permissions import APIKeyPermission
from osis_document.models import Upload
from osis_document.utils import calculate_md5, confirm_upload, get_token


class RequestUploadSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (None, serializers.RequestUploadResponseSerializer),
    }

    def get_operation_id(self, path, method):
        return 'requestUpload'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['429'] = {
            "description": "Too many requests",
            "content": {
                "application/json": {
                    "schema": {}
                }
            }
        }
        return responses

    def get_request_body(self, path, method):
        return {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary"
                            }
                        }
                    }
                }
            }
        }


class UploadUserThrottle(UserRateThrottle):
    def get_rate(self):
        return getattr(settings, 'OSIS_DOCUMENT_UPLOAD_LIMIT', '10/minute')


class RequestUploadView(APIView):
    """Receive a file (from VueJS) and create a temporary upload object"""
    name = 'request-upload'
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UploadUserThrottle]
    http_method_names = ['post']
    parser_classes = [MultiPartParser]
    schema = RequestUploadSchema()

    def post(self, *args, **kwargs):
        # Check that the sent data is ok
        form = modelform_factory(Upload, fields=['file'])(self.request.POST, self.request.FILES)
        if form.is_valid():
            # Process file: calculate md5 and save it to db
            file = self.request.FILES['file']
            md5 = calculate_md5(file)
            instance = Upload(
                file=file,
                mimetype=file.content_type,
                size=file.size,
                metadata={'md5': md5},
            )
            instance.save()

            # Create a write token to allow persistance
            return Response({'token': get_token(instance.uuid)}, status.HTTP_201_CREATED)
        return Response({'error': form.errors}, status.HTTP_400_BAD_REQUEST)


class ConfirmUploadSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (None, serializers.ConfirmUploadResponseSerializer),
    }

    def get_operation_id(self, path, method):
        return 'confirmUpload'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class ConfirmUploadView(APIView):
    """Given a writing token and server-to-server request, persist the matching upload"""
    name = 'confirm-upload'
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    http_method_names = ['post']
    schema = ConfirmUploadSchema()

    def post(self, *args, **kwargs):
        try:
            uuid = confirm_upload(self.kwargs['token'])
        except FieldError as e:
            return Response({
                'error': str(e)
            }, status.HTTP_400_BAD_REQUEST)
        return Response({'uuid': uuid}, status.HTTP_201_CREATED)
