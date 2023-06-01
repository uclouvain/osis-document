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
from django.db.models import Prefetch, Exists

from osis_document.api import serializers
from osis_document.api.permissions import APIKeyPermission
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus, DocumentError, PostProcessingStatus
from osis_document.exceptions import FileInfectedException
from osis_document.models import Upload, PostProcessing, PostProcessAsync


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
        if self.token_access == 'WRITE':
            request.data['upload_id'] = upload.pk
            request.data['access'] = self.token_access
        else:
            post_processing_check = self.check_post_processing(
                    request=request,
                    upload=upload,
                    wanted_post_process=request.data["post_process_type"]if 'post_process_type' in request.data else None
                )
            if upload.status == FileStatus.INFECTED.name:
                raise FileInfectedException
            elif post_processing_check:
                if 'data' in post_processing_check:
                    request.data['upload_id'] = post_processing_check['data']['upload_id']
                    request.data['access'] = self.token_access
                elif post_processing_check['status'] == PostProcessingStatus.PENDING.name:
                    return Response(
                        data=post_processing_check,
                        status=status.HTTP_206_PARTIAL_CONTENT,
                        headers=self.get_success_headers(data=None),
                    )
                elif post_processing_check['status'] == PostProcessingStatus.FAILED.name:
                    return Response(
                        data=post_processing_check,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        headers=self.get_success_headers(data=None),
                    )
            else:
                request.data['upload_id'] = upload.pk
                request.data['access'] = self.token_access
        return super().create(request, *args, **kwargs)

    def check_post_processing(self, request, upload, wanted_post_process=None):
        results = {}
        if PostProcessAsync.objects.filter(data__base_input__contains=request.data):
            post_processing_async_object = PostProcessAsync.objects.get(
                data__base_input__contains=request.data
            )
            if post_processing_async_object.status == PostProcessingStatus.DONE.name:
                if wanted_post_process:
                    output_post_processing_upload = Upload.objects.filter(
                        uuid__in=post_processing_async_object.results[wanted_post_process]['upload_objects']
                    )
                else:
                    output_post_processing_upload = Upload.objects.filter(
                        uuid__in=post_processing_async_object.results[-1]['upload_objects']
                    )
                results['data'].append(
                    {'upload_id': output.pk, 'access': self.token_access} for output in output_post_processing_upload
                )
            elif post_processing_async_object.status == PostProcessingStatus.PENDING.name:
                if wanted_post_process and post_processing_async_object.results[wanted_post_process] == PostProcessingStatus.DONE.name:
                    output_post_processing_upload = Upload.objects.filter(
                        uuid__in=post_processing_async_object.results[wanted_post_process]['upload_objects']
                    )
                    results['data'].append(
                        {'upload_id': output.pk, 'access': self.token_access} for output in output_post_processing_upload
                    )
                else:
                    results["status"] = PostProcessingStatus.PENDING.name
                    for action in post_processing_async_object.data['post_process_actions']:
                        results[action] = {'status': post_processing_async_object.results[action]['status']}
            elif post_processing_async_object.status == PostProcessingStatus.FAILED.name:
                results["status"] = PostProcessingStatus.FAILED.name
                results['errors'] = []
                for action in post_processing_async_object.data['post_process_actions']:
                    if "errors" in post_processing_async_object.results[action]:
                        results['errors'].append(post_processing_async_object.results[action]["errors"])
                    results[action] = {'status': post_processing_async_object.results[action]['status']}
        elif upload.post_processing_input_files.all():
            last = False
            last_post_process_found = upload.post_processing_input_files.first()
            while not last:
                intermediary_post_process = PostProcessing.objects.filter(
                    input_files=last_post_process_found.output_files.first()
                )
                if not intermediary_post_process:
                    last = True
                else:
                    last_post_process_found = intermediary_post_process.first()
            output_post_processing_upload = [object_post_processing.uuid for object_post_processing in
                                             last_post_process_found.output_files.all()]
            results['data'].append(
                {'upload_id': uuid, 'access': self.token_access} for uuid in output_post_processing_upload
            )
        else:
            return None
        return results


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
        responses['206'] = {
            'description': 'Data for unfinished asynchronous post processing',
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
        responses['500'] = {
            'description': 'Data for failed asynchronous post processing',
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

        uploads = self.get_queryset().filter(uuid__in=request.data).prefetch_related(
            Prefetch(
                'post_processing_input_files',
            ))

        data = []
        for upload in uploads:
            if 'post_process_type' in request.data:
                post_processing_check = self.check_post_processing(
                    request=request,
                    upload=upload,
                    wanted_post_process=request.data["post_process_type"]
                )
            else:
                post_processing_check = self.check_post_processing(request=request, upload=upload)
            if upload.status == FileStatus.INFECTED.name:
                results[str(upload.pk)] = {'error': DocumentError.get_dict_error(DocumentError.INFECTED.name)}
            elif post_processing_check:
                if 'data' in post_processing_check:
                    data.append(item for item in post_processing_check['data'])
                elif post_processing_check['status'] == PostProcessingStatus.PENDING.name:
                    return Response(
                        data=post_processing_check,
                        status=status.HTTP_206_PARTIAL_CONTENT,
                        headers=self.get_success_headers(data=None),
                    )
                elif post_processing_check['status'] == PostProcessingStatus.FAILED.name:
                    return Response(
                        data=post_processing_check,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        headers=self.get_success_headers(data=None),
                    )
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
