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
from unittest import mock

from django.core.files.base import ContentFile
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.datetime_safe import datetime
from rest_framework.test import APITestCase

from osis_document.enums import FileStatus, TokenAccess
from osis_document.models import Token, Upload
from osis_document.tests.factories import ImageUploadFactory, PdfUploadFactory, ReadTokenFactory, WriteTokenFactory


@override_settings(ROOT_URLCONF='osis_document.urls')
class RequestUploadViewTestCase(TestCase):
    def test_request_upload_without_file(self):
        response = self.client.post(resolve_url('request-upload'), {})
        self.assertEqual(400, response.status_code)

    def test_upload(self):
        file = ContentFile(b'hello world', 'foo.pdf')
        self.assertFalse(Upload.objects.exists())

        response = self.client.post(resolve_url('request-upload'), {'file': file})
        json = response.json()
        self.assertIn('token', json)
        self.assertTrue(Upload.objects.exists())
        self.assertTrue(Token.objects.exists())
        self.assertEqual(Upload.objects.first().status, FileStatus.REQUESTED.name)
        self.assertTrue(Token.objects.first().access, TokenAccess.WRITE.name)


@override_settings(ROOT_URLCONF="osis_document.urls",
                   OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
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


@override_settings(ROOT_URLCONF="osis_document.urls",
                   OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetTokenViewTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        response = self.client.post(resolve_url('write-token', pk=PdfUploadFactory().pk))
        self.assertEqual(response.status_code, 403)

    def test_write_token(self):
        response = self.client.post(resolve_url('write-token', pk=PdfUploadFactory().pk))
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.WRITE.name)

    def test_read_token(self):
        response = self.client.post(resolve_url('read-token', pk=PdfUploadFactory().pk), {
            'expires_at': datetime(2021, 6, 10)
        })
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertEqual(token['expires_at'], "2021-06-10T00:00:00")

    def test_upload_not_found(self):
        response = self.client.post(resolve_url('read-token', pk='327b946a-4ee5-48a0-8403-c0b9e5dd84a3'))
        self.assertEqual(response.status_code, 404)


@override_settings(ROOT_URLCONF='osis_document.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataViewTestCase(APITestCase):
    def test_get_metadata(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertIn('mimetype', metadata)
        self.assertIn('md5', metadata)
        self.assertIn('name', metadata)
        self.assertIn('uploaded_at', metadata)

    def test_get_file_bad_token(self):
        response = self.client.get(resolve_url('get-metadata', token='token'))
        self.assertEqual(response.status_code, 404)

    def test_bad_md5(self):
        token = ReadTokenFactory(upload__metadata={'md5': 'badvalue'})
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 409)

    def test_change_metadata_read_only(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('change-metadata', token=token.token))
        self.assertEqual(response.status_code, 404)

    def test_change_metadata(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('change-metadata', token=token.token), {
            'name': 'foobar'
        })
        self.assertEqual(response.status_code, 200)
        upload = token.upload
        upload.refresh_from_db()
        self.assertEqual(upload.metadata['name'], 'foobar')


@override_settings(ROOT_URLCONF='osis_document.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
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


@override_settings(ROOT_URLCONF='osis_document.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FileViewTestCase(TestCase):
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

    def test_get_file_bad_md5(self):
        token = ReadTokenFactory(upload__metadata={'md5': 'badvalue'})
        response = self.client.get(resolve_url('raw-file', token=token.token))
        self.assertEqual(response.status_code, 409)

    def test_get_file_bad_token(self):
        response = self.client.get(resolve_url('raw-file', token='token'))
        self.assertEqual(response.status_code, 404)
