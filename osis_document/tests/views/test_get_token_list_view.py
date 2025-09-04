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
from datetime import timedelta

from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.utils.timezone import now
from rest_framework.test import APITestCase, URLPatternsTestCase

from osis_document.enums import (
    FileStatus,
    TokenAccess,
    DocumentError,
    PostProcessingStatus,
    PostProcessingType,
    PostProcessingWanted,
)
from osis_document.tests import QueriesAssertionsMixin
from osis_document.tests.factories import (
    ImageUploadFactory,
    PdfUploadFactory,
    CorrectPDFUploadFactory,
    TextDocumentUploadFactory,
    MergePostProcessingFactory,
    ConvertPostProcessingFactory,
    PendingPostProcessingAsyncFactory,
    DonePostProcessingAsyncFactory,
    FailedPostProcessingAsyncFactory,
)


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenListViewTestCase(QueriesAssertionsMixin, APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        uploads_uuids = [str(PdfUploadFactory().pk)]
        response = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids})
        self.assertEqual(response.status_code, 403)

    def test_read_tokens(self):
        uploads_uuids = [str(PdfUploadFactory().pk), str(PdfUploadFactory().pk)]
        uploads_uuids_2 = [
            str(PdfUploadFactory().pk),
            str(PdfUploadFactory().pk),
            str(PdfUploadFactory().pk),
            str(PdfUploadFactory().pk),
        ]
        with self.assertNumQueriesLessThan(8):
            response = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids})
        with self.assertNumQueriesLessThan(16):
            response2 = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids_2})
        self.assertEqual(response.status_code, 201)
        tokens = response.json()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[uploads_uuids[0]]['access'], TokenAccess.READ.name)
        self.assertEqual(tokens[uploads_uuids[1]]['access'], TokenAccess.READ.name)

    def test_read_token_with_custom_ttl(self):
        start_time = now()
        default_ttl = 900
        uploads_uuids = [str(PdfUploadFactory().pk), str(PdfUploadFactory().pk)]
        request_data = {
            'uuids': uploads_uuids,
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
            'custom_ttl': 3600,
        }
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        tokens = response.json()
        for token in tokens:
            self.assertEqual(tokens[token]['access'], TokenAccess.READ.name)
            self.assertTrue(
                (start_time + timedelta(seconds=default_ttl))
                < datetime.fromisoformat(tokens[token]['expires_at'])
                < (now() + timedelta(seconds=request_data.get('custom_ttl')))
            )

    def test_read_tokens_with_upload_not_found(self):
        uploads_uuids = [str(uuid.uuid4())]
        response = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids})
        self.assertEqual(response.status_code, 201)
        tokens = response.json()
        self.assertEqual(len(tokens), 1)
        self.assertTrue('error' in tokens[uploads_uuids[0]])
        self.assertEqual(tokens[uploads_uuids[0]]['error']['code'], DocumentError.UPLOAD_NOT_FOUND.name)
        self.assertEqual(tokens[uploads_uuids[0]]['error']['message'], DocumentError.UPLOAD_NOT_FOUND.value)

    def test_read_tokens_with_infected_file(self):
        uploads_uuids = [str(PdfUploadFactory(status=FileStatus.INFECTED.name).pk), str(PdfUploadFactory().pk)]
        response = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids})
        self.assertEqual(response.status_code, 422)
        tokens = response.json()
        self.assertEqual(len(tokens), 2)
        self.assertTrue('error' in tokens[uploads_uuids[0]])
        self.assertEqual(tokens[uploads_uuids[0]]['error']['code'], DocumentError.INFECTED.name)
        self.assertEqual(tokens[uploads_uuids[0]]['error']['message'], DocumentError.INFECTED.value)
        self.assertIsNone(tokens[uploads_uuids[1]].get('error'))
        self.assertEqual(tokens[uploads_uuids[1]].get('upload_id'), uploads_uuids[1])


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenListViewWithAsyncPostProcessingTestCase(APITestCase, URLPatternsTestCase):
    from django.urls import path, include

    app_name = 'osis_document'
    urlpatterns = [
        path('', include('osis_document.urls', namespace="osis_document")),
    ]

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.pdf = CorrectPDFUploadFactory()
        self.text = TextDocumentUploadFactory()
        self.img = ImageUploadFactory()
        self.base_input_object = [self.pdf.uuid, self.text.uuid, self.img.uuid]
        self.action_list = [PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name]
        self.action_param_dict = {
            PostProcessingType.CONVERT.name: {},
            PostProcessingType.MERGE.name: {
                "output_filename": "a_test_merge_with_params_and_filename",
                "pages_dimension": "A4",
            },
        }
        self.convert_text = ConvertPostProcessingFactory()
        self.convert_text_output = CorrectPDFUploadFactory()
        self.convert_text.input_files.add(self.text)
        self.convert_text.output_files.add(self.convert_text_output)
        self.convert_img = ConvertPostProcessingFactory()
        self.convert_img_output = CorrectPDFUploadFactory()
        self.convert_img.input_files.add(self.img)
        self.convert_img.output_files.add(self.convert_img_output)
        self.client.raise_request_exception = False

    def test_read_token_with_pending_async_post_processing(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid],
            },
            PostProcessingType.MERGE.name: {
                "status": PostProcessingStatus.PENDING.name,
            },
        }
        PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingType.CONVERT.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIsNotNone(response.data[token_dict_key].get('upload_id'))
            self.assertIsNone(response.data[token_dict_key].get('errors'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIn(response.data[token_dict_key].get('upload_id'), [str(self.text.uuid), str(self.img.uuid)])
            self.assertIsNone(response.data[token_dict_key].get('errors'))

    def test_read_token_with_failed_async_post_processing(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid],
            },
            PostProcessingType.MERGE.name: {
                "errors": {
                    "params": "[<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>]",
                    "messages": [
                        "La valeur « [<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>] » n’est pas un UUID valide."
                    ],
                },
                "status": PostProcessingStatus.FAILED.name,
            },
        }
        FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingType.CONVERT.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIsNone(response.data[token_dict_key].get('errors'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 422)
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 422)
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIn(response.data[token_dict_key].get('upload_id'), [str(self.text.uuid), str(self.img.uuid)])
            self.assertIsNone(response.data[token_dict_key].get('errors'))

    def test_read_token_with_done_async_post_processing(self):
        merge = MergePostProcessingFactory()
        merge_output = CorrectPDFUploadFactory()
        merge.input_files.add(self.convert_text_output, self.convert_img_output)
        merge.output_files.add(merge_output)
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_img_output.uuid, self.convert_text_output.uuid],
                "post_processing_objects": [self.convert_img.uuid, self.convert_text.uuid],
            },
            PostProcessingType.MERGE.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [merge_output.uuid],
                "post_processing_objects": [merge.uuid],
            },
        }
        DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingType.CONVERT.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIsNone(response.data[token_dict_key].get('errors'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIsNone(response.data[token_dict_key].get('errors'))

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIsNone(response.data[token_dict_key].get('errors'))

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
        }
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIn(response.data[token_dict_key].get('upload_id'), [str(self.text.uuid), str(self.img.uuid)])
            self.assertIsNone(response.data[token_dict_key].get('errors'))

    def test_read_token_with_bad_upload_uuid(self):
        wanted_post_process = None
        request_data = {'uuids': [uuid.uuid4(), uuid.uuid4()], 'wanted_post_process': wanted_post_process}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        for token_dict_key in response.data:
            self.assertIsNone(response.data[token_dict_key].get('token'))
            self.assertIsNotNone(response.data[token_dict_key].get('error'))
            self.assertEqual(response.data[token_dict_key].get('error').get('code'), 'UPLOAD_NOT_FOUND')


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenListViewWithSyncPostProcessingTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.text = TextDocumentUploadFactory()
        self.img = ImageUploadFactory()
        self.action_list = [PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name]
        self.action_param_dict = {
            PostProcessingType.CONVERT.name: {},
            PostProcessingType.MERGE.name: {
                "output_filename": "a_test_merge_with_params_and_filename",
                "pages_dimension": "A4",
            },
        }
        self.convert_text = ConvertPostProcessingFactory()
        self.convert_text_output = CorrectPDFUploadFactory()
        self.convert_text.input_files.add(self.text)
        self.convert_text.output_files.add(self.convert_text_output)
        self.convert_img = ConvertPostProcessingFactory()
        self.convert_img_output = CorrectPDFUploadFactory()
        self.convert_img.input_files.add(self.img)
        self.convert_img.output_files.add(self.convert_img_output)
        self.merge = MergePostProcessingFactory()
        self.merge_output = CorrectPDFUploadFactory()
        self.merge.input_files.add(self.convert_text_output, self.convert_img_output)
        self.merge.output_files.add(self.merge_output)

    def test_read_token_with_MERGE_for_wanted_post_process(self):
        wanted_post_process = PostProcessingType.MERGE.name

        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)

    def test_read_token_with_CONVERT_for_wanted_post_process(self):
        wanted_post_process = PostProcessingType.CONVERT.name
        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))

    def test_read_token_without_wanted_post_process(self):
        wanted_post_process = None
        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)

    def test_read_token_with_ORIGINAL_for_wanted_post_process(self):
        wanted_post_process = PostProcessingWanted.ORIGINAL.name
        request_data = {'uuids': [self.text.uuid, self.img.uuid], 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIn(response.data[token_dict_key].get('upload_id'), [str(self.text.uuid), str(self.img.uuid)])
            self.assertIsNone(response.data[token_dict_key].get('error'))

    def test_read_token_with_bad_upload_uuid(self):
        wanted_post_process = None
        request_data = {'uuids': [uuid.uuid4(), uuid.uuid4()], 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        # self.assertEqual(response.status_code, 404)
        for token_dict_key in response.data:
            self.assertIsNone(response.data[token_dict_key].get('token'))
            self.assertIsNotNone(response.data[token_dict_key].get('error'))
