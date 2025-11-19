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

from osis_document.enums import FileStatus, TokenAccess, PostProcessingStatus, PostProcessingType, PostProcessingWanted
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


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenViewTestCase(APITestCase, URLPatternsTestCase):
    from django.urls import path, include
    from django.views.generic.base import RedirectView

    app_name = 'osis_document'
    urlpatterns = [
        path('', include('osis_document.urls', namespace="osis_document")),
        path('home/', RedirectView.as_view(), name="home"),
        path("accounts/", include("django.contrib.auth.urls")),
    ]

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        response = self.client.post(
            reverse(
                'osis_document:write-token',
                kwargs={
                    'pk': PdfUploadFactory().pk,
                },
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_write_token(self):
        response = self.client.post(
            reverse(
                'osis_document:write-token',
                kwargs={
                    'pk': PdfUploadFactory().pk,
                },
            )
        )
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.WRITE.name)

    def test_read_token(self):
        upload = PdfUploadFactory()
        request_data = {
            'uuid': upload.uuid,
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
            'expires_at': datetime(2021, 6, 10),
        }
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': upload.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertEqual(token['expires_at'], "2021-06-10T00:00:00")

    def test_read_token_with_UUID_format(self):
        from uuid import UUID

        upload = PdfUploadFactory()
        uuid = upload.uuid
        self.assertEqual(type(uuid), UUID)
        request_data = {
            'uuid': uuid,
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
            'expires_at': datetime(2021, 6, 10),
        }
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': upload.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)

    def test_read_token_with_custom_ttl(self):
        start_time = now()
        default_ttl = 900
        upload = PdfUploadFactory()
        request_data = {
            'uuid': upload.uuid,
            'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
            'custom_ttl': 1800,
        }
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': upload.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertTrue(
            (start_time + timedelta(seconds=default_ttl))
            < datetime.fromisoformat(token['expires_at'])
            < (now() + timedelta(seconds=request_data.get('custom_ttl')))
        )

    def test_upload_not_found(self):
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': '327b946a-4ee5-48a0-8403-c0b9e5dd84a3',
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_file_infected(self):
        upload = PdfUploadFactory(status=FileStatus.INFECTED.name)
        request_data = {'uuid': upload.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': upload.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 500)


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenViewWithAsyncPostProcessingTestCase(APITestCase, URLPatternsTestCase):
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
        self.client.raise_request_exception = False

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.img.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.img.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_img_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': None}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.text.uuid))
        self.assertIsNotNone(response.data.get('token'))

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
        self.client.raise_request_exception = False

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.CONVERT.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))
        self.assertIsNone(response.data.get('errors'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 422)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': None}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 422)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.text.uuid))
        self.assertIsNotNone(response.data.get('token'))

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

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.CONVERT.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.text.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(merge_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': None}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.pdf.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(merge_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': self.pdf.uuid,
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.base_input_object[0]))
        self.assertIsNotNone(response.data.get('token'))

    def test_read_token_with_bad_upload_uuid(self):
        wanted_post_process = None
        request_data = {'uuid': uuid.uuid4(), 'wanted_post_process': wanted_post_process}
        response = self.client.post(
            reverse(
                'osis_document:read-token',
                kwargs={
                    'pk': uuid.uuid4(),
                },
            ),
            data=request_data,
            follow=False,
        )
        self.assertEqual(response.status_code, 404)


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenViewWithSyncPostProcessingTestCase(APITestCase):
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

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=self.text.uuid), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.merge_output.uuid))

        request_data = {'uuid': self.img.uuid, 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=self.text.uuid), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.merge_output.uuid))

    def test_read_token_with_CONVERT_for_wanted_post_process(self):
        wanted_post_process = PostProcessingType.CONVERT.name
        request_data = {'uuid': self.img.uuid, 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=self.img.uuid), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_img_output.uuid))

    def test_read_token_without_wanted_post_process(self):
        wanted_post_process = None
        request_data = {'uuid': self.text.uuid, 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=self.text.uuid), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.merge_output.uuid))

    def test_read_token_with_ORIGINAL_for_wanted_post_process(self):
        wanted_post_process = PostProcessingWanted.ORIGINAL.name
        request_data = {'uuid': self.text.uuid, 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=self.text.uuid), data=request_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.text.uuid))

    def test_read_token_with_bad_upload_uuid(self):
        wanted_post_process = None
        request_data = {'uuid': uuid.uuid4(), 'wanted_post_process': wanted_post_process}
        response = self.client.post(resolve_url('read-token', pk=uuid.uuid4()), data=request_data)
        self.assertEqual(response.status_code, 404)
