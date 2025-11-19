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
import uuid

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from osis_document.api import serializers
from backoffice.settings.rest_framework.permissions import APIKeyPermission
from drf_spectacular.openapi import AutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import DocumentError
from osis_document.models import Upload, ModifiedUpload


class UploadDuplicationSchema(AutoSchema):
    serializer_mapping = {
        'POST': serializers.UploadDuplicationSerializer,
    }

    def get_operation_id(self):
        return 'duplicateUpload'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['201'] = {
            'description': 'Association between the uuids of the original uploads and the uuids of the copies',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'additionalProperties': {
                            'oneOf': [
                                {'$ref': '#/components/schemas/Upload'},
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


class UploadDuplicationView(CorsAllowOriginMixin, CreateAPIView):
    """
    View to duplicate several uploads.
    """

    name = 'duplicate'
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    schema = UploadDuplicationSchema()

    def post(self, *args, **kwargs):
        # Check input data
        input_serializer = serializers.UploadDuplicationSerializer(data=self.request.data)
        input_serializer.is_valid(raise_exception=True)
        input_data = input_serializer.validated_data

        results = {
            upload: {'error': DocumentError.get_dict_error(DocumentError.UPLOAD_NOT_FOUND.name)}
            for upload in self.request.data['uuids']
        }

        # Get the original uploads
        uploads: QuerySet[Upload] = Upload.objects.filter(uuid__in=input_data['uuids'])

        original_upload_uuids = []

        # Copy the uploads and place the related files in the new location if specified, or in the same location if not
        for upload in uploads:
            original_upload_uuid = str(upload.uuid)
            original_upload_uuids.append(original_upload_uuid)
            upload.pk = None
            upload.uuid = uuid.uuid4()
            upload._state.adding = True

            with upload.file.open() as file:
                upload.file.save(
                    name=input_data['upload_path_by_uuid'].get(original_upload_uuid, upload.file.name),
                    content=file,
                    save=False,
                )

        duplicate_uploads = Upload.objects.bulk_create(uploads)

        duplicate_upload_by_original_uuid = {
            original_upload_uuids[index]: duplicate_upload
            for index, duplicate_upload in enumerate(duplicate_uploads)
        }

        # Copy the modified uploads and place the related files in the right location
        if input_data['with_modified_upload']:

            modified_uploads: QuerySet[ModifiedUpload] = ModifiedUpload.objects.filter(
                upload__uuid__in=input_data['uuids']
            )

            for modified_upload in modified_uploads:
                original_upload_uuid = str(modified_upload.upload_id)
                modified_upload.pk = None
                modified_upload._state.adding = True

                with modified_upload.file.open() as file:
                    modified_upload.file.save(
                        name=input_data['upload_path_by_uuid'].get(original_upload_uuid, modified_upload.file.name),
                        content=file,
                        save=False,
                    )

                modified_upload.upload = duplicate_upload_by_original_uuid[original_upload_uuid]

            ModifiedUpload.objects.bulk_create(modified_uploads)

        for original_upload_uuid, duplicate_upload in duplicate_upload_by_original_uuid.items():
            results[original_upload_uuid] = {
                'upload_id': duplicate_upload.uuid,
            }

        return Response(
            data=results,
            status=status.HTTP_201_CREATED,
        )
