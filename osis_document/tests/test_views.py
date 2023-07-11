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
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.core.files.base import ContentFile, File
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.utils.timezone import now
from osis_document.enums import FileStatus, TokenAccess, DocumentError, PostProcessingStatus, PostProcessingType, \
    PostProcessingWanted
from osis_document.models import Token, Upload
from osis_document.tests import QueriesAssertionsMixin
from osis_document.tests.document_test.models import TestDocument
from osis_document.tests.factories import ImageUploadFactory, PdfUploadFactory, ReadTokenFactory, WriteTokenFactory, \
    CorrectPDFUploadFactory, TextDocumentUploadFactory, MergePostProcessingFactory, ConvertPostProcessingFactory, \
    PendingPostProcessingAsyncFactory, DonePostProcessingAsyncFactory, FailedPostProcessingAsyncFactory
from rest_framework.test import APITestCase, URLPatternsTestCase

SMALLEST_PDF = b"""%PDF-1.
1 0 obj<</Pages 2 0 R>>endobj 2 0 obj<</Kids[3 0 R]/Count 1>>endobj 3 0 obj<</MediaBox[0 0 612 792]>>endobj trailer<</Root 1 0 R>>"""


@override_settings(ROOT_URLCONF='osis_document.urls')
class RequestUploadViewTestCase(TestCase):
    def test_request_upload_without_file(self):
        response = self.client.post(resolve_url('request-upload'), {})
        self.assertEqual(400, response.status_code)

    @override_settings(OSIS_DOCUMENT_ALLOWED_EXTENSIONS=['txt'])
    def test_request_upload_with_bad_extension(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(400, response.status_code)

    def test_request_upload_with_mime_smuggling(self):
        file = ContentFile(SMALLEST_PDF, 'foo.doc')
        response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(409, response.status_code)

    def test_request_upload_with_docx(self):
        with (Path(__file__).parent / 'test.docx').open('rb') as f:
            file = File(f, 'test.docx')
            response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(201, response.status_code)

    def test_upload(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        self.assertFalse(Upload.objects.exists())

        response = self.client.post(resolve_url('request-upload'), {'file': file})
        json = response.json()
        self.assertIn('token', json)
        self.assertTrue(Upload.objects.exists())
        self.assertTrue(Token.objects.exists())
        self.assertEqual(Upload.objects.first().status, FileStatus.REQUESTED.name)
        self.assertTrue(Token.objects.first().access, TokenAccess.WRITE.name)

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=['http://dummyurl.com/'])
    def test_cors(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        response = self.client.post(resolve_url('request-upload'), {'file': file}, HTTP_ORIGIN="http://dummyurl.com/")
        self.assertTrue(response.has_header("Access-Control-Allow-Origin"))
        response = self.client.post(resolve_url('request-upload'), {'file': file}, HTTP_ORIGIN="http://wrongurl.com/")
        self.assertFalse(response.has_header("Access-Control-Allow-Origin"))


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class ConfirmUploadViewTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(403, response.status_code)

    def test_confirm_upload(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)

    def test_confirm_upload_with_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'upload_to': 'custom-path/',
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we explicitly specified
        self.assertRegex(confirmed_upload.file.name, r'custom-path/')

    def test_confirm_upload_with_related_model_and_string_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'documents',
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'path/')

    def test_confirm_upload_with_related_model_and_callable_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'default_path/others/')

    def test_confirm_upload_with_related_model_and_callable_upload_to_based_on_instance(self):
        doc_pk = TestDocument.objects.create(documents=[WriteTokenFactory().upload_id]).pk
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'pk': doc_pk,
                    },
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'default_path/{}/'.format(doc_pk))

    def test_confirm_upload_with_unknown_related_model(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': 'unknown_app',
                    'model': 'unknown_model',
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown_app:unknown_model' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_related_model_field(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'unknown_field',
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown_field' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_instance_filters(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'unknown_filter': '',
                    },
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown field' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_instance(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'pk': -1,
                    },
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('Impossible to find one single object' in response.json()['related_model'][0])

    def test_bad_token(self):
        response = self.client.post(resolve_url('confirm-upload', token='foobar'))
        self.assertEqual(400, response.status_code)

    def test_read_token(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)

    def test_old_token(self):
        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenViewTestCase(APITestCase, URLPatternsTestCase):
    from django.urls import path, include

    app_name = 'osis_document'
    urlpatterns = [
        path('', include('osis_document.urls', namespace="osis_document")),
    ]

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        response = self.client.post(reverse('osis_document:write-token', kwargs={'pk': PdfUploadFactory().pk, }))
        self.assertEqual(response.status_code, 403)

    def test_write_token(self):
        response = self.client.post(reverse('osis_document:write-token', kwargs={'pk': PdfUploadFactory().pk, }))
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.WRITE.name)

    def test_read_token(self):
        upload = PdfUploadFactory()
        request_data = {'uuid': upload.uuid,
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
                        'expires_at': datetime(2021, 6, 10)
                        }
        response = self.client.post(reverse('osis_document:read-token', kwargs={
            'pk': upload.uuid, }), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertEqual(token['expires_at'], "2021-06-10T00:00:00")

    def test_read_token_with_custom_ttl(self):
        start_time = now()
        default_ttl = 900
        upload = PdfUploadFactory()
        request_data = {'uuid': upload.uuid,
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
                        'custom_ttl': 1800
                        }
        response = self.client.post(reverse('osis_document:read-token', kwargs={
            'pk': upload.uuid, }), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertTrue((start_time + timedelta(seconds=default_ttl)) < datetime.fromisoformat(token['expires_at']) < (
            now() + timedelta(seconds=request_data.get('custom_ttl'))))

    def test_upload_not_found(self):
        response = self.client.post(
            reverse('osis_document:read-token', kwargs={'pk': '327b946a-4ee5-48a0-8403-c0b9e5dd84a3', }), )
        self.assertEqual(response.status_code, 404)

    def test_file_infected(self):
        upload = PdfUploadFactory(status=FileStatus.INFECTED.name)
        request_data = {'uuid': upload.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': upload.uuid, }),
                                    data=request_data)
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
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
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
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name, }
        }
        PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )
        self.client.raise_request_exception = False

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.img.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.img.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_img_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 206)
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.text.uuid))
        self.assertIsNotNone(response.data.get('token'))

    def test_read_token_with_failed_async_post_processing(self):
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "errors":
                        {
                            "params": "[<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>]",
                            "messages": [
                                "La valeur « [<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>] » n’est pas un UUID valide."]
                        },
                    "status": PostProcessingStatus.FAILED.name
                }
        }
        FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )
        self.client.raise_request_exception = False

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.CONVERT.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))
        self.assertIsNone(response.data.get('errors'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 422)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 422)
        self.assertIsNotNone(response.data.get('errors'))
        self.assertIsNone(response.data.get('token'))
        self.assertIsNotNone(response.data.get('links'))

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.text.uuid))
        self.assertIsNotNone(response.data.get('token'))

    def test_read_token_with_done_async_post_processing(self):
        merge = MergePostProcessingFactory()
        merge_output = CorrectPDFUploadFactory()
        merge.input_files.add(self.convert_text_output, self.convert_img_output)
        merge.output_files.add(merge_output)
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_img_output.uuid, self.convert_text_output.uuid],
                    "post_processing_objects": [self.convert_img.uuid, self.convert_text.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [merge_output.uuid],
                    "post_processing_objects": [merge.uuid]
                },
        }
        DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'uuid': self.text.uuid, 'wanted_post_process': PostProcessingType.CONVERT.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.convert_text_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        self.client.raise_request_exception = False
        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingType.MERGE.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.text.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(merge_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': None}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.pdf.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(merge_output.uuid))
        self.assertIsNotNone(response.data.get('token'))

        request_data = {'uuid': self.base_input_object[0], 'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': self.pdf.uuid, }),
                                    data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['upload_id'], str(self.base_input_object[0]))
        self.assertIsNotNone(response.data.get('token'))

    def test_read_token_with_bad_upload_uuid(self):
        wanted_post_process = None
        request_data = {'uuid': uuid.uuid4(), 'wanted_post_process': wanted_post_process}
        response = self.client.post(reverse('osis_document:read-token', kwargs={'pk': uuid.uuid4(), }),
                                    data=request_data, follow=False)
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
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
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
        with self.assertNumQueriesLessThan(5):
            response = self.client.post(resolve_url('read-tokens'), data={'uuids': uploads_uuids})
        self.assertEqual(response.status_code, 201)
        tokens = response.json()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[uploads_uuids[0]]['access'], TokenAccess.READ.name)
        self.assertEqual(tokens[uploads_uuids[1]]['access'], TokenAccess.READ.name)

    def test_read_token_with_custom_ttl(self):
        start_time = now()
        default_ttl = 900
        uploads_uuids = [str(PdfUploadFactory().pk), str(PdfUploadFactory().pk)]
        request_data = {'uuids': uploads_uuids,
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name,
                        'custom_ttl': 3600
                        }
        response = self.client.post(resolve_url('read-tokens'), data=request_data)
        self.assertEqual(response.status_code, 201)
        tokens = response.json()
        for token in tokens:
            self.assertEqual(tokens[token]['access'], TokenAccess.READ.name)
            self.assertTrue((start_time + timedelta(seconds=default_ttl)) < datetime.fromisoformat(tokens[token]['expires_at']) < (
                now() + timedelta(seconds=request_data.get('custom_ttl'))))

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
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
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
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name, }
        }
        PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'uuids': [self.text.uuid, self.img.uuid],
                        'wanted_post_process': PostProcessingType.CONVERT.name}
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

        request_data = {'uuids': [self.text.uuid, self.img.uuid],
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
        response = self.client.post(reverse('osis_document:read-tokens'), data=request_data, follow=False)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), len(request_data['uuids']))
        for token_dict_key in response.data:
            self.assertIsNotNone(response.data[token_dict_key].get('token'))
            self.assertIn(response.data[token_dict_key].get('upload_id'), [str(self.text.uuid), str(self.img.uuid)])
            self.assertIsNone(response.data[token_dict_key].get('errors'))

    def test_read_token_with_failed_async_post_processing(self):
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "errors":
                        {
                            "params": "[<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>]",
                            "messages": [
                                "La valeur « [<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>] » n’est pas un UUID valide."]
                        },
                    "status": PostProcessingStatus.FAILED.name
                }
        }
        FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {
            'uuids': [self.text.uuid, self.img.uuid],
            'wanted_post_process': PostProcessingType.CONVERT.name
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

        request_data = {'uuids': [self.text.uuid, self.img.uuid],
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
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
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_img_output.uuid, self.convert_text_output.uuid],
                    "post_processing_objects": [self.convert_img.uuid, self.convert_text.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [merge_output.uuid],
                    "post_processing_objects": [merge.uuid]
                },
        }
        DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'uuids': [self.text.uuid, self.img.uuid],
                        'wanted_post_process': PostProcessingType.CONVERT.name}
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

        request_data = {'uuids': [self.text.uuid, self.img.uuid],
                        'wanted_post_process': PostProcessingWanted.ORIGINAL.name}
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
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
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


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataViewTestCase(APITestCase):
    def test_get_metadata(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertIn('mimetype', metadata)
        self.assertIn('hash', metadata)
        self.assertIn('name', metadata)
        self.assertIn('uploaded_at', metadata)

    def test_get_file_bad_token(self):
        response = self.client.get(resolve_url('get-metadata', token='token'))
        self.assertEqual(response.status_code, 404)

    def test_bad_hash(self):
        token = ReadTokenFactory(upload__metadata={'hash': 'badvalue'})
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 409)

    def test_change_metadata_read_only(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('change-metadata', token=token.token))
        self.assertEqual(response.status_code, 404)

    def test_change_metadata(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('change-metadata', token=token.token), {'name': 'foobar'})
        self.assertEqual(response.status_code, 200)
        upload = token.upload
        upload.refresh_from_db()
        self.assertEqual(upload.metadata['name'], 'foobar')


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataListViewTestCase(QueriesAssertionsMixin, APITestCase):
    def test_get_metadata(self):
        tokens = [ReadTokenFactory().token, ReadTokenFactory().token]
        with self.assertNumQueriesLessThan(4):
            response = self.client.post(resolve_url('get-several-metadata'), data=tokens)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertEqual(len(metadata), 2)
        for token in tokens:
            self.assertIn('mimetype', metadata[token])
            self.assertIn('hash', metadata[token])
            self.assertIn('name', metadata[token])
            self.assertIn('uploaded_at', metadata[token])

    def test_get_file_bad_token(self):
        tokens = ['bad-token']
        response = self.client.post(resolve_url('get-several-metadata'), data=tokens)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertEqual(len(metadata), 1)
        self.assertIn('error', metadata[tokens[0]])
        self.assertEqual(metadata[tokens[0]]['error']['code'], DocumentError.TOKEN_NOT_FOUND.name)
        self.assertEqual(metadata[tokens[0]]['error']['message'], DocumentError.TOKEN_NOT_FOUND.value)


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class RotateViewTestCase(APITestCase):
    def test_write_only(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertEqual(response.status_code, 404)

    def test_image_only(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertEqual(response.status_code, 400)

    def test_successfully_rotates(self):
        token = WriteTokenFactory(upload=ImageUploadFactory())
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertNotEqual(response.json()['token'], token.token)
        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FileViewTestCase(TestCase):
    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=[])
    def test_get_file(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('raw-file', token=token.token))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.has_header('Content-Security-Policy'))

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=['127.0.0.1'])
    def test_get_file_with_csp(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('raw-file', token=token.token))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Security-Policy'))
        self.assertNotIn('attachment', response['Content-Disposition'])

    def test_get_file_as_attachement(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('raw-file', token=token.token) + '?dl=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_get_file_bad_hash(self):
        token = ReadTokenFactory(upload__metadata={'hash': 'badvalue'})
        response = self.client.get(resolve_url('raw-file', token=token.token))
        self.assertEqual(response.status_code, 409)

    def test_get_file_bad_token(self):
        response = self.client.get(resolve_url('raw-file', token='token'))
        self.assertEqual(response.status_code, 404)

    def test_get_file_infected(self):
        token = ReadTokenFactory(upload__status=FileStatus.INFECTED.name)
        response = self.client.get(resolve_url('raw-file', token=token.token))
        self.assertEqual(response.status_code, 500)


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class DeclareFileInfectedViewTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.infected_file = PdfUploadFactory()
        self.infected_filepath = str(self.infected_file.file)
        self.url = resolve_url('declare-file-as-infected')

    def test_protected(self):
        self.client.defaults = {}
        response = self.client.post(self.url, {'path': self.infected_filepath})
        self.assertEqual(403, response.status_code)

    def test_declare_as_infected(self):
        response = self.client.post(self.url, {'path': self.infected_filepath})
        self.assertEqual(202, response.status_code)
        self.assertIn('uuid', response.json())

    def test_confirm_upload_with_unknown_path(self):
        response = self.client.post(self.url, {'path': 'foobar'})
        self.assertEqual(400, response.status_code)


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetProgressAsyncPostProcessingViewTestCase(APITestCase, URLPatternsTestCase):
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
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
        }
        self.convert_text = ConvertPostProcessingFactory()
        self.convert_text_output = CorrectPDFUploadFactory()
        self.convert_text.input_files.add(self.text)
        self.convert_text.output_files.add(self.convert_text_output)
        self.convert_img = ConvertPostProcessingFactory()
        self.convert_img_output = CorrectPDFUploadFactory()
        self.convert_img.input_files.add(self.img)
        self.convert_img.output_files.add(self.convert_img_output)

    def test_get_progress_of_PENDING_async_post_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name, }
        }
        async_post_process = PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': async_post_process.uuid
        }), data=request_data)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 50.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.DONE.name)

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': async_post_process.uuid
        }), data=request_data)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.PENDING.name)

    def test_get_progress_of_DONE_async_post_process(self):
        merge = MergePostProcessingFactory()
        merge_output = CorrectPDFUploadFactory()
        merge.input_files.add(self.convert_text_output, self.convert_img_output)
        merge.output_files.add(merge_output)
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_img_output.uuid, self.convert_text_output.uuid],
                    "post_processing_objects": [self.convert_img.uuid, self.convert_text.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [merge_output.uuid],
                    "post_processing_objects": [merge.uuid]
                },
        }
        async_post_process = DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': async_post_process.uuid
        }), data=request_data)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 100.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.DONE.name)

        request_data = {'pk': async_post_process.uuid}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': async_post_process.uuid
        }), data=request_data)
        self.assertIsNone(response.data.get('wanted_post_process_status'))

    def test_get_progress_of_FAILED_async_post_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name:
                {
                    "status": PostProcessingStatus.DONE.name,
                    "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                    "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid]
                },
            PostProcessingType.MERGE.name:
                {
                    "errors":
                        {
                            "params": "[<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>]",
                            "messages": [
                                "La valeur « [<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>] » n’est pas un UUID valide."]
                        },
                    "status": PostProcessingStatus.FAILED.name
                }
        }
        async_post_process = FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': str(async_post_process.uuid)
        }), data=request_data)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 50.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.FAILED.name)

    def test_get_progress_with_bad_uuid(self):
        request_data = {'pk': uuid.uuid4(), 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.post(reverse('osis_document:get-progress-post-processing', kwargs={
            'pk': uuid.uuid4()
        }), data=request_data)
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response.data.get('error'))
        self.assertIsNone(response.data.get('progress'))
        self.assertIsNone(response.data.get('wanted_post_process_status'))
