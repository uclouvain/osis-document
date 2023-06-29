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
from typing import Dict, List

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from django.db.models import Prefetch, QuerySet
from django.urls import reverse

from osis_document.api import serializers
from osis_document.api.permissions import APIKeyPermission
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import FileStatus, DocumentError, PostProcessingStatus, PostProcessingWanted
from osis_document.contrib.error_code import ASYNC_POST_PROCESS_FAILED
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
            if upload.status == FileStatus.INFECTED.name:
                raise FileInfectedException
            post_processing_check = self.check_post_processing(
                request=request,
                upload=upload,
                wanted_post_process=request.data.get(
                    "wanted_post_process")
            )
            status_post_processing = post_processing_check.get('status')
            if status_post_processing == PostProcessingStatus.PENDING.name:
                return Response(
                    data=post_processing_check,
                    status=status.HTTP_206_PARTIAL_CONTENT,
                    headers=self.get_success_headers(data=None),
                )
            elif status_post_processing == PostProcessingStatus.FAILED.name:
                return Response(
                    data={**post_processing_check,
                          'code': ASYNC_POST_PROCESS_FAILED},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,

                )

            upload_id = post_processing_check.get('data', {}).get('upload_id')
            request.data['upload_id'] = upload_id or upload.pk
            request.data['access'] = self.token_access
        return super().create(request, *args, **kwargs)

    def check_post_processing(
            self,
            request,
            upload: Upload,
            wanted_post_process: str = None
    ) -> Dict[str, str or Dict[str, str]] or None:
        """ Given an Upload object and a type of post-processing,
        returns a dictionary whose content depends on whether a post-processing is found and on its state."""
        results = {}
        if wanted_post_process != PostProcessingWanted.ORIGINAL.name:
            post_process_async_qs = PostProcessAsync.objects.filter(
                data__base_input__contains=request.data.get('uuid') or request.data.get('uuids')
            )
            post_process_files_qs = upload.post_processing_input_files.all()

            if post_process_async_qs.exists():
                results = self.check_post_processing_async(
                    async_qs=post_process_async_qs,
                    upload=upload,
                    wanted_post_process=wanted_post_process
                )
            elif post_process_files_qs.exists():
                results = self.check_post_processing_sync(
                    sync_qs=post_process_files_qs,
                    wanted_post_process=wanted_post_process
                )
        return results

    def check_post_processing_async(
            self,
            async_qs: QuerySet,
            upload: Upload,
            wanted_post_process: str
    ) -> Dict[str, str or Dict[str, str]]:
        """Given an Upload object and a type of post-processing and a QuerySet of PostProcessAsync,
        returns a dictionary whose content depends on its state."""
        results = {}
        post_processing_async_object = async_qs.get()
        last_post_process = post_processing_async_object.data['post_process_actions'][-1]
        post_process_results = post_processing_async_object.results[
            wanted_post_process or last_post_process]

        some_post_process_done = post_processing_async_object.status == PostProcessingStatus.DONE.name or (
                wanted_post_process and post_process_results['status'] == PostProcessingStatus.DONE.name
        )
        if some_post_process_done:
            results = {
                'data': {
                    'upload_id': self.get_output_upload_uuid_from_post_process_async_result(
                        upload=upload,
                        async_result=post_process_results
                    ),
                    'access': self.token_access},
                'status': PostProcessingStatus.DONE.name
            }

        elif post_processing_async_object.status in [
            PostProcessingStatus.PENDING.name,
            PostProcessingStatus.FAILED.name
        ]:
            results["status"] = post_processing_async_object.status
            results["links"] = reverse(
                'osis_document:get-progress-post-processing',
                kwargs={'pk': post_processing_async_object.uuid}
            )
            for action in post_processing_async_object.data['post_process_actions']:
                if post_processing_async_object.status == PostProcessingStatus.FAILED.name and "errors" in \
                        post_processing_async_object.results[action]:
                    results['errors'] = post_processing_async_object.results[action]["errors"]
                results[action] = {
                    'status': post_processing_async_object.results[action]['status']
                }
        return results

    def check_post_processing_sync(
            self,
            sync_qs: QuerySet,
            wanted_post_process: str
    ) -> Dict[str, Dict[str, str]]:
        """Given a type of post-processing and a QuerySet of PostProcessing,
        returns a dictionary whose content depends on its state."""
        last = False
        last_post_process_found = sync_qs.first()
        if last_post_process_found.type != wanted_post_process:
            while not last:
                intermediary_post_process = PostProcessing.objects.filter(
                    input_files=last_post_process_found.output_files.first()
                )
                if not intermediary_post_process.exists() or last_post_process_found.type == wanted_post_process:
                    last = True
                else:
                    last_post_process_found = intermediary_post_process.first()
        results = {
            'data': {
                'upload_id': last_post_process_found.output_files.all().first().uuid,
                'access': self.token_access
            }
        }
        return results

    @staticmethod
    def get_output_upload_uuid_from_post_process_async_result(
            upload: Upload,
            async_result: Dict[str, List[str]]
    ) -> str:
        if len(async_result['upload_objects']) == 1:
            return async_result['upload_objects'][0]
        post_processing_list = PostProcessing.objects.filter(uuid__in=async_result['post_processing_objects'])
        for post_processing in post_processing_list:
            if upload in post_processing.input_files.all():
                return post_processing.output_files.first().uuid


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
        responses['422'] = {
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
            for upload in request.data['uuids']
        }

        uploads = self.get_queryset().filter(uuid__in=request.data['uuids']).prefetch_related(
            Prefetch(
                'post_processing_input_files',
            ))

        data = []
        for upload in uploads:
            post_processing_check = self.check_post_processing(
                request=request,
                upload=upload,
                wanted_post_process=request.data.get('wanted_post_process')
            )
            status_post_processing = post_processing_check.get('status')
            if status_post_processing == PostProcessingStatus.PENDING.name:
                return Response(
                    data=post_processing_check,
                    status=status.HTTP_206_PARTIAL_CONTENT,
                    headers=self.get_success_headers(data=None),
                )
            elif status_post_processing == PostProcessingStatus.FAILED.name:
                return Response(
                    data={
                        **post_processing_check,
                        'code': ASYNC_POST_PROCESS_FAILED
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            if upload.status == FileStatus.INFECTED.name:
                results[str(upload.pk)] = {'error': DocumentError.get_dict_error(DocumentError.INFECTED.name)}
            elif post_processing_check.get('data'):
                results.pop(str(upload.pk))
                if post_processing_check['data'] not in data:
                    data.append(post_processing_check['data'])
            else:
                data.append({'upload_id': upload.pk, 'access': self.token_access})

        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        for token in serializer.data:
            results[token['upload_id']] = token

        if any(results[key].get('error') == DocumentError.get_dict_error(DocumentError.INFECTED.name) for key in results):
            return Response(
                data=results,
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                headers=self.get_success_headers(serializer.data),
            )

        return Response(
            data=results,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )
